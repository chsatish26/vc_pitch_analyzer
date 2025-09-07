"""
Helper functions for the VC Pitch Analysis System.

This module provides common utilities used across the system.
"""

import logging
import json
import re
import os
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

def format_currency(value: Optional[Union[int, float]], 
                   currency: str = "USD", 
                   include_symbol: bool = True,
                   precision: int = 0) -> str:
    """
    Format currency value with appropriate symbols and formatting.
    
    Args:
        value: Numerical value to format
        currency: Currency code (e.g., 'USD', 'INR')
        include_symbol: Whether to include currency symbol
        precision: Decimal precision
        
    Returns:
        Formatted currency string
    """
    if value is None:
        return "N/A"
    
    # Get currency symbol
    symbols = {
        "USD": "$",
        "INR": "₹",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "CNY": "¥",
        "AUD": "A$",
        "CAD": "C$"
    }
    
    symbol = symbols.get(currency, currency)
    
    # Format value
    formatted = f"{value:,.{precision}f}"
    
    # Add suffix for large numbers
    if value >= 1_000_000_000:  # Billions
        formatted = f"{value / 1_000_000_000:.{precision}f}B"
    elif value >= 1_000_000:  # Millions
        formatted = f"{value / 1_000_000:.{precision}f}M"
    elif value >= 1_000:  # Thousands (optional)
        formatted = f"{value / 1_000:.{precision}f}K"
    
    # Combine symbol and value
    if include_symbol:
        return f"{symbol}{formatted}"
    else:
        return formatted

def format_percentage(value: Optional[Union[int, float]], precision: int = 1) -> str:
    """
    Format percentage value.
    
    Args:
        value: Numerical value to format
        precision: Decimal precision
        
    Returns:
        Formatted percentage string
    """
    if value is None:
        return "N/A"
        
    return f"{value:.{precision}f}%"

def format_ratio(numerator: Union[int, float], denominator: Union[int, float]) -> str:
    """
    Format ratio value.
    
    Args:
        numerator: Ratio numerator
        denominator: Ratio denominator
        
    Returns:
        Formatted ratio string
    """
    if denominator == 0:
        return "N/A"
        
    # Calculate ratio
    ratio = numerator / denominator
    
    # For clean ratios, return as X:1
    if ratio >= 1 and abs(ratio - round(ratio)) < 0.05:
        return f"{round(ratio)}:1"
    elif ratio < 1 and abs((1/ratio) - round(1/ratio)) < 0.05:
        return f"1:{round(1/ratio)}"
    
    # Otherwise return decimal form
    return f"{ratio:.1f}:1"

def extract_year_from_period(period: str) -> Optional[int]:
    """
    Extract year from period string.
    
    Args:
        period: Period string (e.g., '2019-20' or '2019')
        
    Returns:
        Extracted year or None if not found
    """
    if not period:
        return None
        
    # Try different formats
    if "-" in period:
        # Format like "2019-20"
        year_str = period.split("-")[0]
        if year_str.isdigit() and len(year_str) == 4:
            return int(year_str)
    elif period.isdigit() and len(period) == 4:
        # Format like "2019"
        return int(period)
    
    return None

def calculate_cagr(start_value: float, end_value: float, periods: int) -> Optional[float]:
    """
    Calculate Compound Annual Growth Rate (CAGR).
    
    Args:
        start_value: Starting value
        end_value: Ending value
        periods: Number of periods
        
    Returns:
        CAGR as a decimal (multiply by 100 for percentage)
    """
    if start_value <= 0 or periods <= 0:
        return None
        
    # CAGR = (end_value / start_value)^(1/periods) - 1
    cagr = (end_value / start_value) ** (1 / periods) - 1
    return cagr

def truncate_text(text: str, max_length: int = 100, add_ellipsis: bool = True) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        add_ellipsis: Whether to add ellipsis (...) at the end
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
        
    truncated = text[:max_length].rstrip()
    if add_ellipsis:
        truncated += "..."
        
    return truncated

def safe_json_serialize(obj: Any) -> Any:
    """
    Safely serialize an object to JSON-compatible format.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON-compatible version of the object
    """
    if isinstance(obj, dict):
        return {k: safe_json_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_json_serialize(item) for item in obj]
    elif isinstance(obj, (datetime, uuid.UUID)):
        return str(obj)
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        # Try to convert to string for unknown types
        return str(obj)

def generate_unique_id(prefix: str = "") -> str:
    """
    Generate a unique ID string.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique ID string
    """
    uid = uuid.uuid4().hex[:12]
    if prefix:
        return f"{prefix}_{uid}"
    return uid

def clean_html_tags(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: Text containing HTML tags
        
    Returns:
        Clean text without HTML tags
    """
    if not text:
        return ""
        
    # Remove all HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    
    # Normalize whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    return clean

def extract_domain_from_url(url: str) -> Optional[str]:
    """
    Extract domain name from URL.
    
    Args:
        url: URL string
        
    Returns:
        Domain name or None if not found
    """
    if not url:
        return None
        
    # Extract domain using regex
    match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    return match.group(1) if match else None

def get_company_name_from_filename(filename: str) -> Optional[str]:
    """
    Extract company name from filename.
    
    Args:
        filename: Filename string
        
    Returns:
        Company name or None if not found
    """
    if not filename:
        return None
        
    # Work with the base filename only (strip any path)
    base = os.path.basename(filename)
    
    # Try to extract company name from common filename patterns
    patterns = [
        # Pattern 1: CompanyName_Date.pdf
        r'^([A-Za-z0-9]+)_.*\.pdf$',
        # Pattern 2: CompanyName-Pitchdeck.pdf
        r'^([A-Za-z0-9]+)-.*\.pdf$',
        # Pattern 3: CompanyName.pdf
        r'^([A-Za-z0-9]+)\.pdf$',
    ]
    
    for pat in patterns:
        match = re.match(pat, base, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def infer_business_model(text: str) -> Optional[str]:
    """
    Infer business model from text description.
    
    Args:
        text: Text to analyze
        
    Returns:
        Inferred business model or None if not found
    """
    if not text:
        return None
        
    # Look for common business model keywords
    b2b_keywords = [
        "b2b", "enterprise", "business-to-business", "saas", "software as a service",
        "platform", "enterprise software", "enterprise solution"
    ]
    
    b2c_keywords = [
        "b2c", "consumer", "business-to-consumer", "retail", "direct-to-consumer",
        "d2c", "app", "marketplace", "subscription", "freemium"
    ]
    
    marketplace_keywords = [
        "marketplace", "two-sided", "platform", "network effects", "buyers and sellers",
        "supply and demand", "match", "connect"
    ]
    
    # Count keyword occurrences
    text_lower = text.lower()
    b2b_count = sum(1 for kw in b2b_keywords if kw in text_lower)
    b2c_count = sum(1 for kw in b2c_keywords if kw in text_lower)
    marketplace_count = sum(1 for kw in marketplace_keywords if kw in text_lower)
    
    # Determine business model
    if marketplace_count > max(b2b_count, b2c_count):
        return "Marketplace"
    elif b2b_count > b2c_count:
        return "B2B"
    elif b2c_count > 0:
        return "B2C"
    
    return None

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        JSON content as dictionary or None if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return None

def save_json_file(data: Any, file_path: str, indent: int = 2) -> bool:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Path to output file
        indent: JSON indentation level
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Serialize data
        serialized = safe_json_serialize(data)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serialized, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON file {file_path}: {e}")
        return False