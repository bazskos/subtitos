from guessit import guessit

class MediaParser:
    """Responsible for parsing media filenames."""
    
    def __init__(self):
        pass

    def parse_filename(self, filename: str) -> dict:
        """
        Parses the filename using guessit to extract essential metadata.
        """
        if not filename:
            raise ValueError("Filename cannot be empty.")

        guess = guessit(filename)
        
        # Extracting only the necessary data for scoring and searching
        parsed_data = {
            "original_filename": filename,
            "title": guess.get("title"),
            "year": guess.get("year"),
            "resolution": guess.get("screen_size"),
            "source": guess.get("format"),               # e.g., BluRay, WEB-DL
            "release_group": guess.get("release_group"), # e.g., BYNDR, NTb
            "type": guess.get("type")                    # 'movie' or 'episode'
        }
        
        return parsed_data

# --- Testing ---
if __name__ == "__main__":
    test_filename = "Hoppers.2026.2160p.MA.WEB-DL.DDP5.1.Atmos.DV.HDR.H.265-BYNDR"
    
    parser = MediaParser()
    try:
        result = parser.parse_filename(test_filename)
        
        print(f"Original filename: {test_filename}\n")
        print("Parsed data:")
        for key, value in result.items():
            print(f" - {key.capitalize()}: {value}")
            
    except Exception as e:
        print(f"An error occurred: {e}")