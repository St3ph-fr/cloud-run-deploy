# 1. Use a Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    # Prevents Python from buffering stdout/stderr
    PORT=8080 \
    # Port Cloud Run expects the app to listen on
    GOOGLE_API_KEY="" \
    # Placeholder for API key - will be set via Cloud Run env vars
    # Set DEBIAN_FRONTEND to noninteractive to avoid prompts during apt-get install
    DEBIAN_FRONTEND=noninteractive

# 2. Install OS dependencies for Chrome and ChromeDriver
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Install Chrome
    wget \
    gnupg \
    # Add Google Chrome's repo key
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    # Add Google Chrome's repo
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    # Install Chrome and ChromeDriver
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    # Cleanup apt caches to reduce image size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome path (optional, often auto-detected but good for clarity)
ENV CHROME_BIN=/usr/bin/google-chrome-stable
# Note: ChromeDriver installed via apt usually lands in /usr/bin/chromedriver, which is in PATH

# 3. Set up the working directory
WORKDIR /app

# 4. Install Python dependencies
# Copy only requirements first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy application code
COPY . .

# 6. Expose the port the app runs on
EXPOSE ${PORT}

# 7. Define the command to run the application
# Use uvicorn to run the FastAPI app defined in main.py (main:app)
# --host 0.0.0.0 makes it accessible from outside the container
# --port ${PORT} uses the env var Cloud Run provides
# --workers 1 is recommended for Cloud Run Gen2 CPU=1, adjust if needed
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT}", "--workers", "1"]
