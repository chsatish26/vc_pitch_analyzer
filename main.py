#!/usr/bin/env python
"""
Main entry point for the VC Pitch Analysis System.
"""

import argparse
import json
import logging
from pathlib import Path
import sys

from orchestrator import Orchestrator
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='VC Pitch Analysis System')
    parser.add_argument('--pitch_id', type=str, required=True,
                        help='The MongoDB ObjectId of the pitch to analyze')
    parser.add_argument('--output_file', type=str, default='output.json',
                        help='Path to save the output JSON (default: output.json)')
    parser.add_argument('--config', type=str, default='config.json',
                        help='Path to configuration file (default: config.json)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    return parser.parse_args()

def main():
    """Main execution function."""
    args = parse_arguments()
    
    # Set logging level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Starting VC Pitch Analysis for pitch ID: {args.pitch_id}")
    
    # Load configuration
    try:
        config = Config(args.config)
        logger.debug("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Initialize orchestrator
    orchestrator = Orchestrator(config)
    
    # Run analysis pipeline
    try:
        result = orchestrator.process_pitch(args.pitch_id)
        logger.info("Analysis completed successfully")
        
        # Save results
        output_path = Path(args.output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()