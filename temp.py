# -*- coding: utf-8 -*-
"""
Created on Tue May 28 19:14:16 2024

@author: RosiD
"""

import soundfile as sf

audio = r"C:\Users\Vartotojas\Desktop\Studijos\Software Quality and Security\Project 2\AFT\data\Free_Test_Data_1MB_MP3.mp3"

audio_info = sf.info(audio, verbose=True)

print(audio_info)


#%%

from mutagen.easyid3 import EasyID3

audio = r"C:\Users\Vartotojas\Desktop\Studijos\Software Quality and Security\Project 2\AFT\data\Free_Test_Data_1MB_MP3.mp3"

audio_info = EasyID3(audio)

print(audio_info)


#%%

import eyed3

audio = r"C:\Users\Vartotojas\Desktop\Studijos\Software Quality and Security\Project 2\AFT\data\Free_Test_Data_1MB_MP3.mp3"

audio_info = eyed3.load(audio)
print(audio_info.tag.title)



#%%

from pydub import AudioSegment

audio = r"C:\Users\Vartotojas\Desktop\Studijos\Software Quality and Security\Project 2\AFT\data\Free_Test_Data_1MB_MP3.mp3"

audio_info = AudioSegment.from_file(audio)
print(audio_info.frame_rate)

#%%

from tinytag import TinyTag

audio = r"C:\Users\Vartotojas\Desktop\Studijos\Software Quality and Security\Project 2\AFT\data\Free_Test_Data_1MB_MP3.mp3"

tag = TinyTag.get(audio)
print(tag.title, tag.artist)



#%%

import subprocess

audio = r"C:\Users\Vartotojas\Desktop\Studijos\Software Quality and Security\Project 2\AFT\data\Free_Test_Data_1MB_MP3.mp3"

def get_metadata(file_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_name", "-of",
             "default=noprint_wrappers=1", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True)
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr.decode('utf-8')}")
        return None

metadata = get_metadata(audio)

if metadata:
    print(metadata)

#%%

"""
MP3 Header (ID3 Tags)

MP3 files often contain ID3 tags for metadata, usually at the beginning of the file. The ID3 tag header is 10 bytes long.

    Header Structure:
        Bytes 0-2: ID3 identifier (ID3).
        Byte 3: Version (e.g., 3 for ID3v2.3).
        Byte 4: Revision (e.g., 0).
        Byte 5: Flags.
        Bytes 6-9: Size (4 bytes, excluding the header).
"""

import struct

def read_mp3_header(file_path):
    with open(file_path, 'rb') as f:
        header = f.read(10)
        
        if header[:3] == b'ID3':
            _, version, flags, size = struct.unpack('>3sBBB4s', header)
            size = int.from_bytes(size, byteorder='big')
            print(f"ID3 version: 2.{version}")
            print(f"Flags: {flags}")
            print(f"Size: {size} bytes")
            
            # Read the extended header and frames if present
            frames_data = f.read(size)
            while frames_data:
                frame_header = frames_data[:10]
                frame_id, frame_size = struct.unpack('>4sI', frame_header[:8])
                frame_size = int.from_bytes(frame_header[4:8], byteorder='big')
                frame_data = frames_data[10:10 + frame_size]
                print(f"Frame ID: {frame_id.decode('utf-8')}")
                print(f"Frame Size: {frame_size}")
                print(f"Frame Data: {frame_data}")
                frames_data = frames_data[10 + frame_size:]
        else:
            print("No ID3 tag found")

# Replace with the path to your MP3 file
mp3_file = r"C:\Users\Vartotojas\Desktop\Studijos\Software Quality and Security\Project 2\AFT\data\Free_Test_Data_1MB_MP3.mp3"
read_mp3_header(mp3_file)



#%%

"""
WAV Header

WAV files use the RIFF (Resource Interchange File Format) and have a structured header. 
They may also contain additional chunks such as "LIST" for metadata.

    Header Structure:
        Bytes 0-3: Chunk ID ("RIFF").
        Bytes 4-7: Chunk Size (size of the rest of the file).
        Bytes 8-11: Format ("WAVE").
        Bytes 12-15: Subchunk1 ID ("fmt ").
        Bytes 16-19: Subchunk1 Size (16 for PCM).
        Bytes 20-21: Audio Format (1 for PCM).
        Bytes 22-23: Number of Channels.
        Bytes 24-27: Sample Rate.
        Bytes 28-31: Byte Rate.
        Bytes 32-33: Block Align.
        Bytes 34-35: Bits per Sample.
        Bytes 36-39: Subchunk2 ID ("data").
        Bytes 40-43: Subchunk2 Size (number of bytes in the data).
"""

import struct

def read_wav_header(file_path):
    with open(file_path, 'rb') as f:
        # Read the first 44 bytes of the file for the WAV header
        header = f.read(44)
        
        # Unpack the RIFF header
        riff, size, fformat = struct.unpack('<4sI4s', header[:12])
        if riff != b'RIFF' or fformat != b'WAVE':
            print("Not a valid WAV file")
            return
        
        # Unpack the fmt subchunk
        fmt_chunk_marker, fmt_chunk_size = struct.unpack('<4sI', header[12:20])
        if fmt_chunk_marker != b'fmt ':
            print("Invalid fmt chunk")
            return
        
        audio_format, num_channels, sample_rate = struct.unpack('<HHI', header[20:28])
        byte_rate, block_align, bits_per_sample = struct.unpack('<IHH', header[28:36])
        
        print(f"Audio Format: {audio_format}")
        print(f"Number of Channels: {num_channels}")
        print(f"Sample Rate: {sample_rate} Hz")
        print(f"Byte Rate: {byte_rate} Bps")
        print(f"Block Align: {block_align} bytes")
        print(f"Bits Per Sample: {bits_per_sample} bits")
        
        # Read additional chunks
        while True:
            chunk_header = f.read(8)
            if len(chunk_header) < 8:
                break
            chunk_id, chunk_size = struct.unpack('<4sI', chunk_header)
            chunk_data = f.read(chunk_size)
            print(f"Chunk ID: {chunk_id.decode('utf-utf-8')}")
            print(f"Chunk Size: {chunk_size}")
            # Process known chunk types, such as "LIST" for metadata
            if chunk_id == b'LIST':
                print(f"LIST Chunk Data: {chunk_data}")

# Replace with the path to your WAV file
wav_file = r"C:\Users\Vartotojas\Desktop\Studijos\Software Quality and Security\Project 2\AFT\data\Free_Test_Data_1MB_WAV.wav"
read_wav_header(wav_file)

#%%

"""
OGG Header

OGG files start with the "OggS" capture pattern and have structured headers for each page. 
OGG files can contain multiple logical streams, each with its own headers and data segments.

    Header Structure:
        Bytes 0-3: Capture Pattern ("OggS").
        Byte 4: Version.
        Byte 5: Header Type.
        Bytes 6-13: Granule Position.
        Bytes 14-17: Bitstream Serial Number.
        Bytes 18-21: Page Sequence Number.
        Bytes 22-25: Checksum.
        Bytes 26-26+N: Page Segments.
"""

import struct

def read_ogg_header(file_path):
    with open(file_path, 'rb') as f:
        header = f.read(27)
        
        if header[:4] != b'OggS':
            print("Not a valid OGG file")
            return
        
        version, header_type = struct.unpack('<BB', header[4:6])
        granule_pos = struct.unpack('<Q', header[6:14])[0]
        bitstream_serial, page_seq_num, checksum = struct.unpack('<III', header[14:26])
        
        print(f"Version: {version}")
        print(f"Header Type: {header_type}")
        print(f"Granule Position: {granule_pos}")
        print(f"Bitstream Serial Number: {bitstream_serial}")
        print(f"Page Sequence Number: {page_seq_num}")
        print(f"Checksum: {checksum}")
        
        # Read additional pages if necessary
        while True:
            page_header = f.read(27)
            if len(page_header) < 27:
                break
            if page_header[:4] != b'OggS':
                break
            version, header_type = struct.unpack('<BB', page_header[4:6])
            granule_pos = struct.unpack('<Q', page_header[6:14])[0]
            bitstream_serial, page_seq_num, checksum = struct.unpack('<III', page_header[14:26])
            print(f"Page - Version: {version}, Header Type: {header_type}, Granule Position: {granule_pos}, Bitstream Serial: {bitstream_serial}, Page Sequence: {page_seq_num}, Checksum: {checksum}")

# Replace with the path to your OGG file
ogg_file = r"C:\Users\Vartotojas\Desktop\Studijos\Software Quality and Security\Project 2\AFT\data\Free_Test_Data_2MB_OGG.ogg"
read_ogg_header(ogg_file)


#%%

"""
FLAC Header

FLAC files have a specific marker and metadata blocks, with STREAMINFO being the first block containing vital information. 
FLAC files can contain multiple metadata blocks such as SEEKTABLE, VORBIS_COMMENT, etc.

    Header Structure:
        Bytes 0-3: Marker ("fLaC").
        Bytes 4-5: Minimum Block Size.
        Bytes 6-7: Maximum Block Size.
        Bytes 8-10: Minimum Frame Size.
        Bytes 11-13: Maximum Frame Size.
        Bytes 14-18: Sample Rate, Channels, Bits per Sample, Total Samples.
        Bytes 19-34: MD5 Signature.
"""

import struct

def read_flac_header(file_path):
    with open(file_path, 'rb') as f:
        marker = f.read(4)
        
        if marker != b'fLaC':
            print("Not a valid FLAC file")
            return
        
        header = f.read(34)
        
        min_block_size, max_block_size = struct.unpack('>HH', header[0:4])
        min_frame_size = int.from_bytes(header[4:7], byteorder='big')
        max_frame_size = int.from_bytes(header[7:10], byteorder='big')
        
        sample_rate, channels, bits_per_sample, total_samples = struct.unpack('>HBBI', header[10:18])
        sample_rate = (sample_rate >> 4) & 0xFFFFF
        channels = (channels >> 1) & 0x07
        bits_per_sample = ((bits_per_sample & 0x01) << 4) | (total_samples >> 28)
        total_samples &= 0x0FFFFFFF
        
        md5 = header[18:34].hex()
        
        print(f"Min Block Size: {min_block_size}")
        print(f"Max Block Size: {max_block_size}")
        print(f"Min Frame Size: {min_frame_size}")
        print(f"Max Frame Size: {max_frame_size}")
        print(f"Sample Rate: {sample_rate} Hz")
        print(f"Channels: {channels}")
        print(f"Bits Per Sample: {bits_per_sample}")
        print(f"Total Samples: {total_samples}")
        print(f"MD5 Signature: {md5}")
        
        # Read additional metadata blocks
        while True:
            block_header = f.read(4)
            if len(block_header) < 4:
                break
            block_type, block_size = struct.unpack('>BI', block_header)
            block_data = f.read(block_size)
            print(f"Metadata Block Type: {block_type & 0x7F}")
            print(f"Metadata Block Size: {block_size}")
            print(f"Metadata Block Data: {block_data}")

# Replace with the path to your FLAC file
flac_file = r"C:\Users\Vartotojas\Desktop\Studijos\Software Quality and Security\Project 2\AFT\data\FLAC_3MB.flac"
read_flac_header(flac_file)


#%%

"""
MP4 Header

MP4 files use the ISO Base Media File Format and contain various boxes (atoms). The 'ftyp' box is typically the first. 
MP4 files can have multiple boxes, such as moov, mdat, free, udta, etc.

    Header Structure:
        Bytes 0-3: Box Size.
        Bytes 4-7: Box Type ("ftyp").
        Bytes 8-11: Major Brand.
        Bytes 12-15: Minor Version.
        Bytes 16-N: Compatible Brands.
"""

import struct

def read_mp4_header(file_path):
    with open(file_path, 'rb') as f:
        box_size, box_type = struct.unpack('>I4s', f.read(8))
        
        if box_type != b'ftyp':
            print("Not a valid MP4 file")
            return
        
        ftyp_data = f.read(box_size - 8)
        
        major_brand, minor_version = struct.unpack('>4sI', ftyp_data[:8])
        compatible_brands = ftyp_data[8:]
        
        print(f"Major Brand: {major_brand.decode('utf-8')}")
        print(f"Minor Version: {minor_version}")
        print(f"Compatible Brands: {compatible_brands.decode('utf-8', errors='ignore')}")
        
        # Read additional boxes
        while True:
            box_header = f.read(8)
            if len(box_header) < 8:
                break
            box_size, box_type = struct.unpack('>I4s', box_header)
            box_data = f.read(box_size - 8)
            print(f"Box Type: {box_type.decode('utf-8')}")
            print(f"Box Size: {box_size}")
            print(f"Box Data: {box_data}")

# Replace with the path to your MP4 file
mp4_file = r'C:\path\to\your\file.mp4'
read_mp4_header(mp4_file)

#%%

import librosa
import logging

logging.basicConfig(level=logging.DEBUG)

def test_librosa_functions(file_path):
    try:
        # Load the audio file using librosa
        samples, sample_rate = librosa.load(file_path, sr=None)
        
        # Calculate tempo
        try:
            tempo = librosa.beat.tempo(y=samples, sr=sample_rate)
            logging.info(f"Tempo: {tempo}")
        except Exception as e:
            logging.error(f"Error calculating tempo: {e}")
        
        # Calculate chroma_stft
        try:
            chroma_stft = librosa.feature.chroma_stft(y=samples, sr=sample_rate)
            logging.info(f"Chroma STFT: {chroma_stft.mean(axis=1).tolist()}")
        except Exception as e:
            logging.error(f"Error calculating chroma_stft: {e}")

        # Calculate spectral_centroid
        try:
            spectral_centroid = librosa.feature.spectral_centroid(y=samples, sr=sample_rate)
            logging.info(f"Spectral Centroid: {spectral_centroid.mean().tolist()}")
        except Exception as e:
            logging.error(f"Error calculating spectral_centroid: {e}")

        # Calculate spectral_bandwidth
        try:
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=samples, sr=sample_rate)
            logging.info(f"Spectral Bandwidth: {spectral_bandwidth.mean().tolist()}")
        except Exception as e:
            logging.error(f"Error calculating spectral_bandwidth: {e}")

        # Calculate spectral_contrast
        try:
            spectral_contrast = librosa.feature.spectral_contrast(y=samples, sr=sample_rate)
            logging.info(f"Spectral Contrast: {spectral_contrast.mean(axis=1).tolist()}")
        except Exception as e:
            logging.error(f"Error calculating spectral_contrast: {e}")

        # Calculate spectral_flatness
        try:
            spectral_flatness = librosa.feature.spectral_flatness(y=samples)
            logging.info(f"Spectral Flatness: {spectral_flatness.mean().tolist()}")
        except Exception as e:
            logging.error(f"Error calculating spectral_flatness: {e}")

        # Calculate zero_crossing_rate
        try:
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y=samples)
            logging.info(f"Zero Crossing Rate: {zero_crossing_rate.mean().tolist()}")
        except Exception as e:
            logging.error(f"Error calculating zero_crossing_rate: {e}")

    except Exception as e:
        logging.error(f"Error loading file with librosa: {e}")

# Example usage
file_path = r"C:\Users\Vartotojas\Desktop\Studijos\Software Quality and Security\Project 2\AFT\data\Recording0005.wav"
test_librosa_functions(file_path)

#%%
import os

def sanitize_path(path):
    if not isinstance(path, str) or not path:
        raise ValueError("Invalid path: Path must be a non-empty string")

    # Normalize the path
    path = os.path.normpath(path)

    # Prevent path traversal by ensuring the normalized path does not escape intended directory structure
    # abs_path = os.path.abspath(path)
    if ".." in path.lstrip(os.path.sep):
        raise ValueError("Path traversal detected")

    # Prevent excessively long paths
    if len(path) > 4096:  # 4096 is a typical maximum path length on many systems
        raise ValueError("Path is too long")

    return path

def is_safe_path(basedir, path, follow_symlinks=True):
    try:
        sanitized_basedir = sanitize_path(basedir)
        sanitized_path = sanitize_path(path)
        
        # Check if the given path is within the basedir or the system's temporary directory
        temp_dir = os.path.realpath(os.path.expanduser(os.getenv('TMP', '/tmp')))

        if follow_symlinks:
            abs_base = os.path.realpath(sanitized_basedir)
            abs_path = os.path.realpath(sanitized_path)
        else:
            abs_base = os.path.abspath(sanitized_basedir)
            abs_path = os.path.abspath(sanitized_path)

        # Check if the absolute path starts with the base directory or the temporary directory
        return abs_path.startswith(abs_base + os.path.sep) or abs_path.startswith(temp_dir + os.path.sep)
    except ValueError as e:
        raise ValueError(f"Unsafe path detected: {e}")

# Testing functions
def test_sanitize_path(path):
    print("Testing sanitize_path function")
    
    # Valid path
    try:
        result = sanitize_path("/safe/base/dir/file.txt")
        expected = os.path.normpath("/safe/base/dir/file.txt")
        assert result == expected
        print(f"Test 1 Passed: {result}")
    except ValueError as e:
        print(f"Test 1 Failed: {e}")

    # Path traversal attempt
    try:
        sanitize_path("/safe/base/dir/../etc/passwd")
        print("Test 2 Failed")
    except ValueError as e:
        print(f"Test 2 Passed: {e}")

    # Path traversal attempt within the base directory
    try:
        sanitize_path("/safe/base/dir/../../etc/passwd")
        print("Test 3 Failed")
    except ValueError as e:
        print(f"Test 3 Passed: {e}")

    # Path with redundant separators
    try:
        result = sanitize_path("/safe//base/./dir/file.txt")
        expected = os.path.normpath("/safe/base/dir/file.txt")
        assert result == expected
        print(f"Test 4 Passed: {result}")
    except ValueError as e:
        print(f"Test 4 Failed: {e}")

    # Absolute path
    try:
        result = sanitize_path("/safe/base/dir/")
        expected = os.path.normpath("/safe/base/dir/")
        assert result == expected
        print(f"Test 5 Passed: {result}")
    except ValueError as e:
        print(f"Test 5 Failed: {e}")

    # Relative path traversal attempt
    try:
        sanitize_path("safe/base/dir/../../../etc/passwd")
        print("Test 6 Failed")
    except ValueError as e:
        print(f"Test 6 Passed: {e}")

    # Empty path
    try:
        sanitize_path("")
        print("Test 7 Failed")
    except ValueError as e:
        print(f"Test 7 Passed: {e}")

    # Non-string path
    try:
        sanitize_path(12345)
        print("Test 8 Failed")
    except ValueError as e:
        print(f"Test 8 Passed: {e}")

    # Excessively long path
    try:
        sanitize_path("/" + "a" * 4097)
        print("Test 9 Failed")
    except ValueError as e:
        print(f"Test 9 Passed: {e}")


path = r"C:\Users\Vartotojas\Desktop\Studijos\Software Quality and Security\Project 2\AFT\data"
test_sanitize_path(path)


def test_is_safe_path():
    base_dir = "/safe/base/dir"
    temp_dir = os.path.realpath(os.path.expanduser(os.getenv('TMP', '/tmp')))

    print("Testing is_safe_path function")

    # Valid path within the base directory
    try:
        assert is_safe_path(base_dir, "/safe/base/dir/file.txt") == True
        print("Test 1 Passed")
    except ValueError as e:
        print(f"Test 1 Failed: {e}")

    # Path traversal attempt
    try:
        assert is_safe_path(base_dir, "/safe/base/dir/../etc/passwd") == False
        print("Test 2 Passed")
    except ValueError as e:
        print(f"Test 2 Passed: {e}")

    # Path outside the base directory
    try:
        assert is_safe_path(base_dir, "/unsafe/dir/file.txt") == False
        print("Test 3 Passed")
    except ValueError as e:
        print(f"Test 3 Passed: {e}")

    # Path within the temporary directory
    try:
        temp_file_path = os.path.join(temp_dir, "file.txt")
        assert is_safe_path(temp_dir, temp_file_path) == True
        print("Test 4 Passed")
    except ValueError as e:
        print(f"Test 4 Failed: {e}")

    # Absolute path
    try:
        assert is_safe_path(base_dir, "/safe/base/dir/") == True
        print("Test 5 Passed")
    except ValueError as e:
        print(f"Test 5 Failed: {e}")

    # Relative path traversal attempt
    try:
        assert is_safe_path(base_dir, "safe/base/dir/../../../etc/passwd") == False
        print("Test 6 Passed")
    except ValueError as e:
        print(f"Test 6 Passed: {e}")

    # Path with redundant separators
    try:
        assert is_safe_path(base_dir, "/safe//base/./dir/file.txt") == True
        print("Test 7 Passed")
    except ValueError as e:
        print(f"Test 7 Failed: {e}")

    # Empty path
    try:
        assert is_safe_path(base_dir, "") == False
        print("Test 8 Passed")
    except ValueError as e:
        print(f"Test 8 Passed: {e}")

    # Non-string path
    try:
        assert is_safe_path(base_dir, 12345) == False
        print("Test 9 Passed")
    except ValueError as e:
        print(f"Test 9 Passed: {e}")

test_is_safe_path()


#%%
from pathlib import Path
import os

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

# Testing functions
def test_sanitize_path():
    print("Testing sanitize_path function")
    
    # Valid path
    try:
        result = sanitize_path("/safe/base/dir/file.txt")
        expected = str(Path("/safe/base/dir/file.txt").resolve())
        assert result == expected
        print(f"Test 1 Passed: {result}")
    except ValueError as e:
        print(f"Test 1 Failed: {e}")

    # Path traversal attempt
    try:
        result = sanitize_path("/safe/base/dir/../etc/passwd")
        print(f"Test 2 Passed: {result}")
    except ValueError as e:
        print(f"Test 2 Failed: {e}")

    # Path traversal attempt within the base directory
    try:
        result = sanitize_path("/safe/base/dir/../../etc/passwd")
        print(f"Test 3 Passed: {result}")
    except ValueError as e:
        print(f"Test 3 Failed: {e}")

    # Path with redundant separators
    try:
        result = sanitize_path("/safe//base/./dir/file.txt")
        expected = str(Path("/safe/base/dir/file.txt").resolve())
        assert result == expected
        print(f"Test 4 Passed: {result}")
    except ValueError as e:
        print(f"Test 4 Failed: {e}")

    # Absolute path
    try:
        result = sanitize_path("/safe/base/dir/")
        expected = str(Path("/safe/base/dir/").resolve())
        assert result == expected
        print(f"Test 5 Passed: {result}")
    except ValueError as e:
        print(f"Test 5 Failed: {e}")

    # Relative path traversal attempt
    try:
        result = sanitize_path("safe/base/dir/../../../etc/passwd")
        print(f"Test 6 Passed: {result}")
    except ValueError as e:
        print(f"Test 6 Failed: {e}")

    # Empty path
    try:
        sanitize_path("")
        print("Test 7 Failed")
    except ValueError as e:
        print(f"Test 7 Passed: {e}")

    # Non-string path
    try:
        sanitize_path(12345)
        print("Test 8 Failed")
    except ValueError as e:
        print(f"Test 8 Passed: {e}")

    # Excessively long path
    try:
        sanitize_path("/" + "a" * 4097)
        print("Test 9 Failed")
    except ValueError as e:
        print(f"Test 9 Passed: {e}")

test_sanitize_path()

# Testing functions
def test_is_safe_path():
    print("Testing is_safe_path function")
    
    # Safe path within base directory
    try:
        result = is_safe_path("/safe/base", "/safe/base/dir/file.txt")
        assert result is True
        print("Test 1 Passed")
    except ValueError as e:
        print(f"Test 1 Failed: {e}")

    # Path traversal attempt outside base directory
    try:
        result = is_safe_path("/safe/base", "/safe/base/dir/../etc/passwd")
        assert result is True
        print("Test 2 Passed")
    except ValueError as e:
        print(f"Test 2 Failed: {e}")

    # Path traversal attempt within base directory
    try:
        result = is_safe_path("/safe/base", "/safe/base/dir/../../etc/passwd")
        assert result is False
        print("Test 3 Passed")
    except ValueError as e:
        print(f"Test 3 Failed: {e}")

    # Safe path in temporary directory
    try:
        temp_dir = Path(os.path.realpath(os.path.expanduser(os.getenv('TMP', '/tmp')))).resolve()
        result = is_safe_path("/safe/base", temp_dir / "file.txt")
        assert result is True
        print("Test 4 Failed")
    except ValueError as e:
        print(f"Test 4 Passed: {e}")

    # Path outside base directory
    try:
        result = is_safe_path("/safe/base", "/unsafe/path/file.txt")
        assert result is False
        print("Test 5 Passed")
    except ValueError as e:
        print(f"Test 5 Failed: {e}")

test_is_safe_path()