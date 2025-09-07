"""
Configuration management for the VC Pitch Analysis System.
"""

import json
import logging
import os
from pathlib import Path
import yaml
from typing import Dict, Any, Optional
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """Configuration handler for the VC Pitch Analysis System."""
    
    DEFAULT_CONFIG = {
        "mongodb": {
            "uri": "mongodb+srv://development:LYSYcByf9XkdAq69@pitchfynd-dev.kcyjk.mongodb.net/pitchfynd-dev?retryWrites=true&w=majority&appName=pitchfynd-dev",
            "database": "pitchfynd-dev",
            "collection": "pitches"
        },
        "currency": {
            "base": "USD",
            "rates": {
                "INR": 87.0,
                "EUR": 0.85,
                "GBP": 0.73
            }
        },
        "scoring": {
            "weights": {
                "market_analysis": 0.2,
                "competitive_landscape": 0.15,
                "product_market_fit": 0.2,
                "finance_analysis": 0.25,
                "why_analysis": 0.1,
                "scalability": 0.1
            },
            "thresholds": {
                "excellent": 8.5,
                "good": 7.0,
                "average": 5.0,
                "below_average": 3.0
            }
        },
        "web_research": {
            "enabled": True,
            "api_key": "",
            "max_searches": 10
        },
        "output": {
            "schema_version": "1.0"
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration with optional file path.
        
        Args:
            config_path: Path to configuration JSON file (optional)
        """
        self.config_data = dict(self.DEFAULT_CONFIG)
        
        if config_path:
            self._load_from_file(config_path)
        
        # Check for environment variable overrides
        self._load_from_env()
    
    def _load_from_file(self, config_path: str) -> None:
        """
        Load configuration from a JSON file.
        
        Args:
            config_path: Path to configuration JSON file
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file isn't valid JSON
        """
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                
            # Deep update the default config with file values
            self._deep_update(self.config_data, file_config)
            logger.debug(f"Loaded configuration from {config_path}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse config file {config_path}: {e}")
            raise
    
    def _load_from_env(self) -> None:
        """Load configuration overrides from environment variables."""
        # MongoDB connection
        if os.environ.get('MONGO_URI'):
            self.config_data['mongodb']['uri'] = os.environ.get('MONGO_URI')
        
        if os.environ.get('MONGO_DB'):
            self.config_data['mongodb']['database'] = os.environ.get('MONGO_DB')
            
        if os.environ.get('MONGO_COLLECTION'):
            self.config_data['mongodb']['collection'] = os.environ.get('MONGO_COLLECTION')
        
        # LLM Configuration
        if os.environ.get('LLM_PROVIDER'):
            if 'llm' not in self.config_data:
                self.config_data['llm'] = {}
            self.config_data['llm']['provider'] = os.environ.get('LLM_PROVIDER')
        
        # API keys based on provider
        if os.environ.get('OPENAI_API_KEY'):
            if 'llm' not in self.config_data:
                self.config_data['llm'] = {}
            self.config_data['llm']['openai_api_key'] = os.environ.get('OPENAI_API_KEY')
            
        if os.environ.get('ANTHROPIC_API_KEY'):
            if 'llm' not in self.config_data:
                self.config_data['llm'] = {}
            self.config_data['llm']['anthropic_api_key'] = os.environ.get('ANTHROPIC_API_KEY')
            
        if os.environ.get('DEEPSEEK_API_KEY'):
            if 'llm' not in self.config_data:
                self.config_data['llm'] = {}
            self.config_data['llm']['deepseek_api_key'] = os.environ.get('DEEPSEEK_API_KEY')
        
        # Web research API key
        if os.environ.get('SERPER_API_KEY'):
            if 'web_research' not in self.config_data:
                self.config_data['web_research'] = {}
            self.config_data['web_research']['api_key'] = os.environ.get('SERPER_API_KEY')
            self.config_data['web_research']['enabled'] = True
            
        logger.debug("Applied configuration overrides from environment variables")
    
    def _deep_update(self, original: Dict[str, Any], update: Dict[str, Any]) -> None:
        """
        Recursively update a dictionary with another dictionary.
        
        Args:
            original: The dictionary to update
            update: The dictionary with updates
        """
        for key, value in update.items():
            if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                self._deep_update(original[key], value)
            else:
                original[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'mongodb.uri')
            default: Default value if key doesn't exist
            
        Returns:
            The configuration value or default
        """
        parts = key.split('.')
        config = self.config_data
        
        for part in parts:
            if part not in config:
                return default
            config = config[part]
        
        return config
    


# Add this method to your Config class:
def _load_from_yaml(self, config_path: str) -> None:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to configuration YAML file
    """
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            # Load YAML configuration
            yaml_config = yaml.safe_load(f)
            
            # Handle environment variable substitution
            yaml_config = self._process_env_vars(yaml_config)
            
            # Deep update the default config with YAML values
            self._deep_update(self.config_data, yaml_config)
            logger.debug(f"Loaded configuration from {config_path}")
            
    except Exception as e:
        logger.error(f"Failed to parse config file {config_path}: {e}")
        raise

def _process_env_vars(self, config: dict) -> dict:
    """
    Process environment variable substitutions in the config.
    
    Args:
        config: Configuration dictionary with potential env vars
        
    Returns:
        Processed configuration with env vars substituted
    """
    if isinstance(config, dict):
        return {k: self._process_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [self._process_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
        # Parse ${ENV_VAR:default} format
        env_var_string = config[2:-1]
        if ':' in env_var_string:
            env_var, default = env_var_string.split(':', 1)
            return os.environ.get(env_var, default)
        else:
            return os.environ.get(env_var_string, '')
    else:
        return config