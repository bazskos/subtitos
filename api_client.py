import requests
import zipfile       # For handling ZIP archives
import io
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from core_scorer import SubtitleScorer

class BaseSubtitleProvider(ABC):
    """Abstract base class for all subtitle providers."""
    
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def search(self, parsed_data: dict, language: str) -> list:
        pass

class OpenSubtitlesProvider(BaseSubtitleProvider):
    """Provider for OpenSubtitles.com REST API."""
    
    def __init__(self, api_key: str):
        super().__init__(name="OpenSubtitles")
        self.api_key = api_key
        self.base_url = "https://api.opensubtitles.com/api/v1/subtitles"
        self.headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "Subtitos v1.0"
        }

    def search(self, parsed_data: dict, language: str) -> list:
        print(f"[{self.name}] Searching for {language.upper()} subtitles...")

        # Use the full original filename as query for the best chance of finding
        # an exact release match (e.g. BAUCKLEY group subtitle)
        query = parsed_data.get("original_filename") or parsed_data.get("title")

        params = {
            "query": query,
            "languages": language,
        }

        if parsed_data.get("year"):
            params["year"] = parsed_data.get("year")
            
        try:
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("data", []):
                attrs = item.get("attributes", {})
                results.append({
                    "provider": self.name,
                    "file_id": attrs.get("files", [{}])[0].get("file_id"),
                    "filename": attrs.get("files", [{}])[0].get("file_name"),
                    "language": attrs.get("language"),
                    "fps": attrs.get("fps"),
                    "download_count": attrs.get("download_count")
                })
            return results
            
        except requests.exceptions.RequestException as e:
            error_msg = f"[{self.name}] API Error: {e}"
            if e.response is not None:
                error_msg += f" | Reason: {e.response.text}"
            print(error_msg)
            return []

    def download(self, file_id: int, save_path: str) -> bool:
        """
        Requests the download link and saves the subtitle file to the disk.
        """
        print(f"[{self.name}] Requesting download link for file ID: {file_id}...")
        download_url = "https://api.opensubtitles.com/api/v1/download"
        payload = {"file_id": file_id}
        
        try:
            response = requests.post(download_url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            file_link = data.get("link")
            
            if file_link:
                print(f"[{self.name}] Downloading .srt file...")
                file_response = requests.get(file_link)
                file_response.raise_for_status()
                
                with open(save_path, "wb") as f:
                    f.write(file_response.content)
                print(f"[SUCCESS] Subtitle perfectly saved to: {save_path}")
                return True
                
        except requests.exceptions.RequestException as e:
            print(f"[{self.name}] Download Error: {e}")
            
        return False

class SubdlProvider(BaseSubtitleProvider):
    """Provider for Subdl.com API."""
    
    def __init__(self, api_key: str):
        super().__init__(name="Subdl")
        self.api_key = api_key
        self.base_url = "https://api.subdl.com/api/v1/subtitles"

    def search(self, parsed_data: dict, language: str) -> list:
        print(f"[{self.name}] Searching for {language.upper()} subtitles...")
        
        # Subdl API uses a slightly different parameter structure
        params = {
            "api_key": self.api_key,
            "film_name": parsed_data.get("title"),
            "languages": language.upper()
        }
        
        if parsed_data.get("year"):
            params["year"] = parsed_data.get("year")
            
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            # Subdl stores subtitle files in the "subtitles" array
            for item in data.get("subtitles", []):
                results.append({
                    "provider": self.name,
                    # We store the direct download URL in the file_id field
                    "file_id": item.get("url"), 
                    "filename": item.get("release_name", "Unknown.Release"),
                    "language": item.get("lang"),
                    "fps": None,  # Subdl doesn't always provide this consistently
                    "download_count": 0
                })
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"[{self.name}] API Error: {e}")
            return []

    def download(self, file_url: str, save_path: str) -> bool:
        """
        Downloads a ZIP archive from Subdl, extracts it in memory, 
        and saves only the .srt file.
        """
        # The file_url comes from the API response
        full_url = "https://dl.subdl.com" + file_url if file_url.startswith("/") else file_url
        print(f"[{self.name}] Downloading ZIP archive...")
        
        try:
            response = requests.get(full_url)
            response.raise_for_status()
            
            # --- THE MAGIC: In-memory ZIP extraction ---
            print(f"[{self.name}] Extracting .srt from ZIP...")
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                # Look for the first .srt file in the archive
                for item in archive.namelist():
                    if item.endswith('.srt'):
                        sub_content = archive.read(item)
                        
                        # Save the extracted .srt file
                        with open(save_path, "wb") as f:
                            f.write(sub_content)
                            
                        print(f"[SUCCESS] Subtitle extracted perfectly to: {save_path}")
                        return True
                        
            print(f"[{self.name}] No .srt file found inside the ZIP.")
            return False
            
        except Exception as e:
            print(f"[{self.name}] Download Error: {e}")
            return False

class FeliratokEuProvider(BaseSubtitleProvider):
    """Scraper Provider for Feliratok.eu (No API key needed)."""
    
    def __init__(self):
        super().__init__(name="Feliratok.eu")
        # Updated to the new .eu domain based on recent changes
        self.base_url = "https://www.feliratok.eu/index.php"
        # We must pretend to be a real browser, otherwise they might block us
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def search(self, parsed_data: dict, language: str) -> list:
        # Feliratok.eu is mainly for Hungarian. Skip if English is requested.
        if language.lower() != "hu":
            return []
            
        print(f"[{self.name}] Scraping website for HU subtitles...")
        
        # We pass the title to the site's search URL parameter
        params = {"search": parsed_data.get("title")}
        
        try:
            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Looking for links that point to downloads
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # If the link looks like a download action
                if 'letoltes' in href or 'download' in href or 'action=letolt' in href:
                    # Get the whole row text to find the release name
                    row = link.find_parent('tr')
                    if row:
                        text_content = row.get_text(separator=" ", strip=True)
                        
                        results.append({
                            "provider": self.name,
                            "file_id": href,  # The download piece of the URL
                            "filename": text_content, # The raw text containing the release name
                            "language": "hu",
                            "fps": None,
                            "download_count": 0
                        })
            return results
            
        except Exception as e:
            print(f"[{self.name}] Scraper Error: {e}")
            return []

    def download(self, file_id: str, save_path: str) -> bool:
        """Downloads the file and handles both raw .srt and .zip files automatically."""
        print(f"[{self.name}] Scraping download link...")
        
        # Build the full download URL safely
        if not file_id.startswith("http"):
            # Ensure we don't duplicate slashes
            separator = "" if file_id.startswith("?") or file_id.startswith("/") else "/"
            download_url = f"https://www.feliratok.eu{separator}{file_id}"
        else:
            download_url = file_id
            
        try:
            response = requests.get(download_url, headers=self.headers)
            response.raise_for_status()
            
            # CHECK THE MAGIC BYTES: Is this a ZIP file? (ZIP files start with b'PK\x03\x04')
            if response.content.startswith(b'PK\x03\x04'):
                print(f"[{self.name}] ZIP detected, extracting .srt...")
                with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                    for item in archive.namelist():
                        if item.endswith('.srt'):
                            sub_content = archive.read(item)
                            with open(save_path, "wb") as f:
                                f.write(sub_content)
                            print(f"[SUCCESS] Subtitle extracted to: {save_path}")
                            return True
                return False
            else:
                # If it's not a ZIP, it's likely a raw SRT file
                print(f"[{self.name}] Raw file detected, saving directly...")
                with open(save_path, "wb") as f:
                    f.write(response.content)
                print(f"[SUCCESS] Subtitle saved perfectly to: {save_path}")
                return True
                
        except Exception as e:
            print(f"[{self.name}] Download Error: {e}")
            return False
            
class SubtitleAggregator:
    """Manages multiple subtitle providers and aggregates their results."""
    
    def __init__(self):
        self.providers = []

    def add_provider(self, provider: BaseSubtitleProvider):
        self.providers.append(provider)

    def search_and_score(self, parsed_data: dict, language: str,
                         target_score: int = 90,
                         min_score: int = 40) -> dict | None:
        """
        Searches all providers and returns the best-scoring subtitle.

        - target_score: stops early if a subtitle reaches this score (ideal match)
        - min_score: minimum score to allow download (default 40 = source must match)
        """
        best_match = None
        highest_score = -1
        total_results = 0

        for provider in self.providers:
            print(f"Checking provider: {provider.name}...")
            results = provider.search(parsed_data, language)
            total_results += len(results)

            for sub in results:
                score = SubtitleScorer.calculate_score(parsed_data, sub["filename"])
                sub["score"] = score

                if score > highest_score:
                    highest_score = score
                    best_match = sub

                # Early exit if we found an ideal match
                if score >= target_score:
                    print(f"\n[SUCCESS] Ideal match ({score}/100) found by {provider.name}. Stopping search.")
                    return best_match

        # No results at all from any provider
        if total_results == 0:
            print(f"\n[INFO] No subtitles found on any provider for this language.")
            return None

        # Results found but none met the minimum score
        if not best_match or highest_score < min_score:
            print(f"\n[REJECTED] {total_results} subtitle(s) found but best score was only "
                  f"{highest_score}/100. Source likely does not match. Sync would be unreliable.")
            # Return the best match anyway but flag it as below threshold
            if best_match:
                best_match["below_threshold"] = True
            return best_match

        print(f"\n[INFO] Best match: {highest_score}/100.")
        return best_match