# MediaServerWeb

A Flask-based web interface for monitoring and controlling a media server with aria2 download management.

## Features

- Real-time download statistics monitoring
- File management for TV shows and movies (URLs and magnet links)
- Download control (pause/resume/purge)
- Log viewing and management
- Media loader process control
- Responsive web interface

## Requirements

- Python 3.x
- Flask 2.0+
- aria2p 0.11+
- aria2c daemon running on network

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure aria2c client connection in `MediaServerWeb.py` (default: 172.16.10.21:6800)

3. Update file paths in the MediaServerWeb class to match your media server setup

## Usage

### Development
```bash
python MediaServerWeb.py
```

### Production (systemd service)
```bash
# Install service
sudo cp mediaserverweb.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mediaserverweb

# Control service
sudo systemctl start mediaserverweb
sudo systemctl stop mediaserverweb
sudo systemctl restart mediaserverweb
```

### Manual script control
```bash
./MediaServerWeb.sh start|stop|restart
```

## API Endpoints

- `GET /` - Main web interface
- `GET /api/stats` - Download statistics
- `GET /api/files/<file_type>` - Get file contents (movie_magnet, movie_url, tv_magnet, tv_url, MediaLoaderLog, MediaLoaderRunLog)
- `POST /api/update_file` - Update file contents
- `POST /api/control/<action>` - Control downloads (pause_all, resume_all, purge, LaunchMediaLoader, clearlogs)

## Configuration

Default configuration assumes:
- Media server data at `/mnt/data/applications/MediaServer/data/`
- Logs at `/mnt/data/applications/MediaServer/log/`
- aria2c RPC at `172.16.10.21:6800`
- Web interface at `172.16.10.21:5000`

## File Structure

- `MediaServerWeb.py` - Main Flask application
- `templates/index.html` - Web interface template
- `mediaserverweb.service` - Systemd service file
- `MediaServerWeb.sh` - Control script
- `requirements.txt` - Python dependencies
