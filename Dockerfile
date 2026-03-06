# Use a lightweight python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy main API code
COPY main.py .

# Expose port (80 for Azure standard deployment)
EXPOSE 80

# Run Uvicorn server on port 80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
