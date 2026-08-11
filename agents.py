# Here we will just define agent not call !! Calling will be done in pipeline

from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
from dotenv import load_dotenv
load_dotenv()

# Model setup
llm = ChatMistralAI(model="mistral-small-2506", temperature=0)

# CREATING AGENTS : We'll not use prompting here cause we'll let the agent do full research !! we'll send that as a prompt then 

# First agent 
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search]
    )

# Second agent

def build_reader_agent():
    return create_agent(
        model= llm,
        tools= [scrape_url]
    )

# Creating Writer chain LCEL Pipleline - We'll use runnables
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports"),
    ("human","""Write a detailed research report on the topic below.

Topic: {topic}
Research Gathered: {research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional.""" )
])

# Creating Chain - Connecting all the runnables using a pipe

writer_chain = writer_prompt | llm | StrOutputParser()

# Critic Chain

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),    
    ("human", """Review the research report below and evaluate it strictly.

Report: {report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
...""" )
])

critic_chain = critic_prompt | llm | StrOutputParser()