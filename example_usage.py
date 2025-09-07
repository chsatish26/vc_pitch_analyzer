#!/usr/bin/env python
"""
Example script demonstrating how to use the VC Pitch Analysis System.

This script shows a complete example of analyzing a pitch and handling the results.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Make sure the package is in the Python path
# If this script lives inside the package folder (vc_pitch_analyzer), add the parent directory
# (project root) to sys.path so the top-level package can be imported by name.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import from the VC Pitch Analyzer package
# Use relative imports because this module lives inside the package.
# Note: run this script with "python -m vc_pitch_analyzer.example_usage" so relative imports work.
from config import Config
from orchestrator import Orchestrator
from utils.helpers import format_currency

def save_json_file(data, path: str) -> None:
    """
    Save data to a JSON file, creating parent directories as needed.
    This local helper replaces a missing import symbol.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

class ExamplePitchAnalyzer:
    """Example class demonstrating the VC Pitch Analysis System."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the example analyzer.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Load configuration
        self.config = Config(config_path)
        
        # Initialize the orchestrator
        self.orchestrator = Orchestrator(self.config)
        
        # Create output directory
        self.output_dir = Path("analysis_results")
        self.output_dir.mkdir(exist_ok=True)
        
    def analyze_pitch(self, pitch_id: str) -> dict:
        """
        Analyze a pitch by ID.
        
        Args:
            pitch_id: MongoDB ObjectId of the pitch to analyze
            
        Returns:
            Analysis results as a dictionary
        """
        logger.info(f"Analyzing pitch ID: {pitch_id}")
        
        # Process the pitch
        result = self.orchestrator.process_pitch(pitch_id)
        
        # Log completion
        logger.info(f"Analysis completed for pitch ID: {pitch_id}")
        
        return result
    
    def save_results(self, result: dict, pitch_id: str) -> Path:
        """
        Save analysis results to JSON file.
        
        Args:
            result: Analysis results dictionary
            pitch_id: Pitch ID for filename
            
        Returns:
            Path to saved file
        """
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"analysis_{pitch_id}_{timestamp}.json"
        
        # Save to file
        save_json_file(result, str(output_path))
        logger.info(f"Results saved to: {output_path}")
        
        return output_path
    
    def print_summary(self, result: dict) -> None:
        """
        Print a summary of the analysis results.
        
        Args:
            result: Analysis results dictionary
        """
        print("\n" + "=" * 80)
        print(f"INVESTMENT ANALYSIS SUMMARY: {result.get('details', {}).get('name', 'Unknown Company')}")
        print("=" * 80)
        
        # Print basic details
        details = result.get("details", {})
        print(f"Company: {details.get('name', 'Unknown')}")
        print(f"Domain: {details.get('domain', 'Unknown')}")
        print(f"Business Model: {details.get('business_model', 'Unknown')}")
        print(f"Founded: {details.get('founded_year', 'Unknown')}")
        print(f"CEO: {details.get('CEO', 'Unknown')}")
        
        # Print summary
        print("\nSUMMARY:")
        print(result.get("summary", "No summary available"))
        
        # Print scores
        print("\nSCORES:")
        print(f"Investment Rating: {result.get('final_irs_score', 0)}/10")
        print(f"Confidence Score: {result.get('final_cs_score', 0)}/10")
        print(f"Uniqueness Factor: {result.get('uniqueness', 0)}/100")
        
        # Print pros and cons
        print("\nPROS:")
        for pro in result.get("pros", []):
            print(f"- {pro}")
        
        print("\nRED FLAGS:")
        for flag in result.get("red_flags", []):
            print(f"- {flag}")
        
        # Print key metrics if available
        print("\nKEY METRICS:")
        validation = result.get("validation_summary", {})
        
        if "MarketAnalysis" in validation and "tam" in validation["MarketAnalysis"]:
            tam = validation["MarketAnalysis"]["tam"].get("validated", "N/A")
            print(f"TAM: {tam}")
            
        if "Finance" in validation:
            finance = validation["Finance"]
            if "gross_margin" in finance:
                gm = finance["gross_margin"].get("validated", "N/A")
                print(f"Gross Margin: {gm}")
            
            if "runway" in finance:
                runway = finance["runway"].get("validated", "N/A")
                print(f"Runway: {runway}")
        
        if "ProductMarketFit" in validation and "ltv_cac" in validation["ProductMarketFit"]:
            ltv_cac = validation["ProductMarketFit"]["ltv_cac"].get("validated", "N/A")
            print(f"LTV/CAC: {ltv_cac}")
        
        # Print due diligence questions
        print("\nDUE DILIGENCE QUESTIONS:")
        for question in result.get("ai_questionnaire", []):
            print(f"- {question}")
            
        print("\n" + "=" * 80)
        print(f"Full results saved to JSON file. Use for detailed analysis.")
        print("=" * 80 + "\n")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='VC Pitch Analysis Example')
    parser.add_argument('--pitch_id', type=str, required=True,
                       help='MongoDB ObjectId of the pitch to analyze')
    parser.add_argument('--config', type=str, default=None,
                       help='Path to configuration file')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    
    return parser.parse_args()


async def main_async():
    """Asynchronous main function."""
    args = parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize analyzer
        analyzer = ExamplePitchAnalyzer(args.config)
        
        # Analyze pitch
        result = analyzer.analyze_pitch(args.pitch_id)
        
        # Save results
        analyzer.save_results(result, args.pitch_id)
        
        # Print summary
        analyzer.print_summary(result)
        
    except Exception as e:
        logger.error(f"Error analyzing pitch: {e}")
        raise


def main():
    """Main entry point."""
    # Create and run event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_async())
    finally:
        loop.close()


if __name__ == "__main__":
    main()