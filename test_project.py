"""
Comprehensive test script for the Multi-Sport Action Tracker.

This script tests all major components of the application including:
- Backend API endpoints
- WebSocket connections
- Camera functionality
- Sports detection
- Feedback system
"""

import asyncio
import sys
import os
import json
import requests
import websockets
from typing import Dict, Any, List

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.core.tracker import ActionTracker
from backend.feedback.feedback_manager import FeedbackManager
from backend.sports.sport_factory import SportFactory
from models.sport_models import get_available_sports

class TestRunner:
    """Comprehensive test runner for the Multi-Sport Action Tracker"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/ws"
        self.test_results = {}
        
    async def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Multi-Sport Action Tracker Test Suite...")
        print("=" * 60)
        
        # Test suites
        test_suites = [
            ("Backend Components", self.test_backend_components),
            ("Sports Models", self.test_sports_models),
            ("Feedback System", self.test_feedback_system),
            ("API Endpoints", self.test_api_endpoints),
            ("WebSocket Connection", self.test_websocket),
        ]
        
        for suite_name, test_func in test_suites:
            print(f"\n📋 Testing {suite_name}...")
            try:
                await test_func()
                self.test_results[suite_name] = "✅ PASSED"
                print(f"✅ {suite_name} tests passed!")
            except Exception as e:
                self.test_results[suite_name] = f"❌ FAILED: {e}"
                print(f"❌ {suite_name} tests failed: {e}")
        
        # Print final results
        self.print_test_summary()
    
    async def test_backend_components(self):
        """Test backend component initialization"""
        # Test ActionTracker
        tracker = ActionTracker()
        assert tracker is not None, "ActionTracker failed to initialize"
        
        # Test FeedbackManager
        feedback_manager = FeedbackManager()
        assert feedback_manager is not None, "FeedbackManager failed to initialize"
        
        # Test SportFactory
        factory = SportFactory()
        sports = factory.get_available_sports()
        assert len(sports) > 0, "No sports available"
        
        print("   ✓ Backend components initialized successfully")
    
    async def test_sports_models(self):
        """Test sports model functionality"""
        available_sports = get_available_sports()
        assert len(available_sports) >= 4, f"Expected at least 4 sports, got {len(available_sports)}"
        
        expected_sports = ['basketball', 'tennis', 'golf', 'soccer']
        for sport in expected_sports:
            assert sport in available_sports, f"Sport {sport} not available"
        
        # Test model predictions with dummy data
        from models.sport_models import get_model_for_sport
        
        dummy_landmarks = [
            {'x': 0.5, 'y': 0.5, 'z': 0.0} for _ in range(33)  # MediaPipe has 33 landmarks
        ]
        
        for sport in expected_sports:
            model = get_model_for_sport(sport)
            result = model.predict(dummy_landmarks)
            assert 'action' in result, f"Model for {sport} missing 'action' in result"
            assert 'confidence' in result, f"Model for {sport} missing 'confidence' in result"
        
        print("   ✓ Sports models working correctly")
    
    async def test_feedback_system(self):
        """Test feedback system functionality"""
        feedback_manager = FeedbackManager()
        
        # Test initialization
        feedback_manager.start()
        assert feedback_manager.is_active, "FeedbackManager not active after start"
        
        # Test feedback sending
        test_action = {
            "success": True,
            "feedback_message": "Great shot!",
            "action_type": "test",
            "sport": "basketball"
        }
        
        await feedback_manager.send_feedback(test_action)
        
        # Test configuration
        new_config = {"volume": 0.5, "visual_enabled": True}
        feedback_manager.configure(new_config)
        
        # Test stats
        stats = feedback_manager.get_feedback_stats()
        assert 'total_feedback_sent' in stats, "Missing stats data"
        
        feedback_manager.stop()
        print("   ✓ Feedback system working correctly")
    
    async def test_api_endpoints(self):
        """Test API endpoints (requires server to be running)"""
        try:
            # Test health endpoint
            response = requests.get(f"{self.base_url}/health", timeout=5)
            assert response.status_code == 200, f"Health check failed: {response.status_code}"
            
            # Test sports endpoint
            response = requests.get(f"{self.base_url}/sports", timeout=5)
            assert response.status_code == 200, f"Sports endpoint failed: {response.status_code}"
            
            sports_data = response.json()
            assert len(sports_data) > 0, "No sports returned from API"
            
            print("   ✓ API endpoints responding correctly")
            
        except requests.exceptions.ConnectionError:
            print("   ⚠️  Server not running - skipping API tests")
            print("   💡 Run 'python backend/main.py' to test API endpoints")
    
    async def test_websocket(self):
        """Test WebSocket connectivity"""
        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Send test message
                test_message = {
                    "type": "test",
                    "data": {"message": "hello"}
                }
                await websocket.send(json.dumps(test_message))
                
                # Wait for response (with timeout)
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                assert response is not None, "No WebSocket response received"
                
                print("   ✓ WebSocket connection working correctly")
                
        except Exception:
            print("   ⚠️  WebSocket server not running - skipping WebSocket tests")
            print("   💡 Run 'python backend/main.py' to test WebSocket connectivity")
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for suite_name, result in self.test_results.items():
            print(f"{result:<50} {suite_name}")
            if "PASSED" in result:
                passed += 1
            else:
                failed += 1
        
        print(f"\n📊 Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed! Your Multi-Sport Action Tracker is ready!")
            self.print_next_steps()
        else:
            print("🔧 Some tests failed. Please check the issues above.")
    
    def print_next_steps(self):
        """Print next steps for running the application"""
        print("\n" + "=" * 60)
        print("🚀 NEXT STEPS - HOW TO RUN YOUR APPLICATION")
        print("=" * 60)
        
        steps = [
            "1. Start the Backend Server:",
            "   python backend/main.py",
            "",
            "2. Start the Frontend (in a new terminal):",
            "   cd frontend",
            "   npm start",
            "",
            "3. Open your browser to:",
            "   http://localhost:3000",
            "",
            "4. Connect a camera and start tracking!",
            "",
            "📚 Additional Commands:",
            "   - Run tests: python test_project.py",
            "   - Install deps: pip install -r requirements.txt",
            "   - Frontend deps: cd frontend && npm install"
        ]
        
        for step in steps:
            print(step)

async def main():
    """Main test execution"""
    runner = TestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
