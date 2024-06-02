# Audio Forensics Tool - AFT

![AFT](AFT.webp)

## Overview
This Audio Metadata Extraction Tool is designed to extract metadata from various audio file formats. It supports single file and batch processing, offers basic and detailed metadata extraction levels, and can save the extracted metadata in multiple formats such as JSON, TXT, PDF, CSV, and TSV. The tool provides a graphical user interface (GUI) using Gradio and can also be run from the command line.

## Features
- **Supports multiple audio formats**: MP3, WAV, OGG, MP4, FLAC, AAC, M4A, WMA, ALAC, AIFF, OPUS, AMR, PCM.
- **Two processing levels**: 
  - Level 1: Basic metadata extraction
  - Level 2: Detailed metadata extraction 
- **Multiple output formats**: JSON, TXT, PDF, CSV, TSV.
- **Graphical User Interface (GUI)**: Built using Gradio.
- **Command line interface (CLI)**: For single or batch processing.

## Requirements
- Python 3.x
- Required Python libraries:
  - `argparse`
  - `gradio`
  - `mutagen`
  - `pydub`
  - `tinytag`
  - `eyed3`
  - `wave`
  - `librosa`
  - `numpy`
  - `torchaudio`
  - `torch`
  - `soundfile`
  - `shutil`
  - `json`
  - `csv`
  - `datetime`
  - `fpdf`
  - `mimetypes`
  - `logging`
- FFmpeg installed and added to PATH.
- MediaInfo installed and added to PATH.

## Installation
1.  Clone this repository:
    ```bash
    git clone https://github.com/your-repo/audio-metadata-extraction-tool.git
    cd audio-metadata-extraction-tool
    ```

2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  Ensure FFmpeg and MediaInfo are installed and added to your system's PATH.

# Usage
## Graphical User Interface (GUI)

1.  Run the tool:
    ```bash
    python main.py
    ```

2.  This will launch a Gradio interface in your web browser where you can upload files or specify a directory for batch processing.

## Command Line Interface (CLI)

1.  To process files from the command line, use the following options:
    ```bash
    python main.py --files <file1> <file2> ... --output <output_dir> --level <level> --format <format> [--aggregate]
    ```
    Example:
    ```bash
    python main.py --files "example1.mp3" "example2.wav" --output ./output --level 1 --format json --aggregate
    ```

2.  To process a directory of files:
    ```bash
    python main.py --directory <directory> --output <output_dir> --level <level> --format <format> [--aggregate]
    ```
    Example:
    ```bash
    python main.py --directory ./audio_files --output ./output --level 2 --format pdf --aggregate
    ```

## File Structure
* main.py: Entry point for the application. Manages the GUI and CLI interfaces.
* file_handler.py: Handles file uploading, directory processing, and saving metadata.
* metadata_extractor.py: Contains functions for extracting metadata using various libraries and tools.
* check_py: Handles safety checks for paths and file types.

## Logging
By default, logging captures only ERROR messages. To change the logging level to capture ALL MESSAGES, modify the logging configuration in main.py:
  ```bash
  logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
  ```

## Authors:
- Rokas
- Nikhil
- Pavlo

Vilnius University Šiauliai Academy