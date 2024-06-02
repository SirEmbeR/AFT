import os
from pathlib import Path
import mimetypes

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

# List of allowed audio MIME types
SUPPORTED_FORMATS = [
    'audio/mpeg',     # .mp3
    'audio/x-mpeg',   # .mp3
    'audio/wav',      # .wav
    'audio/x-wav',    # .wav
    'audio/aac',      # .aac
    'audio/x-aac',    # .aac
    'audio/ogg',      # .ogg
    'audio/vorbis',   # .ogg
    'audio/flac',     # .flac
    'audio/x-flac',   # .flac
    'audio/aiff',     # .aiff
    'audio/x-aiff',   # .aiff
    'audio/m4a',      # .m4a
    'audio/x-m4a',    # .m4a
]

def is_audio_file(file_path):
    try:
        """
        Check if the given file is an audio file based on its MIME type.
    
        Args:
            file_path (str): The path to the file.
    
        Returns:
            bool: True if the file is an audio file, False otherwise.
        """
        # First, use mimetypes to get the MIME type based on the file extension
        mime_type, _ = mimetypes.guess_type(file_path)
        # print(f"Guessed MIME type using mimetypes: {mime_type}")
    
        # If mimetypes did not guess correctly and python-magic is available, use it to detect MIME type based on file content
        if (not mime_type or not mime_type.startswith('audio')) and MAGIC_AVAILABLE:
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(file_path)
            # print(f"Detected MIME type using magic: {mime_type}")
    
        # Check if the MIME type is in the list of allowed audio MIME types
        is_supported = mime_type in SUPPORTED_FORMATS
        # print(f"Is supported format: {is_supported}")
    
        return is_supported
    except ValueError as e:
        raise ValueError(f"Bad file format: {e}") 
        
def sanitize_path(path):
    try:
        if not isinstance(path, str) or not path:
            raise ValueError("Invalid path: Path must be a non-empty string")
    
        # Convert the path to a Path object and resolve it to remove any '..' components
        p = Path(path).resolve()
    
        # Prevent excessively long paths
        if len(str(p)) > 4096:  # 4096 is a typical maximum path length on many systems
            raise ValueError("Path is too long")
        
        if any(part == '..' for part in p.parts):
            raise ValueError("Path traversal detected")
        
        return str(p)
    except ValueError as e:
        raise ValueError(f"Unsafe path detected: {e}") 

def is_safe_path(basedir, path, follow_symlinks=True):
    try:
        sanitized_basedir = Path(sanitize_path(basedir)).resolve()
        sanitized_path = Path(sanitize_path(path)).resolve()

        # Check if the given path is within the basedir or the system's temporary directory
        temp_dir = Path(os.path.realpath(os.path.expanduser(os.getenv('TMP', '/tmp')))).resolve()

        if follow_symlinks:
            abs_base = sanitized_basedir.resolve()
            abs_path = sanitized_path.resolve()
        else:
            abs_base = sanitized_basedir
            abs_path = sanitized_path

        # Check if the absolute path is within the base directory or the temporary directory
        return abs_path.parts[:len(abs_base.parts)] == abs_base.parts or abs_path.parts[:len(temp_dir.parts)] == temp_dir.parts
    except ValueError as e:
        raise ValueError(f"Unsafe path detected: {e}")