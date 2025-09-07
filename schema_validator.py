"""
Schema Validator Agent.

This module validates the final report against a predefined JSON schema.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
import json
import datetime

from agents import BaseAgent

logger = logging.getLogger(__name__)

class SchemaValidator(BaseAgent):
    """
    Agent for validating the final report against a predefined JSON schema.
    
    This agent ensures that the consolidated report adheres to the expected
    structure and data types before returning the final result.
    """
    
    # Default report schema - simplified version for the example
    DEFAULT_SCHEMA = {
        "type": "object",
        "required": ["pitchId", "clientId", "metadata", "validation_summary", "comments", "details", "summary"],
        "properties": {
            "pitchId": {"type": "string"},
            "clientId": {"type": "string"},
            "metadata": {
                "type": "object",
                "required": ["generated_at", "analysis_version"],
                "properties": {
                    "generated_at": {"type": "string", "format": "date-time"},
                    "analysis_version": {"type": "string"},
                    "data_sources_used": {"type": "integer"},
                    "total_validation_points": {"type": "integer"},
                    "processing_time_estimate": {"type": "string"}
                }
            },
            "validation_summary": {
                "type": "object",
                "properties": {
                    "MarketAnalysis": {"type": "object"},
                    "ProductMarketFit": {"type": "object"},
                    "Finance": {"type": "object"},
                    "CompetitiveLandscape": {"type": "object"},
                    "WhyAnalysis": {"type": "object"},
                    "Scalability": {"type": "object"}
                }
            },
            "comments": {
                "type": "array",
                "items": {"type": "string"}
            },
            "details": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "about": {"type": "string"},
                    "status": {"type": "string"},
                    "founded_year": {"type": ["integer", "string"]},
                    "CEO": {"type": "string"},
                    "headquaters": {"type": "string"},
                    "business_model": {"type": "string"},
                    "revenue": {"type": "string"},
                    "domain": {"type": "string"},
                    "sub-domain": {"type": ["string", "null"]},
                    "problem": {"type": ["string", "null"]},
                    "solution": {"type": ["string", "null"]},
                    "usp": {"type": ["string", "null"]}
                }
            },
            "summary": {"type": "string"},
            "pros": {
                "type": "array",
                "items": {"type": "string"}
            },
            "red_flags": {
                "type": "array",
                "items": {"type": "string"}
            },
            "ai_questionnaire": {
                "type": "array",
                "items": {"type": "string"}
            },
            "data_quality_assessment": {"type": "object"},
            "forecasting_methodology": {"type": "object"},
            "final_irs_score": {"type": "integer"},
            "final_cs_score": {"type": "integer"},
            "uniqueness": {"type": "integer"}
        }
    }
    
    async def validate(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the consolidated report against the JSON schema.
        
        Args:
            report: Consolidated report to validate
            
        Returns:
            Validated report with any necessary corrections
        """
        logger.info("Starting schema validation of final report")
        
        # Get schema from config or use default
        schema = self._get_schema()
        
        # Validate and fix the report
        validated_report = self._validate_and_fix(report, schema)
        
        # Add validation stamp
        validated_report["_validation"] = {
            "validated_at": datetime.datetime.now().isoformat(),
            "schema_version": self.config.get("output.schema_version", "1.0"),
            "is_valid": True
        }
        
        logger.debug("Schema validation completed successfully")
        return validated_report
    
    def _get_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema from config or use default.
        
        Returns:
            JSON schema for validation
        """
        # Try to get schema from config
        schema_path = self.config.get("output.schema_path")
        
        if schema_path:
            try:
                with open(schema_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading schema from {schema_path}: {e}")
                logger.warning("Using default schema instead")
        
        return self.DEFAULT_SCHEMA
    
    def _validate_and_fix(self, report: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the report against schema and fix issues.
        
        Args:
            report: Report to validate
            schema: JSON schema for validation
            
        Returns:
            Validated and fixed report
        """
        # Create a copy to avoid modifying the original
        fixed_report = dict(report)
        
        # Validate required properties
        self._validate_required_properties(fixed_report, schema)
        
        # Validate property types and formats
        self._validate_property_types(fixed_report, schema)
        
        # Validate nested objects
        self._validate_nested_objects(fixed_report, schema)
        
        return fixed_report
    
    def _validate_required_properties(self, report: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """
        Validate and fix required properties.
        
        Args:
            report: Report to validate
            schema: JSON schema for validation
        """
        # Check top-level required properties
        required_props = schema.get("required", [])
        for prop in required_props:
            if prop not in report:
                logger.warning(f"Missing required property: {prop}")
                # Add default value
                report[prop] = self._get_default_value(prop, schema.get("properties", {}).get(prop, {}))
        
        # Check nested objects with required properties
        for prop, prop_schema in schema.get("properties", {}).items():
            if isinstance(prop_schema, dict) and prop_schema.get("type") == "object" and "required" in prop_schema:
                if prop in report and isinstance(report[prop], dict):
                    nested_required = prop_schema.get("required", [])
                    nested_props = prop_schema.get("properties", {})
                    
                    for nested_prop in nested_required:
                        if nested_prop not in report[prop]:
                            logger.warning(f"Missing required nested property: {prop}.{nested_prop}")
                            # Add default value
                            report[prop][nested_prop] = self._get_default_value(
                                nested_prop, nested_props.get(nested_prop, {})
                            )
    
    def _validate_property_types(self, report: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """
        Validate and fix property types.
        
        Args:
            report: Report to validate
            schema: JSON schema for validation
        """
        # Check all properties defined in the schema
        for prop, prop_schema in schema.get("properties", {}).items():
            if prop in report:
                self._validate_value_type(report, prop, prop_schema)
    
    def _validate_value_type(self, obj: Dict[str, Any], prop: str, prop_schema: Dict[str, Any]) -> None:
        """
        Validate and fix a single property value type.
        
        Args:
            obj: Object containing the property
            prop: Property name
            prop_schema: Schema for the property
        """
        value = obj[prop]
        expected_type = prop_schema.get("type")
        
        # Skip validation if no type specified
        if not expected_type:
            return
            
        # Handle multiple allowed types
        if isinstance(expected_type, list):
            # Check if value matches any of the allowed types
            if not any(self._check_type(value, t) for t in expected_type):
                logger.warning(f"Property {prop} has invalid type. Expected one of {expected_type}, got {type(value).__name__}")
                # Convert to the first allowed type
                obj[prop] = self._convert_value(value, expected_type[0])
        else:
            # Single type check
            if not self._check_type(value, expected_type):
                logger.warning(f"Property {prop} has invalid type. Expected {expected_type}, got {type(value).__name__}")
                # Convert to the expected type
                obj[prop] = self._convert_value(value, expected_type)
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """
        Check if a value matches the expected type.
        
        Args:
            value: Value to check
            expected_type: Expected type name
            
        Returns:
            True if type matches, False otherwise
        """
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "integer":
            return isinstance(value, int) or (isinstance(value, float) and value.is_integer())
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        elif expected_type == "null":
            return value is None
        else:
            return False
    
    def _convert_value(self, value: Any, target_type: str) -> Any:
        """
        Convert a value to the target type.
        
        Args:
            value: Value to convert
            target_type: Target type name
            
        Returns:
            Converted value
        """
        try:
            if target_type == "string":
                return str(value)
            elif target_type == "number":
                return float(value)
            elif target_type == "integer":
                return int(float(value))
            elif target_type == "boolean":
                return bool(value)
            elif target_type == "array":
                return [value] if value is not None else []
            elif target_type == "object":
                return {} if value is None else (value if isinstance(value, dict) else {})
            elif target_type == "null":
                return None
            else:
                return value
        except (ValueError, TypeError):
            logger.warning(f"Could not convert value {value} to {target_type}")
            return self._get_default_value("", {"type": target_type})
    
    def _validate_nested_objects(self, report: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """
        Validate nested objects in the report.
        
        Args:
            report: Report to validate
            schema: JSON schema for validation
        """
        for prop, prop_schema in schema.get("properties", {}).items():
            if prop in report and isinstance(prop_schema, dict):
                if prop_schema.get("type") == "object" and isinstance(report[prop], dict):
                    # Recursively validate nested object
                    nested_schema = {
                        "type": "object",
                        "required": prop_schema.get("required", []),
                        "properties": prop_schema.get("properties", {})
                    }
                    self._validate_and_fix(report[prop], nested_schema)
                elif prop_schema.get("type") == "array" and isinstance(report[prop], list):
                    # Validate array items
                    items_schema = prop_schema.get("items", {})
                    if items_schema.get("type") == "object":
                        for item in report[prop]:
                            if isinstance(item, dict):
                                nested_schema = {
                                    "type": "object",
                                    "required": items_schema.get("required", []),
                                    "properties": items_schema.get("properties", {})
                                }
                                self._validate_and_fix(item, nested_schema)
    
    def _get_default_value(self, prop: str, prop_schema: Dict[str, Any]) -> Any:
        """
        Get default value for a property based on schema.
        
        Args:
            prop: Property name
            prop_schema: Schema for the property
            
        Returns:
            Default value
        """
        # Check if default value is specified in schema
        if "default" in prop_schema:
            return prop_schema["default"]
        
        # Use type-based defaults
        prop_type = prop_schema.get("type")
        if not prop_type:
            return None
            
        # Handle multiple types
        if isinstance(prop_type, list):
            prop_type = prop_type[0]  # Use first type for default
        
        if prop_type == "string":
            # Use property name as hint for better defaults
            if "date" in prop.lower() or prop_schema.get("format") == "date-time":
                return datetime.datetime.now().isoformat()
            elif "id" in prop.lower():
                return "unknown_id"
            elif "name" in prop.lower():
                return "Unknown"
            elif "version" in prop.lower():
                return "1.0"
            else:
                return ""
        elif prop_type == "number":
            return 0.0
        elif prop_type == "integer":
            return 0
        elif prop_type == "boolean":
            return False
        elif prop_type == "array":
            return []
        elif prop_type == "object":
            return {}
        elif prop_type == "null":
            return None
        else:
            return None
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and validate against schema.
        
        Args:
            data: Dictionary containing the consolidated report
            
        Returns:
            Validated report
        """
        return await self.validate(data)