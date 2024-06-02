# -*- coding: utf-8 -*-
"""
Created on Mon 2024.05

@author: Rokas, Nikhil, Pavlo

Vilnius University Siauliai Academy
"""
import os
import argparse
import gradio as gr
import logging
from file_handler import handle_file_upload, handle_directory, save_metadata
from check import sanitize_path, is_safe_path
from metadata_extractor import extract_metadata
from pathlib import Path

# Default values for output directory, output format and processing level
DEFAULT_OUTPUT_DIR = "./output"
DEFAULT_OUTPUT_FORMAT = "json"
DEFAULT_PROCESSING_LEVEL = 1

# Logging Configuration
LOG_FILE_PATH = "application.log"
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a file handler
file_handler = logging.FileHandler(LOG_FILE_PATH)
file_handler.setLevel(logging.ERROR)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger = logging.getLogger()
logger.addHandler(file_handler)

class Arguments:
    def __init__(self, test_args=None):
        """
        Initialize and parse command-line arguments.
        
        Args:
            test_args (list, optional): List of arguments for testing.
        """
        parser = argparse.ArgumentParser(description="Audio Metadata Extraction Tool")
        parser.add_argument("--files", nargs='+', help="Path to audio files to process")
        parser.add_argument("--directory", help="Directory containing audio files to process")
        parser.add_argument("--output", help="Output directory", default=DEFAULT_OUTPUT_DIR)
        parser.add_argument("--level", type=int, choices=[1, 2], help="Processing level: 1 (basic), 2 (detailed)", default=DEFAULT_PROCESSING_LEVEL)
        parser.add_argument("--format", choices=["json", "txt", "pdf", "csv", "tsv"], help="Output file format", default=DEFAULT_OUTPUT_FORMAT)
        parser.add_argument("--aggregate", action="store_true", help="Aggregate metadata from all extractors into a single dictionary")
        if test_args:
            self.args = parser.parse_args(test_args)
        else:
            self.args = parser.parse_args()
        self.validate_paths()

    def validate_paths(self):
        """
        Validate the provided file and directory paths.

        Raises:
            ValueError: If any file or directory path is invalid.
        """
        if self.args.files:
            for file_path in self.args.files:
                sanitized_path = sanitize_path(file_path)
                if not is_safe_path(os.getcwd(), sanitized_path):
                    raise ValueError("Unsafe file path specified.")
                if not os.path.isfile(sanitized_path):
                    raise ValueError(f"Invalid file path: {sanitized_path}")
        if self.args.directory:
            sanitized_directory = sanitize_path(self.args.directory)
            if not is_safe_path(os.getcwd(), sanitized_directory):
                raise ValueError("Unsafe directory path specified.")
            if not os.path.isdir(sanitized_directory):
                raise ValueError(f"Invalid directory path: {sanitized_directory}")

def gradio_interface():
    """
    Define and launch the Gradio interface for the audio metadata extraction tool.
    """
    def process_files(files, directory, output, level, format, aggregate):
        """
        Process the uploaded files or directory and extract metadata.
    
        Args:
            file (str): Path to a single audio file.
            directory (str): Path to a directory containing audio files.
            output (str): Output directory for metadata.
            level (int): Processing level (1 or 2).
            format (str): Output file format.
            aggregate (bool): Whether to aggregate metadata.
    
        Returns:
            str: Result message indicating success or failure.
        """
        try:
            output_dir = sanitize_path(output)
            if not is_safe_path(os.getcwd(), output_dir):
                raise ValueError("Unsafe output directory path specified.")
    
            metadata = []
            
            if files:
                # Single file upload via Gradio
                sanitized_files = [sanitize_path(files.name if hasattr(files, 'name') else files)]
                metadata = handle_file_upload(sanitized_files, int(level), aggregate)
            elif directory:
                # Directory input for batch processing
                sanitized_directory = sanitize_path(directory)
                if not is_safe_path(os.getcwd(), sanitized_directory):
                   raise ValueError(f"Unsafe directory path specified: {sanitized_directory}")
                metadata = handle_directory(sanitized_directory, int(level), aggregate)
            else:
                return "No files or directory specified."
            
            if metadata:
                save_metadata(metadata, output_dir, format)
            return f"Metadata saved to {output_dir} in {format} format."
        except Exception as e:
            logging.error(f"Error processing files: {e}")
            return f"An error occurred: {e}"


    def show_file_upload(single_or_batch):
        """
        Show or hide file or directory input based on processing type.

        Args:
            single_or_batch (str): Processing type ("Single File" or "Batch Processing").

        Returns:
            tuple: Updates for file and directory input visibility.
        """
        if single_or_batch == "Single File":
            return gr.update(visible=True), gr.update(visible=False, value="")
        else:
            return gr.update(visible=False, value=None), gr.update(visible=True)

    with gr.Blocks() as demo:
        """
        Gradio setup and initialization
        """
        gr.Markdown("# Audio Forensics Tool")

        with gr.Column():
            gr.Image("AFT1.webp", elem_id="header-image", height=300, container=True, show_download_button=False)
            single_or_batch = gr.Radio(label="Processing Type", choices=["Single File", "Batch Processing"], value="Single File")
            file_input = gr.File(label="Upload Audio File", type="filepath", visible=True)
            directory_input = gr.Textbox(label="Directory Path", visible=False)
            single_or_batch.change(show_file_upload, inputs=single_or_batch, outputs=[file_input, directory_input])

        output_input = gr.Textbox(label="Output Directory", value=DEFAULT_OUTPUT_DIR)
        level_input = gr.Radio(label="Processing Level", choices=["1", "2"], value="1")
        format_input = gr.Dropdown(label="Output Format", choices=["json", "txt", "pdf", "csv", "tsv"], value="json")
        aggregate_input = gr.Checkbox(label="Aggregate Metadata", value=True)
        start_button = gr.Button("Start")
        output = gr.Textbox(label="Output")

        start_button.click(process_files, inputs=[file_input, directory_input, output_input, level_input, format_input, aggregate_input], outputs=output)

    demo.launch(inbrowser=True)

def main(test_args=None):
    """
    Main function to execute the script.

    Args:
        test_args (list, optional): List of arguments for testing.
    """
    args = Arguments(test_args).args
    try:
        output_dir = sanitize_path(args.output)
        if not is_safe_path(os.getcwd(), output_dir):
            raise ValueError(f"Unsafe output directory path specified: {output_dir}")

        if args.files or args.directory:
            if args.files:
                sanitized_files = [sanitize_path(file) for file in args.files if is_safe_path(os.getcwd(), sanitize_path(file))]
                metadata = handle_file_upload(sanitized_files, args.level, args.aggregate)
            elif args.directory:
                sanitized_directory = sanitize_path(args.directory)
                if not is_safe_path(os.getcwd(), sanitized_directory):
                    raise ValueError(f"Unsafe directory path specified: {sanitized_directory}")
                metadata = handle_directory(sanitized_directory, args.level, args.aggregate)

            if metadata:
                save_metadata(metadata, output_dir, args.format)
        else:
            gradio_interface()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Uncomment the following line to use manual arguments for testing
    # test_args = ["--directory", "path/to/audio/file/directory", "--output", "./output", "--level", "2", "--format", "json", "--aggregate"]
    # test_args = ["--files", "path/to/audio/file", "--output", "./output", "--level", "2", "--format", "json", "--aggregate"]
    test_args = None
    main(test_args)
