from langchain.tools import tool #This is going to be the decorator
from langchain.text_splitter import CharacterTextSplitter
import requests # python libraray that sends http request to the websites
from bs4 import BeautifulSoup # Lib of python to scrape or to parse HTML 
from tavily import TavilyClient # we can fetch data with the help of tavilyclient
import os 
from rich import print
from dotenv import load_dotenv
load_dotenv()

# =========================================================
# Tool 1: Tavily
# =========================================================

# Load Tavily Client
tavily = TavilyClient(api_key= os.getenv("TAVILY_API_KEY"))

# Create our Tool
# Creating a function

@tool # Langchain create normal python function to ai agent usable tool
def web_search(query : str) -> str: # input is query that is string type and output is also string type
    """Search the web for Recent and Reliable information on a topic. Returns Titles, URLS and Snippets""" # Docstring (normal description but with @tool it has one more important that it helps LLM to know the info of the tool)
    results= tavily.search(query=query, max_results=5) # query = "latest news"

    # We have to save Results
    out =[] # Empty List named out
    for r in results["results"]: # Jo panch results the unpe technically humne loop chlaya

        out.append( #append adds items to the end of the list
            f"Title : {r["title"]}\n"
            f"URL: {r['url']}\n"
            f"Snippet:{r['content'][:300]}\n"  # :300 is content's first 300 chars
            )
        
    return "\n----\n".join(out) # Join add list's items to the string, separator is decided by us "\n---------\n"

# print(web_search.invoke("What are the latest news on Jharkhand Student Protests"))

# =========================================================
# Tool 2: BeautifulSoup
# =========================================================

@tool
def scrape_url(url: str)-> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    try:
        # resp = requests.get(url)
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"}) #Sending request to website to to get the webpage from url, timeout= 8 wait for maximum 8 seconds, headers={"User-Agent": "Mozilla/5.0"} sends additional info to the website with request. Some websites block python like function so User-Agent se request thodi browser-like dikhti hai.

        # Now we have the website's html text 

        soup = BeautifulSoup(resp.text, "html.parser") # resp.text is basically readbale thing that gets the html in readble text formt with all the tagss like script, style bla bla and html parser is telling beautiful soup that the data which is coming is html type to please parse it with th html rules only

        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose() # remove those html elements completely

        text = soup.get_text(separator=" ", strip=True) # get_text() tells bs to remove the html tags and give text in readable format, separator is giving space between differnet element, strip= true cleans the extra/unnecssary white spaces

        splitter = CharacterTextSplitter(chunk_size=3000, chunk_overlap=200, separator=" ")
        chunks = splitter.split_text(text)
        return chunks[0]
    
    except Exception as e:
        return f"Could not scrape URL: {str(e)}" 

# print(scrape_url.invoke("https://www.hindustantimes.com/cricket/players/virat-kohli-3993/news"))





