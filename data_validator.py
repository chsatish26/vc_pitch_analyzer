"""
Data Validation Utilities.

This module provides functions for validating input data across the system.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def validate_pitch_id(pitch_id: str) -> bool:
    """
    Validate MongoDB ObjectId format.
    
    Args:
        pitch_id: Pitch ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not pitch_id or not isinstance(pitch_id, str):
        return False
        
    # MongoDB ObjectId is a 24-character hex string
    return bool(re.match(r'^[0-9a-f]{24}$', pitch_id))

def validate_currency_value(value: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate currency value structure.
    
    Args:
        value: Currency value dict to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, dict):
        return False, "Currency value must be a dictionary"
        
    # Check required fields
    if "value" not in value:
        return False, "Currency value missing 'value' field"
        
    # Check currency field
    if "currency" not in value:
        return False, "Currency value missing 'currency' field"
        
    # Validate currency code
    currency = value.get("currency")
    if currency and not isinstance(currency, str):
        return False, "Currency code must be a string"
        
    # Validate value type
    amount = value.get("value")
    if amount is not None and not isinstance(amount, (int, float)):
        return False, "Currency amount must be a number"
        
    return True, None

def validate_percentage(value: Union[int, float, str]) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Validate and normalize percentage value.
    
    Args:
        value: Percentage value to validate
        
    Returns:
        Tuple of (is_valid, normalized_value, error_message)
    """
    if value is None:
        return False, None, "Percentage value is None"
        
    try:
        # If string with % sign, convert to float
        if isinstance(value, str):
            value = value.strip()
            if value.endswith("%"):
                value = value[:-1]  # Remove % sign
            value = float(value)
            
        # Check range
        if not isinstance(value, (int, float)):
            return False, None, "Percentage must be a number"
            
        # Return normalized value as float
        return True, float(value), None
    except ValueError:
        return False, None, f"Invalid percentage format: {value}"

def validate_ratio(value: Union[int, float, str]) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Validate and normalize ratio value.
    
    Args:
        value: Ratio value to validate
        
    Returns:
        Tuple of (is_valid, normalized_value, error_message)
    """
    if value is None:
        return False, None, "Ratio value is None"
        
    try:
        # Handle string format like "3:1"
        if isinstance(value, str) and ":" in value:
            parts = value.split(":")
            if len(parts) != 2:
                return False, None, f"Invalid ratio format: {value}"
                
            numerator = float(parts[0])
            denominator = float(parts[1])
            
            if denominator == 0:
                return False, None, "Ratio denominator cannot be zero"
                
            ratio_value = numerator / denominator
        else:
            # Direct numerical value
            ratio_value = float(value)
            
        # Check if reasonable
        if ratio_value <= 0:
            return False, None, "Ratio must be positive"
            
        # Return normalized value as float
        return True, float(ratio_value), None
    except ValueError:
        return False, None, f"Invalid ratio format: {value}"

def validate_date_string(date_str: str, formats: List[str] = None) -> Tuple[bool, Optional[datetime], Optional[str]]:
    """
    Validate and parse date string.
    
    Args:
        date_str: Date string to validate
        formats: List of datetime formats to try
        
    Returns:
        Tuple of (is_valid, parsed_date, error_message)
    """
    if not date_str or not isinstance(date_str, str):
        return False, None, "Date string is empty or not a string"
        
    # Default formats to try
    if not formats:
        formats = [
            "%Y-%m-%d",          # 2023-01-15
            "%d/%m/%Y",          # 15/01/2023
            "%m/%d/%Y",          # 01/15/2023
            "%B %d, %Y",         # January 15, 2023
            "%b %d, %Y",         # Jan 15, 2023
            "%Y-%m-%dT%H:%M:%S", # ISO format
            "%Y-%m-%dT%H:%M:%S.%fZ" # ISO format with microseconds and Z
        ]
        
    # Try each format
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return True, parsed_date, None
        except ValueError:
            pass
            
    return False, None, f"Date string does not match any supported format: {date_str}"

def validate_revenue_data(revenues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate and normalize revenue data.
    
    Args:
        revenues: List of revenue dictionaries
        
    Returns:
        List of validation issues
    """
    issues = []
    
    if not isinstance(revenues, list):
        issues.append({"field": "revenues", "issue": "Revenues must be a list"})
        return issues
        
    # Check each revenue entry
    for i, revenue in enumerate(revenues):
        if not isinstance(revenue, dict):
            issues.append({"field": f"revenues[{i}]", "issue": "Revenue entry must be a dictionary"})
            continue
            
        # Check period field
        if "period" not in revenue and "year" not in revenue:
            issues.append({"field": f"revenues[{i}]", "issue": "Revenue entry missing period or year field"})
            
        # Validate currency value
        if "value" in revenue:
            is_valid, error = validate_currency_value({
                "value": revenue.get("value"),
                "currency": revenue.get("currency", "USD")
            })
            
            if not is_valid:
                issues.append({"field": f"revenues[{i}].value", "issue": error})
    
    return issues

def validate_team_data(team: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate team data.
    
    Args:
        team: Team data dictionary
        
    Returns:
        List of validation issues
    """
    issues = []
    
    if not isinstance(team, dict):
        issues.append({"field": "team", "issue": "Team data must be a dictionary"})
        return issues
        
    # Check founders list
    founders = team.get("founders", [])
    if not isinstance(founders, list):
        issues.append({"field": "team.founders", "issue": "Founders must be a list"})
    else:
        # Validate each founder
        for i, founder in enumerate(founders):
            if not isinstance(founder, dict):
                issues.append({"field": f"team.founders[{i}]", "issue": "Founder entry must be a dictionary"})
                continue
                
            # Check required fields
            if "name" not in founder:
                issues.append({"field": f"team.founders[{i}]", "issue": "Founder missing name field"})
    
    return issues

def validate_market_data(market: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate market data.
    
    Args:
        market: Market data dictionary
        
    Returns:
        List of validation issues
    """
    issues = []
    
    if not isinstance(market, dict):
        issues.append({"field": "market", "issue": "Market data must be a dictionary"})
        return issues
        
    # Validate TAM
    if "tam" in market:
        is_valid, error = validate_currency_value(market["tam"])
        if not is_valid:
            issues.append({"field": "market.tam", "issue": error})
    
    # Validate SAM
    if "sam" in market:
        is_valid, error = validate_currency_value(market["sam"])
        if not is_valid:
            issues.append({"field": "market.sam", "issue": error})
    
    # Validate SOM
    if "som" in market:
        is_valid, error = validate_currency_value(market["som"])
        if not is_valid:
            issues.append({"field": "market.som", "issue": error})
    
    # Validate CAGR
    if "cagr" in market:
        cagr = market["cagr"]
        if cagr is not None:
            is_valid, _, error = validate_percentage(cagr)
            if not is_valid:
                issues.append({"field": "market.cagr", "issue": error})
    
    return issues

def validate_normalized_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate normalized pitch data structure.
    
    Args:
        data: Normalized pitch data to validate
        
    Returns:
        List of validation issues
    """
    issues = []
    
    if not isinstance(data, dict):
        issues.append({"field": "root", "issue": "Normalized data must be a dictionary"})
        return issues
        
    # Validate metadata
    if "metadata" not in data:
        issues.append({"field": "metadata", "issue": "Missing metadata section"})
        
    # Validate market data
    if "market" in data:
        market_issues = validate_market_data(data["market"])
        issues.extend(market_issues)
        
    # Validate finance data
    if "finance" in data:
        finance = data["finance"]
        if not isinstance(finance, dict):
            issues.append({"field": "finance", "issue": "Finance data must be a dictionary"})
        else:
            # Validate revenues
            if "revenues" in finance:
                revenue_issues = validate_revenue_data(finance["revenues"])
                for issue in revenue_issues:
                    issue["field"] = "finance." + issue["field"]
                issues.extend(revenue_issues)
        
    # Validate team data
    if "team" in data:
        team_issues = validate_team_data(data["team"])
        issues.extend(team_issues)
    
    return issues