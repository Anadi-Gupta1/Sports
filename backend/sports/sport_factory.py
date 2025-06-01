"""
Sport Factory - Creates sport-specific modules

Factory pattern for creating and managing different sport tracking modules.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SportFactory:
    """Factory for creating sport-specific tracking modules"""
    
    _sport_modules = {}
    
    @classmethod
    def register_sport(cls, sport_name: str, sport_class):
        """Register a new sport module"""
        cls._sport_modules[sport_name.lower()] = sport_class
        logger.info(f"Registered sport module: {sport_name}")
    
    @classmethod
    def create_sport(cls, sport_name: str, config: Dict[str, Any]):
        """Create a sport-specific module"""
        try:
            sport_name_lower = sport_name.lower()
            
            if sport_name_lower not in cls._sport_modules:
                # Try to import and register the sport module
                cls._import_sport_module(sport_name_lower)
            
            if sport_name_lower in cls._sport_modules:
                sport_class = cls._sport_modules[sport_name_lower]
                return sport_class(config)
            else:
                raise ValueError(f"Unknown sport: {sport_name}")
                
        except Exception as e:
            logger.error(f"Failed to create sport module for {sport_name}: {e}")
            raise
    
    @classmethod
    def _import_sport_module(cls, sport_name: str):
        """Dynamically import sport module"""        try:
            if sport_name == "basketball":
                from .basketball import BasketballTracker
                cls.register_sport("basketball", BasketballTracker)
            
            elif sport_name == "tennis":
                from .tennis import TennisTracker
                cls.register_sport("tennis", TennisTracker)
            
            elif sport_name == "soccer" or sport_name == "football":
                from .soccer import SoccerTracker
                cls.register_sport("soccer", SoccerTracker)
                cls.register_sport("football", SoccerTracker)
            
            elif sport_name == "golf":
                from .golf import GolfTracker
                cls.register_sport("golf", GolfTracker)
            
            else:
                logger.warning(f"No module found for sport: {sport_name}")
                
        except ImportError as e:
            logger.error(f"Failed to import sport module {sport_name}: {e}")
    
    @classmethod
    def get_available_sports(cls) -> list:
        """Get list of available sport modules"""
        return list(cls._sport_modules.keys())
    
    @classmethod
    def get_sport_info(cls, sport_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific sport"""
        try:
            sport_name_lower = sport_name.lower()
            
            if sport_name_lower not in cls._sport_modules:
                cls._import_sport_module(sport_name_lower)
            
            if sport_name_lower in cls._sport_modules:
                sport_class = cls._sport_modules[sport_name_lower]
                
                # Get sport information from class
                if hasattr(sport_class, 'get_sport_info'):
                    return sport_class.get_sport_info()
                else:
                    return {
                        "name": sport_name,
                        "available": True
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting sport info for {sport_name}: {e}")
            return None
