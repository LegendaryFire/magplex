# Use an official Python runtime as a parent image
FROM python:3.12-bookworm

# Install Intel Quick Sync driver
RUN apt update && \
    apt install -y intel-media-va-driver vainfo && \
    rm -rf /var/lib/apt/lists/*

# Use Jellyfin FFmpeg build with QSV support
RUN wget https://repo.jellyfin.org/files/ffmpeg/debian/latest-7.x/amd64/jellyfin-ffmpeg7_7.1.2-2-bookworm_amd64.deb && \
    dpkg -i jellyfin-ffmpeg7_7.1.2-2-bookworm_amd64.deb || apt-get update && apt-get install -y -f && \
    rm jellyfin-ffmpeg7_7.1.2-2-bookworm_amd64.deb

ENV PATH="/usr/lib/jellyfin-ffmpeg:${PATH}"

# Reset the working directory in the container
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