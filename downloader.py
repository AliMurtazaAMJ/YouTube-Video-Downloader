import os
import requests
import yt_dlp
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import pyperclip  # For clipboard operations

# Default download folder
DEFAULT_DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "Downloads")
os.makedirs(DEFAULT_DOWNLOAD_FOLDER, exist_ok=True)

def check_link(url):
    """Check if the YouTube link is valid using requests."""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def download_video(url, download_folder, progress_callback=None):
    """Download a YouTube video using yt_dlp with progress callback."""
    try:
        ydl_opts = {
            'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
            'format': 'bv*+ba/best[ext=mp4]',  # Prefer MP4 format
            'merge_output_format': 'mp4',  # Ensure final file is MP4
            'noplaylist': True,  # Prevent downloading full playlists
            'progress_hooks': [progress_callback] if progress_callback else [],  # Use progress callback
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'  # Convert to MP4 if needed
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)  # Get video info without downloading
            video_title = info_dict.get('title', 'Unknown Title')
            if progress_callback:
                progress_callback({'status': 'started', 'title': video_title})
            ydl.download([url])
            if progress_callback:
                progress_callback({'status': 'finished', 'title': video_title})

    except Exception as e:
        if progress_callback:
            progress_callback({'status': 'error', 'message': str(e)})

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Video Downloader")
        self.geometry("600x500")
        self.configure(padx=20, pady=20)

        # Title Label (Bold, Size 16)
        self.title_label = ctk.CTkLabel(self, text="YouTube Video Downloader", font=("Arial", 16, "bold"))
        self.title_label.pack(pady=(0, 10))

        # URL Input Field
        self.url_label = ctk.CTkLabel(self, text="Enter YouTube URL(s):")
        self.url_label.pack(pady=(0, 5))

        self.url_entry = ctk.CTkTextbox(self, height=100)
        self.url_entry.pack(fill="x", pady=(0, 10))

        # Paste and Clear Buttons Frame
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(fill="x", pady=(0, 10))

        # Paste Button
        self.paste_button = ctk.CTkButton(self.button_frame, text="Paste", command=self.paste_urls)
        self.paste_button.pack(side="left", padx=(0, 5))

        # Clear Button (on the right side)
        self.clear_button = ctk.CTkButton(self.button_frame, text="Clear", command=self.clear_urls)
        self.clear_button.pack(side="right")

        # URL Counter Label
        self.url_counter_label = ctk.CTkLabel(self, text="URLs: 0", font=("Arial", 12))
        self.url_counter_label.pack(pady=(0, 10))

        # Download Path Selection
        self.path_label = ctk.CTkLabel(self, text="Download Path:")
        self.path_label.pack(pady=(0, 5))

        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.pack(fill="x", pady=(0, 10))

        self.path_entry = ctk.CTkEntry(self.path_frame, placeholder_text=DEFAULT_DOWNLOAD_FOLDER)
        self.path_entry.insert(0, DEFAULT_DOWNLOAD_FOLDER)  # Set default path
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.browse_button = ctk.CTkButton(self.path_frame, text="Browse", command=self.browse_folder)
        self.browse_button.pack(side="right")

        # Download Button
        self.download_button = ctk.CTkButton(self, text="Start Download", command=self.start_download)
        self.download_button.pack(pady=(10, 0))

        # Progress Label
        self.progress_label = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.progress_label.pack(pady=(10, 0))

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", pady=(10, 0))
        self.progress_bar.set(0)  # Initialize progress bar to 0

        # Footer (Bold, Size 14)
        self.footer_label = ctk.CTkLabel(self, text="@Tools for AMJ", font=("Arial", 14, "bold"))
        self.footer_label.pack(side="bottom", pady=10)

        # Threading
        self.download_thread = None

        # Bind URL counter update
        self.url_entry.bind("<KeyRelease>", self.update_url_counter)

    def browse_folder(self):
        """Open a folder selection dialog and update the path entry."""
        selected_folder = filedialog.askdirectory()
        if selected_folder:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, selected_folder)

    def paste_urls(self):
        """Paste URLs from the clipboard into the URL entry."""
        clipboard_text = pyperclip.paste()
        if clipboard_text:
            # Split clipboard text into lines
            urls = clipboard_text.splitlines()
            valid_urls = []
            for url in urls:
                # Validate URL
                if url.strip().startswith("https://www.youtube.com/"):
                    valid_urls.append(url.strip())
            # Remove duplicates
            valid_urls = list(set(valid_urls))
            # Append valid URLs to the URL entry
            if valid_urls:
                self.url_entry.insert("end", "\n".join(valid_urls) + "\n")
                self.update_url_counter()
            else:
                messagebox.showwarning("Warning", "No valid YouTube URLs found in clipboard!")

    def clear_urls(self):
        """Clear all URLs from the URL entry."""
        self.url_entry.delete("1.0", "end")
        self.update_url_counter()

    def update_url_counter(self, event=None):
        """Update the URL counter label."""
        urls = self.url_entry.get("1.0", "end").strip().splitlines()
        valid_urls = [url for url in urls if url.startswith("https://www.youtube.com/")]
        # Remove duplicates
        valid_urls = list(set(valid_urls))
        self.url_counter_label.configure(text=f"URLs: {len(valid_urls)}")

    def start_download(self):
        """Start downloading videos from the provided URLs using threading."""
        urls = self.url_entry.get("1.0", "end").strip().splitlines()
        valid_urls = [url for url in urls if url.startswith("https://www.youtube.com/")]
        # Remove duplicates
        valid_urls = list(set(valid_urls))
        download_folder = self.path_entry.get().strip() or DEFAULT_DOWNLOAD_FOLDER

        if not valid_urls:
            messagebox.showwarning("Warning", "No valid YouTube URLs provided!")
            return

        os.makedirs(download_folder, exist_ok=True)

        # Disable the download button during download
        self.download_button.configure(state="disabled", text="Downloading...")

        # Reset progress bar and label
        self.progress_bar.set(0)
        self.progress_label.configure(text="", text_color="black")

        # Start a new thread for downloading
        self.download_thread = threading.Thread(
            target=self.download_videos_thread,
            args=(valid_urls, download_folder),
            daemon=True
        )
        self.download_thread.start()

    def download_videos_thread(self, urls, download_folder):
        """Thread function to download videos."""
        for url in urls:
            if check_link(url):
                download_video(url, download_folder, self.update_progress)
            else:
                self.progress_label.configure(text=f"Invalid URL: {url}", text_color="red")
        # Re-enable the download button after all downloads are complete
        self.download_button.configure(state="normal", text="Start Download")
        self.progress_label.configure(text="Download completed!", text_color="green")

    def update_progress(self, data):
        """Update the progress label, progress bar, and button based on download status."""
        if data['status'] == 'started':
            self.progress_label.configure(text=f"Downloading: {data['title']}", text_color="blue")
        elif data['status'] == 'downloading':
            # Update progress bar based on downloaded bytes
            total_bytes = data.get('total_bytes', 0)
            downloaded_bytes = data.get('downloaded_bytes', 0)
            if total_bytes > 0:
                progress = downloaded_bytes / total_bytes
                self.progress_bar.set(progress)
        elif data['status'] == 'finished':
            self.progress_label.configure(text=f"Finished: {data['title']}", text_color="green")
            self.progress_bar.set(1)  # Set progress bar to 100%
        elif data['status'] == 'error':
            self.progress_label.configure(text=f"Error: {data['message']}", text_color="red")
            self.progress_bar.set(0)  # Reset progress bar on error

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()