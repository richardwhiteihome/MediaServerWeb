"""Media server web tool"""

import time
from flask import Flask, render_template, jsonify, request
import aria2p
from paramiko import SSHClient


app = Flask(__name__)


class MediaServerWeb:
    """Web monitor tool for mediaServer"""

    def __init__(self):
        self.tv_file = "/mnt/data/applications/MediaServer/data/tv_urls"
        self.tv_magnet_file = "/mnt/data/applications/MediaServer/data/tv_magnet_urls"
        self.movie_magnet_file = "/mnt/data/applications/MediaServer/data/movie_magnet_urls"
        self.movie_file = "/mnt/data/applications/MediaServer/data/movie_urls"
        self.log_file = "/mnt/data/applications/MediaServer/log/MediaLoader.log"

        self.ssh_pool = None
        self.init_ssh_pool()

        self.file_cache = {}
        self.cache_timeout = 30
        self.aria2_client = None

    def init_ssh_pool(self):
        """Initialize SSH connection pool"""
        self.ssh_pool = SSHClient()
        self.ssh_pool.load_system_host_keys()
        self.ssh_pool.connect("mustang", username="adm-user")

    def get_urls_from_file(self, file_name):
        """Main processing file loader with caching"""
        current_time = time.time()

        if file_name in self.file_cache:
            cache_time, urls = self.file_cache[file_name]
            if current_time - cache_time < self.cache_timeout:
                return urls

        urls = []
        try:
            sftp = self.ssh_pool.open_sftp()
            with sftp.open(file_name) as f:
                urls = [line.rstrip() for line in f]
            sftp.close()
            self.file_cache[file_name] = (current_time, urls)
            return urls
        except OSError as error:
            print(f"get_urls_from_file {error}")
            return urls

    def get_aria_client(self):
        """Get aria2c client for RPC calls"""
        return aria2p.API(aria2p.Client(host="http://172.16.10.21", port=6800, secret=""))

    def get_download_stats(self):
        """Get download statistics"""
        if not self.aria2_client:
            self.aria2_client = self.get_aria_client()

        download_info = []
        try:
            stats = self.aria2_client.get_stats()
            downloads = self.aria2_client.get_downloads()

            for download in downloads:
                download_info.append(
                    {
                        "name": download.name,
                        "status": download.status,
                        "speed": download.download_speed_string(),
                        "eta": download.eta_string(),
                        "progress": download.progress_string(),
                    }
                )
        except Exception as error:
            print(f"get_urls_from_file {error}")
            download_info.append(
                {
                    "name": " ",
                    "status": " ",
                    "speed": " ",
                    "eta": " ",
                    "progress": " ",
                }
            )
            return {
                "stats": {
                    "download_speed": "0",
                    "upload_speed": "0",
                    "active": "0",
                    "waiting": "0",
                    "stopped": "0",
                },
                "downloads": [],
            }

        return {
            "stats": {
                "download_speed": stats.download_speed_string,
                "upload_speed": stats.upload_speed,
                "active": stats.num_active,
                "waiting": stats.num_waiting,
                "stopped": stats.num_stopped,
            },
            "downloads": download_info,
        }


media_server = MediaServerWeb()


@app.route("/")
def index():
    """Initialize index"""
    return render_template("index.html")


@app.route("/api/stats")
def get_stats():
    """get stats to display"""
    return jsonify(media_server.get_download_stats())


@app.route("/api/files/<file_type>")
def get_files(file_type):
    """get files to display
    if not media_server.aria2_client:
        media_server.aria2_client = media_server.get_aria_client()"""
    file_mapping = {
        "movie_magnet": media_server.movie_magnet_file,
        "movie_url": media_server.movie_file,
        "tv_magnet": media_server.tv_magnet_file,
        "tv_url": media_server.tv_file,
        "MediaLoaderLog": media_server.log_file,
    }

    if file_type not in file_mapping:
        return jsonify({"error": "Invalid file type"}), 400

    urls = media_server.get_urls_from_file(file_mapping[file_type])
    return jsonify({"urls": urls})


@app.route("/api/update_file", methods=["POST"])
def update_file():
    """Update selected file"""
    file_type = request.json.get("file_type")
    content = request.json.get("content")

    file_mapping = {
        "movie_magnet": media_server.movie_magnet_file,
        "movie_url": media_server.movie_file,
        "tv_magnet": media_server.tv_magnet_file,
        "tv_url": media_server.tv_file,
        "MediaLoaderLog": media_server.log_file,
    }

    if file_type not in file_mapping:
        return jsonify({"error": "Invalid file type"}), 400

    try:
        client = SSHClient()
        client.load_system_host_keys()
        client.connect("mustang", username="adm-user")
        sftp = client.open_sftp()
        sftp.open(file_mapping[file_type], "w").write(content + "\n")
        sftp.close()
        client.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/control/<action>", methods=["POST"])
def control_downloads(action):
    """Control downloads
    media_server.init_ssh_pool()"""
    if not media_server.aria2_client:
        media_server.aria2_client = media_server.get_aria_client()

    try:
        if action == "pause_all":
            media_server.aria2_client.pause_all(force=False)
        elif action == "resume_all":
            media_server.aria2_client.resume_all()
        elif action == "purge":
            media_server.aria2_client.purge()
        else:
            return jsonify({"error": "Invalid action"}), 400

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="172.16.10.20", port=5000, debug=True)
