"""
MongoDB Fetcher Agent.

This module fetches pitch data from MongoDB based on pitch ID.
"""

import logging
from typing import Dict, Any
import asyncio
import pymongo
from bson import ObjectId

from agents import BaseAgent

logger = logging.getLogger(__name__)

class MongoFetcher(BaseAgent):
    """
    Agent for fetching pitch data from MongoDB.
    
    This agent connects to MongoDB and retrieves the pitch document
    based on the provided ObjectId.
    """
    
    async def get_pitch(self, pitch_id: str) -> Dict[str, Any]:
        """
        Fetch pitch data from MongoDB by ID.
        
        Args:
            pitch_id: MongoDB ObjectId of the pitch
            
        Returns:
            Pitch document from MongoDB
            
        Raises:
            ValueError: If pitch_id is not a valid ObjectId
            RuntimeError: If pitch cannot be found or other database errors
        """
        logger.info(f"Fetching pitch with ID: {pitch_id}")
        
        # Convert to event loop compatible operation
        return await asyncio.to_thread(self._get_pitch_sync, pitch_id)
    
    def _get_pitch_sync(self, pitch_id: str) -> Dict[str, Any]:
        """
        Synchronous version of get_pitch for use with asyncio.to_thread.
        
        Args:
            pitch_id: MongoDB ObjectId of the pitch
            
        Returns:
            Pitch document from MongoDB
        """
        try:
            # Validate the ObjectId
            if not ObjectId.is_valid(pitch_id):
                raise ValueError(f"Invalid pitch ID format: {pitch_id}")
            
            # Connect to MongoDB
            mongo_uri = self.config.get('mongodb.uri')
            db_name = self.config.get('mongodb.database')
            collection_name = self.config.get('mongodb.collection')
            
            client = pymongo.MongoClient(mongo_uri)
            db = client[db_name]
            collection = db[collection_name]
            
            # Fetch the pitch document
            pitch_doc = collection.find_one({"_id": ObjectId(pitch_id)})
            
            if not pitch_doc:
                raise RuntimeError(f"Pitch not found with ID: {pitch_id}")
            
            logger.debug(f"Successfully fetched pitch with ID: {pitch_id}")
            return pitch_doc
            
        except (pymongo.errors.PyMongoError, Exception) as e:
            logger.error(f"Error fetching pitch from MongoDB: {str(e)}")
            raise RuntimeError(f"Database error: {str(e)}") from e
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data (pitch_id) and fetch the pitch.
        
        Args:
            data: Dictionary containing the pitch_id
            
        Returns:
            Pitch document from MongoDB
        """
        pitch_id = data.get("pitch_id")
        if not pitch_id:
            raise ValueError("Missing pitch_id in input data")
            
        return await self.get_pitch(pitch_id)