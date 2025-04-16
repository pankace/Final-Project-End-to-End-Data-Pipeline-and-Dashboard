FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY src/ ./src/
COPY dashboard/ ./dashboard/

# Expose the port for the dashboard
EXPOSE 5000

# Command to run the dashboard application
CMD ["python", "dashboard/app.py"]