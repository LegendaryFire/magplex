# Use an official Python runtime as a parent image
FROM python:3.13-bookworm

# Set the working directory in the container, and initialize image.
WORKDIR /opt/magplex
COPY . .

RUN chmod +x docker/entrypoints/docker-entrypoint.sh

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
RUN wget https://repo.jellyfin.org/files/ffmpeg/debian/latest-7.x/amd64/jellyfin-ffmpeg7_7.1.2-3-bookworm_amd64.deb && \
    dpkg -i jellyfin-ffmpeg7_7.1.2-3-bookworm_amd64.deb || apt update && \
    apt install -y -f && \
    rm jellyfin-ffmpeg7_7.1.2-3-bookworm_amd64.deb

ENV PATH="/usr/lib/jellyfin-ffmpeg:${PATH}"

# Copy the requirements file and install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn
RUN pip install --no-cache-dir gunicorn

# Update the image build date.
RUN python docker/scripts/build_date.py

# Run the application.
ENTRYPOINT ["docker/entrypoints/docker-entrypoint.sh"]