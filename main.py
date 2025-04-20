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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import html2text

from io import StringIO
import sys
from langchain.callbacks import StreamingStdOutCallbackHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Starting application setup...") # Added startup log

# Load environment variables from .env file (mainly for local development)
load_dotenv()

# --- Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PORT = os.getenv("PORT", "8080") # Get PORT env var, default to 8080 for local

if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY environment variable not set. LLM calls will fail.")
    # Consider raising an error if the key is absolutely essential for startup
    # raise ValueError("GOOGLE_API_KEY environment variable not set.")

# --- Global Variables ---
browser = None

# --- FastAPI Setup ---
app = FastAPI()
logger.info("FastAPI app instance created.")

# Mount static files (like script.js)
app.mount("/static", StaticFiles(directory="static"), name="static")
logger.info("Static files mounted.")
# Setup templates
templates = Jinja2Templates(directory="templates")
logger.info("Templates configured.")

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
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # ChromeDriver should be in PATH now due to Dockerfile changes
    # service = Service(executable_path='/usr/local/bin/chromedriver') # Explicit path if needed
    try:
        # driver = webdriver.Chrome(service=service, options=chrome_options)
        driver = webdriver.Chrome(options=chrome_options) # Should find chromedriver in PATH
        logger.info("Selenium WebDriver initialized successfully.")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Selenium WebDriver: {e}", exc_info=True)
        raise

async def run_browser_task(query: str) -> AgentResponse:
    """
    Runs the browser automation task using LangChain and Selenium.
    This is a simplified example. A real implementation would use LangChain agents/tools.
    """
    logs = StringIO()
    final_answer = "Task processing started..."
    driver = None

    try:
        # 1. Initialize LLM
        llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_API_KEY, temperature=0.2)
        logs.write("LLM Initialized: Google Gemini Pro\n")
        logger.info("LLM Initialized.")

        # 2. Initialize Selenium Browser
        driver = await asyncio.to_thread(get_selenium_driver)
        logs.write("Selenium WebDriver Initialized (Headless Chrome)\n")
        logger.info("Selenium driver obtained.")

        # 3. Simplified "Agent" Logic
        logs.write(f"Received query: {query}\n")
        logger.info(f"Processing query: {query}")

        target_url = "https://www.google.com"
        if "bbc weather" in query.lower():
             target_url = "https://www.bbc.co.uk/weather"
        elif "google search" in query.lower():
             target_url = "https://www.google.com/search?q=example"
        else:
             logs.write("Query not recognized for specific URL, going to Google.\n")

        logs.write(f"Navigating to: {target_url}\n")
        logger.info(f"Navigating to: {target_url}")
        await asyncio.to_thread(driver.get, target_url)
        await asyncio.sleep(2) # Replace with explicit waits

        logs.write("Fetching page content...\n")
        logger.info("Fetching page source.")
        page_source = await asyncio.to_thread(lambda: driver.page_source)

        soup = BeautifulSoup(page_source, 'html.parser')
        text_content = html2text.html2text(soup.prettify())
        logs.write(f"Page content retrieved (length: {len(text_content)} chars).\n")
        logger.info(f"Page content length: {len(text_content)}")

        logs.write("Simulating LLM processing of page content...\n")
        logger.info("Simulating LLM interaction.")
        prompt = f"Based on the following content from {target_url}, answer the query: '{query}'\n\nContent:\n{text_content[:2000]}..."
        # llm_response = await llm.ainvoke(prompt)
        # final_answer = llm_response.content
        await asyncio.sleep(1)
        final_answer = f"Based on content from {target_url}, the answer to '{query}' would be processed here. (Content length: {len(text_content)})"
        logs.write("LLM simulation complete.\n")
        logger.info("LLM simulation done.")

    except Exception as e:
        logger.error(f"Error during browser task execution: {e}", exc_info=True)
        logs.write(f"\n--- ERROR ---\n{type(e).__name__}: {e}\n")
        final_answer = f"An error occurred during processing: {e}"
        # Don't raise HTTPException here, return error info in the response object
        # raise HTTPException(status_code=500, detail=f"Agent execution failed: {e}")

    finally:
        if driver:
            logger.info("Closing Selenium WebDriver.")
            try:
                await asyncio.to_thread(driver.quit)
                logs.write("Selenium WebDriver closed.\n")
            except Exception as e:
                logger.error(f"Error closing Selenium WebDriver: {e}", exc_info=True)
                logs.write(f"Error closing Selenium WebDriver: {e}\n")
        else:
            logs.write("Selenium WebDriver was not initialized or failed to initialize.\n")

    log_content = logs.getvalue()
    return AgentResponse(logs=log_content, final_answer=final_answer)


# --- FastAPI Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def get_root_html(request: Request):
    """Serves the main HTML page."""
    logger.info("Serving index.html")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/_health", status_code=200) # Or use "/" if preferred, but /_health avoids conflict
async def health_check():
    """Simple health check endpoint for Cloud Run."""
    logger.debug("Health check endpoint called")
    return {"status": "ok"}

@app.post("/run", response_model=AgentResponse)
async def handle_run_query(request: QueryRequest):
    """Handles the query submission, runs the agent, and returns results."""
    logger.info(f"Received query via /run endpoint: {request.query}")
    if not GOOGLE_API_KEY:
         # Return a structured error instead of raising HTTPException immediately
         # This allows logs to be potentially captured and returned
         error_msg = "Server configuration error: GOOGLE_API_KEY not set."
         logger.error(error_msg)
         return AgentResponse(logs=error_msg, final_answer="Configuration Error")
         # Or raise: raise HTTPException(status_code=500, detail=error_msg)

    try:
        result = await run_browser_task(request.query)
        return result
    # Removed broad Exception catch here - let run_browser_task handle errors and return AgentResponse
    # Errors during driver init are now raised by get_selenium_driver and caught by FastAPI default handler
    except Exception as e:
         # Catch any unexpected errors *outside* run_browser_task if they occur
         logger.error(f"Unexpected error in /run endpoint handler: {e}", exc_info=True)
         # Return error information in the response model
         return AgentResponse(logs=f"Unexpected server error: {e}", final_answer="Server Error")
         # Or raise: raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {e}")


# --- Main execution (for local testing) ---
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Uvicorn server locally on http://127.0.0.1:{PORT}")
    # Use the PORT variable consistent with Cloud Run expectation
    uvicorn.run("main:app", host="127.0.0.1", port=int(PORT), reload=True) # Added reload for local dev

logger.info("Application setup complete. Ready to accept requests.") # Added final setup log
