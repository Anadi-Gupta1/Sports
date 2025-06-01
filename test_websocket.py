"""
WebSocket Connection Test Script

This script tests the WebSocket connection to the Multi-Sport Action Tracker backend.
It tries to connect to multiple WebSocket endpoints and reports the results.
"""

import asyncio
import websockets
import json
import sys
import time
from datetime import datetime

# Configuration
WS_ENDPOINTS = [
    "ws://localhost:8000/ws",
    "ws://localhost:8000/ws/test",
    "ws://localhost:8000/ws/test-session",
    "ws://127.0.0.1:8000/ws",
]

TEST_MESSAGE = {
    "type": "ping",
    "data": {
        "message": "Hello from test client!",
        "timestamp": str(datetime.now())
    }
}

async def test_websocket(url):
    """Test a single WebSocket endpoint"""
    print(f"\n[{datetime.now()}] Testing connection to: {url}")
    try:
        async with websockets.connect(url, ping_interval=None, close_timeout=2) as websocket:
            print(f"✅ Connected to {url}")
            
            # Send a test message
            message = json.dumps(TEST_MESSAGE)
            print(f"📤 Sending: {message}")
            await websocket.send(message)
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"📥 Received: {response}")
                
                # Try to parse JSON response
                try:
                    json_response = json.loads(response)
                    print(f"✅ Valid JSON response received")
                    return True, f"Successfully connected to {url} and received response"
                except json.JSONDecodeError:
                    print(f"⚠️ Response is not valid JSON")
                    return True, f"Connected to {url}, but response is not JSON: {response[:100]}"
            
            except asyncio.TimeoutError:
                print(f"⚠️ No response received within timeout")
                return True, f"Connected to {url}, but no response within timeout"
    
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed with status code: {e.status_code}")
        return False, f"Failed to connect to {url}: {e}"
    
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ Connection closed: {e}")
        return False, f"Connection to {url} was closed: {e}"
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, f"Error connecting to {url}: {e}"

async def run_tests():
    """Run tests for all endpoints"""
    results = []
    
    for endpoint in WS_ENDPOINTS:
        success, message = await test_websocket(endpoint)
        results.append({
            "endpoint": endpoint,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    return results

def print_summary(results):
    """Print a summary of test results"""
    print("\n" + "="*60)
    print("WebSocket Connection Test Summary")
    print("="*60)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"Total endpoints tested: {len(results)}")
    print(f"✅ Successful connections: {len(successful)}")
    print(f"❌ Failed connections: {len(failed)}")
    
    if successful:
        print("\n✅ Working Endpoints:")
        for result in successful:
            print(f"  - {result['endpoint']}: {result['message']}")
    
    if failed:
        print("\n❌ Failed Endpoints:")
        for result in failed:
            print(f"  - {result['endpoint']}: {result['message']}")
    
    print("\n📋 Recommendations:")
    if successful:
        print(f"  ✓ Use one of the working endpoints for your WebSocket connections")
        print(f"    Example: {successful[0]['endpoint']}")
    else:
        print("  ✗ Make sure the backend server is running")
        print("  ✗ Check CORS settings and WebSocket configurations")
        print("  ✗ Verify the port (8000) is correct and not blocked")
        print("  ✗ Check for any firewall or security software blocking WebSockets")

if __name__ == "__main__":
    print("="*60)
    print("Multi-Sport Action Tracker - WebSocket Connection Tester")
    print("="*60)
    print("This script will attempt to connect to several WebSocket endpoints")
    print("and verify if they are working correctly.")
    print("\nEnsure that your backend server is running before starting.")
    
    try:
        # Run the tests
        results = asyncio.run(run_tests())
        
        # Print summary
        print_summary(results)
        
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        sys.exit(1)
