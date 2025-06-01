"""
Session Tracker - Tracks training sessions and performance metrics

Manages session data, calculates statistics, and provides analytics.
"""

import time
import json
import sqlite3
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class ActionRecord:
    """Record of a single action"""
    timestamp: float
    sport: str
    action_type: str
    success: bool
    confidence: float
    metrics: Dict[str, Any]
    feedback_message: str
    session_id: str

@dataclass
class SessionSummary:
    """Summary of a training session"""
    session_id: str
    sport: str
    start_time: float
    end_time: Optional[float]
    duration: float
    total_actions: int
    successful_actions: int
    success_rate: float
    actions_by_type: Dict[str, int]
    average_confidence: float
    performance_trend: float
    notes: str = ""

class SessionTracker:
    """Tracks training sessions and performance analytics"""
    
    def __init__(self, db_path: str = "data/sessions.db"):
        self.db_path = db_path
        self.current_session = None
        self.session_actions = []
        
        # Initialize database
        self._init_database()
        
        logger.info("SessionTracker initialized")
    
    def _init_database(self):
        """Initialize SQLite database for session storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    sport TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    duration REAL,
                    total_actions INTEGER,
                    successful_actions INTEGER,
                    success_rate REAL,
                    average_confidence REAL,
                    performance_trend REAL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create actions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    sport TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    confidence REAL NOT NULL,
                    metrics TEXT,
                    feedback_message TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            ''')
            
            # Create indices for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON actions(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON actions(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sport ON actions(sport)')
            
            conn.commit()
            conn.close()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def start_session(self, sport: str, notes: str = "") -> str:
        """Start a new training session"""
        try:
            session_id = f"{sport}_{int(time.time())}"
            
            self.current_session = {
                "session_id": session_id,
                "sport": sport,
                "start_time": time.time(),
                "notes": notes
            }
            
            self.session_actions = []
            
            logger.info(f"Started session: {session_id} for sport: {sport}")
            
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            raise
    
    def end_session(self) -> Optional[SessionSummary]:
        """End the current session and save to database"""
        try:
            if not self.current_session:
                logger.warning("No active session to end")
                return None
            
            end_time = time.time()
            duration = end_time - self.current_session["start_time"]
            
            # Calculate session statistics
            session_summary = self._calculate_session_summary(end_time, duration)
            
            # Save to database
            self._save_session_to_db(session_summary)
            
            logger.info(f"Ended session: {self.current_session['session_id']} "
                       f"Duration: {duration:.1f}s, Actions: {session_summary.total_actions}")
            
            self.current_session = None
            self.session_actions = []
            
            return session_summary
            
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            return None
    
    def record_action(self, action_result) -> bool:
        """Record an action in the current session"""
        try:
            if not self.current_session:
                logger.warning("No active session to record action")
                return False
            
            # Create action record
            action_record = ActionRecord(
                timestamp=getattr(action_result, 'timestamp', time.time()),
                sport=self.current_session["sport"],
                action_type=getattr(action_result, 'action_type', 'unknown'),
                success=getattr(action_result, 'success', False),
                confidence=getattr(action_result, 'confidence', 0.0),
                metrics=getattr(action_result, 'metrics', {}),
                feedback_message=getattr(action_result, 'feedback_message', ''),
                session_id=self.current_session["session_id"]
            )
            
            # Add to session actions
            self.session_actions.append(action_record)
            
            logger.debug(f"Recorded action: {action_record.action_type} "
                        f"({'Success' if action_record.success else 'Failed'})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to record action: {e}")
            return False
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get statistics for the current session"""
        try:
            if not self.current_session or not self.session_actions:
                return {
                    "session_active": bool(self.current_session),
                    "total_actions": 0,
                    "successful_actions": 0,
                    "success_rate": 0.0,
                    "duration": 0.0,
                    "recent_actions": []
                }
            
            total_actions = len(self.session_actions)
            successful_actions = sum(1 for action in self.session_actions if action.success)
            success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0
            
            current_time = time.time()
            duration = current_time - self.current_session["start_time"]
            
            # Get recent actions (last 5)
            recent_actions = []
            for action in self.session_actions[-5:]:
                recent_actions.append({
                    "action_type": action.action_type,
                    "success": action.success,
                    "timestamp": action.timestamp,
                    "confidence": action.confidence
                })
            
            return {
                "session_active": True,
                "session_id": self.current_session["session_id"],
                "sport": self.current_session["sport"],
                "total_actions": total_actions,
                "successful_actions": successful_actions,
                "success_rate": success_rate,
                "duration": duration,
                "recent_actions": recent_actions,
                "actions_by_type": self._get_actions_by_type()
            }
            
        except Exception as e:
            logger.error(f"Error getting current stats: {e}")
            return {}
    
    def get_session_summary(self) -> Optional[Dict[str, Any]]:
        """Get summary of current session without ending it"""
        try:
            if not self.current_session:
                return None
            
            current_time = time.time()
            duration = current_time - self.current_session["start_time"]
            
            summary = self._calculate_session_summary(current_time, duration)
            
            return asdict(summary)
            
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")
            return None
    
    def _calculate_session_summary(self, end_time: float, duration: float) -> SessionSummary:
        """Calculate session summary statistics"""
        total_actions = len(self.session_actions)
        successful_actions = sum(1 for action in self.session_actions if action.success)
        success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0
        
        # Calculate average confidence
        avg_confidence = 0.0
        if self.session_actions:
            avg_confidence = sum(action.confidence for action in self.session_actions) / len(self.session_actions)
        
        # Calculate performance trend
        performance_trend = self._calculate_performance_trend()
        
        # Count actions by type
        actions_by_type = self._get_actions_by_type()
        
        return SessionSummary(
            session_id=self.current_session["session_id"],
            sport=self.current_session["sport"],
            start_time=self.current_session["start_time"],
            end_time=end_time,
            duration=duration,
            total_actions=total_actions,
            successful_actions=successful_actions,
            success_rate=success_rate,
            actions_by_type=actions_by_type,
            average_confidence=avg_confidence,
            performance_trend=performance_trend,
            notes=self.current_session.get("notes", "")
        )
    
    def _get_actions_by_type(self) -> Dict[str, int]:
        """Get count of actions by type"""
        actions_by_type = {}
        for action in self.session_actions:
            action_type = action.action_type
            actions_by_type[action_type] = actions_by_type.get(action_type, 0) + 1
        return actions_by_type
    
    def _calculate_performance_trend(self) -> float:
        """Calculate performance trend (positive = improving, negative = declining)"""
        try:
            if len(self.session_actions) < 6:
                return 0.0
            
            # Split into two halves and compare success rates
            mid_point = len(self.session_actions) // 2
            first_half = self.session_actions[:mid_point]
            second_half = self.session_actions[mid_point:]
            
            first_half_success = sum(1 for action in first_half if action.success) / len(first_half)
            second_half_success = sum(1 for action in second_half if action.success) / len(second_half)
            
            return second_half_success - first_half_success
            
        except Exception as e:
            logger.error(f"Error calculating performance trend: {e}")
            return 0.0
    
    def _save_session_to_db(self, session_summary: SessionSummary):
        """Save session summary and actions to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Save session summary
            cursor.execute('''
                INSERT INTO sessions (
                    session_id, sport, start_time, end_time, duration,
                    total_actions, successful_actions, success_rate,
                    average_confidence, performance_trend, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_summary.session_id,
                session_summary.sport,
                session_summary.start_time,
                session_summary.end_time,
                session_summary.duration,
                session_summary.total_actions,
                session_summary.successful_actions,
                session_summary.success_rate,
                session_summary.average_confidence,
                session_summary.performance_trend,
                session_summary.notes
            ))
            
            # Save individual actions
            for action in self.session_actions:
                cursor.execute('''
                    INSERT INTO actions (
                        session_id, timestamp, sport, action_type,
                        success, confidence, metrics, feedback_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    action.session_id,
                    action.timestamp,
                    action.sport,
                    action.action_type,
                    action.success,
                    action.confidence,
                    json.dumps(action.metrics),
                    action.feedback_message
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Session saved to database: {session_summary.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to save session to database: {e}")
            raise
    
    def get_historical_sessions(self, sport: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get historical session summaries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if sport:
                cursor.execute('''
                    SELECT * FROM sessions 
                    WHERE sport = ? 
                    ORDER BY start_time DESC 
                    LIMIT ?
                ''', (sport, limit))
            else:
                cursor.execute('''
                    SELECT * FROM sessions 
                    ORDER BY start_time DESC 
                    LIMIT ?
                ''', (limit,))
            
            columns = [description[0] for description in cursor.description]
            sessions = []
            
            for row in cursor.fetchall():
                session_dict = dict(zip(columns, row))
                sessions.append(session_dict)
            
            conn.close()
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting historical sessions: {e}")
            return []
    
    def get_performance_analytics(self, sport: str = None, days: int = 30) -> Dict[str, Any]:
        """Get performance analytics over time"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get sessions from last N days
            start_date = time.time() - (days * 24 * 60 * 60)
            
            if sport:
                cursor.execute('''
                    SELECT * FROM sessions 
                    WHERE sport = ? AND start_time >= ?
                    ORDER BY start_time
                ''', (sport, start_date))
            else:
                cursor.execute('''
                    SELECT * FROM sessions 
                    WHERE start_time >= ?
                    ORDER BY start_time
                ''', (start_date,))
            
            columns = [description[0] for description in cursor.description]
            sessions = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            
            if not sessions:
                return {
                    "total_sessions": 0,
                    "total_actions": 0,
                    "overall_success_rate": 0.0,
                    "improvement_trend": 0.0,
                    "sessions_by_day": [],
                    "action_types_distribution": {}
                }
            
            # Calculate analytics
            total_sessions = len(sessions)
            total_actions = sum(session["total_actions"] for session in sessions)
            total_successful = sum(session["successful_actions"] for session in sessions)
            overall_success_rate = (total_successful / total_actions * 100) if total_actions > 0 else 0
            
            # Calculate improvement trend
            if len(sessions) >= 2:
                recent_sessions = sessions[-5:]  # Last 5 sessions
                older_sessions = sessions[:len(sessions)-5] if len(sessions) > 5 else []
                
                if older_sessions:
                    recent_avg = sum(s["success_rate"] for s in recent_sessions) / len(recent_sessions)
                    older_avg = sum(s["success_rate"] for s in older_sessions) / len(older_sessions)
                    improvement_trend = recent_avg - older_avg
                else:
                    improvement_trend = 0.0
            else:
                improvement_trend = 0.0
            
            # Group sessions by day
            sessions_by_day = self._group_sessions_by_day(sessions)
            
            return {
                "total_sessions": total_sessions,
                "total_actions": total_actions,
                "overall_success_rate": overall_success_rate,
                "improvement_trend": improvement_trend,
                "sessions_by_day": sessions_by_day,
                "recent_sessions": sessions[-10:],  # Last 10 sessions
                "best_session": max(sessions, key=lambda s: s["success_rate"]) if sessions else None,
                "average_session_duration": sum(s["duration"] for s in sessions) / len(sessions)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance analytics: {e}")
            return {}
    
    def _group_sessions_by_day(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group sessions by day for analytics"""
        try:
            daily_stats = {}
            
            for session in sessions:
                date_str = datetime.fromtimestamp(session["start_time"]).strftime("%Y-%m-%d")
                
                if date_str not in daily_stats:
                    daily_stats[date_str] = {
                        "date": date_str,
                        "sessions": 0,
                        "total_actions": 0,
                        "successful_actions": 0,
                        "total_duration": 0
                    }
                
                daily_stats[date_str]["sessions"] += 1
                daily_stats[date_str]["total_actions"] += session["total_actions"]
                daily_stats[date_str]["successful_actions"] += session["successful_actions"]
                daily_stats[date_str]["total_duration"] += session["duration"] or 0
            
            # Calculate success rates
            for day_data in daily_stats.values():
                day_data["success_rate"] = (
                    day_data["successful_actions"] / day_data["total_actions"] * 100
                    if day_data["total_actions"] > 0 else 0
                )
            
            return list(daily_stats.values())
            
        except Exception as e:
            logger.error(f"Error grouping sessions by day: {e}")
            return []
    
    def export_session_data(self, session_id: str, format: str = "json") -> Optional[str]:
        """Export session data in specified format"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get session summary
            cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
            session_row = cursor.fetchone()
            
            if not session_row:
                logger.warning(f"Session not found: {session_id}")
                return None
            
            # Get session actions
            cursor.execute('SELECT * FROM actions WHERE session_id = ?', (session_id,))
            action_rows = cursor.fetchall()
            
            conn.close()
            
            # Format data
            session_columns = [desc[0] for desc in cursor.description]
            session_data = dict(zip(session_columns, session_row))
            
            actions_data = []
            for row in action_rows:
                action_dict = dict(zip([
                    'id', 'session_id', 'timestamp', 'sport', 'action_type',
                    'success', 'confidence', 'metrics', 'feedback_message'
                ], row))
                # Parse metrics JSON
                try:
                    action_dict['metrics'] = json.loads(action_dict['metrics'])
                except:
                    action_dict['metrics'] = {}
                actions_data.append(action_dict)
            
            export_data = {
                "session": session_data,
                "actions": actions_data,
                "export_timestamp": time.time()
            }
            
            if format.lower() == "json":
                return json.dumps(export_data, indent=2)
            else:
                logger.warning(f"Unsupported export format: {format}")
                return None
                
        except Exception as e:
            logger.error(f"Error exporting session data: {e}")
            return None
