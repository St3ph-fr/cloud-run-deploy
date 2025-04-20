# 1. Use a Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    GOOGLE_API_KEY="" \
    DEBIAN_FRONTEND=noninteractive

# 2. Install OS dependencies
# Step 2.1: Update apt cache and install essential tools + common Chrome deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    # Add other common dependencies if needed, but start minimal
    # Example: libu2f-udev libvulkan1 added based on some recommendations
    # libu2f-udev \
    # libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# Step 2.2: Download and install Google Chrome stable using apt install
RUN echo "Downloading Google Chrome..." \
    && wget --progress=dot:giga -O /tmp/google-chrome-stable_current_amd64.deb \
       https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && echo "Updating package lists before installing Chrome..." \
    && apt-get update \
    && echo "Installing downloaded Chrome package via apt (handles dependencies)..." \
    # Use apt install directly on the .deb file
    && apt-get install -y --no-install-recommends /tmp/google-chrome-stable_current_amd64.deb \
    && echo "Cleaning up apt lists and downloaded Chrome package..." \
    && rm -rf /var/lib/apt/lists/* \
    && rm /tmp/google-chrome-stable_current_amd64.deb \
    && echo "Chrome installation step finished."

# Step 2.3: Install ChromeDriver matching the installed Chrome version
RUN CHROME_MAJOR_VERSION=$(google-chrome-stable --version | sed 's/Google Chrome \([0-9]*\)\..*/\1/') \
    && echo "Detected Chrome major version: $CHROME_MAJOR_VERSION" \
    # Find the latest chromedriver version for the detected major Chrome version
    && CHROME_DRIVER_VERSION=$(wget -qO- "https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build.json" | grep "\"${CHROME_MAJOR_VERSION}\." | sed -E 's/.*"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)".*/\1/') \
    && echo "Attempting to download ChromeDriver version: $CHROME_DRIVER_VERSION" \
    && if [ -z "$CHROME_DRIVER_VERSION" ]; then echo "Error: Could not automatically determine ChromeDriver version."; exit 1; fi \
    && echo "Downloading ChromeDriver..." \
    && wget --progress=dot:giga -O /tmp/chromedriver-linux64.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_DRIVER_VERSION}/linux64/chromedriver-linux64.zip" \
    && echo "Unzipping ChromeDriver..." \
    && unzip -q /tmp/chromedriver-linux64.zip -d /tmp \
    # Move chromedriver to /usr/local/bin
    && echo "Moving ChromeDriver to /usr/local/bin..." \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    # Clean up temp files/dirs
    && echo "Cleaning up ChromeDriver temp files..." \
    && rm /tmp/chromedriver-linux64.zip \
    && rm -rf /tmp/chromedriver-linux64 \
    # Make chromedriver executable
    && echo "Making ChromeDriver executable..." \
    && chmod +x /usr/local/bin/chromedriver \
    && echo "ChromeDriver installation finished."

# Set Chrome path (optional, often auto-detected but good for clarity)
ENV CHROME_BIN=/usr/bin/google-chrome-stable
# Point Selenium to the driver if needed, though PATH should work
ENV CHROME_DRIVER_PATH=/usr/local/bin/chromedriver

# 3. Set up the working directory
WORKDIR /app

# 4. Install Python dependencies
COPY requirements.txt ./
# Add --verbose flag to pip install for more detailed output if needed
RUN echo "Installing Python dependencies from requirements.txt..." \
    && pip install --no-cache-dir -r requirements.txt --verbose \
    && echo "Python dependencies installed."

# 5. Copy application code
COPY . .

# 6. Expose the port the app runs on
EXPOSE ${PORT}

# 7. Define the command to run the application (using shell form for env var substitution)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1
