#!/usr/bin/env python3
"""
Google Drive Subset Downloader for DogSpeak Dataset
Downloads and extracts a pre-created subset from Google Drive.

This script can handle both folder URLs and direct file URLs.
"""

import os
import zipfile
import requests
from pathlib import Path
import pandas as pd
import shutil
from datetime import datetime
import logging
from typing import Dict, Optional, List, Tuple, Any
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_id_from_url(drive_url: str) -> Tuple[Optional[str], str]:
    """
    Extract Google Drive ID from URL and determine if it's a file or folder.
    
    Args:
        drive_url: Google Drive sharing URL
        
    Returns:
        Tuple of (ID, type) where type is 'file' or 'folder'
    """
    # File URL patterns
    file_patterns = [
        r'/file/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+).*file'
    ]
    
    # Folder URL patterns  
    folder_patterns = [
        r'/folders/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+).*folder'
    ]
    
    # Check for file patterns first
    for pattern in file_patterns:
        match = re.search(pattern, drive_url)
        if match:
            return match.group(1), 'file'
    
    # Check for folder patterns
    for pattern in folder_patterns:
        match = re.search(pattern, drive_url)
        if match:
            return match.group(1), 'folder'
    
    return None, 'unknown'

def download_file_from_google_drive(file_id: str, destination: str) -> bool:
    """
    Download a file from Google Drive using its file ID.
    
    Args:
        file_id: Google Drive file ID
        destination: Path where to save the file
    
    Returns:
        True if download successful, False otherwise
    """
    
    logger.info(f"Starting download from Google Drive...")
    logger.info(f"   File ID: {file_id}")
    logger.info(f"   Destination: {destination}")
    
    # Google Drive download URL
    URL = "https://drive.google.com/uc?export=download"
    
    session = requests.Session()
    
    try:
        response = session.get(URL, params={'id': file_id}, stream=True)
        token = get_confirm_token(response)
        
        if token:
            params = {'id': file_id, 'confirm': token}
            response = session.get(URL, params=params, stream=True)
        
        save_response_content(response, destination)
        logger.info("Download completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False

def get_confirm_token(response: requests.Response) -> Optional[str]:
    """
    Extract confirmation token from Google Drive response.
    
    Args:
        response: HTTP response from Google Drive
        
    Returns:
        Confirmation token if found, None otherwise
    """
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response: requests.Response, destination: str) -> None:
    """
    Save the response content to a file with progress indication.
    
    Args:
        response: HTTP response to save
        destination: File path to save to
    """
    CHUNK_SIZE = 32768
    
    # Get file size if available
    total_size = response.headers.get('content-length')
    if total_size:
        total_size = int(total_size)
        logger.info(f"File size: {total_size / (1024*1024):.1f} MB")
    
    downloaded = 0
    
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                downloaded += len(chunk)
                
                if total_size:
                    progress = (downloaded / total_size) * 100
                    print(f"\rProgress: {progress:.1f}% ({downloaded / (1024*1024):.1f} MB)", end='')
    
    print()  # New line after progress

def extract_and_organize_subset(zip_path: str, base_dir: str) -> Optional[Dict[str, Any]]:
    """
    Extract the downloaded zip file and organize it in the expected structure.
    
    Args:
        zip_path: Path to the downloaded zip file
        base_dir: Base directory for the project
        
    Returns:
        Dictionary containing extraction summary, None if failed
    """
    
    logger.info("Extracting subset data...")
    
    # Define paths
    base_path = Path(base_dir)
    raw_dir = base_path / "data" / "raw"
    subset_dir = raw_dir / "subset"
    
    # Create directories
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Remove existing subset if it exists
    if subset_dir.exists():
        logger.info("Removing existing subset directory...")
        shutil.rmtree(subset_dir)
    
    # Extract zip file
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract to temporary location first
            temp_extract = base_path / "temp_extract"
            temp_extract.mkdir(exist_ok=True)
            
            zip_ref.extractall(temp_extract)
            
            # Find the actual data directory in the extracted files
            extracted_items = list(temp_extract.iterdir())
            
            # Look for the main data directory
            data_dir = None
            for item in extracted_items:
                if item.is_dir():
                    # Check if this looks like our subset directory
                    subdirs = [subdir for subdir in item.iterdir() if subdir.is_dir()]
                    if any(subdir.name.endswith(('_male', '_female')) for subdir in subdirs):
                        data_dir = item
                        break
            
            if not data_dir:
                # If no clear structure, use the first directory or the temp directory itself
                if extracted_items:
                    data_dir = extracted_items[0] if extracted_items[0].is_dir() else temp_extract
                else:
                    data_dir = temp_extract
            
            # Move to final location
            shutil.move(str(data_dir), str(subset_dir))
            
            # Clean up temporary directory
            if temp_extract.exists():
                shutil.rmtree(temp_extract)
            
            logger.info(f"Extracted to: {subset_dir}")
            
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return None
    
    # Analyze extracted content
    summary = analyze_subset_structure(subset_dir)
    
    # Create metadata if not present
    create_metadata_from_structure(subset_dir, Path(base_dir))
    
    return summary

def analyze_subset_structure(subset_dir: Path) -> Dict[str, Any]:
    """
    Analyze the structure of the extracted subset.
    
    Args:
        subset_dir: Path to subset directory
        
    Returns:
        Dictionary containing analysis summary
    """
    
    logger.info("Analyzing subset structure...")
    
    summary: Dict[str, Any] = {
        'total_files': 0,
        'breeds': {},
        'folders': []
    }
    
    if not subset_dir.exists():
        logger.warning("Subset directory not found!")
        return summary
    
    # Scan directories
    for item in subset_dir.iterdir():
        if item.is_dir():
            folder_name = item.name
            summary['folders'].append(folder_name)
            
            # Count wav files in this folder
            wav_files = list(item.glob("*.wav"))
            file_count = len(wav_files)
            summary['total_files'] += file_count
            
            # Parse breed and sex from folder name
            if '_' in folder_name:
                parts = folder_name.rsplit('_', 1)
                if len(parts) == 2:
                    breed, sex = parts
                    
                    if breed not in summary['breeds']:
                        summary['breeds'][breed] = {'male': 0, 'female': 0}
                    
                    summary['breeds'][breed][sex] = file_count
            
            logger.info(f"   {folder_name}: {file_count} files")
    
    # Display summary
    logger.info("Subset Summary:")
    logger.info(f"   Total files: {summary['total_files']}")
    logger.info(f"   Breeds found: {len(summary['breeds'])}")
    
    for breed, counts in summary['breeds'].items():
        logger.info(f"   {breed}: {counts['male']} male + {counts['female']} female files")
    
    return summary

def create_metadata_from_structure(subset_dir: Path, base_path: Path) -> Optional[Path]:
    """
    Create metadata CSV from the subset directory structure.
    
    Args:
        subset_dir: Path to subset directory
        base_path: Base project path
        
    Returns:
        Path to created metadata file, None if failed
    """
    
    logger.info("Creating metadata from directory structure...")
    
    metadata_records: List[Dict[str, str]] = []
    
    # Scan all folders and files
    for folder in subset_dir.iterdir():
        if folder.is_dir():
            folder_name = folder.name
            
            # Parse breed and sex from folder name
            if '_' in folder_name:
                parts = folder_name.rsplit('_', 1)
                if len(parts) == 2:
                    breed, sex = parts
                    
                    # Process each wav file
                    for wav_file in folder.glob("*.wav"):
                        filename = wav_file.name
                        
                        # Try to extract dog_id from various filename patterns
                        dog_id = "unknown"
                        if "_dog_" in filename:
                            dog_parts = filename.split("_dog_")
                            if len(dog_parts) > 1:
                                dog_id = f"dog_{dog_parts[-1].replace('.wav', '')}"
                        
                        metadata_records.append({
                            'filename': filename,
                            'breed': breed.replace('_', ' '),  # Handle multi-word breeds
                            'sex': sex,
                            'dog_id': dog_id
                        })
    
    # Create DataFrame and save
    if metadata_records:
        df = pd.DataFrame(metadata_records)
        
        # Ensure exploration directory exists
        exploration_dir = base_path / "data" / "exploration"
        exploration_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata_path = exploration_dir / "metadata_subset.csv"
        df.to_csv(metadata_path, index=False)
        
        logger.info(f"Metadata saved to: {metadata_path}")
        logger.info(f"   Records: {len(df)}")
        
        return metadata_path
    else:
        logger.warning("No metadata records created")
        return None

def create_download_report(base_path: Path, summary: Dict[str, Any], source_info: str) -> Path:
    """
    Create a report of the download and extraction process.
    
    Args:
        base_path: Base project path
        summary: Extraction summary dictionary
        source_info: Information about the source (folder ID or file ID)
        
    Returns:
        Path to created report file
    """
    
    exploration_dir = base_path / "data" / "exploration"
    exploration_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = exploration_dir / "gdrive_download_report.txt"
    
    with open(report_path, 'w') as f:
        f.write("Google Drive Subset Download Report\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Download Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Google Drive Source: {source_info}\n")
        f.write(f"Total Files Downloaded: {summary['total_files']}\n")
        f.write(f"Breeds: {len(summary['breeds'])}\n\n")
        
        f.write("BREED BREAKDOWN:\n")
        f.write("-" * 20 + "\n")
        
        for breed, counts in summary['breeds'].items():
            total = counts['male'] + counts['female']
            f.write(f"{breed.upper()}:\n")
            f.write(f"  Male files: {counts['male']}\n")
            f.write(f"  Female files: {counts['female']}\n")
            f.write(f"  Total: {total}\n\n")
        
        f.write("FOLDER STRUCTURE:\n")
        f.write("-" * 16 + "\n")
        for folder in summary['folders']:
            f.write(f"  {folder}\n")
    
    logger.info(f"Report saved to: {report_path}")
    return report_path

def main() -> int:
    """
    Main function to download and setup subset from Google Drive.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    
    # Configuration
    base_dir = "/Users/nika/Downloads/NMSML"
    
    # Google Drive URL - can be either file or folder
    GDRIVE_URL = "https://drive.google.com/file/d/1nbywuZJZBiMv-qktTR--dqhCmxC9Z6CN/view?usp=sharing"
    
    try:
        logger.info("DogSpeak Subset Downloader from Google Drive")
        logger.info("=" * 50)
        
        # Extract ID and determine type from URL
        drive_id, url_type = extract_id_from_url(GDRIVE_URL)
        
        if not drive_id:
            logger.error("Could not extract ID from Google Drive URL")
            logger.error(f"URL provided: {GDRIVE_URL}")
            return 1
        
        logger.info(f"Drive ID: {drive_id}")
        logger.info(f"Type: {url_type}")
        
        # Create download directory
        download_dir = Path(base_dir) / "downloads"
        download_dir.mkdir(parents=True, exist_ok=True)
        
        if url_type == 'file':
            # Direct file download
            zip_filename = f"dogspeak_subset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = download_dir / zip_filename
            
            logger.info("Attempting direct file download...")
            if download_file_from_google_drive(drive_id, str(zip_path)):
                logger.info(f"File downloaded to: {zip_path}")
                
                # Extract and organize
                summary = extract_and_organize_subset(str(zip_path), base_dir)
                
                if summary:
                    # Create report
                    create_download_report(Path(base_dir), summary, f"File ID: {drive_id}")
                    
                    # Clean up zip file
                    os.remove(zip_path)
                    logger.info("Cleaned up download file")
                    
                    logger.info("Subset setup completed successfully!")
                    logger.info(f"   Total files: {summary['total_files']}")
                    logger.info(f"   Breeds: {len(summary['breeds'])}")
                    logger.info("   Ready for formant extraction and analysis!")
                    
                    return 0
                else:
                    logger.error("Failed to extract and organize subset")
                    return 1
            else:
                logger.error("Direct download failed")
                return 1
                
        elif url_type == 'folder':
            # Folder - require manual download
            logger.info("MANUAL DOWNLOAD INSTRUCTIONS for folder:")
            logger.info("=" * 40)
            logger.info("1. Go to the Google Drive folder:")
            logger.info(f"   {GDRIVE_URL}")
            logger.info("2. Select all files (Ctrl+A or Cmd+A)")
            logger.info("3. Right-click and choose 'Download'")
            logger.info("4. Save the downloaded zip file as 'dogspeak_subset.zip'")
            logger.info("5. Place it in the downloads directory")
            
            # Check for manually downloaded file
            manual_zip_path = download_dir / "dogspeak_subset.zip"
            
            if manual_zip_path.exists():
                logger.info(f"Found manually downloaded zip: {manual_zip_path}")
                summary = extract_and_organize_subset(str(manual_zip_path), base_dir)
                
                if summary:
                    # Create report
                    create_download_report(Path(base_dir), summary, f"Manual folder: {drive_id}")
                    
                    # Clean up zip file
                    os.remove(manual_zip_path)
                    logger.info("Cleaned up download file")
                    
                    logger.info("Subset setup completed successfully!")
                    logger.info(f"   Total files: {summary['total_files']}")
                    logger.info(f"   Breeds: {len(summary['breeds'])}")
                    
                    return 0
                else:
                    logger.error("Failed to process manually downloaded zip")
                    return 1
            else:
                logger.info(f"Waiting for manual download at: {manual_zip_path}")
                return 1
        else:
            logger.error("Could not determine if URL is for file or folder")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())