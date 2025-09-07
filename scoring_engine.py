"""
Scoring Engine Agent.

This module calculates scores for different aspects of the pitch based on analysis results.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
import datetime

from agents import BaseAgent

logger = logging.getLogger(__name__)

class ScoringEngine(BaseAgent):
    """
    Agent for calculating scores for various aspects of the pitch.
    
    This agent applies scoring rules to the analysis results from other agents
    to produce standardized scores for each section and an overall score.
    """
    
    # Default weights for different analysis categories
    DEFAULT_WEIGHTS = {
        "MarketAnalysis": 0.20,
        "CompetitiveLandscape": 0.15,
        "ProductMarketFit": 0.20,
        "Finance": 0.25,
        "WhyAnalysis": 0.10,
        "Scalability": 0.10
    }
    
    # Scoring thresholds
    SCORE_THRESHOLDS = {
        "excellent": 8.5,
        "good": 7.0,
        "average": 5.0,
        "below_average": 3.0
    }
    
    async def score(self, analysis_results: Dict[str, Any], 
                  research_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Score the pitch based on analysis results.
        
        Args:
            analysis_results: Analysis results from all agents
            research_results: Web research results (optional)
            
        Returns:
            Scoring results
        """
        logger.info("Starting pitch scoring")
        
        # Load weights from config or use defaults
        weights = self._get_weights()
        
        # Score each category
        category_scores = {}
        for category, weight in weights.items():
            if category in analysis_results:
                # Get the category_average from the analysis results
                category_average = analysis_results[category].get("category_average", 0)
                
                # Apply any adjustments based on web research
                adjusted_score = self._adjust_score_with_research(
                    category, category_average, research_results
                )
                
                # Store category score
                category_scores[category] = {
                    "raw_score": category_average,
                    "adjusted_score": adjusted_score,
                    "weight": weight,
                    "weighted_score": adjusted_score * weight
                }
        
        # Calculate overall score
        overall_raw = self._calculate_overall_score(category_scores)
        overall_adjusted = self._apply_overall_adjustments(overall_raw, analysis_results)
        
        # Generate score explanations
        explanations = self._generate_explanations(category_scores, overall_adjusted)
        
        # Build final scoring result
        result = {
            "category_scores": category_scores,
            "overall_raw": overall_raw,
            "overall_adjusted": overall_adjusted,
            "explanations": explanations,
            "investment_recommendation": self._generate_investment_recommendation(overall_adjusted),
            "confidence": self._calculate_confidence(analysis_results),
            "scoring_version": "2.1",
            "scored_at": datetime.datetime.now().isoformat()
        }
        
        logger.debug("Pitch scoring completed successfully")
        return result
    
    def _get_weights(self) -> Dict[str, float]:
        """
        Get category weights from config or use defaults.
        
        Returns:
            Dictionary of category weights
        """
        # Try to get weights from config
        config_weights = self.config.get("scoring.weights", {})
        
        # Use config weights or defaults
        weights = dict(self.DEFAULT_WEIGHTS)
        for category, weight in config_weights.items():
            if category in weights:
                weights[category] = weight
                
        # Normalize weights to sum to 1
        total_weight = sum(weights.values())
        if total_weight > 0:
            for category in weights:
                weights[category] /= total_weight
                
        return weights
    
    def _adjust_score_with_research(self, category: str, score: float, 
                                  research_results: Optional[Dict[str, Any]] = None) -> float:
        """
        Adjust category score based on web research results.
        
        Args:
            category: Analysis category name
            score: Raw category score
            research_results: Web research results
            
        Returns:
            Adjusted score
        """
        if not research_results:
            return score
            
        # Extract research summary
        summary = research_results.get("summary", {})
        credibility_score = summary.get("credibility_score", 0)
        
        # Calculate adjustment factor based on credibility score
        # Higher credibility confirms claims, lower credibility penalizes
        if credibility_score >= 80:
            adjustment = 0.5  # Positive adjustment
        elif credibility_score >= 50:
            adjustment = 0  # No adjustment
        else:
            adjustment = -1.0  # Negative adjustment
            
        # Apply adjustment but keep within bounds
        adjusted_score = max(1, min(10, score + adjustment))
        
        return adjusted_score
    
    def _calculate_overall_score(self, category_scores: Dict[str, Dict[str, Any]]) -> float:
        """
        Calculate overall score from category scores.
        
        Args:
            category_scores: Dictionary of category scores
            
        Returns:
            Overall raw score
        """
        # Sum weighted scores
        weighted_sum = sum(
            cat_score.get("weighted_score", 0) 
            for cat_score in category_scores.values()
        )
        
        # Sum weights that were actually used
        weights_sum = sum(
            cat_score.get("weight", 0) 
            for cat_score in category_scores.values()
        )
        
        # Calculate weighted average
        if weights_sum > 0:
            overall_score = weighted_sum / weights_sum
        else:
            overall_score = 0
            
        return round(overall_score, 1)
    
    def _apply_overall_adjustments(self, overall_raw: float, 
                                 analysis_results: Dict[str, Any]) -> float:
        """
        Apply overall adjustments to raw score.
        
        Args:
            overall_raw: Overall raw score
            analysis_results: Analysis results from all agents
            
        Returns:
            Adjusted overall score
        """
        # Start with raw score
        adjusted = overall_raw
        
        # Apply adjustments based on critical factors
        
        # Check for red flags in risk analysis
        if "RiskMitigation" in analysis_results:
            risk_score = analysis_results["RiskMitigation"].get("category_average", 0)
            if risk_score <= 3:  # Serious risks identified
                adjusted -= 1.0  # Substantial penalty
            elif risk_score <= 5:  # Moderate risks
                adjusted -= 0.5  # Moderate penalty
        
        # Check for strong product-market fit
        if "ProductMarketFit" in analysis_results:
            pmf_score = analysis_results["ProductMarketFit"].get("category_average", 0)
            if pmf_score >= 9:  # Exceptional PMF
                adjusted += 0.5  # Bonus
        
        # Check for strong market opportunity
        if "MarketAnalysis" in analysis_results:
            market_score = analysis_results["MarketAnalysis"].get("category_average", 0)
            if market_score >= 9:  # Exceptional market
                adjusted += 0.5  # Bonus
        
        # Keep within bounds
        adjusted = max(1.0, min(10.0, adjusted))
        
        return round(adjusted, 1)
    
    def _generate_explanations(self, category_scores: Dict[str, Dict[str, Any]], 
                             overall_score: float) -> List[str]:
        """
        Generate explanations for the scores.
        
        Args:
            category_scores: Dictionary of category scores
            overall_score: Overall adjusted score
            
        Returns:
            List of explanation strings
        """
        explanations = []
        
        # Overall score explanation
        if overall_score >= self.SCORE_THRESHOLDS["excellent"]:
            explanations.append("Overall score indicates an excellent investment opportunity with strong fundamentals.")
        elif overall_score >= self.SCORE_THRESHOLDS["good"]:
            explanations.append("Overall score indicates a good investment opportunity with solid potential but some areas for improvement.")
        elif overall_score >= self.SCORE_THRESHOLDS["average"]:
            explanations.append("Overall score indicates an average investment opportunity with both strengths and weaknesses.")
        elif overall_score >= self.SCORE_THRESHOLDS["below_average"]:
            explanations.append("Overall score indicates a below-average investment opportunity with significant concerns.")
        else:
            explanations.append("Overall score indicates a poor investment opportunity with major issues that need addressing.")
        
        # Add category-specific explanations
        for category, score_data in category_scores.items():
            adjusted_score = score_data.get("adjusted_score", 0)
            
            if adjusted_score >= 9:
                explanations.append(f"{category} is exceptionally strong, presenting a compelling advantage.")
            elif adjusted_score >= 8:
                explanations.append(f"{category} is very strong, contributing significantly to overall potential.")
            elif adjusted_score <= 3:
                explanations.append(f"{category} is critically weak, posing a significant risk to success.")
            elif adjusted_score <= 5 and score_data.get("weight", 0) >= 0.2:
                explanations.append(f"{category} shows concerning weaknesses in a high-impact area.")
        
        return explanations
    
    def _generate_investment_recommendation(self, overall_score: float) -> Dict[str, Any]:
        """
        Generate investment recommendation based on overall score.
        
        Args:
            overall_score: Overall adjusted score
            
        Returns:
            Investment recommendation data
        """
        if overall_score >= self.SCORE_THRESHOLDS["excellent"]:
            return {
                "recommendation": "Strong Buy",
                "conviction": "High",
                "rationale": "Exceptional opportunity with strong fundamentals across key categories.",
                "timeline": "Immediate action recommended."
            }
        elif overall_score >= self.SCORE_THRESHOLDS["good"]:
            return {
                "recommendation": "Buy",
                "conviction": "Medium",
                "rationale": "Solid opportunity with good fundamentals and manageable risks.",
                "timeline": "Near-term action recommended."
            }
        elif overall_score >= self.SCORE_THRESHOLDS["average"]:
            return {
                "recommendation": "Hold/Watch",
                "conviction": "Low",
                "rationale": "Average opportunity with mixed signals. Some strengths but also notable weaknesses.",
                "timeline": "Monitor for improvements before committing."
            }
        elif overall_score >= self.SCORE_THRESHOLDS["below_average"]:
            return {
                "recommendation": "Weak Pass",
                "conviction": "Medium",
                "rationale": "Below-average opportunity with significant concerns in key areas.",
                "timeline": "Pass for now, but consider revisiting if major improvements occur."
            }
        else:
            return {
                "recommendation": "Strong Pass",
                "conviction": "High",
                "rationale": "Poor opportunity with major issues across multiple critical categories.",
                "timeline": "Do not pursue."
            }
    
    def _calculate_confidence(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate confidence in the scoring.
        
        Args:
            analysis_results: Analysis results from all agents
            
        Returns:
            Confidence assessment
        """
        # Collect confidence scores from each analysis section
        confidence_scores = []
        data_completeness = 0
        total_fields = 0
        
        for category, category_data in analysis_results.items():
            # Check if the category has a category_metadata field
            if "category_metadata" in category_data:
                # Get reliability score if available
                reliability = category_data["category_metadata"].get("data_reliability_score", 0.5)
                confidence_scores.append(reliability)
                
            # Count data completeness
            for key, value in category_data.items():
                if isinstance(value, dict) and "validated" in value:
                    total_fields += 1
                    if value.get("validated"):
                        data_completeness += 1
        
        # Calculate average confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        # Calculate data completeness percentage
        completeness_pct = (data_completeness / total_fields * 100) if total_fields > 0 else 0
        
        # Determine overall confidence level
        if avg_confidence >= 0.8 and completeness_pct >= 80:
            confidence_level = "High"
        elif avg_confidence >= 0.6 and completeness_pct >= 60:
            confidence_level = "Medium"
        else:
            confidence_level = "Low"
        
        return {
            "level": confidence_level,
            "score": round(avg_confidence, 2),
            "completeness": f"{round(completeness_pct)}%",
            "factors": [
                "Data quality and completeness",
                "Source reliability",
                "Consistency across analyses"
            ]
        }
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and calculate scores.
        
        Args:
            data: Dictionary containing analysis results and research results
            
        Returns:
            Scoring results
        """
        analysis_results = data.get("analysis", {})
        research_results = data.get("research", {})
        
        return await self.score(analysis_results, research_results)