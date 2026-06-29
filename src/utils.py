"""
Utility functions for RAG Enterprise System
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

from config.constants import LOG_FORMAT, LOG_DATE_FORMAT
from config.settings import settings


def setup_logger(name: str) -> logging.Logger:
    """
    Setup logger with consistent formatting
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.log_level))
    
    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger


logger = setup_logger(__name__)


def ensure_directory_exists(path: str) -> None:
    """
    Ensure directory exists, create if not
    
    Args:
        path: Directory path
    """
    Path(path).mkdir(parents=True, exist_ok=True)
    logger.info(f"Directory ensured: {path}")


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: Name of the file
        
    Returns:
        File extension (e.g., '.pdf')
    """
    return Path(filename).suffix.lower()


def is_supported_format(filename: str) -> bool:
    """
    Check if file format is supported
    
    Args:
        filename: Name of the file
        
    Returns:
        True if format is supported, False otherwise
    """
    from config.constants import SUPPORTED_DOCUMENT_FORMATS
    return get_file_extension(filename) in SUPPORTED_DOCUMENT_FORMATS


def save_json(data: Dict[str, Any], filepath: str) -> None:
    """
    Save data to JSON file
    
    Args:
        data: Data to save
        filepath: Path to save file
    """
    ensure_directory_exists(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Data saved to: {filepath}")


def load_json(filepath: str) -> Dict[str, Any]:
    """
    Load data from JSON file
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    logger.info(f"Data loaded from: {filepath}")
    return data


def split_text_into_lines(text: str, max_length: int = 100) -> List[str]:
    """
    Split text into lines with max length
    
    Args:
        text: Text to split
        max_length: Maximum line length
        
    Returns:
        List of lines
    """
    lines = []
    current_line = ""
    
    for word in text.split():
        if len(current_line) + len(word) + 1 <= max_length:
            current_line += word + " "
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
    
    if current_line:
        lines.append(current_line.strip())
    
    return lines


def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing extra whitespace and special characters
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove common problematic characters
    text = text.replace('\x00', '')  # Null character
    text = text.replace('\r', '\n')  # Carriage return
    
    return text.strip()


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format
    
    Returns:
        Timestamp string
    """
    return datetime.now().isoformat()


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to max length with ellipsis
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def calculate_text_stats(text: str) -> Dict[str, int]:
    """
    Calculate statistics about text
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with text statistics
    """
    words = text.split()
    sentences = text.split('.')
    
    return {
        "character_count": len(text),
        "word_count": len(words),
        "sentence_count": len([s for s in sentences if s.strip()]),
        "average_word_length": len(text) / len(words) if words else 0,
    }


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes to human-readable size
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"


def retry_on_exception(max_retries: int = 3, delay: int = 1):
    """
    Decorator to retry function on exception
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
    """
    import time
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed after {max_retries} attempts: {str(e)}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator
