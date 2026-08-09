# Use the official Python slim image
FROM python:3.11-slim

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

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
