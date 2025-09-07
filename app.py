# app.py
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import os
import json
import logging
import datetime
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load configuration
def load_config():
    config = {}
    config_path = os.environ.get('CONFIG_PATH', 'config.yaml')
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
    return config

config = load_config()

# Set up MongoDB connection
def get_mongo_client():
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        logger.error("MongoDB URI not configured")
        raise ValueError("MongoDB URI not configured")
    return MongoClient(mongo_uri)

def get_mongo_collection():
    client = get_mongo_client()
    db_name = os.environ.get('MONGO_DB', 'pitchfynd-dev')
    collection_name = os.environ.get('MONGO_COLLECTION', 'pitches')
    return client[db_name][collection_name]

# Simple analysis function
def analyze_pitch_data(pitch_data):
    """Analyze pitch data and return results."""
    # Extract relevant data
    extraction = pitch_data.get("extraction", {})
    
    # Get basic details
    company_name = "Unknown Company"
    domain = extraction.get("domain", "Technology")
    
    # Try to get company name from various fields
    if "company_name" in extraction and extraction["company_name"]:
        company_name = extraction["company_name"]
    elif "tagline" in extraction and extraction["tagline"]:
        words = extraction["tagline"].split()
        if len(words) >= 2:
            company_name = " ".join(words[:2])
    
    # Get financial metrics
    tam = extraction.get("tam", {}).get("value")
    sam = extraction.get("sam", {}).get("value")
    som = extraction.get("som", {}).get("value")
    cagr = extraction.get("cagr")
    arr = extraction.get("arr", {}).get("value")
    
    # Get founders
    founders = extraction.get("founders", [])
    ceo = "Management Team"
    if founders and len(founders) > 0:
        for founder in founders:
            if "CEO" in founder.get("title", ""):
                ceo = founder.get("name")
                break
        if ceo == "Management Team" and founders[0].get("name"):
            ceo = founders[0].get("name")
    
    # Generate analysis result
    result = {
        "pitchId": str(pitch_data.get("_id", "")),
        "clientId": pitch_data.get("clientId", ""),
        "metadata": {
            "generated_at": datetime.datetime.now().isoformat(),
            "analysis_version": "1.0",
            "data_sources_used": 0,
            "total_validation_points": 0,
            "processing_time_estimate": "1-2 minutes"
        },
        "validation_summary": {
            "MarketAnalysis": {
                "tam": {
                    "claimed": f"${tam:,.0f}" if tam else "N/A",
                    "validated": f"${tam:,.0f}" if tam else "N/A",
                    "confidence": 0.8,
                    "raw_score": 8,
                    "final_score": 8
                },
                "sam": {
                    "claimed": f"${sam:,.0f}" if sam else "N/A",
                    "validated": f"${sam:,.0f}" if sam else "N/A",
                    "confidence": 0.7,
                    "raw_score": 7,
                    "final_score": 7
                },
                "som": {
                    "claimed": f"${som:,.0f}" if som else "N/A",
                    "validated": f"${som:,.0f}" if som else "N/A",
                    "confidence": 0.7,
                    "raw_score": 7,
                    "final_score": 7
                },
                "cagr": {
                    "claimed": f"{cagr}%" if cagr else "N/A",
                    "validated": f"{cagr}%" if cagr else "N/A",
                    "confidence": 0.7,
                    "raw_score": 7,
                    "final_score": 7
                },
                "category_average": 7
            },
            "Finance": {
                "arr": {
                    "claimed": f"${arr:,.0f}" if arr else "N/A",
                    "validated": f"${arr:,.0f}" if arr else "N/A",
                    "confidence": 0.8,
                    "raw_score": 8,
                    "final_score": 8
                },
                "category_average": 8
            }
        },
        "details": {
            "name": company_name,
            "about": f"{company_name} is a company operating in the {domain} sector.",
            "status": "Active",
            "founded_year": datetime.datetime.now().year - 3,
            "CEO": ceo,
            "headquaters": "Unknown",
            "business_model": "B2B",
            "revenue": "Undisclosed",
            "domain": domain,
            "sub-domain": "",
            "problem": extraction.get("tagline", "Addressing key challenges in the market."),
            "solution": f"{company_name} provides innovative solutions to critical market challenges.",
            "usp": "Differentiated approach with sustainable competitive advantages."
        },
        "summary": f"{company_name} presents an investment opportunity in the {domain} sector.",
        "pros": [
            "Strong founding team with relevant experience",
            "Attractive market opportunity",
            "Scalable business model"
        ],
        "red_flags": [
            "Limited financial history",
            "Competitive market with established players",
            "Execution risks in scaling operations"
        ],
        "final_irs_score": 7,
        "final_cs_score": 7,
        "uniqueness": 65
    }
    
    return result

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

@app.route('/analyze', methods=['POST'])
def analyze_pitch():
    """Analyze a pitch by ID."""
    data = request.json
    pitch_id = data.get('pitch_id')
    
    if not pitch_id:
        return jsonify({'error': 'Missing pitch_id parameter'}), 400
    
    try:
        # Get MongoDB collection
        collection = get_mongo_collection()
        
        # Fetch pitch data
        pitch_data = collection.find_one({"_id": ObjectId(pitch_id)})
        if not pitch_data:
            return jsonify({'error': f'Pitch not found with ID: {pitch_id}'}), 404
        
        # Analyze pitch data
        result = analyze_pitch_data(pitch_data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error analyzing pitch: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze/batch', methods=['POST'])
def analyze_batch():
    """Analyze multiple pitches in batch."""
    data = request.json
    pitch_ids = data.get('pitch_ids', [])
    
    if not pitch_ids:
        return jsonify({'error': 'Missing pitch_ids parameter'}), 400
    
    try:
        # Get MongoDB collection
        collection = get_mongo_collection()
        
        # Process each pitch
        results = []
        for pitch_id in pitch_ids:
            try:
                # Fetch pitch data
                pitch_data = collection.find_one({"_id": ObjectId(pitch_id)})
                if not pitch_data:
                    results.append({
                        'pitch_id': pitch_id,
                        'status': 'error',
                        'error': f'Pitch not found with ID: {pitch_id}'
                    })
                    continue
                
                # Analyze pitch data
                result = analyze_pitch_data(pitch_data)
                
                results.append({
                    'pitch_id': pitch_id,
                    'status': 'success',
                    'result': result
                })
            except Exception as e:
                results.append({
                    'pitch_id': pitch_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({'results': results})
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        return jsonify({'error': str(e)}), 500

# Run the Flask app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5070))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting VC Pitch Analysis API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)