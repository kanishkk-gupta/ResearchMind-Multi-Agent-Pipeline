document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('startBtn');
    const topicInput = document.getElementById('topicInput');
    const resultSection = document.getElementById('resultSection');
    
    // Tabs
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(btn.dataset.target).classList.add('active');
        });
    });
    
    const agents = [
        document.getElementById('agent-1'),
        document.getElementById('agent-2'),
        document.getElementById('agent-3'),
        document.getElementById('agent-4')
    ];
    
    const connectors = [
        document.getElementById('conn-1'),
        document.getElementById('conn-2'),
        document.getElementById('conn-3')
    ];

    startBtn.addEventListener('click', async () => {
        const topic = topicInput.value.trim();
        if (!topic) {
            alert('Please enter a research topic first.');
            return;
        }

        // Reset UI
        startBtn.disabled = true;
        startBtn.textContent = 'Pipeline Running...';
        resultSection.classList.remove('show');
        
        document.getElementById('reportContent').innerHTML = '';
        document.getElementById('criticContent').innerHTML = '';
        document.getElementById('scrapedContent').textContent = '';
        document.getElementById('searchContent').textContent = '';
        
        agents.forEach(a => {
            a.classList.remove('active', 'completed');
        });
        connectors.forEach(c => c.classList.remove('active'));

        // Start dynamic streaming
        await runDynamicPipeline(topic);
    });

    async function runDynamicPipeline(topic) {
        let currentAgentIndex = -1;

        const activateAgent = (index) => {
            if (currentAgentIndex >= 0 && currentAgentIndex < agents.length) {
                agents[currentAgentIndex].classList.remove('active');
                agents[currentAgentIndex].classList.add('completed');
                if (currentAgentIndex < connectors.length) {
                    connectors[currentAgentIndex].classList.add('active');
                }
            }
            currentAgentIndex = index;
            if (index < agents.length) {
                agents[index].classList.add('active');
            }
        };

        try {
            // Note: If you access index.html directly, this will call localhost:8000.
            // If you open it via localhost:8000/ui, relative paths would also work.
            const response = await fetch('http://localhost:8000/api/research', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic })
            });

            if (!response.body) throw new Error("ReadableStream not supported in this browser.");
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                
                const lines = buffer.split('\n\n');
                buffer = lines.pop(); // keep incomplete chunk
                
                for (const chunk of lines) {
                    if (chunk.startsWith('event: stdout')) {
                        const dataLine = chunk.split('\n').find(l => l.startsWith('data: '));
                        if (dataLine) {
                            const text = JSON.parse(dataLine.substring(6));
                            
                            // Match terminal prints to UI steps! Parallel execution matching.
                            if (text.includes("Step 1: Search agent is working")) {
                                activateAgent(0);
                            } else if (text.includes("Step 2: Reader agent is scraping")) {
                                activateAgent(1);
                            } else if (text.includes("Step 3: Writer is drafting")) {
                                activateAgent(2);
                            } else if (text.includes("Step 4: Critic is reviewing")) {
                                activateAgent(3);
                            }
                        }
                    } else if (chunk.startsWith('event: result')) {
                        const dataLine = chunk.split('\n').find(l => l.startsWith('data: '));
                        if (dataLine) {
                            const result = JSON.parse(dataLine.substring(6));
                            
                            // Finish the last agent
                            activateAgent(4); 
                            
                            await showResults(result);
                        }
                    } else if (chunk.startsWith('event: error')) {
                        const dataLine = chunk.split('\n').find(l => l.startsWith('data: '));
                        if (dataLine) {
                            console.error(JSON.parse(dataLine.substring(6)));
                            alert("An error occurred during pipeline execution. Check console.");
                        }
                        startBtn.disabled = false;
                        startBtn.textContent = 'Generate Report';
                    }
                }
            }
        } catch (err) {
            console.error("Pipeline error:", err);
            startBtn.disabled = false;
            startBtn.textContent = 'Generate Report';
        }
    }

    async function showResults(resultData) {
        startBtn.textContent = 'Report Complete';
        resultSection.classList.add('show');
        
        if (resultData) {
            // Render Markdown using marked.js
            document.getElementById('reportContent').innerHTML = marked.parse(resultData.report || "*No report generated.*");
            document.getElementById('criticContent').innerHTML = marked.parse(resultData.feedback || "*No feedback provided.*");
            
            // Raw content
            document.getElementById('scrapedContent').textContent = resultData.scraped_content || "No scraped content.";
            document.getElementById('searchContent').textContent = resultData.search_results || "No search results.";
        } else {
            document.getElementById('reportContent').innerHTML = "<p>Pipeline finished, but no data was returned.</p>";
        }
        
        setTimeout(() => {
            startBtn.disabled = false;
            startBtn.textContent = 'Generate New Report';
            topicInput.value = '';
        }, 1000);
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    topicInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            startBtn.click();
        }
    });
});
