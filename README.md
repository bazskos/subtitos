# Subtitos

Smart multi-provider subtitle finder desktop application built with Python.

Subtitos automatically searches, scores, and downloads the best matching subtitles for movies and TV shows using multiple subtitle providers and intelligent release matching.

---

##Preview

<img width="600" height="674" alt="screen" src="https://github.com/user-attachments/assets/b822c968-17cf-4e93-b668-072503cc230f" />


---

## Features

- Multi-provider subtitle search
- Intelligent subtitle scoring system
- Automatic subtitle synchronization matching
- Release group detection
- Resolution and source matching
- Automatic ZIP extraction
- GUI desktop application
- Hungarian and English subtitle support
- Fast threaded background processing
- Automatic subtitle download to the Windows Downloads folder

---

## Supported Providers

- OpenSubtitles API
- Subdl API
- Feliratok.eu scraper integration

---

## Tech Stack

- Python
- CustomTkinter
- Requests
- BeautifulSoup4
- Guessit
- Threading
- python-dotenv

---

## How It Works

Subtitos analyzes a movie or TV show filename and extracts metadata such as:

- Title
- Year
- Resolution
- Source type
- Release group

The application then searches multiple subtitle providers and calculates a match score based on:

| Match Type | Score |
|---|---|
| Source Match | +40 |
| Resolution Match | +30 |
| Release Group Match | +30 |

A perfect release match guarantees properly synchronized subtitles.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/bazskos/subtitos.git
cd subtitos
```

Install required packages:

```bash
pip install customtkinter requests beautifulsoup4 guessit python-dotenv
```

Create a `.env` file in the project root:

```env
OPENSUBTITLES_API_KEY=your_api_key
SUBDL_API_KEY=your_api_key
```

Run the application:

```bash
python app_gui.py
```

---

## Example Filename Input

```text
Movie.Name.2026.1080p.WEB-DL.x264-GROUP.mkv
```

---

## Project Structure

```text
Subtitos/
│
├── api_client.py
├── app_gui.py
├── core_parser.py
├── core_scorer.py
├── icon.ico
├── .gitignore
└── README.md
```

---

## Future Improvements

- Drag & drop file support
- Automatic subtitle syncing
- Multi-language support
- Batch subtitle downloading
- Packaging and installer support

---

## Disclaimer

This project is intended for educational and personal use only.

Users are responsible for complying with the terms of service of subtitle providers.

---

## Author

GitHub: [@bazskos](https://github.com/bazskos)
