# LangChain Browser Agent on Cloud Run

This project deploys a Python application to Google Cloud Run featuring a web interface that allows users to submit queries to a LangChain agent. The agent utilizes Google's Gemini Pro LLM and Selenium to interact with a web browser (headless Chrome) to perform tasks based on the user's query.

**Features:**

*   Web interface for submitting queries.
*   Displays action logs from the agent's execution.
*   Shows the final answer derived by the agent.
*   Uses LangChain with Google GenAI (Gemini Pro).
*   Performs browser automation using Selenium and headless Chrome.
*   Containerized with Docker for deployment on Cloud Run.

**Warning:** This application allows interaction with the live internet based on user input processed by an LLM. This carries inherent risks. **Do not expose this service publicly without proper authentication, authorization, and careful consideration of the potential security implications.** The LLM might interpret queries in unexpected ways, leading to unintended browser actions.

## Deploy to Cloud Run

[![Run on Google Cloud](https://deploy.cloud.run/button.svg)](https://deploy.cloud.run)

**Clicking the button will:**

1.  Require you to log into your Google Cloud account.
2.  Ask you to select a Google Cloud project.
3.  Prompt you to configure the deployment settings.

**Manual Deployment Steps (using gcloud):**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
    cd YOUR_REPO_NAME
    ```
    *(Replace `YOUR_USERNAME/YOUR_REPO_NAME` with your actual GitHub repo)*

2.  **Set up Google Cloud SDK:** Make sure `gcloud` is installed and configured.
    ```bash
    gcloud auth login
    gcloud config set project YOUR_PROJECT_ID
    ```

3.  **Enable necessary APIs:**
    ```bash
    gcloud services enable run.googleapis.com
    gcloud services enable artifactregistry.googleapis.com
    gcloud services enable aiplatform.googleapis.com
    # Add others if needed (e.g., Secret Manager)
    ```

4.  **Build and Deploy:**
    *   **IMPORTANT:** You **must** set the `GOOGLE_API_KEY` environment variable during deployment. Replace `YOUR_GOOGLE_API_KEY_HERE` with your actual key. Consider using Secret Manager for better security in production.
    *   Adjust `--region`, `--memory`, and `--cpu` as needed. Selenium + Chrome can be resource-intensive. Start with at least 1Gi memory.

    ```bash
    gcloud run deploy langchain-browser-agent \
        --source . \
        --region us-central1 \
        --platform managed \
        --allow-unauthenticated \
        --memory=1Gi \
        --cpu=1 \
        --set-env-vars="GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE"
        # Consider '--no-allow-unauthenticated' and setting up IAM or IAP for security
    ```

5.  **Access the Service:** Once deployed, `gcloud` will provide the URL for your service.

## Configuration

*   **`GOOGLE_API_KEY`**: Your API key for Google AI Studio (Gemini). This **must** be provided as an environment variable during Cloud Run deployment. For local development, create a `.env` file from `.env.example` and add your key there.
*   **Cloud Run Settings:**
    *   **Memory:** At least 1Gi is recommended due to Chrome's memory usage.
    *   **CPU:** 1 vCPU might be sufficient, but monitor performance.
    *   **Timeout:** Increase the request timeout if browser tasks take longer than the default (e.g., `--timeout=300`).
    *   **Concurrency:** Keep concurrency low (e.g., `--concurrency=1` or slightly higher) as each instance runs a full browser.

## Local Development

1.  **Prerequisites:**
    *   Python 3.10+
    *   Pip
    *   Google Chrome browser installed locally.
    *   ChromeDriver installed locally and available in your system's PATH. Ensure its version matches your Chrome version.
    *   Virtual environment tool (like `venv`).

2.  **Setup:**
    ```bash
    # Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`

    # Install dependencies
    pip install -r requirements.txt

    # Create .env file and add your API key
    cp .env.example .env
    # (Edit .env and add your GOOGLE_API_KEY)
    ```

3.  **Run the FastAPI server:**
    ```bash
    python main.py
    # or using uvicorn for live reload during development:
    # uvicorn main:app --reload --port 8000
    ```

4.  **Access:** Open your web browser to `http://127.0.0.1:8000`.

## Project Structure
