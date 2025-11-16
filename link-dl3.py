# #!/usr/bin/env python3


# import tkinter as tk
# from tkinter import ttk, filedialog
# import subprocess
# import threading


# class YouTubeDownloader(tk.Tk):
#     def __init__(self):
#         super().__init__()
#         self.title("YouTube Downloader")
#         self.create_widgets()
#         self.download_directory = ""

#     def create_widgets(self):
#         # Directory selection
#         self.dir_frame = ttk.Frame(self, padding="10")
#         self.dir_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
#         self.dir_label = ttk.Label(self.dir_frame, text="Save to:")
#         self.dir_label.grid(row=0, column=0, sticky=tk.W)
#         self.dir_button = ttk.Button(
#             self.dir_frame, text="Choose Directory", command=self.choose_directory)
#         self.dir_button.grid(row=0, column=1, sticky=tk.W)

#         # URL entries
#         self.url_frame = ttk.Frame(self, padding="10")
#         self.url_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
#         self.url_entries = [ttk.Entry(self.url_frame, width=40)
#                             for _ in range(10)]
#         for i, entry in enumerate(self.url_entries):
#             entry.grid(row=i, column=0, padx=5, pady=2)

#         # Download options
#         self.radio_var = tk.StringVar(value="audio")
#         self.audio_button = ttk.Radiobutton(
#             self.url_frame, text="Audio only", variable=self.radio_var, value="audio")
#         self.audio_button.grid(row=11, column=0, sticky=tk.W)
#         self.video_button = ttk.Radiobutton(
#             self.url_frame, text="Video", variable=self.radio_var, value="video")
#         self.video_button.grid(row=11, column=1, sticky=tk.W)

#         # Download button
#         self.download_button = ttk.Button(
#             self.url_frame, text="Download", command=self.start_download)
#         self.download_button.grid(row=12, column=0, columnspan=2, pady=10)

#     def choose_directory(self):
#         self.download_directory = filedialog.askdirectory()
#         if self.download_directory:
#             self.dir_label.config(text=f"Save to: {self.download_directory}")
#         else:
#             self.dir_label.config(text="Save to:")

#     def download_youtube(self, url_entry):
#         url = url_entry.get()
#         if not url:
#             return
#         choice = self.radio_var.get()
#         output_path = f'"{self.download_directory}/%(title)s.%(ext)s"'

#         if choice == "audio":
#             cmd = f"yt-dlp  --impersonate chrome --buffer-size 16K --limit-rate 1M -x --audio-format m4a -o {output_path} {url}"
#         else:
#             cmd = f"yt-dlp --impersonate chrome --buffer-size 16K --limit-rate 1M -f bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best -o {output_path} {url}"

#         subprocess.run(cmd, shell=True, check=True)
#         url_entry.delete(0, tk.END)
#     def start_download(self):
#         for entry in self.url_entries:
#             threading.Thread(target=self.download_youtube,
#                              args=(entry,), daemon=True).start()

#     # def download_youtube(self, url_entry):
#     #     url = url_entry.get().strip()
#     #     if not url:
#     #         return
#     #     output_path = f'"{self.download_directory}/%(title)s.%(ext)s"'

#     #     # Use for direct .mp4 links (copied from browser DevTools)
#     #     user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
#     #     referer = "https://thothd.to/"

#     #     headers = (
#     #         f'--add-header "User-Agent: {user_agent}" '
#     #         f'--add-header "Referer: {referer}" '
#     #         f'--force-generic-extractor'
#     #     )

#     #     cmd = f'yt-dlp {headers} -o {output_path} "{url}"'

#     #     try:
#     #         subprocess.run(cmd, shell=True, check=True)
#     #         url_entry.delete(0, tk.END)
#     #     except subprocess.CalledProcessError as e:
#     #         print(f"[ERROR] Download failed for: {url}")
#     #         print("stderr:", e)

#     # not sure if i need this???/
#     # def download_youtube(self, url_entry):
#     #     url = url_entry.get()
#     #     if not url:
#     #         return
#     #     choice = self.radio_var.get()
#     #     output_path = f'"{self.download_directory}/%(title)s.%(ext)s"'

#     #     # 👇 Replace with real values from your browser
#     #     user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
#     #     referer = "https://thothd.to/"
#     #     cookies = "cf_clearance=OoFtIh0lMlW48hNtuYGIicQP5XeDOQWf6GfuiopTuhs-1748117364-1.2.1.1-LGghKHJzgLZfT_s7JFy7DtLcMEgwYjSjGU8z7ideCbxxYTOhP6QxoJldoYPyP.6A6OBpr08pZqKDvbkTWZJ80jycEi1rKzFVuaob_kQbpVnrP6RZXBqKS71UpGCUKeI7d8O0owRcsqTC.H1oyXn_J7qUda8sfyXIFzYShIGrqTdVIQbISgLxSTuqqTDDtuS0fc2krGQIp2tDex16FHoGgKN7bZUBSZdvfWYRrYrZ.P3eVZjBcQoypYl0JC6sxbP5ebCsrLd3wydzIzz58Z4vM7Xwx2mVRjKv7b3bZfrnOHCN4sGl6hfeKRUcvymxzaqFcDE__6riaVTe.1gS3sKIGbLFoxyaRyiOlgXBoUgJr1w; cart_p=2; CHCK=1; kt_ips=50.91.33.167; kt_params=id%3D271875%26dir%3Dbishoujomom-you-get-to-watch-this-milfy-witch-fuck-her-oiled-up-tits"

#     #     headers = (
#     #         f'--add-header "User-Agent: {user_agent}" '
#     #         f'--add-header "Referer: {referer}" '
#     #         f'--add-header "Cookie: {cookies}"'
#     #     )

#     #     if choice == "audio":
#     #         cmd = f'yt-dlp {headers} -x --audio-format m4a -o {output_path} "{url}"'
#     #     else:
#     #         cmd = f'yt-dlp {headers} -f bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best -o {output_path} "{url}"'

#     #     try:
#     #         subprocess.run(cmd, shell=True, check=True)
#     #         url_entry.delete(0, tk.END)
#     #     except subprocess.CalledProcessError as e:
#     #         print(f"[ERROR] Download failed for: {url}")
#     #         print("stderr:", e)


# if __name__ == "__main__":
#     app = YouTubeDownloader()
#     app.mainloop()

import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
import threading


class YouTubeDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader")
        self.create_widgets()
        self.download_directory = ""

    def create_widgets(self):
        # Directory selection
        self.dir_frame = ttk.Frame(self, padding="10")
        self.dir_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.dir_label = ttk.Label(self.dir_frame, text="Save to:")
        self.dir_label.grid(row=0, column=0, sticky=tk.W)
        self.dir_button = ttk.Button(
            self.dir_frame, text="Choose Directory", command=self.choose_directory)
        self.dir_button.grid(row=0, column=1, sticky=tk.W)

        # URL entries
        self.url_frame = ttk.Frame(self, padding="10")
        self.url_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.url_entries = [ttk.Entry(self.url_frame, width=40)
                            for _ in range(10)]
        for i, entry in enumerate(self.url_entries):
            entry.grid(row=i, column=0, padx=5, pady=2)

        # Download options
        self.radio_var = tk.StringVar(value="audio")
        self.audio_button = ttk.Radiobutton(
            self.url_frame, text="Audio only", variable=self.radio_var, value="audio")
        self.audio_button.grid(row=11, column=0, sticky=tk.W)
        self.video_button = ttk.Radiobutton(
            self.url_frame, text="Video", variable=self.radio_var, value="video")
        self.video_button.grid(row=11, column=1, sticky=tk.W)

        # Download button
        self.download_button = ttk.Button(
            self.url_frame, text="Download", command=self.start_download)
        self.download_button.grid(row=12, column=0, columnspan=2, pady=10)

    def choose_directory(self):
        self.download_directory = filedialog.askdirectory()
        if self.download_directory:
            self.dir_label.config(text=f"Save to: {self.download_directory}")
        else:
            self.dir_label.config(text="Save to:")

    def download_youtube(self, url_entry):
        url = url_entry.get()
        if not url:
            return
        choice = self.radio_var.get()
        output_path = f'"{self.download_directory}/%(title)s.%(ext)s"'

        if choice == "audio":
            cmd = f"yt-dlp  --impersonate chrome --buffer-size 16K --limit-rate 1M -x --audio-format m4a -o {output_path} {url}"
        else:
            cmd = f"yt-dlp --impersonate chrome --buffer-size 16K --limit-rate 1M -f bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best -o {output_path} {url}"

        subprocess.run(cmd, shell=True, check=True)
        url_entry.delete(0, tk.END)

    def start_download(self):
        for entry in self.url_entries:
            threading.Thread(target=self.download_youtube,
                             args=(entry,), daemon=True).start()


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
