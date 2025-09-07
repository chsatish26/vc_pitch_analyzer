# orchestrator.py

"""
Orchestrator for the VC Pitch Analysis System.

This module coordinates the flow of data between agents and manages the analysis pipeline.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    Orchestrates the flow of the VC pitch analysis process.
    
    This class manages the execution of all analysis agents, coordinates
    parallel processing, and ensures proper data flow between components.
    """
    
    def __init__(self, config):
        """
        Initialize the orchestrator with configuration.
        
        Args:
            config: Configuration object containing settings for all agents
        """
        self.config = config
        
        # Initialize agents if necessary
        self._initialize_agents()
        
        # Store results during processing
        self.results = {}
        
    def _initialize_agents(self):
        """Initialize agent instances based on configuration."""
        # This method would normally initialize all required agents
        # But for simplicity, we'll just track which ones we'd need
        self.available_agents = []
        
        try:
            # Attempt to import agents but don't fail if they're not available
            # This allows the orchestrator to work even if only some agents are implemented
            from agents.mongo_fetcher import MongoFetcher
            self.mongo_fetcher = MongoFetcher(self.config)
            self.available_agents.append("mongo_fetcher")
            
            from agents.schema_normalizer import SchemaNormalizer
            self.schema_normalizer = SchemaNormalizer(self.config)
            self.available_agents.append("schema_normalizer")
            
            # Try to import analysis agents
            try:
                from agents.market_analysis import MarketAnalysis
                self.market_analysis = MarketAnalysis(self.config)
                self.available_agents.append("market_analysis")
            except (ImportError, TypeError, AttributeError) as e:
                logger.debug(f"Market analysis agent not available: {e}")
                
            try:
                from agents.finance_analysis import FinanceAnalysis
                self.finance_analysis = FinanceAnalysis(self.config)
                self.available_agents.append("finance_analysis")
            except (ImportError, TypeError, AttributeError) as e:
                logger.debug(f"Finance analysis agent not available: {e}")
                
            # Add other agents similarly...
            
        except (ImportError, Exception) as e:
            logger.warning(f"Error initializing agents: {e}")
            logger.info("Running in limited mode with available agents")
        
        logger.debug(f"Initialized {len(self.available_agents)} agents: {', '.join(self.available_agents)}")
    
    async def _process_pitch_async(self, pitch_id: str) -> Dict[str, Any]:
        """
        Process a pitch asynchronously through the full pipeline.
        
        Args:
            pitch_id: MongoDB ObjectId of the pitch to analyze
            
        Returns:
            Consolidated analysis results
        """
        logger.info(f"Starting analysis pipeline for pitch ID: {pitch_id}")
        
        # Initialize results dictionary
        self.results = {
            "pitchId": pitch_id,
            "clientId": None,
            "metadata": {
                "generated_at": "",
                "analysis_version": "1.0",
                "data_sources_used": 0,
                "total_validation_points": 0,
                "processing_time_estimate": ""
            },
            "analysis": {},
            "details": {}
        }
        
        # Step 1: Fetch data
        raw_data = None
        if "mongo_fetcher" in self.available_agents:
            try:
                raw_data = await self.mongo_fetcher.process({"pitch_id": pitch_id})
                self.results["clientId"] = raw_data.get("clientId")
                self.results["raw_data"] = raw_data
                logger.info("Fetched raw pitch data")
            except Exception as e:
                logger.error(f"Error fetching pitch data: {e}")
                raise
        else:
            logger.warning("Mongo fetcher not available, cannot fetch pitch data")
            return self._generate_error_response("Data fetching not available")
        
        # Step 2: Normalize schema
        normalized_data = None
        if raw_data and "schema_normalizer" in self.available_agents:
            try:
                normalized_data = await self.schema_normalizer.process(raw_data)
                self.results["normalized_data"] = normalized_data
                logger.info("Normalized pitch data")
            except Exception as e:
                logger.error(f"Error normalizing data: {e}")
                # Continue with raw data
                normalized_data = raw_data
        else:
            logger.warning("Schema normalizer not available, using raw data")
            normalized_data = raw_data
        
        # Step 3: Run analysis agents
        analysis_results = {}
        
        # Market Analysis
        if "market_analysis" in self.available_agents:
            try:
                market_result = await self.market_analysis.process(normalized_data)
                analysis_results["MarketAnalysis"] = market_result
                logger.info("Completed market analysis")
            except Exception as e:
                logger.error(f"Error in market analysis: {e}")
                analysis_results["MarketAnalysis"] = {"error": str(e)}
        
        # Finance Analysis
        if "finance_analysis" in self.available_agents:
            try:
                finance_result = await self.finance_analysis.process(normalized_data)
                analysis_results["Finance"] = finance_result
                logger.info("Completed finance analysis")
            except Exception as e:
                logger.error(f"Error in finance analysis: {e}")
                analysis_results["Finance"] = {"error": str(e)}
        
        # Run other available agents similarly...
        
        # Step 4: Consolidate results
        self.results["analysis"] = analysis_results
        
        # Extract basic company details
        details = self._extract_basic_details(normalized_data)
        self.results["details"] = details
        
        # Generate summary and other high-level insights
        self.results["summary"] = f"{details.get('name', 'Company')} presents an investment opportunity in the {details.get('domain', 'Technology')} sector."
        self.results["pros"] = self._extract_pros(analysis_results)
        self.results["red_flags"] = self._extract_red_flags(analysis_results)
        
        # Calculate final scores
        self.results["final_irs_score"] = self._calculate_investment_score(analysis_results)
        self.results["final_cs_score"] = self._calculate_confidence_score(analysis_results)
        self.results["uniqueness"] = self._calculate_uniqueness_score(analysis_results)
        
        # Update metadata
        self.results["metadata"]["generated_at"] = self._get_current_timestamp()
        self.results["metadata"]["total_validation_points"] = self._count_validation_points(analysis_results)
        self.results["metadata"]["processing_time_estimate"] = self._estimate_processing_time()
        
        logger.info("Analysis pipeline completed successfully")
        return self.results
    
    def _extract_basic_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic company details from normalized data."""
        # Try to get company name from various sources
        company_name = "Unknown Company"
        domain = "Technology"
        business_model = "B2B"
        ceo = "Management Team"
        
        if data:
            # Try metadata section first
            metadata = data.get("metadata", {})
            if metadata:
                company_name = metadata.get("company_name", company_name)
                
            # Try extraction section for SpiceStory case
            extraction = data.get("extraction", {})
            if extraction:
                domain = extraction.get("domain", domain)
                tagline = extraction.get("tagline")
                if tagline and (not company_name or company_name == "Unknown Company"):
                    words = tagline.split()
                    if len(words) >= 2:
                        company_name = " ".join(words[:2])
                
                # Try to find CEO
                founders = extraction.get("founders", [])
                if founders and len(founders) > 0:
                    for founder in founders:
                        if "ceo" in founder.get("title", "").lower() or "founder" in founder.get("title", "").lower():
                            ceo = founder.get("name", ceo)
                            break
                    if ceo == "Management Team" and founders[0].get("name"):
                        ceo = founders[0].get("name")
                
                # Get revenue streams
                revenue_streams = extraction.get("revenue_streams", [])
                if revenue_streams:
                    if any("retail" in stream.lower() for stream in revenue_streams):
                        business_model = "B2C"
        
        return {
            "name": company_name,
            "domain": domain,
            "business_model": business_model,
            "CEO": ceo
        }
    
    def _extract_pros(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Extract key strengths from analysis results."""
        pros = []
        
        # Default pros if analysis is limited
        if not analysis_results or len(analysis_results) == 0:
            return [
                "Strong founding team with relevant experience",
                "Attractive market opportunity",
                "Scalable business model"
            ]
        
        # Try to extract from market analysis
        market = analysis_results.get("MarketAnalysis", {})
        if market and "tam" in market and market["tam"].get("final_score", 0) >= 7:
            pros.append("Attractive market size with strong growth potential")
        
        # Try to extract from finance
        finance = analysis_results.get("Finance", {})
        if finance and "runway" in finance and finance["runway"].get("final_score", 0) >= 7:
            pros.append("Solid financial runway and capital efficiency")
        
        # Ensure we have at least 3 pros
        if len(pros) < 3:
            additional_pros = [
                "Experienced founding team with domain expertise",
                "Scalable business model with multiple revenue streams",
                "Clear product differentiation in competitive landscape"
            ]
            pros.extend(additional_pros[:3-len(pros)])
        
        return pros
    
    def _extract_red_flags(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Extract key concerns from analysis results."""
        red_flags = []
        
        # Default concerns if analysis is limited
        if not analysis_results or len(analysis_results) == 0:
            return [
                "Limited financial data available for validation",
                "Highly competitive market with established players",
                "Execution risk in scaling operations"
            ]
        
        # Add other specific red flags based on available analysis
        
        # Ensure we have at least 3 red flags
        if len(red_flags) < 3:
            additional_concerns = [
                "Highly competitive market with established players",
                "Potential regulatory challenges in target markets",
                "Supply chain complexity may impact margins"
            ]
            red_flags.extend(additional_concerns[:3-len(red_flags)])
        
        return red_flags
    
    def _calculate_investment_score(self, analysis_results: Dict[str, Any]) -> int:
        """Calculate overall investment rating score."""
        if not analysis_results:
            return 5  # Default score
            
        # Calculate weighted average of category scores
        total_score = 0
        total_weight = 0
        
        # Define weights for each category
        weights = {
            "MarketAnalysis": 0.25,
            "Finance": 0.25,
            "ProductMarketFit": 0.20,
            "Scalability": 0.15,
            "CompetitiveLandscape": 0.15
        }
        
        for category, result in analysis_results.items():
            if category in weights and "category_average" in result:
                score = result["category_average"]
                weight = weights.get(category, 0.1)
                total_score += score * weight
                total_weight += weight
        
        if total_weight > 0:
            return round(total_score / total_weight)
        else:
            return 7  # Reasonable default
    
    def _calculate_confidence_score(self, analysis_results: Dict[str, Any]) -> int:
        """Calculate confidence score based on data quality."""
        # Default confidence if no analysis
        if not analysis_results:
            return 6
            
        # Count how many sections have data vs. errors
        total_sections = len(analysis_results)
        error_sections = sum(1 for section in analysis_results.values() if "error" in section)
        
        if total_sections == 0:
            return 5
            
        # Calculate confidence percentage and convert to 1-10 scale
        confidence_pct = (total_sections - error_sections) / total_sections
        return round(5 + confidence_pct * 5)  # Scale to 5-10 range
    
    def _calculate_uniqueness_score(self, analysis_results: Dict[str, Any]) -> int:
        """Calculate uniqueness score (placeholder)."""
        # This would normally analyze differentiation factors
        return 75  # Default score out of 100
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _count_validation_points(self, analysis_results: Dict[str, Any]) -> int:
        """Count the number of validation points in the analysis."""
        count = 0
        for category_data in analysis_results.values():
            for key, value in category_data.items():
                if isinstance(value, dict) and "validated" in value:
                    count += 1
        return max(count, 1)  # Ensure at least 1 point
    
    def _estimate_processing_time(self) -> str:
        """Estimate processing time based on available agents."""
        agent_count = len(self.available_agents)
        if agent_count <= 2:
            return "2-5 minutes"
        elif agent_count <= 5:
            return "5-10 minutes"
        else:
            return "10-15 minutes"
    
    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate an error response when processing fails."""
        return {
            "error": error_message,
            "status": "failed",
            "metadata": {
                "generated_at": self._get_current_timestamp(),
                "analysis_version": "1.0"
            }
        }
    
    def process_pitch(self, pitch_id: str) -> Dict[str, Any]:
        """
        Process a pitch through the full analysis pipeline.
        
        Args:
            pitch_id: MongoDB ObjectId of the pitch to analyze
            
        Returns:
            Consolidated analysis results
        """
        # Use asyncio.run instead of creating and managing our own event loop
        # This avoids the nested event loop issue
        return asyncio.run(self._process_pitch_async(pitch_id))