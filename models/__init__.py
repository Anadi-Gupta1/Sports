"""
Model loading utilities for the Multi-Sport Action Tracker.

This module provides utilities to load and manage machine learning models
for sports action detection and analysis.
"""

import os
import logging
from typing import Optional, Dict, Any
import pickle
import json

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages loading and caching of ML models"""
    
    def __init__(self, model_path: str = "./models/"):
        self.model_path = model_path
        self.loaded_models = {}
        self.model_configs = {}
        
        # Ensure models directory exists
        os.makedirs(model_path, exist_ok=True)
        
        logger.info(f"ModelManager initialized with path: {model_path}")
    
    def load_model(self, model_name: str, model_type: str = "pickle") -> Optional[Any]:
        """Load a model from file"""
        try:
            if model_name in self.loaded_models:
                logger.debug(f"Model {model_name} already loaded from cache")
                return self.loaded_models[model_name]
            
            model_file = os.path.join(self.model_path, f"{model_name}.{model_type}")
            
            if not os.path.exists(model_file):
                logger.warning(f"Model file not found: {model_file}")
                return None
            
            if model_type == "pickle":
                with open(model_file, 'rb') as f:
                    model = pickle.load(f)
            elif model_type == "json":
                with open(model_file, 'r') as f:
                    model = json.load(f)
            else:
                logger.error(f"Unsupported model type: {model_type}")
                return None
            
            self.loaded_models[model_name] = model
            logger.info(f"Successfully loaded model: {model_name}")
            return model
            
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return None
    
    def save_model(self, model: Any, model_name: str, model_type: str = "pickle") -> bool:
        """Save a model to file"""
        try:
            model_file = os.path.join(self.model_path, f"{model_name}.{model_type}")
            
            if model_type == "pickle":
                with open(model_file, 'wb') as f:
                    pickle.dump(model, f)
            elif model_type == "json":
                with open(model_file, 'w') as f:
                    json.dump(model, f, indent=2)
            else:
                logger.error(f"Unsupported model type: {model_type}")
                return False
            
            # Cache the model
            self.loaded_models[model_name] = model
            logger.info(f"Successfully saved model: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving model {model_name}: {e}")
            return False
    
    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        """List all available models"""
        models = {}
        
        try:
            if not os.path.exists(self.model_path):
                return models
            
            for file in os.listdir(self.model_path):
                if file.endswith(('.pkl', '.pickle', '.json')):
                    name = os.path.splitext(file)[0]
                    ext = os.path.splitext(file)[1]
                    
                    file_path = os.path.join(self.model_path, file)
                    stat = os.stat(file_path)
                    
                    models[name] = {
                        "type": ext[1:],  # Remove the dot
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "loaded": name in self.loaded_models
                    }
            
            return models
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return {}

# Global model manager instance
model_manager = ModelManager()

def get_model_manager() -> ModelManager:
    """Get the global model manager instance"""
    return model_manager
