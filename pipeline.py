from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

def run_research_pipeline(topic: str) -> dict:
    state={}

    # Search Agent Working
    print("\n" + "="*50)
    print("Step 1: Search agent is working...")
    print("="*50)

    search_agent = build_search_agent()
    search_result = search_agent.invoke({ # This is not a react_create_agent this is a create_agent so we have to structure the input in that format only 
        "messages": [("user", f"Find recent, reliable and detailed information about {topic}")]
    })
    state["search_results"]= search_result["messages"][-1].content
    print("\n Search Result ", state["search_results"])

    # Step 2: Reader agent 
    print("\n" + "="*50)
    print("Step 2: Reader agent is scraping top resources...")
    print("="*50)

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages":[("user",
        f"Based on the following search results about '{topic}',"
        f"Pick the most relevant URL and scrape it for deeper content. \n\n"
        f"Search Results: \n{state['search_results'][:800]}"
        )]
    })

    state['scraped_content']= reader_result['messages'][-1].content #-1 because we have to extract last meassega cause create_agent output is somewhat like this : {
    # "messages": [
    #     HumanMessage(content="What is the capital of France?"),
    #     AIMessage(content="", tool_calls=[{"name": "web_search", ...}]),
    #     ToolMessage(content="Title: Capital of France - Wikipedia..."),
    #     AIMessage(content="The capital of France is Paris.")
    # ]
# }
    print("\nscraped_content\n", state["scraped_content"])

    # Step 3- Writer chain
    # Check for Scraping Errors so we don't hallucinate on the error text
    if "Could not scrape URL:" in state["scraped_content"]:
        state["report"] = (
            f"I could not generate a report for '{topic}' because the scraped source failed to load.\n\n"
            f"Scraping error: {state['scraped_content']}"
        )
        print("\nFinal Report\n", state["report"])
        return state

    print("\n" + "="*50)
    print("Step 3: Writer is drafting the report...")
    print("="*50)

    #Combining the search results - like search agent brought links, reader agent dive deep so we have to combine both

    research_combine= (
        f"SEARCH RESULTS: /n {state['search_results']}\n\n"
        f"DETAILED SCRAPED CONTENT: /n {state['scraped_content']}"
    )

    state["report"]= writer_chain.invoke({
        "topic" : topic,
        "research" : research_combine 
    })

    print("\nFinal Report\n", state["report"])

    # Critic Report
    print("\n" + "="*50)
    print("Step 4: Critic is reviewing the report...")
    print("="*50)

    state["feedback"]=critic_chain.invoke({
        "report": state["report"]
    })

    print("\nCritic Report\n", state["feedback"])

    return state

# Call function with inputs
if __name__ =="__main__": # Type of thing whenever i have to call my pipeline.py
    topic = input("\n Enter a Research Topic: ")
    run_research_pipeline(topic)
