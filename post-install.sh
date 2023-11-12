#!/bin/bash

# Backup existing nginx.conf
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

# Download nginx.conf from the provided URL
sudo wget -O /etc/nginx/nginx.conf https://raw.githubusercontent.com/chimerako/server/master/nginx.conf?token=GHSAT0AAAAAACKFQ7XV3KXEH24R5HIT6EOIZKQKADQ

# Download live.conf from the provided URL
sudo wget -O /etc/nginx/sites-enabled/live.conf https://raw.githubusercontent.com/chimerako/server/master/live.conf?token=GHSAT0AAAAAACKFQ7XU7EZZYXF6T5QDWZRIZKQJ7KA

# Change ownership of /mnt/hls to www-data
sudo mkdir /mnt/hls
sudo chown -R www-data:www-data /mnt/hls

# Install streamlink
sudo apt-get update
sudo apt-get install -y streamlink

# Install youtube-dl
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/youtube-dlp
sudo chmod a+rx /usr/local/bin/youtube-dlp

# Download and install the latest version of FFmpeg
cd /usr/bin
sudo wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
sudo tar xvf ffmpeg-release-amd64-static.tar.xz
sudo cp ffmpeg-*-amd64-static/ffmpeg /usr/bin/ffmpeg
sudo cp ffmpeg-*-amd64-static/ffprobe /usr/bin/ffprobe
sudo chmod +x /usr/bin/ffmpeg /usr/bin/ffprobe

# Clean up downloaded files
sudo rm -rf ffmpeg-*-amd64-static ffmpeg-release-amd64-static.tar.xz

# Test nginx configuration for errors
sudo nginx -t

# Reload nginx to apply changes
sudo systemctl reload nginx
