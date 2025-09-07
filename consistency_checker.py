"""
Consistency & Math Checker Agent.

This module checks for consistency and mathematical errors in analysis results.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
import math

from agents import BaseAgent

logger = logging.getLogger(__name__)

class ConsistencyChecker(BaseAgent):
    """
    Agent for checking consistency and mathematical correctness of analysis results.
    
    This agent validates:
    - Units and currency consistency
    - Mathematical calculations (CAGR, TAM/SAM/SOM hierarchy, etc.)
    - Internal consistency across different analysis sections
    """
    
    async def check(self, normalized_data: Dict[str, Any], analysis_results: Dict[str, Any],
                  scores: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Check consistency and mathematical correctness of analysis results.
        
        Args:
            normalized_data: Normalized pitch data
            analysis_results: Analysis results from all agents
            scores: Scoring results (optional)
            
        Returns:
            Consistency check results
        """
        logger.info("Starting consistency and mathematical check")
        
        # Initialize issues and fixes lists
        issues = []
        fixes = []
        
        # Check currency consistency
        currency_issues, currency_fixes = self._check_currency_consistency(normalized_data, analysis_results)
        issues.extend(currency_issues)
        fixes.extend(currency_fixes)
        
        # Check market size hierarchy (TAM > SAM > SOM)
        market_issues, market_fixes = self._check_market_size_hierarchy(normalized_data, analysis_results)
        issues.extend(market_issues)
        fixes.extend(market_fixes)
        
        # Check CAGR calculations
        cagr_issues, cagr_fixes = self._check_cagr_calculations(normalized_data, analysis_results)
        issues.extend(cagr_issues)
        fixes.extend(cagr_fixes)
        
        # Check LTV/CAC ratio
        ltvcac_issues, ltvcac_fixes = self._check_ltvcac_ratio(normalized_data, analysis_results)
        issues.extend(ltvcac_issues)
        fixes.extend(ltvcac_fixes)
        
        # Check for scoring consistency
        if scores:
            score_issues, score_fixes = self._check_scoring_consistency(analysis_results, scores)
            issues.extend(score_issues)
            fixes.extend(score_fixes)
        
        # Compile results
        results = {
            "issues": issues,
            "fixes": fixes,
            "consistency_score": self._calculate_consistency_score(issues),
            "checked_at": asyncio.get_event_loop().time(),
            "checked_fields": self._get_checked_fields_count(normalized_data, analysis_results)
        }
        
        logger.debug(f"Consistency check completed: {len(issues)} issues found")
        return results
    
    def _check_currency_consistency(self, normalized_data: Dict[str, Any], 
                                  analysis_results: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Check for currency consistency across the analysis.
        
        Args:
            normalized_data: Normalized pitch data
            analysis_results: Analysis results from all agents
            
        Returns:
            Tuple of (issues, fixes)
        """
        issues = []
        fixes = []
        
        # Get base currency from normalized data
        base_currency = normalized_data.get("units", {}).get("base_currency", "USD")
        
        # Check market analysis section
        if "MarketAnalysis" in analysis_results:
            market_analysis = analysis_results["MarketAnalysis"]
            
            # Check TAM, SAM, SOM currency units
            for metric in ["tam", "sam", "som"]:
                if metric in market_analysis:
                    metric_data = market_analysis[metric]
                    unit = metric_data.get("unit")
                    
                    if unit and unit != base_currency:
                        issues.append({
                            "section": "MarketAnalysis",
                            "field": metric,
                            "issue": f"Currency mismatch: {metric} uses {unit} instead of {base_currency}",
                            "severity": "medium"
                        })
                        
                        fixes.append({
                            "section": "MarketAnalysis",
                            "field": metric + ".unit",
                            "current": unit,
                            "corrected": base_currency
                        })
        
        # Check finance analysis section
        if "Finance" in analysis_results:
            finance_analysis = analysis_results["Finance"]
            
            # Check currency units for financial metrics
            for metric in ["gross_margin", "ebitda", "valuation", "ask"]:
                if metric in finance_analysis:
                    metric_data = finance_analysis[metric]
                    unit = metric_data.get("unit")
                    
                    if unit and unit != base_currency and unit != "Percent" and unit != "Ratio":
                        issues.append({
                            "section": "Finance",
                            "field": metric,
                            "issue": f"Currency mismatch: {metric} uses {unit} instead of {base_currency}",
                            "severity": "medium"
                        })
                        
                        fixes.append({
                            "section": "Finance",
                            "field": metric + ".unit",
                            "current": unit,
                            "corrected": base_currency
                        })
        
        return issues, fixes
    
    def _check_market_size_hierarchy(self, normalized_data: Dict[str, Any], 
                                   analysis_results: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Check market size hierarchy (TAM > SAM > SOM).
        
        Args:
            normalized_data: Normalized pitch data
            analysis_results: Analysis results from all agents
            
        Returns:
            Tuple of (issues, fixes)
        """
        issues = []
        fixes = []
        
        # Check if MarketAnalysis section exists
        if "MarketAnalysis" not in analysis_results:
            return issues, fixes
            
        market_analysis = analysis_results["MarketAnalysis"]
        
        # Extract TAM, SAM, SOM values
        tam_value = None
        sam_value = None
        som_value = None
        
        # Try to extract numerical values from validated fields
        for metric, data in [("tam", None), ("sam", None), ("som", None)]:
            if metric in market_analysis:
                metric_data = market_analysis[metric]
                validated = metric_data.get("validated")
                
                if validated and isinstance(validated, str):
                    # Try to extract numerical value from string (e.g., "$50B")
                    try:
                        # Remove currency symbol and convert to float
                        clean_value = validated.replace("$", "").replace(",", "")
                        
                        # Handle suffixes like B, M, K
                        multiplier = 1
                        if clean_value.endswith("B"):
                            multiplier = 1_000_000_000
                            clean_value = clean_value[:-1]
                        elif clean_value.endswith("M"):
                            multiplier = 1_000_000
                            clean_value = clean_value[:-1]
                        elif clean_value.endswith("K"):
                            multiplier = 1_000
                            clean_value = clean_value[:-1]
                            
                        value = float(clean_value) * multiplier
                        
                        if metric == "tam":
                            tam_value = value
                        elif metric == "sam":
                            sam_value = value
                        elif metric == "som":
                            som_value = value
                    except (ValueError, TypeError):
                        # If conversion fails, skip this check
                        pass
        
        # Check hierarchy: TAM > SAM > SOM
        if tam_value is not None and sam_value is not None and tam_value <= sam_value:
            issues.append({
                "section": "MarketAnalysis",
                "field": "tam_sam_hierarchy",
                "issue": f"Market size hierarchy violation: TAM (${tam_value:,.0f}) <= SAM (${sam_value:,.0f})",
                "severity": "high"
            })
            
            # Propose a fix (adjust SAM to be 25% of TAM if TAM is valid)
            if tam_value > 0:
                corrected_sam = tam_value * 0.25
                fixes.append({
                    "section": "MarketAnalysis",
                    "field": "sam.validated",
                    "current": market_analysis["sam"].get("validated"),
                    "corrected": f"${corrected_sam:,.0f}",
                    "note": "Adjusted SAM to 25% of TAM to maintain proper hierarchy"
                })
        
        if sam_value is not None and som_value is not None and sam_value <= som_value:
            issues.append({
                "section": "MarketAnalysis",
                "field": "sam_som_hierarchy",
                "issue": f"Market size hierarchy violation: SAM (${sam_value:,.0f}) <= SOM (${som_value:,.0f})",
                "severity": "high"
            })
            
            # Propose a fix (adjust SOM to be 25% of SAM if SAM is valid)
            if sam_value > 0:
                corrected_som = sam_value * 0.25
                fixes.append({
                    "section": "MarketAnalysis",
                    "field": "som.validated",
                    "current": market_analysis["som"].get("validated"),
                    "corrected": f"${corrected_som:,.0f}",
                    "note": "Adjusted SOM to 25% of SAM to maintain proper hierarchy"
                })
        
        return issues, fixes
    
    def _check_cagr_calculations(self, normalized_data: Dict[str, Any], 
                              analysis_results: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Check CAGR calculations for consistency with revenue data.
        
        Args:
            normalized_data: Normalized pitch data
            analysis_results: Analysis results from all agents
            
        Returns:
            Tuple of (issues, fixes)
        """
        issues = []
        fixes = []
        
        # Get historical revenues
        revenues = normalized_data.get("finance", {}).get("revenues", [])
        
        # Check if we have enough revenue data points (at least 2)
        if len(revenues) < 2:
            return issues, fixes
            
        # Try to extract years from period strings and sort chronologically
        try:
            # Extract year from period (assuming format like "2019-20" or "2019")
            dated_revenues = []
            for revenue in revenues:
                period = revenue.get("period") or ""
                value = revenue.get("value")
                
                # Skip if value is missing
                if value is None:
                    continue
                    
                # Try to extract year
                year = None
                if period and "-" in period:
                    # Format like "2019-20"
                    year_str = period.split("-")[0]
                    if year_str.isdigit():
                        year = int(year_str)
                elif period and period.isdigit() and len(period) == 4:
                    # Format like "2019"
                    year = int(period)
                
                if year:
                    dated_revenues.append({"year": year, "value": value})
            
            # Sort by year
            dated_revenues.sort(key=lambda x: x["year"])
            
            # Need at least 2 dated revenue points
            if len(dated_revenues) >= 2:
                # Calculate CAGR
                start_revenue = dated_revenues[0]["value"]
                end_revenue = dated_revenues[-1]["value"]
                years = dated_revenues[-1]["year"] - dated_revenues[0]["year"]
                
                if start_revenue <= 0 or years <= 0:
                    # Cannot calculate CAGR with these values
                    return issues, fixes
                
                # Calculate CAGR: (end_revenue / start_revenue)^(1/years) - 1
                calculated_cagr = (end_revenue / start_revenue) ** (1/years) - 1
                calculated_cagr_pct = calculated_cagr * 100
                
                # Get claimed CAGR from market analysis
                claimed_cagr = None
                if "MarketAnalysis" in analysis_results and "cagr" in analysis_results["MarketAnalysis"]:
                    cagr_data = analysis_results["MarketAnalysis"]["cagr"]
                    claimed_str = cagr_data.get("claimed", "")
                    
                    # Try to extract numerical value
                    if claimed_str and isinstance(claimed_str, str):
                        try:
                            claimed_cagr = float(claimed_str.replace("%", ""))
                        except (ValueError, TypeError):
                            pass
                
                # If we have claimed CAGR, compare with calculated CAGR
                if claimed_cagr is not None:
                    # Allow 5% difference
                    tolerance = 5.0
                    if abs(claimed_cagr - calculated_cagr_pct) > tolerance:
                        issues.append({
                            "section": "MarketAnalysis",
                            "field": "cagr",
                            "issue": f"CAGR inconsistency: claimed {claimed_cagr:.1f}%, calculated {calculated_cagr_pct:.1f}%",
                            "severity": "medium"
                        })
                        
                        fixes.append({
                            "section": "MarketAnalysis",
                            "field": "cagr.validated",
                            "current": cagr_data.get("validated"),
                            "corrected": f"{calculated_cagr_pct:.1f}%",
                            "note": "Adjusted CAGR to match historical revenue growth"
                        })
        
        except Exception as e:
            logger.warning(f"Error checking CAGR calculations: {e}")
        
        return issues, fixes
    
    def _check_ltvcac_ratio(self, normalized_data: Dict[str, Any], 
                         analysis_results: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Check LTV/CAC ratio calculations.
        
        Args:
            normalized_data: Normalized pitch data
            analysis_results: Analysis results from all agents
            
        Returns:
            Tuple of (issues, fixes)
        """
        issues = []
        fixes = []
        
        # Check if ProductMarketFit section exists with ltv_cac metric
        if "ProductMarketFit" not in analysis_results or "ltv_cac" not in analysis_results["ProductMarketFit"]:
            return issues, fixes
            
        ltv_cac_data = analysis_results["ProductMarketFit"]["ltv_cac"]
        
        # Extract claimed ratio
        claimed_ratio = ltv_cac_data.get("claimed")
        if not claimed_ratio:
            return issues, fixes
            
        # Try to parse ratio (e.g., "7:1" or "7")
        try:
            if isinstance(claimed_ratio, str) and ":" in claimed_ratio:
                numerator = float(claimed_ratio.split(":")[0])
                denominator = float(claimed_ratio.split(":")[1])
                ratio = numerator / denominator if denominator else None
            else:
                ratio = float(claimed_ratio)
                
            # Check if ratio is reasonable (typical range is 3:1 to 5:1)
            if ratio and ratio > 10:
                issues.append({
                    "section": "ProductMarketFit",
                    "field": "ltv_cac",
                    "issue": f"LTV/CAC ratio is unusually high: {claimed_ratio} (typical range is 3:1 to 5:1)",
                    "severity": "low"
                })
                
                # Suggest a more reasonable ratio
                corrected_ratio = "3:1"
                fixes.append({
                    "section": "ProductMarketFit",
                    "field": "ltv_cac.validated",
                    "current": ltv_cac_data.get("validated"),
                    "corrected": corrected_ratio,
                    "note": "Adjusted LTV/CAC ratio to more reasonable industry benchmark"
                })
        except (ValueError, TypeError, ZeroDivisionError):
            # If parsing fails, skip this check
            pass
        
        return issues, fixes
    
    def _check_scoring_consistency(self, analysis_results: Dict[str, Any], 
                                scores: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Check consistency between analysis scores and overall score.
        
        Args:
            analysis_results: Analysis results from all agents
            scores: Scoring results
            
        Returns:
            Tuple of (issues, fixes)
        """
        issues = []
        fixes = []
        
        # Check if category_scores exists in scores
        if "category_scores" not in scores:
            return issues, fixes
            
        category_scores = scores["category_scores"]
        
        # Check each category's score
        for category, category_data in analysis_results.items():
            if category in category_scores and "category_average" in category_data:
                analysis_score = category_data["category_average"]
                scoring_raw = category_scores[category].get("raw_score")
                
                # Check if scores are consistent (allow 1-point difference)
                if scoring_raw is not None and abs(analysis_score - scoring_raw) > 1:
                    issues.append({
                        "section": "Scoring",
                        "field": f"{category}.raw_score",
                        "issue": f"Score inconsistency: analysis {analysis_score}, scoring {scoring_raw}",
                        "severity": "medium"
                    })
                    
                    fixes.append({
                        "section": "Scoring",
                        "field": f"category_scores.{category}.raw_score",
                        "current": scoring_raw,
                        "corrected": analysis_score,
                        "note": f"Adjusted scoring to match analysis score for {category}"
                    })
        
        return issues, fixes
    
    def _calculate_consistency_score(self, issues: List[Dict[str, Any]]) -> float:
        """
        Calculate overall consistency score based on issues.
        
        Args:
            issues: List of identified issues
            
        Returns:
            Consistency score (0-10)
        """
        # Start with perfect score
        score = 10.0
        
        # Count issues by severity
        high_count = sum(1 for issue in issues if issue.get("severity") == "high")
        medium_count = sum(1 for issue in issues if issue.get("severity") == "medium")
        low_count = sum(1 for issue in issues if issue.get("severity") == "low")
        
        # Deduct points based on severity
        score -= high_count * 2.0  # -2 points per high severity issue
        score -= medium_count * 1.0  # -1 point per medium severity issue
        score -= low_count * 0.5  # -0.5 points per low severity issue
        
        # Ensure score is within range
        return max(1.0, min(10.0, score))
    
    def _get_checked_fields_count(self, normalized_data: Dict[str, Any], 
                                analysis_results: Dict[str, Any]) -> int:
        """
        Count the number of fields checked for consistency.
        
        Args:
            normalized_data: Normalized pitch data
            analysis_results: Analysis results from all agents
            
        Returns:
            Number of fields checked
        """
        # Count fields in market analysis
        market_fields = 0
        if "MarketAnalysis" in analysis_results:
            market_analysis = analysis_results["MarketAnalysis"]
            market_fields += sum(1 for metric in ["tam", "sam", "som", "cagr"] if metric in market_analysis)
        
        # Count fields in finance analysis
        finance_fields = 0
        if "Finance" in analysis_results:
            finance_analysis = analysis_results["Finance"]
            finance_fields += sum(1 for metric in ["gross_margin", "ebitda", "valuation", "ask"] if metric in finance_analysis)
        
        # Count fields in product-market fit analysis
        pmf_fields = 0
        if "ProductMarketFit" in analysis_results:
            pmf_analysis = analysis_results["ProductMarketFit"]
            pmf_fields += sum(1 for metric in ["ltv_cac", "retention"] if metric in pmf_analysis)
        
        # Count revenue data points
        revenue_fields = len(normalized_data.get("finance", {}).get("revenues", []))
        
        return market_fields + finance_fields + pmf_fields + revenue_fields
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and check for consistency.
        
        Args:
            data: Dictionary containing normalized data, analysis results, and scores
            
        Returns:
            Consistency check results
        """
        normalized_data = data.get("normalized_data", {})
        analysis_results = data.get("analysis", {})
        scores = data.get("scores", {})
        
        return await self.check(normalized_data, analysis_results, scores)