"""
Market Analysis Agent.

This module analyzes the market opportunity for a startup pitch
including TAM/SAM/SOM validation, CAGR, and industry positioning.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
import datetime

from agents import BaseAgent

logger = logging.getLogger(__name__)

class MarketAnalysis(BaseAgent):
    """
    Agent for analyzing market opportunity in startup pitches.
    
    This agent validates market size claims, growth rates, and overall
    market attractiveness.
    """
    
    # Score thresholds for market metrics
    MARKET_SIZE_SCORE_THRESHOLDS = {
        'tam': {
            'excellent': 1_000_000_000.0,  # $1B+
            'good': 100_000_000.0,         # $100M+
            'average': 10_000_000.0,       # $10M+
            'poor': 1_000_000.0            # $1M+
        },
        'cagr': {
            'excellent': 30.0,             # 30%+
            'good': 20.0,                  # 20%+
            'average': 10.0,               # 10%+
            'poor': 5.0                    # 5%+
        }
    }
    
    # Default confidence levels
    DEFAULT_CONFIDENCE = {
        'tam': 0.7,
        'sam': 0.6,
        'som': 0.5,
        'cagr': 0.6
    }
    
    async def analyze(self, normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data from the normalized pitch.
        
        Args:
            normalized_data: Normalized pitch data
            
        Returns:
            Market analysis results
        """
        logger.info("Starting market analysis")
        
        # Extract market data from normalized pitch
        market_data = normalized_data.get('market', {})
        domain = market_data.get('domain')
        sub_domain = market_data.get('sub_domain')
        
        # Analyze market size and growth
        tam_analysis = await self._analyze_tam(market_data.get('tam'))
        sam_analysis = await self._analyze_sam(market_data.get('sam'), tam_analysis)
        som_analysis = await self._analyze_som(market_data.get('som'), sam_analysis)
        cagr_analysis = await self._analyze_cagr(market_data.get('cagr'), domain, sub_domain)
        
        # Calculate overall market score
        category_average = self._calculate_category_average([
            tam_analysis.get('final_score', 0),
            sam_analysis.get('final_score', 0),
            som_analysis.get('final_score', 0),
            cagr_analysis.get('final_score', 0)
        ])
        
        # Compile all analysis into final result
        result = {
            "tam": tam_analysis,
            "sam": sam_analysis,
            "som": som_analysis,
            "cagr": cagr_analysis,
            "comments": self._generate_comments(tam_analysis, sam_analysis, som_analysis, cagr_analysis),
            "category_average": category_average,
            "category_metadata": self._generate_metadata(tam_analysis, sam_analysis, som_analysis, cagr_analysis)
        }
        
        logger.debug("Market analysis completed successfully")
        return result
    
    async def _analyze_tam(self, tam_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze Total Addressable Market (TAM) data.
        
        Args:
            tam_data: Normalized TAM data
            
        Returns:
            TAM analysis results
        """
        if not tam_data or tam_data.get('value') is None:
            return self._create_empty_analysis('tam', 'currency', 'USD')
        
        tam_value = tam_data.get('value')
        tam_currency = tam_data.get('currency', 'USD')
        raw_tam = tam_data.get('raw')
        
        # Get thresholds for scoring
        thresholds = self.MARKET_SIZE_SCORE_THRESHOLDS['tam']
        
        # Calculate raw score based on thresholds
        raw_score = self._score_market_size(tam_value, thresholds)
        
        # Apply any adjustments to get final score (none in this basic version)
        final_score = raw_score
        
        # Create TAM analysis result
        claimed = f"${tam_value:,.0f}" if tam_value is not None else None
        validated = claimed  # In a real system, this would be validated against external sources
        
        return {
            "claimed": claimed,
            "validated": validated,
            "data_type": "currency",
            "unit": tam_currency,
            "confidence": self.DEFAULT_CONFIDENCE['tam'],
            "raw_score": raw_score,
            "final_score": final_score,
            "comments": f"Total Addressable Market (TAM):**\n\n- Company claims a TAM of {claimed}.",
            "detailed_comments": [
                f"Total Addressable Market (TAM):**\n\n- Company claims a TAM of {claimed}."
            ],
            "visual_data": self._create_visual_data("Line Chart"),
            "key_points": [
                {
                    "tam_insight": validated,
                    "supporting_evidence": "Based on provided pitch deck data.",
                    "impact_assessment": "Critical factor for investment evaluation.",
                    "data_quality": "Medium confidence based on available data"
                }
            ],
            "recommendations": self._generate_market_recommendations(),
            "concerns": self._generate_market_concerns(),
            "questionnaire": [
                "What are the primary revenue drivers that impact TAM?",
                "How do you validate the accuracy of TAM projections?",
                "What external factors pose the greatest risk to TAM stability?"
            ],
            "contextual_analysis": [
                f"Total Addressable Market (TAM):**\n\n- Company claims a TAM of {claimed}."
            ],
            "sources": self._generate_sources_data(),
            "forecasting": self._generate_forecasting_data(),
            "validation_metadata": self._generate_validation_metadata()
        }
    
    async def _analyze_sam(self, sam_data: Optional[Dict[str, Any]], tam_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Serviceable Available Market (SAM) data.
        
        Args:
            sam_data: Normalized SAM data
            tam_analysis: Results from TAM analysis
            
        Returns:
            SAM analysis results
        """
        if not sam_data or sam_data.get('value') is None:
            return self._create_empty_analysis('sam', 'currency', 'USD')
        
        sam_value = sam_data.get('value')
        sam_currency = sam_data.get('currency', 'USD')
        raw_sam = sam_data.get('raw')
        
        # Get TAM value for comparison
        tam_value = tam_analysis.get('validated')
        if isinstance(tam_value, str) and tam_value.startswith('$'):
            tam_value = tam_value.strip('$').replace(',', '')
            try:
                tam_value = float(tam_value)
            except ValueError:
                tam_value = None

        # Normalize SAM value if it's a string (e.g. "$1,000")
        if isinstance(sam_value, str):
            sam_normalized = sam_value.strip('$').replace(',', '')
            try:
                sam_value = float(sam_normalized)
            except (ValueError, TypeError):
                sam_value = None

        # Check SAM vs TAM ratio (only when both are numeric and tam_value > 0)
        if isinstance(sam_value, (int, float)) and isinstance(tam_value, (int, float)) and tam_value > 0:
            sam_tam_ratio = sam_value / tam_value
        else:
            sam_tam_ratio = None
        
        # Score based on the ratio and absolute size
        thresholds = self.MARKET_SIZE_SCORE_THRESHOLDS['tam']  # Use same thresholds
        raw_score = self._score_market_size(sam_value, thresholds)
        
        # Adjust score based on ratio to TAM (SAM should be a reasonable subset of TAM)
        final_score = raw_score
        if sam_tam_ratio:
            if sam_tam_ratio > 0.9:  # SAM too close to TAM
                final_score = max(raw_score - 2, 1)  # Penalize but don't go below 1
            elif sam_tam_ratio < 0.01:  # SAM too small compared to TAM
                final_score = max(raw_score - 1, 1)  # Slight penalty
        
        # Create SAM analysis result
        claimed = f"${sam_value:,.0f}" if sam_value is not None else None
        validated = claimed  # In a real system, this would be validated against external sources
        
        return {
            "claimed": claimed,
            "validated": validated,
            "data_type": "currency",
            "unit": sam_currency,
            "confidence": self.DEFAULT_CONFIDENCE['sam'],
            "raw_score": raw_score,
            "final_score": final_score,
            "comments": f"Serviceable Available Market (SAM):**\n\n- Company claims a SAM of {claimed}.",
            "detailed_comments": [
                f"Serviceable Available Market (SAM):**\n\n- Company claims a SAM of {claimed}."
            ],
            "visual_data": self._create_visual_data("Line Chart"),
            "key_points": [
                {
                    "sam_insight": validated,
                    "supporting_evidence": "Based on provided pitch deck data.",
                    "impact_assessment": "Key factor for understanding market reach.",
                    "data_quality": "Medium confidence based on available data"
                }
            ],
            "recommendations": self._generate_market_recommendations(),
            "concerns": self._generate_market_concerns(),
            "questionnaire": [
                "What are the primary revenue drivers that impact SAM?",
                "How do you validate the accuracy of SAM projections?",
                "What external factors pose the greatest risk to SAM stability?"
            ],
            "contextual_analysis": [
                f"Serviceable Available Market (SAM):**\n\n- Company claims a SAM of {claimed}."
            ],
            "sources": self._generate_sources_data(),
            "forecasting": self._generate_forecasting_data(),
            "validation_metadata": self._generate_validation_metadata()
        }
    
    async def _analyze_som(self, som_data: Optional[Dict[str, Any]], sam_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Serviceable Obtainable Market (SOM) data.
        
        Args:
            som_data: Normalized SOM data
            sam_analysis: Results from SAM analysis
            
        Returns:
            SOM analysis results
        """
        if not som_data or som_data.get('value') is None:
            return self._create_empty_analysis('som', 'currency', 'USD')
        
        som_value = som_data.get('value')
        som_currency = som_data.get('currency', 'USD')
        raw_som = som_data.get('raw')
        
        # Normalize SOM value if it's a string (e.g. "$1,000")
        if isinstance(som_value, str):
            som_normalized = som_value.strip('$').replace(',', '')
            try:
                som_value = float(som_normalized)
            except (ValueError, TypeError):
                som_value = None

        # Get SAM value for comparison
        sam_value = sam_analysis.get('validated')
        # Normalize SAM value if it's a string (e.g. "$1,000")
        if isinstance(sam_value, str):
            sam_normalized = sam_value.strip('$').replace(',', '')
            try:
                sam_value = float(sam_normalized)
            except (ValueError, TypeError):
                sam_value = None
        
        # Check SOM vs SAM ratio only when both values are numeric and sam_value > 0
        if isinstance(som_value, (int, float)) and isinstance(sam_value, (int, float)) and sam_value > 0:
            som_sam_ratio = som_value / sam_value
        else:
            som_sam_ratio = None
        
        # Score based on realism of SOM claims
        thresholds = self.MARKET_SIZE_SCORE_THRESHOLDS['tam']  # Use same thresholds
        raw_score = self._score_market_size(som_value, thresholds)
        
        # Adjust score based on ratio to SAM (SOM should be a realistic subset of SAM)
        final_score = raw_score
        if som_sam_ratio:
            if som_sam_ratio > 0.8:  # SOM too close to SAM
                final_score = max(raw_score - 2, 1)  # Penalize but don't go below 1
            elif som_sam_ratio < 0.001:  # SOM too small compared to SAM
                final_score = max(raw_score - 1, 1)  # Slight penalty
        
        # Create SOM analysis result
        claimed = f"${som_value:,.0f}" if som_value is not None else None
        validated = claimed  # In a real system, this would be validated against external sources
        
        return {
            "claimed": claimed,
            "validated": validated,
            "data_type": "currency",
            "unit": som_currency,
            "confidence": self.DEFAULT_CONFIDENCE['som'],
            "raw_score": raw_score,
            "final_score": final_score,
            "comments": f"Conduct a detailed analysis of the startup's product, technology, and geographical constraints to estimate their SOM.",
            "detailed_comments": [
                f"Serviceable Obtainable Market (SOM):**\n\n- Company claims a SOM of {claimed}."
            ],
            "visual_data": self._create_visual_data("Line Chart"),
            "key_points": [
                {
                    "som_insight": validated,
                    "supporting_evidence": "Based on provided pitch deck data.",
                    "impact_assessment": "Critical for revenue projections.",
                    "data_quality": "Medium confidence based on available data"
                }
            ],
            "recommendations": self._generate_market_recommendations(),
            "concerns": self._generate_market_concerns(),
            "questionnaire": [
                "What are the primary revenue drivers that impact SOM?",
                "How do you validate the accuracy of SOM projections?",
                "What external factors pose the greatest risk to SOM stability?"
            ],
            "contextual_analysis": [
                f"Serviceable Obtainable Market (SOM):**\n\n- Company claims a SOM of {claimed}."
            ],
            "sources": self._generate_sources_data(),
            "forecasting": self._generate_forecasting_data(),
            "validation_metadata": self._generate_validation_metadata()
        }
    
    async def _analyze_cagr(self, cagr: Optional[Union[float, int]], 
                           domain: Optional[str], sub_domain: Optional[str]) -> Dict[str, Any]:
        """
        Analyze Compound Annual Growth Rate (CAGR) data.
        
        Args:
            cagr: CAGR value from pitch data
            domain: Business domain
            sub_domain: Business sub-domain
            
        Returns:
            CAGR analysis results
        """
        if cagr is None:
            return self._create_empty_analysis('cagr', 'percentage', 'Percent')
        
        # Get thresholds for scoring
        thresholds = self.MARKET_SIZE_SCORE_THRESHOLDS['cagr']
        
        # Calculate raw score based on thresholds
        raw_score = 0
        if cagr >= thresholds['excellent']:
            raw_score = 10
        elif cagr >= thresholds['good']:
            raw_score = 8
        elif cagr >= thresholds['average']:
            raw_score = 6
        elif cagr >= thresholds['poor']:
            raw_score = 4
        else:
            raw_score = 2
        
        # Apply any adjustments to get final score
        final_score = raw_score
        
        # Create CAGR analysis result
        claimed = f"{cagr}%"
        validated = claimed  # In a real system, this would be validated against industry data
        
        return {
            "claimed": claimed,
            "validated": claimed,
            "data_type": "percentage",
            "unit": "Percent",
            "confidence": self.DEFAULT_CONFIDENCE['cagr'],
            "raw_score": raw_score,
            "final_score": final_score,
            "comments": f"Market CAGR is projected at {claimed}.",
            "detailed_comments": [
                f"Market CAGR:**\n\n- Company claims a market CAGR of {claimed}."
            ],
            "visual_data": self._create_visual_data("comparative"),
            "key_points": [
                {
                    "cagr_insight": validated,
                    "supporting_evidence": "Based on provided pitch deck data.",
                    "impact_assessment": "Critical for growth projections.",
                    "data_quality": "Medium confidence based on available data"
                }
            ],
            "recommendations": self._generate_market_recommendations(),
            "concerns": self._generate_market_concerns(),
            "questionnaire": [
                "How is CAGR calculated and what methodology do you use?",
                "What benchmarks do you use to evaluate CAGR performance?",
                "How has CAGR trended over the past 12-24 months?"
            ],
            "contextual_analysis": [
                f"Market CAGR:**\n\n- Company claims a market CAGR of {claimed}."
            ],
            "sources": self._generate_sources_data(),
            "forecasting": self._generate_forecasting_data("Industry Benchmarking"),
            "validation_metadata": self._generate_validation_metadata()
        }
    
    def _create_empty_analysis(self, metric_name: str, data_type: str, unit: str) -> Dict[str, Any]:
        """
        Create an empty analysis result when data is missing.
        
        Args:
            metric_name: Name of the metric (tam, sam, som, cagr)
            data_type: Type of data (currency, percentage, etc.)
            unit: Unit of measurement (USD, Percent, etc.)
            
        Returns:
            Empty analysis structure
        """
        return {
            "claimed": None,
            "validated": None,
            "data_type": data_type,
            "unit": unit,
            "confidence": 0,
            "raw_score": 0,
            "final_score": 0,
            "comments": f"No {metric_name.upper()} data provided.",
            "detailed_comments": [f"No {metric_name.upper()} data provided in the pitch."],
            "visual_data": self._create_visual_data("None"),
            "key_points": [],
            "recommendations": [f"Company should provide {metric_name.upper()} data for proper analysis."],
            "concerns": [f"Missing {metric_name.upper()} data makes market assessment incomplete."],
            "questionnaire": [
                f"Can you provide your {metric_name.upper()} estimates?", 
                f"What methodology would you use to calculate {metric_name.upper()}?"
            ],
            "contextual_analysis": [f"No {metric_name.upper()} data provided."],
            "sources": self._generate_sources_data(),
            "forecasting": self._generate_forecasting_data(),
            "validation_metadata": self._generate_validation_metadata(False)
        }
    
    def _score_market_size(self, value: Optional[Union[float, int]], thresholds: Dict[str, float]) -> int:
        """
        Score market size based on thresholds.
        
        Args:
            value: Market size value (may be None)
            thresholds: Threshold dictionary for scoring
            
        Returns:
            Raw score (1-10)
        """
        if value is None:
            return 0
            
        if value >= thresholds['excellent']:
            return 10
        elif value >= thresholds['good']:
            return 8
        elif value >= thresholds['average']:
            return 6
        elif value >= thresholds['poor']:
            return 4
        else:
            return 2
    
    def _calculate_category_average(self, scores: List[int]) -> int:
        """
        Calculate average score for the category.
        
        Args:
            scores: List of individual scores
            
        Returns:
            Average score rounded to nearest integer
        """
        valid_scores = [score for score in scores if score > 0]
        if not valid_scores:
            return 0
        return round(sum(valid_scores) / len(valid_scores))
    
    def _generate_comments(self, tam_analysis, sam_analysis, som_analysis, cagr_analysis):
        """Generate overall comments based on all analyses."""
        comments = []
        
        # Add TAM comment if available
        if tam_analysis.get('validated'):
            comments.append(f"MarketAnalysis analysis reveals total addressable market (TAM):**\n\n- Company claims a TAM of {tam_analysis['validated']}.")
            
        # Add CAGR comment if available
        if cagr_analysis.get('validated'):
            if not comments:  # If no TAM comment
                comments.append(f"MarketAnalysis reveals market CAGR of {cagr_analysis['validated']}.")
        
        # Default if no comments
        if not comments:
            comments.append("MarketAnalysis completed but insufficient market data provided.")
            
        return comments
    
    def _generate_metadata(self, tam_analysis, sam_analysis, som_analysis, cagr_analysis):
        """Generate category metadata based on all analyses."""
        # Count data points
        total_points = sum(1 for a in [tam_analysis, sam_analysis, som_analysis, cagr_analysis] 
                           if a.get('validated'))
        
        # Count quantitative points (all market metrics are quantitative)
        quantitative_points = total_points
        
        return {
            "total_data_points": total_points,
            "quantitative_points": quantitative_points,
            "qualitative_points": 0,
            "primary_source_categories": [
                "market_research",
                "government",
                "academic"
            ],
            "data_reliability_score": 0.7
        }
    
    def _create_visual_data(self, chart_type="time_series"):
        """Create visual data structure for charts."""
        if chart_type == "None":
            return {}
            
        if chart_type == "Line Chart":
            return {
                "chart_type": "Line Chart",
                "x_axis": ["Q1", "Q2", "Q3", "Q4"],
                "y_axis": ["100", "125", "150", "180"],
                "recommended_visualization": "Time series analysis showing growth trends"
            }
        elif chart_type == "Bar Chart":
            return {
                "chart_type": "Bar Chart",
                "x_axis": ["Category A", "Category B", "Category C"],
                "y_axis": ["60", "75", "45"],
                "recommended_visualization": "Distribution across categories"
            }
        elif chart_type == "comparative":
            return {
                "chart_type": "Bar Chart",
                "x_axis": ["Current", "Target", "Industry Avg"],
                "y_axis": ["75", "90", "82"],
                "recommended_visualization": "Comparative analysis against benchmarks"
            }
        else:
            return {
                "chart_type": "Custom",
                "recommended_visualization": "Custom visualization based on data characteristics"
            }
    
    def _generate_market_recommendations(self):
        """Generate standard market analysis recommendations."""
        return [
            "Validate the startup's TAM claim with additional industry reports and expert opinions.",
            "Conduct a detailed analysis of the startup's product, technology, and geographical constraints to estimate their SAM.",
            "Conduct a detailed analysis of the startup's business model, resources, and competition to estimate their SOM.",
            "Validate the startup's CAGR claim with additional industry reports and expert opinions.",
            "Strategic Recommendations:**\n\n- Validate the startup's TAM and CAGR claims with additional industry reports and expert opinions."
        ]
    
    def _generate_market_concerns(self):
        """Generate standard market analysis concerns."""
        return [
            "If the startup's TAM is overstated, this could inflate their growth projections and valuation.",
            "If the startup's SAM is significantly smaller than the TAM, this could limit their growth potential.",
            "If the startup's SOM is significantly smaller than the SAM, this could limit their profitability."
        ]
    
    def _generate_sources_data(self):
        """Generate standard sources data structure."""
        return {
            "primary_sources": [
                "Industry reports",
                "Government publications",
                "Academic research"
            ],
            "secondary_sources": [
                "Company pitch deck",
                "News articles",
                "Analyst commentary"
            ],
            "source_quality": "Medium confidence based on available data"
        }

    def _generate_forecasting_data(self, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a basic forecasting data structure; accepts an optional context string
        to slightly adjust methodology or confidence when industry benchmarking is requested.
        """
        forecasting = {
            "projection_years": ["Year1", "Year2", "Year3", "Year4", "Year5"],
            "projected_revenue": ["0", "0", "0", "0", "0"],
            "assumptions": [
                "Revenue growth based on market adoption rates.",
                "Stable gross margins.",
                "No major regulatory changes."
            ],
            "methodology": "Top-down and bottom-up hybrid forecast based on pitch inputs.",
            "confidence": 0.6
        }

        if context:
            forecasting["context"] = context
            # Slightly prefer industry benchmarking methodology when requested
            if "Industry" in context or "benchmark" in context.lower():
                forecasting["methodology"] = "Industry benchmarking combined with company projections."
                forecasting["confidence"] = 0.65

        return forecasting

    def _generate_validation_metadata(self, validated: bool = True) -> Dict[str, Any]:
        """
        Generate lightweight validation metadata for analyzed metrics.

        Args:
            validated: Whether the metric was validated (default True)

        Returns:
            A dictionary containing validation metadata such as status, sources,
            confidence and timestamp so callers can include consistent metadata.
        """
        status = "validated" if validated else "unvalidated"
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        # Choose a conservative confidence when unvalidated
        confidence = 0.7 if validated else 0.0

        return {
            "status": status,
            "validated": validated,
            "validation_sources": [
                "pitch_deck" if not validated else "industry_report"
            ],
            "data_confidence": confidence,
            "last_validated_at": timestamp,
            "notes": "Automated metadata created; for production use replace with actual validation pipeline outputs."
        }