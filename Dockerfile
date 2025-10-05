# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install ffmpeg and clean up cache
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn
RUN pip install --no-cache-dir gunicorn

# Copy the rest of the application code
COPY . .

# Expose the port that the Flask app will run on
EXPOSE 8080

# Define the command to run the application
CMD ["sh", "-c", "gunicorn --worker-class gthread -w $((2*$(nproc)+1)) --threads 8 -b 0.0.0.0:8080 main:app"]