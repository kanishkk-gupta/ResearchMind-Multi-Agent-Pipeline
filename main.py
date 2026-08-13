import asyncio
import sys
import threading
import contextlib
import queue
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from pipeline import run_research_pipeline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the UI folder statically
app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")

@app.get("/")
async def root():
    return RedirectResponse(url="/ui")

class TopicRequest(BaseModel):
    topic: str

class StreamCapture:
    def __init__(self, q: queue.Queue):
        self.q = q
        # Keep original stdout so it still prints to terminal!
        self.original_stdout = sys.__stdout__
        
    def write(self, data):
        if data:
            self.q.put(("stdout", data))
            self.original_stdout.write(data)
            self.original_stdout.flush()
            
    def flush(self):
        self.original_stdout.flush()

@app.post("/api/research")
async def research_endpoint(req: TopicRequest):
    q = queue.Queue()
    
    def run_pipeline():
        capture = StreamCapture(q)
        try:
            # Redirect stdout to capture everything printed by pipeline.py
            with contextlib.redirect_stdout(capture):
                result = run_research_pipeline(req.topic)
                q.put(("result", result))
        except Exception as e:
            q.put(("error", str(e)))
        finally:
            q.put(("done", None))
            
    thread = threading.Thread(target=run_pipeline)
    thread.start()
    
    async def event_generator():
        while True:
            try:
                # wait for items from the queue
                item_type, data = await asyncio.to_thread(q.get, timeout=1.0)
                if item_type == "done":
                    break
                elif item_type == "stdout":
                    yield f"event: stdout\ndata: {json.dumps(data)}\n\n"
                elif item_type == "result":
                    # Make sure the result dictionary is sent correctly
                    yield f"event: result\ndata: {json.dumps(data)}\n\n"
                elif item_type == "error":
                    yield f"event: error\ndata: {json.dumps(data)}\n\n"
            except queue.Empty:
                # Send a keep-alive comment to prevent connection timeout
                yield ": keep-alive\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
