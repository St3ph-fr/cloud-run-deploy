import os
import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field # Ensure Pydantic V1 BaseModel if needed by Langchain
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
# Ensure browser_use and its dependencies are installed correctly
# from langchain.agents.agent_toolkits import PlayWrightBrowserToolkit # Example using Playwright
# from langchain.tools.playwright.utils import create_async_playwright_browser # Example using Playwright

# Using Selenium directly as 'browser_use' might refer to a specific implementation or concept
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# from langchain.tools import SeleniumBrowserTool # Example using a potential Selenium tool abstraction
# For direct interaction or simpler custom tool:
from bs4 import BeautifulSoup
import html2text

# For capturing logs within Langchain/Agent execution (if using standard agent)
from io import StringIO
import sys
from langchain.callbacks import StreamingStdOutCallbackHandler # Simple callback example

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file (mainly for local development)
load_dotenv()

# --- Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY environment variable not set. LLM calls will fail.")
    # raise ValueError("GOOGLE_API_KEY environment variable not set.") # Or raise error

# --- Global Variables ---
# We'll manage the browser lifecycle within the request or use a lifespan context
browser = None # Placeholder

# --- FastAPI Setup ---
# Use lifespan manager for resources like the browser if needed across requests (more complex)
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup: Initialize browser (example, might need refinement)
#     logger.info("Lifespan startup: Initializing browser...")
#     global browser
#     # browser = await initialize_browser() # Your browser init function
#     yield
#     # Shutdown: Cleanup browser
#     logger.info("Lifespan shutdown: Closing browser...")
#     # if browser:
#     #     await browser.close() # Your browser close function

# app = FastAPI(lifespan=lifespan) # Enable lifespan if using it
app = FastAPI() # Simpler setup without lifespan for now

# Mount static files (like script.js)
app.mount("/static", StaticFiles(directory="static"), name="static")
# Setup templates
templates = Jinja2Templates(directory="templates")

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)

class AgentResponse(BaseModel):
    logs: str
    final_answer: str

# --- Helper Functions ---

def get_selenium_driver():
    """Initializes and returns a Selenium WebDriver instance."""
    logger.info("Initializing Selenium WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome headlessly
    chrome_options.add_argument("--no-sandbox") # Required for running as root in Docker
    chrome_options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    chrome_options.add_argument("--disable-gpu") # Applicable to Windows, but good practice
    chrome_options.add_argument("--window-size=1920,1080") # Specify window size

    # Assumes chromedriver is in PATH (installed via apt in Dockerfile)
    # service = Service(executable_path='/usr/bin/chromedriver') # Explicit path if needed
    try:
        # driver = webdriver.Chrome(service=service, options=chrome_options)
        driver = webdriver.Chrome(options=chrome_options) # Simpler if chromedriver is in PATH
        logger.info("Selenium WebDriver initialized successfully.")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Selenium WebDriver: {e}")
        raise

async def run_browser_task(query: str) -> AgentResponse:
    """
    Runs the browser automation task using LangChain and Selenium.
    This is a simplified example. A real implementation would use LangChain agents/tools.
    """
    logs = StringIO()
    # Redirect stdout to capture prints (basic logging)
    # More robust logging would use Langchain callbacks
    # old_stdout = sys.stdout
    # sys.stdout = logs

    final_answer = "Default Answer: Task needs implementation."
    driver = None # Ensure driver is defined

    try:
        # 1. Initialize LLM
        llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_API_KEY, temperature=0.2)
        logs.write("LLM Initialized: Google Gemini Pro\n")
        logger.info("LLM Initialized.")

        # 2. Initialize Selenium Browser
        # Run blocking Selenium init in a separate thread to avoid blocking FastAPI event loop
        driver = await asyncio.to_thread(get_selenium_driver)
        logs.write("Selenium WebDriver Initialized (Headless Chrome)\n")
        logger.info("Selenium driver obtained.")

        # 3. Simplified "Agent" Logic (Replace with actual LangChain Agent/Tool usage)
        # This is a placeholder to show browser interaction
        logs.write(f"Received query: {query}\n")
        logger.info(f"Processing query: {query}")

        # Example: Navigate based on query (very basic interpretation)
        target_url = "https://www.google.com" # Default
        if "bbc weather" in query.lower():
             target_url = "https://www.bbc.co.uk/weather"
        elif "google search" in query.lower():
            # You'd typically extract the search term here
             target_url = "https://www.google.com/search?q=example"
        else:
             logs.write("Query not recognized for specific URL, going to Google.\n")


        logs.write(f"Navigating to: {target_url}\n")
        logger.info(f"Navigating to: {target_url}")
        await asyncio.to_thread(driver.get, target_url) # Run blocking I/O in thread

        # Wait briefly for page load (replace with explicit waits in real code)
        await asyncio.sleep(2)

        # Get page content
        logs.write("Fetching page content...\n")
        logger.info("Fetching page source.")
        page_source = await asyncio.to_thread(lambda: driver.page_source) # Run blocking I/O in thread

        # Extract text using BeautifulSoup and html2text (common in browser tools)
        soup = BeautifulSoup(page_source, 'html.parser')
        text_content = html2text.html2text(soup.prettify())
        logs.write(f"Page content retrieved (length: {len(text_content)} chars).\n")
        logger.info(f"Page content length: {len(text_content)}")

        # Simulate passing content to LLM for summarization/answer
        # In a real agent, the LLM would decide actions (click, type, scroll, summarize)
        logs.write("Simulating LLM processing of page content...\n")
        logger.info("Simulating LLM interaction.")
        # Example prompt (replace with actual LLM call)
        prompt = f"Based on the following content from {target_url}, answer the query: '{query}'\n\nContent:\n{text_content[:2000]}..." # Truncate for prompt
        # llm_response = await llm.ainvoke(prompt) # Actual async LLM call
        # final_answer = llm_response.content
        await asyncio.sleep(1) # Simulate LLM processing time
        final_answer = f"Based on content from {target_url}, the answer to '{query}' would be processed here. (Content length: {len(text_content)})"
        logs.write("LLM simulation complete.\n")
        logger.info("LLM simulation done.")


    except Exception as e:
        logger.error(f"Error during browser task execution: {e}", exc_info=True)
        logs.write(f"\n--- ERROR ---\n{type(e).__name__}: {e}\n")
        final_answer = f"An error occurred: {e}"
        # Ensure response indicates failure
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {e}")

    finally:
        # sys.stdout = old_stdout # Restore stdout
        if driver:
            logger.info("Closing Selenium WebDriver.")
            # Run blocking close in thread
            await asyncio.to_thread(driver.quit)
            logs.write("Selenium WebDriver closed.\n")
        else:
            logs.write("Selenium WebDriver was not initialized or failed to initialize.\n")


    # --- Construct Response ---
    log_content = logs.getvalue()
    return AgentResponse(logs=log_content, final_answer=final_answer)


# --- FastAPI Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    """Serves the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/run", response_model=AgentResponse)
async def handle_run_query(request: QueryRequest):
    """Handles the query submission, runs the agent, and returns results."""
    logger.info(f"Received query via /run endpoint: {request.query}")
    if not GOOGLE_API_KEY:
         raise HTTPException(status_code=500, detail="Server configuration error: GOOGLE_API_KEY not set.")
    try:
        result = await run_browser_task(request.query)
        return result
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions (like 500 errors from the task)
        raise http_exc
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error in /run endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {e}")

# --- Main execution (for local testing) ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server locally on http://127.0.0.1:8000")
    # Use port 8000 for local dev, Cloud Run uses $PORT (default 8080)
    uvicorn.run(app, host="127.0.0.1", port=8000)
