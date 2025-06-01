<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Multi-Sport Action Tracker - Copilot Instructions

## Project Overview
This is a comprehensive multi-sport action tracking system that uses computer vision and machine learning to detect and analyze sports-specific actions in real-time, providing instant feedback and performance analytics.

## Key Technologies & Frameworks
- **Backend**: Python with FastAPI for real-time API endpoints
- **Computer Vision**: OpenCV and MediaPipe for pose estimation and object tracking
- **Machine Learning**: TensorFlow Lite for on-device inference
- **Frontend**: React.js for dashboard and configuration interface
- **Database**: SQLite for local data storage
- **Real-time Communication**: WebSocket connections
- **Audio Processing**: Pygame for feedback sounds

## Architecture Patterns
- **Modular Design**: Each sport has its own module with configurable parameters
- **Plugin Architecture**: Easy to add new sports and feedback mechanisms
- **Real-time Processing**: Low-latency computer vision pipeline
- **Event-driven**: Action detection triggers immediate feedback
- **Data-driven**: All configurations stored in JSON/YAML files

## Code Style & Standards
- **Python**: Follow PEP 8, use type hints, async/await patterns
- **FastAPI**: Use dependency injection, proper HTTP status codes
- **Computer Vision**: Optimize for real-time processing, handle camera failures gracefully
- **Error Handling**: Comprehensive exception handling with user-friendly messages
- **Configuration**: Use Pydantic models for settings validation
- **Testing**: Include unit tests for all core functionality

## Sport-Specific Modules
Each sport should have:
1. **Detection Logic**: Action recognition algorithms
2. **Success Criteria**: Rules for determining successful actions
3. **Feedback Templates**: Customized messages and sounds
4. **Analytics Models**: Performance calculation methods
5. **Configuration Schema**: Sport-specific settings

## Performance Considerations
- **Real-time Requirements**: Target <100ms latency for feedback
- **Resource Management**: Efficient camera and CPU usage
- **Scalability**: Support multiple concurrent users/cameras
- **Offline Capability**: Core functionality without internet
- **Cross-platform**: Support Windows, macOS, Linux

## Security & Privacy
- **Local Processing**: Keep video data on device
- **Data Anonymization**: Remove personal identifiers from exports
- **Secure Storage**: Encrypt sensitive configuration data
- **User Consent**: Clear permissions for camera and data usage

## Integration Points
- **Wearable Devices**: Support for smartwatch data
- **Cloud Services**: Optional backup and sync
- **External APIs**: Sports data providers
- **Hardware**: Camera calibration and multiple camera support

## Helpful Context
When generating code:
1. Always consider real-time performance implications
2. Include proper error handling for hardware failures
3. Make configurations easily modifiable through UI
4. Add comprehensive logging for debugging
5. Consider accessibility features for all users
6. Include proper documentation and examples
