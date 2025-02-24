# Stage 1: Build environment
FROM python:3.11 AS builder
WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Smaller Final Image
FROM python:3.11-alpine
WORKDIR /app

# ✅ Install necessary dependencies
RUN apk add --no-cache ffmpeg flac

# Copy installed Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy all app files
COPY . .

# Run Flask
CMD ["python", "app.py"]
