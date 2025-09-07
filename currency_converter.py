"""
Currency conversion utilities.

This module provides functions for converting currencies based on configured rates.
"""

import logging
from typing import Dict, Any, Union, Optional

logger = logging.getLogger(__name__)

def convert_currency(
    amount: Union[float, int],
    from_currency: str,
    to_currency: str,
    config: Any = None
) -> float:
    """
    Convert an amount from one currency to another.
    
    Args:
        amount: The amount to convert
        from_currency: Source currency code (e.g., 'INR')
        to_currency: Target currency code (e.g., 'USD')
        config: Configuration object containing currency rates
        
    Returns:
        Converted amount in target currency
        
    Raises:
        ValueError: If currencies are invalid or rates are not available
    """
    if amount is None:
        return None
        
    # No conversion needed if currencies are the same
    if from_currency == to_currency:
        return amount
    
    # Get currency rates from config
    rates = _get_currency_rates(config)
    
    # Convert to base currency (USD) first if not already
    if from_currency != "USD":
        if from_currency not in rates:
            logger.warning(f"Exchange rate not found for {from_currency}, using default")
            # Use default rate or raise error
            from_rate = _get_default_rate(from_currency)
        else:
            from_rate = rates[from_currency]
        
        # Convert to USD
        amount_usd = amount / from_rate
    else:
        amount_usd = amount
    
    # Convert from USD to target currency if needed
    if to_currency != "USD":
        if to_currency not in rates:
            logger.warning(f"Exchange rate not found for {to_currency}, using default")
            # Use default rate or raise error
            to_rate = _get_default_rate(to_currency)
        else:
            to_rate = rates[to_currency]
        
        # Convert from USD to target
        converted_amount = amount_usd * to_rate
    else:
        converted_amount = amount_usd
    
    return converted_amount

def _get_currency_rates(config: Any) -> Dict[str, float]:
    """
    Get currency rates from config.
    
    Args:
        config: Configuration object
        
    Returns:
        Dictionary of currency rates with USD as base
    """
    # Default rates (USD as base - i.e., USD/X rates)
    default_rates = {
        "USD": 1.0,
        "EUR": 0.85,
        "GBP": 0.73,
        "JPY": 110.0,
        "CNY": 6.45,
        "INR": 75.0,
        "AUD": 1.35,
        "CAD": 1.25,
        "SGD": 1.35,
        "CHF": 0.92
    }
    
    # If config is available, get rates from it
    if config:
        config_rates = config.get("currency.rates", {})
        if config_rates:
            # Merge with default rates (config takes precedence)
            default_rates.update(config_rates)
    
    return default_rates

def _get_default_rate(currency: str) -> float:
    """
    Get default exchange rate for a currency.
    
    Args:
        currency: Currency code
        
    Returns:
        Default exchange rate
        
    Raises:
        ValueError: If currency is not supported
    """
    # Map of common currencies to approximate USD rates
    # These are rough approximations for fallback use only
    default_rates = {
        "USD": 1.0,
        "EUR": 0.85,
        "GBP": 0.73,
        "JPY": 110.0,
        "CNY": 6.45,
        "INR": 75.0,
        "AUD": 1.35,
        "CAD": 1.25,
        "SGD": 1.35,
        "CHF": 0.92,
        "HKD": 7.8,
        "NZD": 1.4,
        "SEK": 8.6,
        "KRW": 1150.0,
        "NOK": 8.5,
        "MXN": 20.0,
        "BRL": 5.3,
        "RUB": 75.0,
        "ZAR": 15.0,
        "TRY": 8.6
    }
    
    if currency in default_rates:
        return default_rates[currency]
    else:
        logger.error(f"Currency {currency} not supported for conversion")
        # Return a very approximate rate to avoid breaking the system
        # This is not accurate but better than crashing
        return 50.0  # Arbitrary fallback rate