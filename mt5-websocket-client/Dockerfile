FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src/ ./src/

# Create directory for data
RUN mkdir -p /tmp/forex_data

# Set the environment variable for the Python output
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "src/main.py"]