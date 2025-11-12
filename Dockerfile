# Use an official Python runtime as a parent image
FROM python:3.13-bookworm

# Set the working directory in the container, and initialize image.
WORKDIR /opt/magplex
COPY . .

RUN chmod +x docker/entrypoints/docker-entrypoint.sh

# Install Nginx
RUN apt-get update -y && \
    apt-get install -y nginx gettext-base && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY docker/nginx/nginx.conf.template /etc/nginx/templates/nginx.conf.template

# Install Intel Quick Sync driver
RUN apt update -y && \
    apt install -y intel-media-va-driver vainfo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Use Jellyfin FFmpeg build with QSV support
RUN apt-get update && apt-get install -y curl gnupg apt-transport-https && \
    curl -fsSL https://repo.jellyfin.org/debian/jellyfin_team.gpg.key \
    | gpg --dearmor -o /usr/share/keyrings/jellyfin-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/jellyfin-archive-keyring.gpg arch=$(dpkg --print-architecture)] \
    https://repo.jellyfin.org/debian bookworm main" > /etc/apt/sources.list.d/jellyfin.list && \
    apt-get update && \
    apt-get install -y jellyfin-ffmpeg7 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/lib/jellyfin-ffmpeg:${PATH}"

# Copy the requirements file and install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn
RUN pip install --no-cache-dir gunicorn

# Update the image build date.
RUN python docker/scripts/build_date.py

# Run the application.
ENTRYPOINT ["docker/entrypoints/docker-entrypoint.sh"]