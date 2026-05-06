FROM python:3.12-slim

WORKDIR /app

# Set environment variables for headless operation
ENV DISPLAY=:99
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for Chrome
RUN apt-get update && apt-get install -y \
    wget \
    zip \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

### install chrome and chromedriver with matching versions
# Install Google Chrome directly from deb package
RUN wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome.deb \
    && rm google-chrome.deb \
    && rm -rf /var/lib/apt/lists/*

# Create the expected directory structure for your app
RUN mkdir -p /snap/chromium/current/usr/lib/chromium-browser/ \
    && ln -s /usr/bin/google-chrome /snap/chromium/current/usr/lib/chromium-browser/chrome

# Install matching ChromeDriver version
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+') \
    && echo "Chrome version: $CHROME_VERSION" \
    && wget -O /tmp/chromedriver.zip "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_VERSION}.0/linux64/chromedriver-linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64

# Copy requirements first (changes less frequently)  
COPY ["requirements.txt", "./"]
RUN pip install -r requirements.txt

# Copy application code (changes more frequently)
COPY [".", "./"]

# Verify installations and create test user for Chrome security
RUN google-chrome --version && chromedriver --version \
    && useradd -m -s /bin/bash chromeuser \
    && mkdir -p /home/chromeuser \
    && chown -R chromeuser:chromeuser /app /home/chromeuser

EXPOSE 8000

# Switch to non-root user for security
USER chromeuser

CMD ["python", "main.py"]