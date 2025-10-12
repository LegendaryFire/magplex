# Use an official Python runtime as a parent image
FROM python:3.12-bookworm

# Copy entrypoint to image
COPY docker/entrypoints/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Copy Gunicorn config to image
COPY docker/scripts/gunicorn.conf.py /gunicorn.conf.py

# Install Nginx
RUN apt-get update && \
    apt-get install -y nginx gettext-base && \
    rm -rf /var/lib/apt/lists/*

COPY docker/nginx/nginx.conf.template /etc/nginx/templates/nginx.conf.template

# Install Intel Quick Sync driver
RUN apt update && \
    apt install -y intel-media-va-driver vainfo && \
    rm -rf /var/lib/apt/lists/*

# Use Jellyfin FFmpeg build with QSV support
RUN wget https://repo.jellyfin.org/files/ffmpeg/debian/latest-7.x/amd64/jellyfin-ffmpeg7_7.1.2-2-bookworm_amd64.deb && \
    dpkg -i jellyfin-ffmpeg7_7.1.2-2-bookworm_amd64.deb || apt update && \
    apt install -y -f && \
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

ENTRYPOINT ["/docker-entrypoint.sh"]