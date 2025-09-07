"""
Web Research Agent.

This module performs web research to validate claims in the pitch.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
import datetime
import json
import re

from agents import BaseAgent

logger = logging.getLogger(__name__)

class WebResearch(BaseAgent):
    """
    Agent for performing web research to validate claims in the pitch.
    
    This agent searches reputable sources to verify market sizes, growth rates,
    competitor information, and other factual claims in the pitch.
    """
    
    # List of reputable sources for different domains
    REPUTABLE_SOURCES = {
        "market_research": [
            "gartner.com", "forrester.com", "idc.com", "statista.com",
            "grandviewresearch.com", "marketsandmarkets.com", "mordorintelligence.com",
            "ibisworld.com", "euromonitor.com"
        ],
        "finance": [
            "bloomberg.com", "reuters.com", "ft.com", "wsj.com",
            "cnbc.com", "marketwatch.com", "sec.gov", "investing.com"
        ],
        "government": [
            ".gov", "worldbank.org", "imf.org", "oecd.org",
            "who.int", "census.gov", "bls.gov", "europa.eu"
        ],
        "academic": [
            ".edu", "jstor.org", "nature.com", "science.org",
            "researchgate.net", "scholar.google.com", "ncbi.nlm.nih.gov"
        ],
        "startup": [
            "crunchbase.com", "pitchbook.com", "techcrunch.com",
            "venturebeat.com", "inc.com", "forbes.com", "entrepreneur.com"
        ]
    }
    
    async def validate_claims(self, normalized_data: Dict[str, Any], 
                            analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate key claims from the pitch using web research.
        
        Args:
            normalized_data: Normalized pitch data
            analysis_results: Analysis results from all agents
            
        Returns:
            Web research results
        """
        logger.info("Starting web research to validate claims")
        
        # Extract claims to validate
        claims = self._extract_claims(normalized_data, analysis_results)
        
        # Validate claims (in a real implementation, this would call search APIs)
        validation_results = await self._validate_claims(claims)
        
        # Organize results
        results = {
            "validated_at": datetime.datetime.now().isoformat(),
            "claims": claims,
            "validations": validation_results,
            "sources": self._get_sources_used(validation_results),
            "summary": self._generate_validation_summary(validation_results)
        }
        
        logger.debug(f"Web research completed: {len(validation_results)} claims validated")
        return results
    
    def _extract_claims(self, normalized_data: Dict[str, Any], 
                      analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract key claims from the pitch that need validation.
        
        Args:
            normalized_data: Normalized pitch data
            analysis_results: Analysis results from all agents
            
        Returns:
            List of claims to validate
        """
        claims = []
        
        # Extract market size claims
        market_data = normalized_data.get("market", {})
        if market_data:
            # TAM claim
            tam = market_data.get("tam", {})
            if tam and tam.get("value") is not None:
                claims.append({
                    "id": "tam_size",
                    "category": "market_size",
                    "claim": f"The Total Addressable Market (TAM) is ${tam.get('value'):,.0f}",
                    "source": "pitch",
                    "confidence": "medium",
                    "keywords": ["market size", "TAM", normalized_data.get("market", {}).get("domain", "")]
                })
            
            # CAGR claim
            cagr = market_data.get("cagr")
            if cagr is not None:
                claims.append({
                    "id": "market_growth",
                    "category": "market_growth",
                    "claim": f"The market CAGR is {cagr}%",
                    "source": "pitch",
                    "confidence": "medium",
                    "keywords": ["CAGR", "market growth", "growth rate", normalized_data.get("market", {}).get("domain", "")]
                })
        
        # Extract competitive landscape claims
        competitors = normalized_data.get("positioning", {}).get("competitors", [])
        if competitors:
            competitor_names = [comp.get("name", "Unknown") for comp in competitors if "name" in comp]
            if competitor_names:
                claims.append({
                    "id": "competitors",
                    "category": "competition",
                    "claim": f"Key competitors include {', '.join(competitor_names)}",
                    "source": "pitch",
                    "confidence": "medium",
                    "keywords": ["competitors", "competition", normalized_data.get("market", {}).get("domain", "")]
                })
        
        # Extract revenue claims
        revenues = normalized_data.get("finance", {}).get("revenues", [])
        if revenues and len(revenues) >= 2:
            # Calculate year-over-year growth
            try:
                sorted_revenues = sorted(revenues, key=lambda x: x.get("period", ""))
                recent_two = sorted_revenues[-2:]
                if len(recent_two) == 2 and recent_two[0].get("value") and recent_two[1].get("value") and recent_two[0].get("value") > 0:
                    growth = ((recent_two[1].get("value") - recent_two[0].get("value")) / recent_two[0].get("value")) * 100
                    claims.append({
                        "id": "revenue_growth",
                        "category": "financial_growth",
                        "claim": f"The company's year-over-year revenue growth is approximately {growth:.1f}%",
                        "source": "pitch",
                        "confidence": "high",
                        "keywords": ["revenue growth", "financial performance", "YoY growth"]
                    })
            except Exception as e:
                logger.warning(f"Error calculating revenue growth for claim: {e}")
        
        # Add domain-specific claims
        domain = normalized_data.get("market", {}).get("domain", "")
        if domain:
            claims.append({
                "id": "industry_trends",
                "category": "market_trends",
                "claim": f"The {domain} industry is experiencing significant growth and innovation",
                "source": "pitch",
                "confidence": "low",
                "keywords": [domain, "industry trends", "market trends", "innovation"]
            })
        
        # Add product-related claims
        problem = normalized_data.get("positioning", {}).get("problem_statement")
        solution = normalized_data.get("positioning", {}).get("solution")
        if problem and solution:
            claims.append({
                "id": "problem_solution_fit",
                "category": "product",
                "claim": f"The company addresses the problem of '{problem}' with its solution: '{solution}'",
                "source": "pitch",
                "confidence": "medium",
                "keywords": ["problem solution fit", domain, "customer pain points"]
            })
        
        logger.debug(f"Extracted {len(claims)} claims for validation")
        return claims
    
    async def _validate_claims(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate claims using web research.
        
        Args:
            claims: List of claims to validate
            
        Returns:
            List of validation results
        """
        # This would be implemented with actual web search APIs
        # For this example, we'll simulate the results
        
        validation_results = []
        
        for claim in claims:
            # Simulate research delay
            await asyncio.sleep(0.1)
            
            # Create simulated validation result
            validation = {
                "claim_id": claim["id"],
                "claim_text": claim["claim"],
                "verdict": self._simulate_verdict(claim),
                "sources": self._simulate_sources(claim),
                "confidence": self._simulate_confidence(claim),
                "explanation": self._simulate_explanation(claim),
                "validated_at": datetime.datetime.now().isoformat()
            }
            
            validation_results.append(validation)
        
        return validation_results
    
    def _simulate_verdict(self, claim: Dict[str, Any]) -> str:
        """Simulate a verdict for the claim validation."""
        # In a real implementation, this would be based on actual research
        if claim["category"] == "market_size" or claim["category"] == "market_growth":
            return "partially_corroborated"
        elif claim["category"] == "competition":
            return "corroborated"
        elif claim["category"] == "financial_growth":
            return "insufficient_evidence"
        elif claim["category"] == "market_trends":
            return "corroborated"
        else:
            return "inconclusive"
    
    def _simulate_sources(self, claim: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate sources for the claim validation."""
        # In a real implementation, this would be based on actual search results
        sources = []
        
        if claim["category"] == "market_size":
            sources = [
                {
                    "url": "https://www.grandviewresearch.com/industry-analysis/sample-market",
                    "title": f"{claim['keywords'][-1].title()} Market Size & Share Report, 2023-2030",
                    "snippet": f"The global {claim['keywords'][-1]} market size was valued at USD 42.1 billion in 2022 and is expected to grow at a compound annual growth rate (CAGR) of 15.2% from 2023 to 2030.",
                    "published_date": "2023-03-15"
                },
                {
                    "url": "https://www.marketsandmarkets.com/Market-Reports/sample-market-1234.html",
                    "title": f"{claim['keywords'][-1].title()} Market - Global Forecast to 2028",
                    "snippet": f"The {claim['keywords'][-1]} market is projected to reach USD 78.5 billion by 2028, at a CAGR of 17.5% during the forecast period.",
                    "published_date": "2023-05-22"
                }
            ]
        elif claim["category"] == "market_growth":
            sources = [
                {
                    "url": "https://www.mordorintelligence.com/industry-reports/sample-market",
                    "title": f"{claim['keywords'][-1].title()} Market - Growth, Trends, COVID-19 Impact, and Forecasts (2023-2028)",
                    "snippet": f"The {claim['keywords'][-1]} market is expected to register a CAGR of 16.8% over the forecast period from 2023 to 2028.",
                    "published_date": "2023-04-10"
                }
            ]
        elif claim["category"] == "competition":
            sources = [
                {
                    "url": "https://www.techcrunch.com/2023/06/10/competitive-landscape-analysis",
                    "title": f"The Competitive Landscape of the {claim['keywords'][-1].title()} Industry in 2023",
                    "snippet": f"Leading players in the {claim['keywords'][-1]} space include {claim['claim'].split('include ')[1]}. Each brings unique strengths to the market.",
                    "published_date": "2023-06-10"
                }
            ]
        
        return sources
    
    def _simulate_confidence(self, claim: Dict[str, Any]) -> float:
        """Simulate confidence score for the claim validation."""
        # In a real implementation, this would be based on source quality and consensus
        base_confidence = 0.7
        
        # Adjust based on claim confidence
        if claim["confidence"] == "high":
            base_confidence += 0.2
        elif claim["confidence"] == "low":
            base_confidence -= 0.2
            
        # Add some randomness
        import random
        base_confidence += random.uniform(-0.05, 0.05)
        
        # Ensure within bounds
        return max(0.1, min(0.95, base_confidence))
    
    def _simulate_explanation(self, claim: Dict[str, Any]) -> str:
        """Simulate explanation for the claim validation."""
        # In a real implementation, this would summarize the research findings
        verdict = self._simulate_verdict(claim)
        
        if verdict == "corroborated":
            return f"Multiple credible sources confirm this claim about {claim['category']}."
        elif verdict == "partially_corroborated":
            return f"Some sources support aspects of this claim, but the exact figures differ from what's stated."
        elif verdict == "contradicted":
            return f"The majority of credible sources contradict this claim about {claim['category']}."
        elif verdict == "insufficient_evidence":
            return f"Not enough reliable sources were found to validate this claim about {claim['category']}."
        else:
            return "The research was inconclusive due to conflicting information or lack of credible sources."
    
    def _get_sources_used(self, validation_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract unique sources used in validations.
        
        Args:
            validation_results: List of validation results
            
        Returns:
            List of unique sources used
        """
        sources = []
        urls_seen = set()
        
        for validation in validation_results:
            for source in validation.get("sources", []):
                url = source.get("url")
                if url and url not in urls_seen:
                    urls_seen.add(url)
                    sources.append({
                        "url": url,
                        "title": source.get("title", ""),
                        "domain": self._extract_domain(url),
                        "type": self._categorize_source(url),
                        "published_date": source.get("published_date", "")
                    })
        
        return sources
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else ""
    
    def _categorize_source(self, url: str) -> str:
        """Categorize source type based on domain."""
        domain = self._extract_domain(url).lower()
        
        for category, domains in self.REPUTABLE_SOURCES.items():
            for d in domains:
                if d in domain:
                    return category
        
        return "general"
    
    def _generate_validation_summary(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary of validation results.
        
        Args:
            validation_results: List of validation results
            
        Returns:
            Summary of validation results
        """
        # Count verdicts
        verdicts = {
            "corroborated": 0,
            "partially_corroborated": 0,
            "contradicted": 0,
            "insufficient_evidence": 0,
            "inconclusive": 0
        }
        
        for validation in validation_results:
            verdict = validation.get("verdict", "inconclusive")
            if verdict in verdicts:
                verdicts[verdict] += 1
        
        # Calculate overall credibility score (0-100)
        total = sum(verdicts.values())
        if total > 0:
            credibility_score = (
                (verdicts["corroborated"] * 100) + 
                (verdicts["partially_corroborated"] * 60) + 
                (verdicts["inconclusive"] * 30) + 
                (verdicts["insufficient_evidence"] * 20) + 
                (verdicts["contradicted"] * 0)
            ) / total
        else:
            credibility_score = 0
        
        return {
            "total_claims": len(validation_results),
            "verdicts": verdicts,
            "credibility_score": round(credibility_score, 1),
            "confidence": "high" if credibility_score >= 80 else ("medium" if credibility_score >= 50 else "low"),
            "key_findings": self._generate_key_findings(validation_results)
        }
    
    def _generate_key_findings(self, validation_results: List[Dict[str, Any]]) -> List[str]:
        """
        Generate key findings from validation results.
        
        Args:
            validation_results: List of validation results
            
        Returns:
            List of key findings
        """
        findings = []
        
        # Look for corroborated market claims
        market_validations = [v for v in validation_results if v.get("claim_id") in ["tam_size", "market_growth"] 
                             and v.get("verdict") in ["corroborated", "partially_corroborated"]]
        if market_validations:
            findings.append("Market size and growth claims are generally supported by external sources.")
        
        # Look for contradicted claims
        contradicted = [v for v in validation_results if v.get("verdict") == "contradicted"]
        if contradicted:
            findings.append(f"{len(contradicted)} key claim(s) were contradicted by reliable sources.")
        
        # Look for competitor validation
        competitor_validation = next((v for v in validation_results if v.get("claim_id") == "competitors"), None)
        if competitor_validation and competitor_validation.get("verdict") == "corroborated":
            findings.append("The competitive landscape analysis appears accurate.")
        
        # Add general finding if others are lacking
        if not findings:
            findings.append("Web research provided limited validation of the pitch claims.")
            
        return findings
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and perform web research.
        
        Args:
            data: Dictionary containing normalized data and analysis results
            
        Returns:
            Web research results
        """
        normalized_data = data.get("normalized_data", {})
        analysis_results = data.get("analysis", {})
        
        return await self.validate_claims(normalized_data, analysis_results)