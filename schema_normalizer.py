"""
Schema Normalizer Agent.

This module normalizes heterogeneous pitch data into a canonical schema.
"""

import logging
from typing import Dict, Any, Optional, List, Union
import asyncio

from utils.currency_converter import convert_currency
from agents import BaseAgent

logger = logging.getLogger(__name__)

class SchemaNormalizer(BaseAgent):
    """
    Agent for normalizing pitch data schema.
    
    This agent converts varying pitch data formats into a consistent
    canonical schema for further analysis.
    """
    
    # Canonical schema structure with default values
    CANONICAL_SCHEMA = {
        "metadata": {
            "company_name": None,
            "tagline": None,
            "website": None,
            "date": None,
            "source": None,
            "client_id": None,
            "original_file_name": None
        },
        "contact": {
            "email": None,
            "phone": None,
            "address": None
        },
        "team": {
            "founders": [],
            "experience": None
        },
        "market": {
            "tam": {"value": None, "currency": "USD", "raw": None},
            "sam": {"value": None, "currency": "USD", "raw": None},
            "som": {"value": None, "currency": "USD", "raw": None},
            "cagr": None,
            "domain": None,
            "sub_domain": None
        },
        "positioning": {
            "problem_statement": None,
            "solution": None,
            "usp": None,
            "competitors": []
        },
        "finance": {
            "arr": {"value": None, "currency": "USD", "raw": None},
            "mrr": {"value": None, "currency": "USD", "raw": None},
            "total_revenue": {"value": None, "currency": "USD", "raw": None},
            "gross_profit": {"value": None, "currency": "USD", "raw": None},
            "ebita": {"value": None, "currency": "USD", "raw": None},
            "year_on_year_growth": None,
            "revenues": [],
            "runway": None
        },
        "fundraise": {
            "ask": {"value": None, "currency": "USD", "raw": None},
            "valuation": {"value": None, "currency": "USD", "raw": None},
            "funds_raised": {"value": None, "currency": "USD", "raw": None},
        },
        "gtm": {
            "revenue_streams": [],
            "business_model": None,
            "channels": []
        },
        "units": {
            "base_currency": "USD"
        },
        "extras": {}  # For any non-standard fields that don't fit elsewhere
    }
    
    async def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize the raw pitch data to canonical schema.
        
        Args:
            raw_data: Raw pitch data from MongoDB
            
        Returns:
            Normalized pitch data in canonical schema
        """
        logger.info("Normalizing pitch data schema")
        
        # Deep copy the schema template to avoid modifying the class attribute
        canonical = self._deep_copy(self.CANONICAL_SCHEMA)
        
        # Extract the extraction data which contains all the pitch info
        extraction = raw_data.get("extraction", {})
        if not extraction:
            logger.warning("No extraction data found in raw pitch data")
        
        # Map metadata fields
        canonical["metadata"]["company_name"] = extraction.get("company_name")
        canonical["metadata"]["tagline"] = extraction.get("tagline")
        canonical["metadata"]["website"] = extraction.get("website")
        canonical["metadata"]["date"] = extraction.get("date")
        canonical["metadata"]["source"] = raw_data.get("source")
        canonical["metadata"]["client_id"] = raw_data.get("clientId")
        canonical["metadata"]["original_file_name"] = raw_data.get("originalFileName")
        
        # Map contact fields
        canonical["contact"]["email"] = extraction.get("email")
        canonical["contact"]["phone"] = extraction.get("phone")
        canonical["contact"]["address"] = extraction.get("address")
        
        # Map team fields
        canonical["team"]["founders"] = self._normalize_founders(extraction.get("founders", []))
        canonical["team"]["experience"] = extraction.get("experience")
        
        # Map market fields
        canonical["market"]["tam"] = self._normalize_currency(extraction.get("tam"))
        canonical["market"]["sam"] = self._normalize_currency(extraction.get("sam"))
        canonical["market"]["som"] = self._normalize_currency(extraction.get("som"))
        canonical["market"]["cagr"] = extraction.get("cagr")
        canonical["market"]["domain"] = extraction.get("domain")
        canonical["market"]["sub_domain"] = extraction.get("sub_domain")
        
        # Map positioning fields
        canonical["positioning"]["problem_statement"] = extraction.get("problem_statement")
        canonical["positioning"]["solution"] = extraction.get("solution")
        canonical["positioning"]["usp"] = extraction.get("USP")  # Note the capitalization
        canonical["positioning"]["competitors"] = extraction.get("competitors", [])
        
        # Map finance fields
        canonical["finance"]["arr"] = self._normalize_currency(extraction.get("arr"))
        canonical["finance"]["mrr"] = self._normalize_currency(extraction.get("mrr"))
        canonical["finance"]["total_revenue"] = self._normalize_currency(extraction.get("total_revenue"))
        canonical["finance"]["gross_profit"] = self._normalize_currency(extraction.get("gross_profit"))
        canonical["finance"]["ebita"] = self._normalize_currency(extraction.get("ebita"))
        canonical["finance"]["year_on_year_growth"] = extraction.get("year_on_year_growth")
        canonical["finance"]["revenues"] = self._normalize_revenues(extraction.get("revenues", []))
        canonical["finance"]["runway"] = extraction.get("runway")
        
        # Map fundraise fields
        canonical["fundraise"]["ask"] = self._normalize_currency(extraction.get("ask"))
        canonical["fundraise"]["valuation"] = self._normalize_currency(extraction.get("valuation"))
        canonical["fundraise"]["funds_raised"] = self._normalize_currency(extraction.get("funds_raised"))
        
        # Map GTM fields
        canonical["gtm"]["revenue_streams"] = extraction.get("revenue_streams", [])
        canonical["gtm"]["business_model"] = extraction.get("business_model")
        canonical["gtm"]["channels"] = extraction.get("channels", [])
        
        # Store any unknown fields in extras
        canonical["extras"] = self._extract_extras(extraction, canonical)
        
        # Ensure the base currency is set correctly
        canonical["units"]["base_currency"] = "USD"
        
        logger.debug("Schema normalization completed successfully")
        return canonical
    
    def _deep_copy(self, obj: Any) -> Any:
        """Create a deep copy of a nested dictionary/list structure."""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj
    
    def _normalize_currency(self, currency_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Normalize currency data to a standard format with USD conversion.
        
        Args:
            currency_data: Dictionary with value and currency fields
            
        Returns:
            Normalized currency data with USD conversion
        """
        if not currency_data or not isinstance(currency_data, dict):
            return {"value": None, "currency": "USD", "raw": None}
        
        value = currency_data.get("value")
        currency = currency_data.get("currency", "USD")
        
        # Store the original value
        raw = {"value": value, "currency": currency} if value is not None else None
        
        # Convert to USD if needed and value exists
        if value is not None and currency and currency != "USD":
            value_usd = convert_currency(value, currency, "USD", self.config)
        else:
            value_usd = value
        
        return {
            "value": value_usd,
            "currency": "USD",
            "raw": raw
        }
    
    def _normalize_founders(self, founders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize founders data to a standard format.
        
        Args:
            founders: List of founder dictionaries
            
        Returns:
            Normalized founders data
        """
        normalized_founders = []
        
        for founder in founders:
            if not isinstance(founder, dict):
                continue
                
            normalized_founder = {
                "name": founder.get("name"),
                "title": founder.get("title"),
                "linkedin": founder.get("linkedin"),
                "bio": founder.get("bio")
            }
            
            normalized_founders.append(normalized_founder)
            
        return normalized_founders
    
    def _normalize_revenues(self, revenues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize revenue data to a standard format with USD conversion.
        
        Args:
            revenues: List of revenue dictionaries by year/quarter
            
        Returns:
            Normalized revenue data with USD conversion
        """
        normalized_revenues = []
        
        for revenue in revenues:
            if not isinstance(revenue, dict):
                continue
                
            value = revenue.get("value")
            currency = revenue.get("currency", "USD")
            period = revenue.get("year") or revenue.get("quarter") or revenue.get("period")
            
            # Store the original value
            raw = {"value": value, "currency": currency} if value is not None else None
            
            # Convert to USD if needed and value exists
            if value is not None and currency and currency != "USD":
                value_usd = convert_currency(value, currency, "USD", self.config)
            else:
                value_usd = value
            
            normalized_revenue = {
                "period": period,
                "value": value_usd,
                "currency": "USD",
                "raw": raw
            }
            
            normalized_revenues.append(normalized_revenue)
            
        # Sort by period if possible
        try:
            normalized_revenues.sort(key=lambda x: x["period"])
        except (TypeError, KeyError):
            logger.warning("Could not sort revenues by period")
            
        return normalized_revenues
    
    def _extract_extras(self, extraction: Dict[str, Any], canonical: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract fields that don't fit into the canonical schema.
        
        Args:
            extraction: Raw extraction data
            canonical: Canonical schema
            
        Returns:
            Dictionary of extra fields
        """
        extras = {}
        
        # Flatten the canonical schema to get all field paths
        canonical_paths = set()
        self._get_paths(canonical, [], canonical_paths)
        
        # Check each field in extraction
        extraction_paths = set()
        self._get_paths(extraction, [], extraction_paths)
        
        # Find paths in extraction that aren't in canonical
        for path in extraction_paths:
            if not any(p.endswith(path) for p in canonical_paths):
                # Get the value using the path
                value = self._get_by_path(extraction, path.split('.'))
                if value is not None:
                    extras[path] = value
        
        return extras
    
    def _get_paths(self, obj: Union[Dict, List], current_path: List[str], result: set) -> None:
        """
        Get all paths in a nested dictionary/list structure.
        
        Args:
            obj: The dictionary or list to process
            current_path: The current path
            result: Set to store all paths
        """
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = current_path + [k]
                result.add('.'.join(new_path))
                if isinstance(v, (dict, list)):
                    self._get_paths(v, new_path, result)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    self._get_paths(item, current_path, result)
    
    def _get_by_path(self, obj: Dict[str, Any], path: List[str]) -> Any:
        """
        Get a value from a nested dictionary using a path.
        
        Args:
            obj: The dictionary to search
            path: The path as a list of keys
            
        Returns:
            The value at the path or None if not found
        """
        for key in path:
            if isinstance(obj, dict) and key in obj:
                obj = obj[key]
            else:
                return None
        return obj
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and normalize it.
        
        Args:
            data: Raw pitch data
            
        Returns:
            Normalized pitch data
        """
        return await self.normalize(data)