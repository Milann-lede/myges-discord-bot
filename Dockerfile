FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (git is often needed for py packages)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py .
COPY myges_utils.py .
# We don't copy schedule_state.json to avoid overwriting with old state; it will be created if missing.

# Run the bot
CMD ["python", "bot.py"]
