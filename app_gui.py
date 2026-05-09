import customtkinter as ctk
import os
import threading
from dotenv import load_dotenv
from core_parser import MediaParser
from api_client import SubtitleAggregator, OpenSubtitlesProvider, SubdlProvider, FeliratokEuProvider

# --- CONFIGURATION ---
load_dotenv()

OS_API_KEY = os.getenv("OPENSUBTITLES_API_KEY")
SUBDL_API_KEY = os.getenv("SUBDL_API_KEY")

if not OS_API_KEY or not SUBDL_API_KEY:
    print("WARNING: Missing API keys in the .env file!")

class SubtitleHunterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Subtitos")
        try:
            self.iconbitmap("icon.ico")
        except Exception:
            pass
        self.geometry("600x650")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # State variables
        self.current_subtitle = None
        self.aggregator = None
        self.target_filename = ""

        self.create_widgets()

    def create_widgets(self):
        self.title_label = ctk.CTkLabel(self, text="Subtitos", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(30, 10))

        self.subtitle_label = ctk.CTkLabel(self, text="Paste your movie/show filename below:", text_color="gray")
        self.subtitle_label.pack(pady=(0, 10))

        self.filename_input = ctk.CTkEntry(self, width=500, placeholder_text="e.g., Movie.Name.2023.1080p.WEB-DL.x264.mkv")
        self.filename_input.pack(pady=10)

        self.lang_var = ctk.StringVar(value="Hungarian (HU)")
        self.lang_dropdown = ctk.CTkOptionMenu(
            self,
            values=["Hungarian (HU)", "English (EN)"],
            variable=self.lang_var,
            width=200
        )
        self.lang_dropdown.pack(pady=(0, 10))

        self.search_btn = ctk.CTkButton(self, text="1. Search Subtitles", command=self.start_search_thread, height=40)
        self.search_btn.pack(pady=10)

        self.download_btn = ctk.CTkButton(
            self, text="2. Download Subtitle", command=self.start_download_thread,
            height=40, fg_color="#28a745", hover_color="#218838", state="disabled"
        )
        self.download_btn.pack(pady=10)

        self.log_box = ctk.CTkTextbox(self, width=500, height=220, state="disabled", font=ctk.CTkFont(size=12))
        self.log_box.pack(pady=10)

        self.log_box.tag_config("success", foreground="#2ECC71")
        self.log_box.tag_config("warning", foreground="#F1C40F")
        self.log_box.tag_config("error", foreground="#E74C3C")
        self.log_box.tag_config("highlight", foreground="#3498DB")

    def log_message(self, message: str, tag: str = None):
        """Prints a message to the GUI textbox with optional color tags."""
        self.log_box.configure(state="normal")
        if tag:
            self.log_box.insert("end", message + "\n", tag)
        else:
            self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def start_search_thread(self):
        """Starts the search logic in a background thread to keep UI responsive."""
        filename = self.filename_input.get().strip()
        if not filename:
            self.log_message("❌ Please enter a filename first!", "error")
            return

        self.target_filename = filename
        self.current_subtitle = None
        self.search_btn.configure(state="disabled", text="Searching...")
        self.download_btn.configure(state="disabled", text="2. Download Subtitle", fg_color="#28a745")

        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

        selected_lang = self.lang_var.get()
        thread = threading.Thread(target=self.run_search_logic, args=(filename, selected_lang))
        thread.start()

    def run_search_logic(self, filename: str, selected_lang: str):
        """Parses the input, searches providers, and scores results."""
        self.log_message(f"🔍 Analyzing: ", "highlight")
        self.log_message(f"   {filename}")

        parser = MediaParser()
        try:
            parsed_data = parser.parse_filename(filename)
        except Exception as e:
            self.log_message(f"\n❌ Parsing failed: {e}", "error")
            self.after(0, self.reset_search_button)
            return

        self.aggregator = SubtitleAggregator()

        if OS_API_KEY:
            self.aggregator.add_provider(OpenSubtitlesProvider(api_key=OS_API_KEY))
        if SUBDL_API_KEY:
            self.aggregator.add_provider(SubdlProvider(api_key=SUBDL_API_KEY))
        self.aggregator.add_provider(FeliratokEuProvider())

        lang_code = "hu" if selected_lang == "Hungarian (HU)" else "en"

        self.log_message(f"⏳ Searching for {selected_lang} subtitles...\n")

        best_subtitle = self.aggregator.search_and_score(parsed_data, lang_code)

        if best_subtitle:
            self.current_subtitle = best_subtitle
            score = best_subtitle['score']
            below_threshold = best_subtitle.get("below_threshold", False)

            self.log_message("✅ MATCH FOUND", "success")
            self.log_message(f"🌐 Source Site: {best_subtitle['provider']}", "highlight")
            self.log_message(f"📄 File: {best_subtitle['filename']}")

            # Display sync quality based on score
            if score == 100:
                self.log_message(f"✅ Sync: PERFECT MATCH (100/100)", "success")
                self.log_message("   Same release group. Subtitle is guaranteed to be synced.")
            elif score >= 70:
                self.log_message(f"✅ Sync: VERY GOOD ({score}/100)", "success")
                self.log_message("   Source and resolution match. Should be perfectly synced.")
            elif score >= 40:
                self.log_message(f"⚠️ Sync: ACCEPTABLE ({score}/100)", "warning")
                self.log_message("   Source matches. Slight delay is possible.")
            else:
                self.log_message(f"❌ Sync: POOR MATCH ({score}/100)", "error")
                self.log_message("   Source does not match. High risk of sync issues.")

            # Only enable download if source matched (score >= 40)
            if not below_threshold:
                self.after(0, lambda: self.download_btn.configure(
                    state="normal",
                    text=f"Download {lang_code.upper()} Subtitle"
                ))
            else:
                self.log_message("\n⛔ Download disabled - source mismatch too risky.", "error")
        else:
            # Differentiate between "no results" and "results but all rejected"
            self.log_message(f"❌ No subtitles found for {selected_lang}.", "error")
            self.log_message("   This subtitle may not exist yet for your release.", "warning")

        self.after(0, self.reset_search_button)

    def start_download_thread(self):
        """Starts the download process in a background thread."""
        if not self.current_subtitle or not self.aggregator:
            return

        self.download_btn.configure(state="disabled", text="Downloading...")
        thread = threading.Thread(target=self.run_download_logic)
        thread.start()

    def run_download_logic(self):
        """Downloads the selected subtitle to the Windows Downloads folder."""
        # Save to the user's Downloads folder
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads_folder, exist_ok=True)

        lang_code = self.current_subtitle['language']
        base_name = os.path.splitext(self.target_filename)[0]
        save_path = os.path.join(downloads_folder, f"{base_name}.{lang_code}.srt")

        self.log_message(f"\n⬇️ Downloading from {self.current_subtitle['provider']}...", "highlight")

        success = False
        for p in self.aggregator.providers:
            if p.name == self.current_subtitle["provider"]:
                success = p.download(self.current_subtitle["file_id"], save_path)
                break

        if success:
            self.log_message(f"🎉 SUCCESS! Saved to:", "success")
            self.log_message(f"   {save_path}")
            self.after(0, lambda: self.download_btn.configure(text="Downloaded!", fg_color="gray"))
        else:
            self.log_message("❌ Download failed. Please try again.", "error")
            self.after(0, lambda: self.download_btn.configure(state="normal", text="Try Download Again"))

    def reset_search_button(self):
        """Resets the search button to its default state."""
        self.search_btn.configure(state="normal", text="1. Search Subtitles")

if __name__ == "__main__":
    app = SubtitleHunterApp()
    app.mainloop()