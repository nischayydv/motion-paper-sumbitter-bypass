# Use the official Python slim image
FROM python:3.11-slim

# Install Chrome and dependencies using the modern GPG key method
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Add Google Chrome's GPG key and repository (without using apt-key)
RUN set -eux; \
    mkdir -p /etc/apt/keyrings; \
    wget -qO- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/keyrings/google-linux-signing-key.gpg; \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-linux-signing-key.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends google-chrome-stable; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

# Set Chrome binary location as an environment variable
ENV CHROME_BIN=/usr/bin/google-chrome-stable

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port (Render uses 10000 by default, but we'll let Gunicorn use the PORT env var)
EXPOSE 10000

# Start Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
