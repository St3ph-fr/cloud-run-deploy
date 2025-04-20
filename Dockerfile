# 1. Use a Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    GOOGLE_API_KEY="" \
    DEBIAN_FRONTEND=noninteractive

# 2. Install OS dependencies for Chrome and ChromeDriver
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    # Add Google Chrome's repo key and repo
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    # Install Chrome
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    # --- Install ChromeDriver ---
    # Get the latest stable ChromeDriver version matching Chrome stable
    && CHROME_DRIVER_VERSION=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$(google-chrome-stable --version | sed 's/.*Google Chrome \([0-9]*\.[0-9]*\.[0-9]*\).*/\1/')) \
    && echo "Using ChromeDriver version: $CHROME_DRIVER_VERSION" \
    && wget -q --continue -P /tmp https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip \
    && unzip -q /tmp/chromedriver_linux64.zip -d /usr/local/bin \
    && rm /tmp/chromedriver_linux64.zip \
    # Make chromedriver executable
    && chmod +x /usr/local/bin/chromedriver \
    # --- Cleanup ---
    && apt-get purge -y --auto-remove wget unzip gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/google-chrome.list

# Set Chrome path (optional, often auto-detected but good for clarity)
ENV CHROME_BIN=/usr/bin/google-chrome-stable
# Point Selenium to the driver if needed, though PATH should work  <-- MOVED COMMENT HERE
ENV CHROME_DRIVER_PATH=/usr/local/bin/chromedriver                 <-- ENV instruction without comment

# 3. Set up the working directory
WORKDIR /app

# 4. Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy application code
COPY . .

# 6. Expose the port the app runs on
EXPOSE ${PORT}

# 7. Define the command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT}", "--workers", "1"]
