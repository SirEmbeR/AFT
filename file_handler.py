import os
from metadata_extractor import extract_metadata
import json
import csv
from datetime import datetime
from fpdf import FPDF
import logging

from check import sanitize_path, is_safe_path, is_audio_file, SUPPORTED_FORMATS


def handle_file_upload(files, level, aggregate):
    """
    Handle the upload of audio files and extract their metadata.

    Args:
        files (list): List of file paths to process.
        level (int): Processing level (1 or 2).
        aggregate (bool): Whether to aggregate metadata from all files.

    Returns:
        list: List of extracted metadata dictionaries.
    """
    try:
        results = []
        for file in files:
            try:
                sanitized_file_path = sanitize_path(file)
                if not is_safe_path(os.getcwd(), sanitized_file_path):
                    raise ValueError("Unsafe file path specified.")
                if is_audio_file(sanitized_file_path):
                    metadata = extract_metadata(sanitized_file_path, level, aggregate)
                    if metadata:
                        results.append(metadata)
                else:
                    logging.error(f"Incorrect file format: {sanitized_file_path}")
            except Exception as e:
                logging.error(f"Unexpected error processing file {file}: {e}")
        return results
    except Exception as e:
        logging.error(f"Error in handle file upload: {e}")
        return None

def handle_directory(directory, level, aggregate):
    """
    Handle a directory of audio files and extract their metadata.

    Args:
        directory (str): Path to the directory to process.
        level (int): Processing level (1 or 2).
        aggregate (bool): Whether to aggregate metadata from all files.

    Returns:
        list: List of extracted metadata dictionaries.
    """
    try:
        sanitized_directory = sanitize_path(directory)
        if not is_safe_path(os.getcwd(), sanitized_directory):
            raise ValueError("Unsafe directory path specified.")
            
        if not os.path.isdir(sanitized_directory):
            raise ValueError(f"Invalid directory path: {sanitized_directory}")
            
        results = []
        for root, _, files in os.walk(sanitized_directory):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    sanitized_file_path = sanitize_path(file_path)
                    if is_audio_file(sanitized_file_path):
                        metadata = extract_metadata(sanitized_file_path, level, aggregate)
                        if metadata:
                            results.append(metadata)
                    else:
                        logging.error(f"Incorrect file format: {sanitized_file_path}")
                except Exception as e:
                    logging.error(f"Unexpected error processing file {file}: {e}")
        logging.debug(f"Files processed and results collected {len(results)}")                
        return results
    except ValueError as e:
        logging.error(f"Error in handle directory: {e}")
        return None

def save_metadata(metadata, output_dir, output_format):
    """
    Save the extracted metadata to a file in the specified format.

    Args:
        metadata (list): List of metadata dictionaries to save.
        output_dir (str): Directory to save the metadata files.
        output_format (str): Format to save the metadata in (json, csv, tsv, txt, pdf).

    Raises:
        ValueError: If the output directory path is unsafe.
        Exception: If an error occurs while saving metadata.
    """
    sanitized_output_dir = sanitize_path(output_dir)
    if not is_safe_path(os.getcwd(), sanitized_output_dir):
        raise ValueError("Unsafe output directory path specified.")
        
    os.makedirs(sanitized_output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    try:
        if output_format == "json":
            output_path = os.path.join(sanitized_output_dir, f"metadata_{timestamp}.json")
            with open(output_path, 'w') as outfile:
                json.dump(metadata, outfile, indent=4)
        elif output_format in ["csv", "tsv"]:
            output_path = os.path.join(sanitized_output_dir, f"metadata_{timestamp}.{output_format}")
            delimiter = '\t' if output_format == "tsv" else ','
            with open(output_path, 'w', newline='') as outfile:
                writer = csv.writer(outfile, delimiter=delimiter)
                headers = metadata[0].keys()
                writer.writerow(headers)
                for data in metadata:
                    writer.writerow([data[key] for key in headers])
        elif output_format == "txt":
            output_path = os.path.join(sanitized_output_dir, f"metadata_{timestamp}.txt")
            with open(output_path, 'w') as outfile:
                for data in metadata:
                    for key, value in data.items():
                        if isinstance(value, dict):
                            outfile.write(f"{key}:\n")
                            for sub_key, sub_value in value.items():
                                outfile.write(f"  {sub_key}: {sub_value}\n")
                        else:
                            outfile.write(f"{key}: {value}\n")
                    outfile.write("\n")
        elif output_format == "pdf":
            output_path = os.path.join(sanitized_output_dir, f"metadata_{timestamp}.pdf")
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for data in metadata:
                for key, value in data.items():
                    if isinstance(value, dict):
                        pdf.cell(200, 10, txt=f"{key}:", ln=True, align='L')
                        for sub_key, sub_value in value.items():
                            pdf.cell(200, 10, txt=f"  {sub_key}: {sub_value}", ln=True, align='L')
                    else:
                        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True, align='L')
                pdf.cell(200, 10, txt="", ln=True, align='L')  # Blank line between records
            pdf.output(output_path)

        logging.info(f"Metadata saved to {output_path}.")
    except Exception as e:
        logging.error(f"Error saving metadata: {e}")
        raise

def format_metadata(metadata, format):
    """
    Format the metadata into the specified format.

    Args:
        metadata (list): List of metadata dictionaries to format.
        format (str): Format to convert the metadata to (json, csv, tsv, txt, pdf).

    Returns:
        str: Formatted metadata as a string or bytes for PDF.

    Raises:
        Exception: If an error occurs while formatting metadata.
    """
    try:
        if format == "json":
            return json.dumps(metadata, indent=4)
        elif format in ["csv", "tsv"]:
            output = []
            delimiter = '\t' if format == "tsv" else ','
            headers = metadata[0].keys()
            output.append(delimiter.join(headers))
            for data in metadata:
                output.append(delimiter.join([str(data[key]) for key in headers]))
            return "\n".join(output)
        elif format == "txt":
            output = []
            for data in metadata:
                for key, value in data.items():
                    if isinstance(value, dict):
                        output.append(f"{key}:")
                        for sub_key, sub_value in value.items():
                            output.append(f"  {sub_key}: {sub_value}")
                    else:
                        output.append(f"{key}: {value}")
                output.append("")
            return "\n".join(output)
        elif format == "pdf":
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for data in metadata:
                for key, value in data.items():
                    if isinstance(value, dict):
                        pdf.cell(200, 10, txt=f"{key}:", ln=True, align='L')
                        for sub_key, sub_value in value.items():
                            pdf.cell(200, 10, txt=f"  {sub_key}: {sub_value}", ln=True, align='L')
                    else:
                        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True, align='L')
                pdf.cell(200, 10, txt="", ln=True, align='L')  # Blank line between records
            return pdf.output(dest='S').encode('latin1')
        return ""
    except Exception as e:
        logging.error(f"Error formatting metadata: {e}")
        raise
