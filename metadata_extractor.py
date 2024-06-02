import os
# os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE' # Workarround to persistent OpenMP runtime issue
#   -> issue was triggered by imports for torch/numpy.....
import html
import re
import json
import subprocess
import logging
import hashlib
from datetime import datetime
from mutagen import File, MutagenError
from pydub import AudioSegment
from tinytag import TinyTag
import eyed3
import wave
import librosa
import soundfile as sf
import shutil

from check import sanitize_path, is_safe_path

def sanitize_string(input_string):
    """
    Sanitize a string by escaping HTML characters and removing potentially dangerous content.

    Args:
        input_string (str): The string to sanitize.

    Returns:
        str: The sanitized string.
    """
    if not isinstance(input_string, str):
        return input_string

    # Escape HTML characters
    sanitized = html.escape(input_string)

    # Remove any non-printable characters
    sanitized = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', sanitized)

    # Limit the length of the string to prevent excessively long inputs
    max_length = 1000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized

def sanitize_metadata(metadata):
    """
    Sanitize metadata by ensuring all fields contain safe content.

    Args:
        metadata (dict): The metadata dictionary to sanitize.

    Returns:
        dict: The sanitized metadata dictionary.
    """
    sanitized_metadata = {}
    for key, value in metadata.items():
        if isinstance(value, str):
            sanitized_metadata[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized_metadata[key] = sanitize_metadata(value)  # Recursively sanitize nested dictionaries
        elif isinstance(value, list):
            sanitized_metadata[key] = [
                sanitize_metadata(item) if isinstance(item, dict) else 
                sanitize_string(item) if isinstance(item, str) else 
                item for item in value
            ]
        else:
            sanitized_metadata[key] = value  # Keep the value as is if it's not a string, dict, or list
    return sanitized_metadata

def calculate_checksum(file_path, algorithm='sha256'):
    """
    Calculate the checksum of a file using the specified algorithm.

    Args:
        file_path (str): The path to the file.
        algorithm (str): The hashing algorithm to use (default: 'sha256').

    Returns:
        str: The calculated checksum as a hexadecimal string, or "Unknown" if an error occurs.
    """
    try:
        sanitized_file_path = sanitize_path(file_path)
        if not is_safe_path(os.getcwd(), sanitized_file_path):
            raise ValueError("Unsafe file path specified.")
        hash_func = getattr(hashlib, algorithm)()
        with open(sanitized_file_path, 'rb') as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logging.error(f"Error calculating checksum for {file_path}: {e}")
        return "Unknown"

def get_file_modification_date(file_path):
    """
    Get the last modification date of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        datetime: The modification date, or "Unknown" if an error occurs.
    """
    try:
        sanitized_file_path = sanitize_path(file_path)
        if not is_safe_path(os.getcwd(), sanitized_file_path):
            raise ValueError("Unsafe file path specified.")
        timestamp = os.path.getmtime(sanitized_file_path)
        return datetime.fromtimestamp(timestamp)
    except Exception as e:
        logging.error(f"Error getting modification date for {file_path}: {e}")
        return "Unknown"

def get_creation_date(file_path):
    """
    Get the creation date of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        datetime: The creation date, or "Unknown" if an error occurs.
    """
    try:
        sanitized_file_path = sanitize_path(file_path)
        if not is_safe_path(os.getcwd(), sanitized_file_path):
            raise ValueError("Unsafe file path specified.")
        timestamp = os.path.getctime(sanitized_file_path)
        return datetime.fromtimestamp(timestamp)
    except Exception as e:
        logging.error(f"Error getting creation date for {file_path}: {e}")
        return "Unknown"

def get_access_date(file_path):
    """
    Get the last access date of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        datetime: The access date, or "Unknown" if an error occurs.
    """
    try:
        sanitized_file_path = sanitize_path(file_path)
        if not is_safe_path(os.getcwd(), sanitized_file_path):
            raise ValueError("Unsafe file path specified.")
        timestamp = os.path.getatime(sanitized_file_path)
        return datetime.fromtimestamp(timestamp)
    except Exception as e:
        logging.error(f"Error getting access date for {file_path}: {e}")
        return "Unknown"

def get_bit_depth(file_path):
    """
    Get the bit depth of an audio file.

    Args:
        file_path (str): The path to the audio file.

    Returns:
        int or str: The bit depth in bits, or "Unknown" if it cannot be determined.
    """
    try:
        sanitized_file_path = sanitize_path(file_path)
        if not is_safe_path(os.getcwd(), sanitized_file_path):
            raise ValueError("Unsafe file path specified.")
        try:
            audio = AudioSegment.from_file(sanitized_file_path)
            return audio.sample_width * 8  # sample_width is in bytes
        except:
            pass
    
        try:
            with wave.open(sanitized_file_path, 'rb') as wav_file:
                return wav_file.getsampwidth() * 8
        except:
            pass
    
        return "Unknown"
    except Exception as e:
        logging.error(f"Error getting access date for {file_path}: {e}")
        return "Unknown"

def serialize_mutagen_value(value):
    """
    Serialize a Mutagen tag value to a plain data structure.

    Args:
        value: The Mutagen tag value.

    Returns:
        str or list or dict: The serialized value.
    """
    if isinstance(value, list):
        return [serialize_mutagen_value(v) for v in value]
    if isinstance(value, dict):
        return {k: serialize_mutagen_value(v) for k, v in value.items()}
    if hasattr(value, 'text'):
        return value.text
    return str(value)

def extract_with_ffmpeg(file_path):
    """
    Extract metadata from an audio file using FFmpeg.

    Args:
        file_path (str): The path to the audio file.

    Returns:
        dict: Extracted metadata dictionary, or None if an error occurs.
    """
    try:
        logging.debug(f"Opening file with FFmpeg: {file_path}")
        sanitized_file_path = sanitize_path(file_path)
        if not is_safe_path(os.getcwd(), sanitized_file_path):
            raise ValueError("Unsafe file path specified.")

        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format', '-of', 'json', sanitized_file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        if result.returncode != 0:
            raise Exception(result.stderr)
        info = json.loads(result.stdout)
        format_info = info['format']
        metadata = {
            "Source": "FFmpeg",
            "Info": {
                "Format": format_info.get('format_name', "Unknown"),
                "Duration": float(format_info.get('duration', 0)),
                "Size": int(format_info.get('size', 0)),
                "Bit Rate": int(format_info.get('bit_rate', 0)),
                "Extra Info": format_info.get('tags', {})
            },
            "Extra": format_info
        }
        return sanitize_metadata(metadata)
    except Exception as e:
        logging.error(f"FFmpeg error extracting metadata from {file_path}: {e}")
    return None

def extract_with_soundfile(file_path):
    """
    Extract metadata from an audio file using SoundFile.

    Args:
        file_path (str): The path to the audio file.

    Returns:
        dict: Extracted metadata dictionary, or None if an error occurs.
    """
    try:
        logging.debug(f"Opening file with soundfile: {file_path}")
        sanitized_file_path = sanitize_path(file_path)
        if not is_safe_path(os.getcwd(), sanitized_file_path):
            raise ValueError("Unsafe file path specified.")

        info = sf.info(sanitized_file_path, verbose=True)
        metadata = {
            "Source": "SoundFile",
            "Info": {
                "Format": info.format,
                "Subtype": info.subtype,
                "Sample Rate": info.samplerate,
                "Channels": info.channels,
                "Duration": info.duration,
                "Frames": info.frames,
            },
            "Extra": {
                "Endian": info.endian,
                "Extra Info": info.extra_info
            }
        }
        return sanitize_metadata(metadata)
    except Exception as e:
        logging.error(f"SoundFile error extracting metadata from {file_path}: {e}")
    return None

def build_metadata_dict(file_path):
    """
    Build a base metadata dictionary for an audio file.

    Args:
        file_path (str): The path to the audio file.

    Returns:
        dict: Base metadata dictionary.
    """
    sanitized_file_path = sanitize_path(file_path)
    if not is_safe_path(os.getcwd(), sanitized_file_path):
        raise ValueError("Unsafe file path specified.")

    return {
        "Source": "Aggregated",
        "File Name": os.path.basename(sanitized_file_path),
        "Checksum": calculate_checksum(sanitized_file_path),
        "Creation Date": str(get_creation_date(sanitized_file_path)),
        "Modification Date": str(get_file_modification_date(sanitized_file_path)),
        "Access Date": str(get_access_date(sanitized_file_path)),
        "Title": "Unknown",
        "Artist": "Unknown",
        "Album": "Unknown",
        "Year": "Unknown",
        "Genre": "Unknown",
        "Track Number": "Unknown",
        "Disc Number": "Unknown",
        "Composer": "Unknown",
        "Conductor": "Unknown",
        "Lyrics": "Unknown",
        "Language": "Unknown",
        "Geolocation": {
            "Latitude": "Unknown",
            "Longitude": "Unknown"
        },
        "Device Information": {
            "Encoder": "Unknown",
            "Software": "Unknown"
        },
        "Info": {
            "Format": "Unknown",
            "Type": "Audio",
            "Subtype": "Unknown",
            "Sample Rate": "Unknown",
            "Bit Rate": "Unknown",
            "Encoding": "Unknown",
            "Channels": "Unknown",
            "Bit Depth": get_bit_depth(sanitized_file_path),
            "File Size": os.path.getsize(sanitized_file_path),
            "Duration": "Unknown",
        },
        "Additional": {},
        "Extra": {}
    }

def extract_metadata(file_path, level, aggregate=True):
    """
    Extract metadata from an audio file using multiple extractors.

    Args:
        file_path (str): The path to the audio file.
        level (int): Processing level (1 or 2).
        aggregate (bool): Whether to aggregate metadata from all extractors.

    Returns:
        dict or list: Aggregated metadata dictionary or list of metadata dictionaries.
    """
    sanitized_file_path = sanitize_path(file_path)
    if not is_safe_path(os.getcwd(), sanitized_file_path):
        raise ValueError("Unsafe file path specified.")
        
    base_metadata = build_metadata_dict(sanitized_file_path)
    
    try:
        level = int(level)
    except ValueError:
        raise ValueError("Level must be an integer")

    extractors = [
        ("FFmpeg", extract_with_ffmpeg),
        ("SoundFile", extract_with_soundfile),
        ("Mutagen", extract_with_mutagen),
        ("TinyTag", extract_with_tinytag),
        ("eyeD3", extract_with_eyed3),
        ("MediaInfo", extract_with_mediainfo)
    ]

    all_metadata = []
    for name, extractor in extractors:
        metadata = extractor(sanitized_file_path)
        if metadata:
            metadata["Source"] = name
            all_metadata.append(metadata)
                 
    if aggregate:
        for new_metadata in all_metadata:
            merge_metadata(base_metadata, new_metadata)
        if level == 2:
            base_metadata = add_level_2_metadata(sanitized_file_path, base_metadata)
        return base_metadata
    else:
        if level == 2:
            for md in all_metadata:
                md = add_level_2_metadata(sanitized_file_path, md)
        return all_metadata

def add_level_2_metadata(file_path, metadata, enable_level_2=True):
    """
    Add level 2 metadata to the base metadata dictionary.

    Args:
        file_path (str): The path to the audio file.
        metadata (dict): The base metadata dictionary.
        enable_level_2 (bool): Whether to enable level 2 metadata extraction.

    Returns:
        dict: Updated metadata dictionary.
    """
    if not enable_level_2:
        logging.info("Level 2 metadata extraction is temporarily disabled due to hardware/software issues.")
        return metadata

    try:
        sanitized_file_path = sanitize_path(file_path)
        if not is_safe_path(os.getcwd(), sanitized_file_path):
            raise ValueError("Unsafe file path specified.")

        audio_segment = AudioSegment.from_file(sanitized_file_path)
        rms_loudness = audio_segment.rms
        samples, sample_rate = librosa.load(sanitized_file_path, sr=None)
        
        try:
            tempo = librosa.beat.tempo(y=samples, sr=sample_rate)[0]
        except Exception as e:
            logging.error(f"Error calculating tempo: {e}")
            tempo = "Unknown"

        try:
            chroma_stft = librosa.feature.chroma_stft(y=samples, sr=sample_rate)
            chroma_stft_mean = chroma_stft.mean(axis=1).tolist()
        except Exception as e:
            logging.error(f"Error calculating chroma_stft: {e}")
            chroma_stft_mean = "Unknown"

        try:
            spectral_centroid = librosa.feature.spectral_centroid(y=samples, sr=sample_rate)
            spectral_centroid_mean = spectral_centroid.mean().tolist()
        except Exception as e:
            logging.error(f"Error calculating spectral_centroid: {e}")
            spectral_centroid_mean = "Unknown"

        try:
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=samples, sr=sample_rate)
            spectral_bandwidth_mean = spectral_bandwidth.mean().tolist()
        except Exception as e:
            logging.error(f"Error calculating spectral_bandwidth: {e}")
            spectral_bandwidth_mean = "Unknown"

        try:
            spectral_contrast = librosa.feature.spectral_contrast(y=samples, sr=sample_rate)
            spectral_contrast_mean = spectral_contrast.mean(axis=1).tolist()
        except Exception as e:
            logging.error(f"Error calculating spectral_contrast: {e}")
            spectral_contrast_mean = "Unknown"

        try:
            spectral_flatness = librosa.feature.spectral_flatness(y=samples)
            spectral_flatness_mean = spectral_flatness.mean().tolist()
        except Exception as e:
            logging.error(f"Error calculating spectral_flatness: {e}")
            spectral_flatness_mean = "Unknown"

        try:
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y=samples)
            zero_crossing_rate_mean = zero_crossing_rate.mean().tolist()
        except Exception as e:
            logging.error(f"Error calculating zero_crossing_rate: {e}")
            zero_crossing_rate_mean = "Unknown"

        level_2_metadata = {
            "Info": {
                "RMS Loudness": rms_loudness,
                "Tempo": tempo,
            },
            "Additional": {
                "Chroma STFT": chroma_stft_mean,
                "Spectral Centroid": spectral_centroid_mean,
                "Spectral Bandwidth": spectral_bandwidth_mean,
                "Spectral Contrast": spectral_contrast_mean,
                "Spectral Flatness": spectral_flatness_mean,
                "Zero Crossing Rate": zero_crossing_rate_mean,
            }
        }

        merge_metadata(metadata, level_2_metadata)
        return metadata
        
    except Exception as e:
        logging.error(f"Error in add_level_2_metadata: {e}")
        # logging.info("Level 2 metadata extraction is temporarily disabled due to hardware/software issues.")
        return metadata
        
    except Exception as e:
        logging.error(f"Error in add_level_2_metadata: {e}")
        # logging.info("Level 2 metadata extraction is temporarily disabled due to hardware/software issues.")
        return metadata

def merge_metadata(base, new):
    """
    Merge new metadata into the base metadata dictionary.

    Args:
        base (dict): The base metadata dictionary.
        new (dict): The new metadata dictionary to merge.

    Returns:
        None
    """
    for key, value in new.items():
        if isinstance(value, dict):
            if key not in base:
                base[key] = {}
            merge_metadata(base[key], value)
        else:
            if base.get(key, "Unknown") == "Unknown" and value != "Unknown":
                base[key] = value
            elif key not in base:
                base["Extra"][key] = value

def extract_with_mutagen(file_path):
    """
    Extract metadata from an audio file using Mutagen.

    Args:
        file_path (str): The path to the audio file.

    Returns:
        dict: Extracted metadata dictionary, or None if an error occurs.
    """
    try:
        logging.debug(f"Opening file with Mutagen: {file_path}")
        sanitized_file_path = sanitize_path(file_path)
        if not is_safe_path(os.getcwd(), sanitized_file_path):
            raise ValueError("Unsafe file path specified.")
            
        audio = File(sanitized_file_path)
        if not audio:
            raise MutagenError(f"Could not open file: {sanitized_file_path}")

        geolocation = {
            "Latitude": audio.tags.get('GEO_LAT', "Unknown") if audio.tags else "Unknown",
            "Longitude": audio.tags.get('GEO_LON', "Unknown") if audio.tags else "Unknown"
        }

        device_info = {
            "Encoder": serialize_mutagen_value(audio.tags.get('TENC', 'Unknown') if audio.tags else "Unknown"),
            "Software": serialize_mutagen_value(audio.tags.get('TSSE', 'Unknown') if audio.tags else "Unknown")
        }

        metadata = {
            "Source": "Mutagen",
            "Title": serialize_mutagen_value(audio.tags.get('TIT2', "Unknown") if audio.tags else "Unknown"),
            "Artist": serialize_mutagen_value(audio.tags.get('TPE1', "Unknown") if audio.tags else "Unknown"),
            "Album": serialize_mutagen_value(audio.tags.get('TALB', "Unknown") if audio.tags else "Unknown"),
            "Year": serialize_mutagen_value(audio.tags.get('TDRC', "Unknown") if audio.tags else "Unknown"),
            "Genre": serialize_mutagen_value(audio.tags.get('TCON', "Unknown") if audio.tags else "Unknown"),
            "Track Number": serialize_mutagen_value(audio.tags.get('TRCK', "Unknown") if audio.tags else "Unknown"),
            "Disc Number": serialize_mutagen_value(audio.tags.get('TPOS', "Unknown") if audio.tags else "Unknown"),
            "Composer": serialize_mutagen_value(audio.tags.get('TCOM', "Unknown") if audio.tags else "Unknown"),
            "Conductor": serialize_mutagen_value(audio.tags.get('TPE3', "Unknown") if audio.tags else "Unknown"),
            "Lyrics": serialize_mutagen_value(audio.tags.get('USLT::eng', "Unknown") if audio.tags else "Unknown"),  
            "Language": serialize_mutagen_value(audio.tags.get('TLAN', "Unknown") if audio.tags else "Unknown"),
            "Geolocation": geolocation,
            "Device Information": device_info,
            "Info": {
                "Format": serialize_mutagen_value(audio.mime[0] if audio.mime else "Unknown"),
                "Sample Rate": audio.info.sample_rate if hasattr(audio.info, 'sample_rate') else "Unknown",
                "Bit Rate": audio.info.bitrate if hasattr(audio.info, 'bitrate') else "Unknown",
                "Encoding": "CBR" if hasattr(audio.info, 'bitrate_mode') and audio.info.bitrate_mode == 0 else "VBR",
                "Channels": audio.info.channels if hasattr(audio.info, 'channels') else "Unknown",
                "Duration": audio.info.length if hasattr(audio.info, 'length') else "Unknown",
            },
            "Extra": serialize_mutagen_value(audio.info.pprint())
        }
        return sanitize_metadata(metadata)
    except MutagenError as e:
        logging.error(f"MutagenError extracting metadata from {file_path}: {e}")
    except Exception as e:
        logging.error(f"Error extracting metadata from {file_path} with Mutagen: {e}")

    return None

def extract_with_tinytag(file_path):
    """
    Extract metadata from an audio file using TinyTag.

    Args:
        file_path (str): The path to the audio file.

    Returns:
        dict: Extracted metadata dictionary, or None if an error occurs.
    """
    try:
        logging.debug(f"Opening file with TinyTag: {file_path}")
        sanitized_file_path = sanitize_path(file_path)
        if not is_safe_path(os.getcwd(), sanitized_file_path):
            raise ValueError("Unsafe file path specified.")

        tag = TinyTag.get(sanitized_file_path)
        metadata = {
            "Source": "TinyTag",
            "Title": tag.title if tag.title else "Unknown",
            "Artist": tag.artist if tag.artist else "Unknown",
            "Album": tag.album if tag.album else "Unknown",
            "Year": tag.year if tag.year else "Unknown",
            "Genre": tag.genre if tag.genre else "Unknown",
            "Track Number": tag.track if tag.track else "Unknown",
            "Disc Number": tag.disc if tag.disc else "Unknown",
            "Info": {
                "Sample Rate": tag.samplerate if tag.samplerate else "Unknown",
                "Bit Rate": tag.bitrate if tag.bitrate else "Unknown",
                "Channels": tag.channels if tag.channels else "Unknown",
                "Duration": tag.duration if tag.duration else "Unknown",
            },
            "Extra": tag.as_dict()
        }
        return sanitize_metadata(metadata)
    except Exception as e:
        logging.error(f"TinyTag error extracting metadata from {file_path}: {e}")
    return None

def extract_with_eyed3(file_path):
    """
    Extract metadata from an audio file using eyeD3.

    Args:
        file_path (str): The path to the audio file.

    Returns:
        dict: Extracted metadata dictionary, or None if an error occurs.
    """
    try:
        logging.debug(f"Opening file with eyeD3: {file_path}")
        sanitized_file_path = sanitize_path(file_path)
        if not is_safe_path(os.getcwd(), sanitized_file_path):
            raise ValueError("Unsafe file path specified.")

        audio = eyed3.load(sanitized_file_path)
        if audio is None:
            return None
        
        extra_info = {}
        try:
            extra_info = {
                "bit_rate": audio.info.bit_rate_str,
                "sample_rate": audio.info.sample_freq,
                "channels": audio.info.mode,
                "length": audio.info.time_secs
            }
        except AttributeError as e:
            logging.error(f"AttributeError: {e}")
        
        metadata = {
            "Source": "eyeD3",
            "Title": audio.tag.title if audio.tag and audio.tag.title else "Unknown",
            "Artist": audio.tag.artist if audio.tag and audio.tag.artist else "Unknown",
            "Album": audio.tag.album if audio.tag and audio.tag.album else "Unknown",
            "Year": audio.tag.release_date if audio.tag and audio.tag.release_date else "Unknown",
            "Genre": audio.tag.genre.name if audio.tag and audio.tag.genre else "Unknown",
            "Track Number": audio.tag.track_num[0] if audio.tag and audio.tag.track_num else "Unknown",
            "Disc Number": audio.tag.disc_num[0] if audio.tag and audio.tag.disc_num else "Unknown",
            "Composer": audio.tag.composer if audio.tag and audio.tag.composer else "Unknown",
            "Info": {
                "Format": "MP3",
                "Bit Rate": audio.info.bit_rate[1] if audio.info and hasattr(audio.info, 'bit_rate') else "Unknown",
                "Encoding": "CBR" if audio.info and hasattr(audio.info, 'bitrate_mode') and audio.info.bitrate_mode == 'cbr' else "VBR",
                "Channels": audio.info.mode if audio.info and hasattr(audio.info, 'mode') else "Unknown",
                "Duration": audio.info.time_secs if audio.info and hasattr(audio.info, 'time_secs') else "Unknown",
            },
            "Extra": extra_info
        }
        return sanitize_metadata(metadata)
    except Exception as e:
        logging.error(f"eyeD3 error extracting metadata from {file_path}: {e}")
    return None

def extract_with_mediainfo(file_path):
    """
    Extract metadata from an audio file using MediaInfo.

    Args:
        file_path (str): The path to the audio file.

    Returns:
        dict: Extracted metadata dictionary, or None if an error occurs.
    """
    try:
        logging.debug(f"Opening file with MediaInfo: {file_path}")
        sanitized_file_path = sanitize_path(file_path)
        if not is_safe_path(os.getcwd(), sanitized_file_path):
            raise ValueError("Unsafe file path specified.")

        mediainfo_path = shutil.which("mediainfo")
        if mediainfo_path is None:
            raise FileNotFoundError("mediainfo executable not found in PATH")
        
        result = subprocess.run(
            [mediainfo_path, '--Output=JSON', sanitized_file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        if result.returncode != 0:
            raise Exception(result.stderr)
        info = json.loads(result.stdout)
        general = info['media']['track'][0]
        audio = info['media']['track'][1]

        geolocation = {
            "Latitude": general.get('Location_Latitude', "Unknown"),
            "Longitude": general.get('Location_Longitude', "Unknown")
        }

        device_info = {
            "Encoder": general.get('Encoded_Library/String', 'Unknown'),
            "Software": general.get('Encoded_Application', 'Unknown')
        }

        metadata = {
            "Source": "MediaInfo",
            "Title": general.get('Title', "Unknown"),
            "Artist": general.get('Performer', "Unknown"),
            "Album": general.get('Album', "Unknown"),
            "Year": general.get('Recorded_Date', "Unknown"),
            "Genre": general.get('Genre', "Unknown"),
            "Track Number": general.get('Track_Position', "Unknown"),
            "Disc Number": general.get('Part', "Unknown"),
            "Composer": general.get('Composer', "Unknown"),
            "Conductor": general.get('Conductor', "Unknown"),
            "Lyrics": general.get('Lyrics', "Unknown"),
            "Language": general.get('Language', "Unknown"),
            "Geolocation": geolocation,
            "Device Information": device_info,
            "Info": {
                "Format": general.get('Format', "Unknown"),
                "Sample Rate": audio.get('SamplingRate', "Unknown"),
                "Bit Rate": audio.get('BitRate', "Unknown"),
                "Encoding": audio.get('Format_Settings_Mode', "Unknown"),
                "Channels": audio.get('Channel(s)', "Unknown"),
                "Bit Depth": audio.get('BitDepth', "Unknown"),
                "Duration": general.get('Duration', "Unknown"),
            },
            "Extra": info
        }
        return sanitize_metadata(metadata)
    except FileNotFoundError as e:
        logging.error(f"MediaInfo error: {e}")
    except Exception as e:
        logging.error(f"MediaInfo error extracting metadata from {file_path}: {e}")
    return None

# Example usage:
# file_path = "path/to/audio/file"
# metadata = extract_metadata(file_path, level=2, aggregate=True)
# print(json.dumps(metadata, indent=4))
