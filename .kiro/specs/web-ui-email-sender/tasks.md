# Implementation Plan: Web UI Email Sender

## Overview

This implementation plan breaks down the Web UI Email Sender into discrete coding tasks. The application is a Flask-based web interface for the existing Gmail Cold Email Sender, providing file upload, campaign management, real-time progress monitoring, and email history viewing. Each task builds incrementally, with checkpoints to ensure stability before proceeding.

## Tasks

- [ ] 1. Set up Flask project structure and dependencies
  - Create project directory structure (templates/, static/css/, static/js/)
  - Create requirements.txt with Flask, Flask-CORS dependencies
  - Create basic app.py with Flask initialization
  - Set up static file serving for CSS and JavaScript
  - _Requirements: 1.1, 1.2, 1.4_

- [ ] 2. Implement Campaign Manager core
  - [ ] 2.1 Create campaign_manager.py with CampaignState enum and CampaignProgress dataclass
    - Define CampaignState enum (IDLE, RUNNING, STOPPED, COMPLETED, ERROR)
    - Define CampaignProgress dataclass with all progress fields
    - _Requirements: 3.3, 4.1, 4.2, 4.3, 4.4_
  
  - [ ] 2.2 Implement CampaignManager class with thread-safe state management
    - Implement __init__ with threading.Lock for thread safety
    - Implement upload_leads() method to store lead data
    - Implement get_progress() method with lock protection
    - _Requirements: 2.5, 2.6, 3.3, 4.1_
  
  - [ ] 2.3 Implement campaign start/stop methods
    - Implement start_campaign() with background thread creation
    - Implement stop_campaign() with stop flag setting
    - Implement _run_campaign() stub for background execution
    - _Requirements: 3.1, 3.2, 3.3, 11.1, 11.2, 11.3_

- [ ] 3. Implement Email Sender Adapter
  - [ ] 3.1 Create email_adapter.py with EmailSenderAdapter class
    - Implement __init__ with progress callback parameter
    - Implement authenticate() wrapping email_sender.authenticate()
    - Implement load_sent_log() wrapping email_sender.load_sent_log()
    - _Requirements: 3.4, 3.5, 7.1, 7.2, 10.1_
  
  - [ ] 3.2 Implement send_campaign() method with progress callbacks
    - Implement lead iteration loop with duplicate checking
    - Implement progress callbacks for 'processing', 'sent', 'failed', 'skipped' events
    - Integrate email_sender functions (generate_email, send_email, mark_as_sent)
    - Implement stop flag checking between sends
    - Implement delay application and daily limit checking
    - _Requirements: 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.1, 4.2, 4.3, 4.4, 10.2, 10.3, 10.4, 10.5, 10.6, 11.3, 11.4_

- [ ] 4. Implement API endpoints - File upload and configuration
  - [ ] 4.1 Implement POST /api/upload endpoint
    - Validate file presence and CSV format
    - Parse CSV with csv.DictReader
    - Validate required columns (name, email, pitch_type, price)
    - Load sent_log and mark duplicates in preview
    - Return JSON with total_leads, new_leads, duplicate_leads, preview
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 12.1, 12.2, 12.3, 12.4_
  
  - [ ] 4.2 Implement GET /api/config and POST /api/config endpoints
    - Implement GET to return current daily_limit and delay_seconds
    - Implement POST with validation (daily_limit: 1-500, delay_seconds: 10-300)
    - Persist configuration to config.json
    - Return error messages for invalid ranges
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

- [ ] 5. Implement API endpoints - Campaign control
  - [ ] 5.1 Implement POST /api/campaign/start endpoint
    - Validate leads are uploaded
    - Validate campaign is not already running
    - Call campaign_manager.start_campaign() with config
    - Return success or error JSON response
    - _Requirements: 3.1, 3.2, 3.3, 3.10_
  
  - [ ] 5.2 Implement POST /api/campaign/stop endpoint
    - Call campaign_manager.stop_campaign()
    - Return success JSON response
    - _Requirements: 11.1, 11.2, 11.5_
  
  - [ ] 5.3 Implement GET /api/progress endpoint
    - Call campaign_manager.get_progress()
    - Calculate percentage completion
    - Return JSON with state, counts, current_lead, percentage
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 6. Implement API endpoints - History and authentication
  - [ ] 6.1 Implement GET /api/history endpoint with pagination
    - Load sent_log.json
    - Implement pagination logic (page, per_page parameters)
    - Return JSON with emails, timestamps, total_count, pagination metadata
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_
  
  - [ ] 6.2 Implement GET /api/auth/status endpoint
    - Check for credentials.json and token.pickle existence
    - Attempt to load and validate token
    - Return JSON with authenticated status and email address
    - _Requirements: 7.1, 7.2, 7.3, 7.7, 7.8_
  
  - [ ] 6.3 Implement POST /api/auth/initiate endpoint
    - Trigger Gmail OAuth flow
    - Return auth_url for browser redirect
    - _Requirements: 7.4, 7.5, 7.6_

- [ ] 7. Create frontend HTML structure
  - [ ] 7.1 Create templates/index.html with base layout
    - Create HTML structure with header, nav, main sections
    - Define four view containers (dashboard, upload, history, settings)
    - Include CSS and JavaScript file references
    - _Requirements: 1.2, 1.3_
  
  - [ ] 7.2 Create dashboard view HTML
    - Add statistics display elements (total leads, sent count, remaining sends)
    - Add campaign control buttons (start, stop)
    - Add progress bar and progress counters
    - Add current lead display
    - _Requirements: 3.1, 4.7, 4.8, 4.9, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 11.1_
  
  - [ ] 7.3 Create upload view HTML
    - Add file upload input and button
    - Add lead preview table
    - Add duplicate indicator display
    - Add estimated duration display
    - _Requirements: 2.1, 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [ ] 7.4 Create history and settings views HTML
    - Add history table with pagination controls
    - Add settings form with daily_limit and delay_seconds inputs
    - Add authentication status display
    - _Requirements: 5.1, 5.4, 5.5, 5.7, 6.1, 6.2, 7.1, 7.3, 7.7_

- [ ] 8. Implement frontend CSS styling
  - Create static/css/styles.css with responsive layout
  - Style navigation, buttons, forms, tables
  - Style progress bar and status indicators
  - Add toast notification styles
  - Ensure mobile-responsive design
  - _Requirements: 1.2_

- [ ] 9. Implement frontend JavaScript - Core application
  - [ ] 9.1 Create static/js/app.js with EmailCampaignApp class
    - Implement constructor with state initialization
    - Implement init() method with setup calls
    - Implement setupNavigation() for view switching
    - Implement switchView() to show/hide views
    - _Requirements: 1.2_
  
  - [ ] 9.2 Implement file upload functionality
    - Implement uploadCSV() method with FormData and fetch
    - Implement renderLeadPreview() to display uploaded leads
    - Implement duplicate marking in preview table
    - Implement estimated duration calculation
    - _Requirements: 2.1, 2.2, 2.5, 2.6, 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [ ] 9.3 Implement campaign control functionality
    - Implement startCampaign() method calling /api/campaign/start
    - Implement stopCampaign() method calling /api/campaign/stop
    - Implement button state management (disable during campaign)
    - _Requirements: 3.1, 3.2, 11.1, 11.2_

- [ ] 10. Implement frontend JavaScript - Progress monitoring
  - [ ] 10.1 Implement progress polling mechanism
    - Implement startProgressPolling() with setInterval (2 second interval)
    - Implement stopProgressPolling() with clearInterval
    - Implement fetchProgress() calling /api/progress
    - _Requirements: 4.5, 4.6_
  
  - [ ] 10.2 Implement progress rendering
    - Implement renderProgress() to update progress bar
    - Update sent, failed, skipped counters
    - Update current lead display
    - Update statistics dashboard
    - Stop polling when campaign completes/stops/errors
    - _Requirements: 4.7, 4.8, 4.9, 9.5_

- [ ] 11. Implement frontend JavaScript - History, settings, and auth
  - [ ] 11.1 Implement history view functionality
    - Implement loadHistory() calling /api/history with pagination
    - Implement renderHistory() to populate table
    - Implement pagination controls
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_
  
  - [ ] 11.2 Implement settings functionality
    - Implement loadConfig() calling /api/config
    - Implement saveConfig() calling POST /api/config
    - Implement validation for daily_limit and delay_seconds
    - Display validation error messages
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_
  
  - [ ] 11.3 Implement authentication status checking
    - Implement checkAuthStatus() calling /api/auth/status
    - Implement renderAuthStatus() to display connection status
    - Implement OAuth initiation button handler
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7, 7.8_

- [ ] 12. Implement error handling and user feedback
  - [ ] 12.1 Implement toast notification system
    - Create showError(), showSuccess(), showWarning() methods
    - Implement toast auto-dismiss after 5 seconds
    - Style toast notifications (green, red, yellow)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [ ] 12.2 Implement error handling for all API calls
    - Add try-catch blocks to all fetch calls
    - Implement 10-second timeout for fetch requests
    - Display connection error for timeouts
    - Display appropriate error messages for 400, 401, 500 responses
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.6_
  
  - [ ] 12.3 Implement loading states
    - Add spinner overlay during file upload
    - Add loading indicators during API calls
    - Disable buttons during operations
    - _Requirements: 8.1, 8.2, 8.3_

- [ ] 13. Checkpoint - Test basic functionality
  - Ensure Flask server starts on port 3000
  - Ensure all views render correctly
  - Ensure navigation works between views
  - Ensure file upload accepts CSV files
  - Ensure configuration can be saved and loaded
  - Ask the user if questions arise

- [ ] 14. Integrate Campaign Manager with Email Sender Adapter
  - [ ] 14.1 Implement _run_campaign() in CampaignManager
    - Create EmailSenderAdapter instance with progress callback
    - Call authenticate() and handle authentication errors
    - Call load_sent_log()
    - Call send_campaign() with leads and config
    - Update campaign state based on completion/stop/error
    - _Requirements: 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 11.3, 11.4, 11.5_
  
  - [ ] 14.2 Implement progress callback handler in CampaignManager
    - Handle 'processing' event to update current_lead
    - Handle 'sent' event to increment sent_count
    - Handle 'failed' event to increment failed_count
    - Handle 'skipped' event to increment skipped_count
    - Ensure thread-safe updates with lock
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 10.4_

- [ ] 15. Implement configuration persistence
  - Create config.json file structure
  - Implement load_config() function to read from config.json
  - Implement save_config() function to write to config.json
  - Load config on application startup
  - _Requirements: 6.7_

- [ ] 16. Implement port binding error handling
  - Add try-except block around app.run()
  - Catch OSError for port already in use
  - Display clear error message and exit gracefully
  - _Requirements: 1.3_

- [ ] 17. Add timestamp tracking to sent_log
  - Modify mark_as_sent() to store email with timestamp
  - Update sent_log.json format to include timestamps
  - Update load_sent_log() to handle new format
  - Maintain backward compatibility with old format
  - _Requirements: 5.3, 5.5_

- [ ]* 18. Write unit tests for backend components
  - Write tests for CampaignManager (upload_leads, start_campaign, stop_campaign, get_progress)
  - Write tests for EmailSenderAdapter (authenticate, load_sent_log, progress callbacks)
  - Write tests for API endpoints (upload, campaign start/stop, progress, history, config)
  - Write tests for configuration validation
  - _Requirements: All requirements_

- [ ]* 19. Write integration tests
  - Write end-to-end test: upload CSV → start campaign → monitor progress → view history
  - Write test for stop campaign mid-execution
  - Write test for duplicate prevention across multiple uploads
  - Write test for configuration persistence across restarts
  - _Requirements: 2.1-2.6, 3.1-3.10, 4.1-4.9, 5.1-5.7, 10.1-10.6_

- [ ] 20. Final checkpoint - End-to-end testing
  - Test complete workflow: upload leads, configure settings, start campaign, monitor progress, stop campaign, view history
  - Test error scenarios: invalid CSV, missing authentication, port conflict
  - Test duplicate prevention with real sent_log.json
  - Test daily limit enforcement
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- The implementation builds incrementally: core components → API endpoints → frontend → integration
- All code should integrate with the existing email_sender.py without modifying it
- Thread safety is critical for campaign execution and progress tracking
