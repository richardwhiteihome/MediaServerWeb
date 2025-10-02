"""
Class representing a Gui Interface to MediaServer file
"""

# pylint: disable=C0103 W0718 C0301
import time
import tkinter as tk

from tkinter import ttk, messagebox
import aria2p
from paramiko import SSHClient


class MediaServerGui:
    """
    Class representing a Gui Interface to MediaServer file
    """

    def __init__(self):
        self.root = None
        self.exit_button = None
        self.button_frame = None
        self.status_frame = None
        self.input_frame = None

        self.background_default = "#999999"
        self.file_select_combo_box = None
        self.entry_url = None
        self.running_stats = True
        self.text_area_stats = None
        self.text_area_stats_text = "stats"
        self.text_area_file = None
        self.text_area_file_text = "file"

        self.tv_file = "/mnt/data/applications/MediaServer/data/tv_urls"
        self.tv_magnet_file = "/mnt/data/applications/MediaServer/data/tv_magnet_urls"
        self.movie_magnet_file = "/mnt/data/applications/MediaServer/data/movie_magnet_urls"
        self.movie_file = "/mnt/data/applications/MediaServer/data/movie_urls"

        self.ssh_pool = None
        self.init_ssh_pool()
        self.file_cache = {}
        self.cache_timeout = 300  # 5 minutes

        self.aria2_client = None
        self.button_text_start_monitoring = "Start Monitoring"
        self.button_text_stop_monitoring = "Stop Monitoring"
        self.button_text_update_file = "Update Data file"
        self.button_text_purge = "Purge"
        self.button_text_pause_all = "Pause All"
        self.button_text_resume_all = "Resume All"

        self.create_main_window()
        self.styles = self.styles_configure()

        self.root.mainloop()

    def on_file_selection(self):
        """Select file to update"""
        selected = self.file_select_combo_box.get()
        selected_file = self.tv_file
        if selected == "Movie Magnet":
            selected_file = self.movie_magnet_file
        if selected == "Movie URL":
            selected_file = self.movie_file
        if selected == "TV Magnet":
            selected_file = self.tv_magnet_file
        if selected == "TV URL":
            selected_file = self.tv_file
        list_of_urls = self.get_urls_from_file(selected_file)
        self.text_area_file.delete("1.0", tk.END)
        for entry in list_of_urls:
            self.text_area_file.insert(tk.END, f"{entry}\n")

    def init_ssh_pool(self):
        """Initialize SSH connection pool"""
        self.ssh_pool = SSHClient()
        self.ssh_pool.load_system_host_keys()
        self.ssh_pool.connect("172.16.10.21", username="adm-user")

    def __del__(self):
        """Cleanup resources"""
        if self.ssh_pool:
            self.ssh_pool.close()
        if hasattr(self, "aria2_client"):
            self.aria2_client = None

    def get_urls_from_file(self, file_name):
        """Main processing file loader with caching"""
        current_time = time.time()

        # Check cache first
        if file_name in self.file_cache:
            cache_time, urls = self.file_cache[file_name]
            if current_time - cache_time < self.cache_timeout:
                return urls

        # If not in cache or expired, load from file
        urls = []
        try:
            sftp = self.ssh_pool.open_sftp()
            with sftp.open(file_name) as f:
                urls = [line.rstrip() for line in f]
            sftp.close()

            # Update cache
            self.file_cache[file_name] = (current_time, urls)
            return urls
        except OSError as error:
            print(f"get_urls_from_file {error}")
            return urls

    def button_clicked_purge(self):
        """Purge completed, removed or failed downloads from the queue."""
        self.aria2_client.purge()

    def button_clicked_pause_all(self):
        """Pause all (active) downloads."""
        self.aria2_client.pause_all(force=False)

    def button_clicked_resume_all(self):
        """Resume (unpause) all downloads."""
        self.aria2_client.resume_all()

    def get_aria_client(self):
        """Get ari2c client for RPC calls"""
        return aria2p.API(aria2p.Client(host="http://172.16.10.21", port=6800, secret=""))

    def button_clicked_start_monitoring(self):
        """Start Monitoring"""
        self.running_stats = True
        print(self.button_text_start_monitoring)
        try:
            self.aria2_client = self.get_aria_client()
            self.aria2_client.get_global_options()
        except Exception as error:
            print(f"button_clicked_start_monitoring {error}")
            messagebox.showerror("error", f"Unable to connect to MediaServer! {error} ")
            self.running_stats = False
            return

        self.update_stats()

    def update_stats(self):
        """Update stats using after() method"""
        if not self.running_stats:
            return

        self.text_area_stats.delete("1.0", tk.END)
        stats = self.aria2_client.get_stats()

        # Combine stats text into a single string
        stats_text = (
            f" Download Speed: {stats.download_speed}\n"
            f" Upload Speed {stats.upload_speed}\n"
            f" Active: {stats.num_active} Waiting {stats.num_waiting}\n"
            f" Stopped: {stats.num_stopped}\n"
        )
        self.text_area_stats.insert(tk.END, stats_text)

        # Configure tags once, not in loop
        self.text_area_stats.tag_configure("true", foreground="red")
        self.text_area_stats.tag_configure("false", foreground="black")

        # Build download information
        downloads = self.aria2_client.get_downloads()
        for active_download in downloads:
            download_text = (
                f"{active_download.name}\n"
                f" Status: {active_download.status} Download Speed {active_download.download_speed_string()}\n"
                f" ETA: {active_download.eta_string()} Progress {active_download.progress_string()}\n"
            )
            self.text_area_stats.insert(tk.END, active_download.name + "\n", "true")
            self.text_area_stats.insert(tk.END, download_text[len(active_download.name) + 1 :])

        # Schedule next update
        self.root.after(5000, self.update_stats)

    def button_clicked_stop_monitoring(self):
        """Stop Monitoring"""
        print(self.button_text_stop_monitoring)
        self.running_stats = False

    def button_clicked_add_url(self):
        """Add a URL's to selected file"""
        self.file_select_combo_box.get()
        selected = self.file_select_combo_box.get()
        selected_file = None
        if selected == "Movie Magnet":
            selected_file = self.movie_magnet_file
        if selected == "Movie URL":
            selected_file = self.movie_file
        if selected == "TV Magnet":
            selected_file = self.tv_magnet_file
        if selected == "TV URL":
            selected_file = self.tv_file

        the_text = self.text_area_file.get("1.0", "end")
        self.update_file(the_text.strip(), selected_file)

    def update_file(self, text_value, selected_file):
        """Add successful downloads to archive file"""

        client = SSHClient()
        client.load_system_host_keys()
        client.connect("172.16.10.21", username="adm-user")
        sftp = client.open_sftp()
        sftp.open(selected_file, "w").write(text_value + "\n")
        sftp.close()
        client.close()

    def styles_configure(self):
        """Configure styles"""

        background_default = self.background_default
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", width=15, foreground="black", background=background_default)
        style.configure("TFrame", foreground="white", background=background_default)
        style.configure("TLabel", foreground="black", background=background_default)
        style.configure("TEntry", foreground="black", background=background_default)
        style.configure("TCheckbutton", foreground="black", background=background_default)
        return style

    def create_input_frame(self, container):
        """Create main input frame"""
        frame = ttk.Frame(container)

        # grid layout for the input frame
        frame.columnconfigure(4, weight=1)
        # frame.columnconfigure(0, weight=3)

        ttk.Label(frame, text="Select URL Data file:").grid(column=2, row=0, sticky=tk.W)
        self.file_select_combo_box = ttk.Combobox(
            frame,
            width=30,
            state="readonly",
            values=["Movie Magnet", "Movie URL", "TV Magnet", "TV URL"],
        )
        self.file_select_combo_box.current(0)
        self.file_select_combo_box.grid(column=2, row=0, sticky=tk.W)
        self.file_select_combo_box.bind("<<ComboboxSelected>>", self.on_file_selection)
        ttk.Button(
            frame,
            text=self.button_text_update_file,
            command=self.button_clicked_add_url,
        ).grid(column=3, row=0)

        for widget in frame.winfo_children():
            widget.grid(padx=5, pady=5)
        return frame

    def create_status_frame(self, container):
        """Create status frame"""
        frame = ttk.Frame(container)
        frame.columnconfigure(4, weight=3)

        ttk.Label(frame, text="Active Jobs:").grid(column=0, row=0, sticky=tk.W)
        tk.Text(
            frame,
            width=160,
            height=20,
            name=self.text_area_stats_text,
            background="#000000",
            foreground="white",
        ).grid(column=0, row=1)
        ttk.Label(frame, text="Selected File:").grid(column=0, row=2, sticky=tk.W)
        tk.Text(
            frame,
            insertbackground="white",
            width=160,
            height=20,
            name=self.text_area_file_text,
            background="#000000",
            foreground="white",
        ).grid(column=0, row=3)

        for widget in frame.winfo_children():
            widget.grid(padx=5, pady=5)
            # self.text_area_dict[widget.winfo_name()] = widget
            if self.text_area_file_text in widget.winfo_name():
                self.text_area_file = widget
            if self.text_area_stats_text in widget.winfo_name():
                self.text_area_stats = widget
        return frame

    def create_button_frame(self, container):
        """Create button frame"""
        frame = ttk.Frame(container)
        frame.columnconfigure(4, weight=1)

        ttk.Button(
            frame,
            text=self.button_text_start_monitoring,
            command=self.button_clicked_start_monitoring,
        ).grid(
            column=0,
            row=0,
        )
        ttk.Button(
            frame,
            text=self.button_text_stop_monitoring,
            command=self.button_clicked_stop_monitoring,
        ).grid(column=1, row=0)
        ttk.Button(frame, text="Exit", command=quit).grid(column=2, row=0)
        ttk.Button(frame, text=self.button_text_purge, command=self.button_clicked_purge).grid(column=0, row=1)
        ttk.Button(
            frame,
            text=self.button_text_pause_all,
            command=self.button_clicked_pause_all,
        ).grid(column=1, row=1)
        ttk.Button(
            frame,
            text=self.button_text_resume_all,
            command=self.button_clicked_resume_all,
        ).grid(column=2, row=1)

        for widget in frame.winfo_children():
            widget.grid(padx=5, pady=5)
        return frame

    def create_main_window(self):
        """Create main window"""
        self.root = tk.Tk()
        self.root.title("MediaServer GUI")
        # self.root.resizable(0, 0)
        # self.root.geometry("800x850")
        self.root.configure(background=self.background_default)

        # layout on the root window
        self.root.columnconfigure(0, weight=4)
        self.root.columnconfigure(1, weight=1)

        self.status_frame = self.create_status_frame(self.root)
        self.status_frame.grid(column=0, row=0)

        self.input_frame = self.create_input_frame(self.root)
        self.input_frame.grid(column=0, row=1)

        self.button_frame = self.create_button_frame(self.root)
        self.button_frame.grid(column=0, row=2)


def main():
    """Main function"""
    MediaServerGui()


if __name__ == "__main__":
    main()
