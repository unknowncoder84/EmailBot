# Design Document: Web UI Email Sender

## Overview

The Web UI Email Sender provides a browser-based interface for the existing Gmail Cold Email Sender functionality. Built with Flask as the backend framework and vanilla HTML/CSS/JavaScript for the frontend, the application exposes RESTful API endpoints for campaign management, file uploads, and real-time progress monitoring. The system runs on port 3000 and integrates seamlessly with the existing `email_sender.py` module without modifying its core logic.

### Design Goals

- **Minimal Modification**: Integrate with existing `email_sender.py` without altering its core functionality
- **Real-Time Feedback**: Provide live progress updates during campaign execution
- **Stateful Sessions**: Maintain campaign state across HTTP requests
- **Simple Deployment**: Single-command startup with no external database dependencies
- **Responsive UI**: Clean, accessible interface that works across modern browsers

### Technology Stack

- **Backend**: Flask 3.x (Python web framework)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (ES6+)
- **Real-Time Updates**: Server-Sent Events (SSE) or polling mechanism
- **File Handling**: Flask file upload with CSV parsing
- **State Management**: In-memory session state with optional JSON persistence
- **API Style**: RESTful endpoints with JSON responses

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Dashboard │  │ Upload View  │  │  History View    │   │
│  └────────────┘  └──────────────┘  └──────────────────┘   │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP/SSE
┌───────────────────────┴─────────────────────────────────────┐
│                    Flask Application                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Routes Layer                         │  │
│  │  /api/upload  /api/campaign  /api/progress  /api/... │  │
│  └────────────────────┬─────────────────────────────────┘  │
│  ┌────────────────────┴─────────────────────────────────┐  │
│  │           Campaign Manager                            │  │
│  │  - Session state management                           │  │
│  │  - Progress tracking                                  │  │
│  │  - Thread coordination                                │  │
│  └────────────────────┬─────────────────────────────────┘  │
│  ┌────────────────────┴─────────────────────────────────┐  │
│  │         Email Sender Adapter                          │  │
│  │  - Wraps email_sender.py functions                    │  │
│  │  - Progress callbacks                                 │  │
│  │  - Thread-safe execution                              │  │
│  └────────────────────┬─────────────────────────────────┘  │
└───────────────────────┴─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│              email_sender.py (Existing Module)               │
│  - Gmail API authentication                                  │
│  - Email generation and sending                              │
│  - Duplicate tracking (sent_log.json)                        │
│  - Rate limiting                                             │
└──────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**Frontend (Browser)**
- Render UI views (dashboard, upload, history, settings)
- Handle user interactions (file upload, button clicks, form submissions)
- Poll or listen for progress updates
- Display real-time campaign status
- Show error messages and notifications

**API Routes Layer**
- Define RESTful endpoints
- Validate request parameters
- Handle file uploads
- Return JSON responses
- Manage HTTP error codes

**Campaign Manager**
- Maintain campaign state (idle, running, stopped, completed)
- Store uploaded lead data in session
- Track progress metrics (sent, failed, skipped counts)
- Coordinate background thread execution
- Provide thread-safe access to campaign status

**Email Sender Adapter**
- Wrap `email_sender.py` functions for web context
- Execute email sending in background thread
- Provide progress callbacks to Campaign Manager
- Handle stop signals
- Catch and report exceptions

**email_sender.py (Existing)**
- Unchanged core functionality
- Gmail API authentication
- Email generation and sending
- Duplicate prevention via sent_log.json
- Rate limiting and delays

### Threading Model

Campaign execution runs in a background thread to avoid blocking HTTP requests:

```
Main Thread (Flask)          Background Thread
     │                              │
     │  POST /api/campaign/start    │
     ├──────────────────────────────┤
     │  Create thread               │
     │  Set state = RUNNING         │
     │  ──────────────────────────> │
     │  Return 200 OK               │  Start sending loop
     │                              │  For each lead:
     │  GET /api/progress           │    - Check stop flag
     │  <────────────────────────── │    - Send email
     │  Return current status       │    - Update progress
     │                              │    - Apply delay
     │  POST /api/campaign/stop     │
     │  Set stop_flag = True        │
     │  ──────────────────────────> │  Check stop_flag
     │  Return 200 OK               │  Exit loop
     │                              │  Set state = STOPPED
     │                              │  Thread exits
```

### Data Flow

**Upload Flow**
1. User selects CSV file in browser
2. Frontend sends multipart/form-data POST to `/api/upload`
3. Flask receives file, validates format
4. Backend parses CSV using `csv.DictReader`
5. Backend validates required columns (name, email, pitch_type, price)
6. Backend stores leads in session state
7. Backend loads sent_log.json and marks duplicates
8. Backend returns lead count, duplicate count, preview data

**Campaign Execution Flow**
1. User clicks "Start Campaign" button
2. Frontend sends POST to `/api/campaign/start`
3. Backend validates campaign can start (leads uploaded, not already running)
4. Backend spawns background thread
5. Background thread iterates through leads
6. For each lead:
   - Check if duplicate (skip if yes)
   - Generate email content
   - Send via Gmail API
   - Update progress counters
   - Check stop flag
   - Apply delay
7. Frontend polls `/api/progress` every 2 seconds
8. Backend returns current progress JSON
9. Frontend updates UI with progress data

**Stop Flow**
1. User clicks "Stop Campaign" button
2. Frontend sends POST to `/api/campaign/stop`
3. Backend sets stop_flag = True
4. Background thread checks flag after current email
5. Background thread exits loop
6. Backend sets state = STOPPED
7. Frontend receives final progress update

## Components and Interfaces

### Backend Components

#### Flask Application (`app.py`)

Main application entry point:

```python
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import threading
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
CORS(app)  # Enable CORS for development

# Global campaign manager instance
campaign_manager = CampaignManager()

@app.route('/')
def index():
    """Serve main HTML page"""
    return render_template('index.html')

# API routes defined below...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False, threaded=True)
```

#### Campaign Manager (`campaign_manager.py`)

Manages campaign state and coordinates execution:

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from threading import Lock
from enum import Enum

class CampaignState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class CampaignProgress:
    state: CampaignState
    total_leads: int
    sent_count: int
    failed_count: int
    skipped_count: int
    current_lead: Optional[Dict[str, str]]
    error_message: Optional[str]

class CampaignManager:
    def __init__(self):
        self.state = CampaignState.IDLE
        self.leads: List[Dict[str, str]] = []
        self.progress = CampaignProgress(
            state=CampaignState.IDLE,
            total_leads=0,
            sent_count=0,
            failed_count=0,
            skipped_count=0,
            current_lead=None,
            error_message=None
        )
        self.stop_flag = False
        self.lock = Lock()  # Thread-safe access
        self.background_thread: Optional[threading.Thread] = None
    
    def upload_leads(self, leads: List[Dict[str, str]]) -> None:
        """Store uploaded leads"""
        with self.lock:
            self.leads = leads
            self.progress.total_leads = len(leads)
    
    def start_campaign(self, config: Dict) -> bool:
        """Start campaign in background thread"""
        with self.lock:
            if self.state == CampaignState.RUNNING:
                return False
            if not self.leads:
                return False
            
            self.state = CampaignState.RUNNING
            self.stop_flag = False
            self.progress.sent_count = 0
            self.progress.failed_count = 0
            self.progress.skipped_count = 0
            self.progress.error_message = None
            
            # Start background thread
            self.background_thread = threading.Thread(
                target=self._run_campaign,
                args=(config,),
                daemon=True
            )
            self.background_thread.start()
            return True
    
    def stop_campaign(self) -> None:
        """Signal campaign to stop"""
        with self.lock:
            self.stop_flag = True
    
    def get_progress(self) -> CampaignProgress:
        """Get current progress (thread-safe)"""
        with self.lock:
            return CampaignProgress(
                state=self.state,
                total_leads=self.progress.total_leads,
                sent_count=self.progress.sent_count,
                failed_count=self.progress.failed_count,
                skipped_count=self.progress.skipped_count,
                current_lead=self.progress.current_lead.copy() if self.progress.current_lead else None,
                error_message=self.progress.error_message
            )
    
    def _run_campaign(self, config: Dict) -> None:
        """Background thread execution (calls email_sender functions)"""
        # Implementation in Email Sender Adapter section
        pass
```

#### Email Sender Adapter (`email_adapter.py`)

Wraps `email_sender.py` functions for web context:

```python
import email_sender
from typing import Dict, Callable

class EmailSenderAdapter:
    def __init__(self, progress_callback: Callable):
        self.progress_callback = progress_callback
        self.service = None
        self.sent_log = set()
    
    def authenticate(self) -> bool:
        """Authenticate with Gmail API"""
        try:
            self.service = email_sender.authenticate()
            return True
        except Exception as e:
            return False
    
    def load_sent_log(self) -> None:
        """Load sent log from disk"""
        self.sent_log = email_sender.load_sent_log()
    
    def send_campaign(self, leads: List[Dict], config: Dict, stop_flag_check: Callable) -> None:
        """
        Send emails to leads with progress callbacks
        
        Args:
            leads: List of lead dictionaries
            config: Configuration dict with daily_limit, delay_seconds
            stop_flag_check: Function that returns True if should stop
        """
        daily_limit = config.get('daily_limit', 50)
        delay_seconds = config.get('delay_seconds', 30)
        
        sent_count = 0
        
        for lead in leads:
            # Check stop flag
            if stop_flag_check():
                break
            
            email = lead.get('email', '')
            
            # Check duplicate
            if email_sender.is_duplicate(email, self.sent_log):
                self.progress_callback('skipped', lead)
                continue
            
            # Generate email
            location_type = email_sender.extract_location_type(lead.get('price', ''))
            subject, body = email_sender.generate_email(lead, location_type)
            
            # Update current lead
            self.progress_callback('processing', lead)
            
            # Send email
            try:
                success = email_sender.send_email(self.service, email, subject, body)
                
                if success:
                    email_sender.mark_as_sent(email, self.sent_log)
                    sent_count += 1
                    self.progress_callback('sent', lead)
                    
                    # Check daily limit
                    if sent_count >= daily_limit:
                        break
                    
                    # Apply delay
                    email_sender.apply_delay(delay_seconds)
                else:
                    self.progress_callback('failed', lead)
            
            except Exception as e:
                self.progress_callback('failed', lead, str(e))
```

### API Endpoints

#### GET `/`
Serves the main HTML page.

**Response**: HTML document

#### POST `/api/upload`
Upload CSV file with lead data.

**Request**:
- Content-Type: multipart/form-data
- Body: file field with CSV file

**Response**:
```json
{
  "success": true,
  "total_leads": 150,
  "new_leads": 120,
  "duplicate_leads": 30,
  "preview": [
    {
      "name": "John Doe",
      "email": "john@example.com",
      "pitch_type": "Website",
      "price": "$100",
      "is_duplicate": false
    }
  ]
}
```

**Error Response** (400):
```json
{
  "success": false,
  "error": "Missing required columns: name, email"
}
```

#### POST `/api/campaign/start`
Start email campaign.

**Request**:
```json
{
  "daily_limit": 50,
  "delay_seconds": 30
}
```

**Response**:
```json
{
  "success": true,
  "message": "Campaign started"
}
```

**Error Response** (400):
```json
{
  "success": false,
  "error": "No leads uploaded"
}
```

#### POST `/api/campaign/stop`
Stop running campaign.

**Response**:
```json
{
  "success": true,
  "message": "Campaign stop signal sent"
}
```

#### GET `/api/progress`
Get current campaign progress.

**Response**:
```json
{
  "state": "running",
  "total_leads": 150,
  "sent_count": 25,
  "failed_count": 2,
  "skipped_count": 10,
  "current_lead": {
    "name": "Jane Smith",
    "email": "jane@example.com"
  },
  "percentage": 24.7
}
```

#### GET `/api/history`
Get email sending history.

**Query Parameters**:
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 50)

**Response**:
```json
{
  "total_count": 523,
  "emails": [
    {
      "email": "john@example.com",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "page": 1,
  "per_page": 50,
  "total_pages": 11
}
```

#### GET `/api/config`
Get current configuration.

**Response**:
```json
{
  "daily_limit": 50,
  "delay_seconds": 30
}
```

#### POST `/api/config`
Update configuration.

**Request**:
```json
{
  "daily_limit": 75,
  "delay_seconds": 45
}
```

**Response**:
```json
{
  "success": true,
  "config": {
    "daily_limit": 75,
    "delay_seconds": 45
  }
}
```

**Error Response** (400):
```json
{
  "success": false,
  "error": "daily_limit must be between 1 and 500"
}
```

#### GET `/api/auth/status`
Check Gmail authentication status.

**Response**:
```json
{
  "authenticated": true,
  "email": "rishi.sawant2005@gmail.com",
  "credentials_exist": true,
  "token_exist": true
}
```

#### POST `/api/auth/initiate`
Initiate OAuth flow (triggers browser redirect).

**Response**:
```json
{
  "success": true,
  "auth_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

### Frontend Components

#### HTML Structure (`templates/index.html`)

Single-page application with multiple views:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Campaign Manager</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <div id="app">
        <header>
            <h1>Email Campaign Manager</h1>
            <div id="auth-status"></div>
        </header>
        
        <nav>
            <button class="nav-btn active" data-view="dashboard">Dashboard</button>
            <button class="nav-btn" data-view="upload">Upload</button>
            <button class="nav-btn" data-view="history">History</button>
            <button class="nav-btn" data-view="settings">Settings</button>
        </nav>
        
        <main>
            <div id="dashboard-view" class="view active">
                <!-- Dashboard content -->
            </div>
            
            <div id="upload-view" class="view">
                <!-- Upload form -->
            </div>
            
            <div id="history-view" class="view">
                <!-- History table -->
            </div>
            
            <div id="settings-view" class="view">
                <!-- Settings form -->
            </div>
        </main>
    </div>
    
    <script src="/static/js/app.js"></script>
</body>
</html>
```

#### JavaScript Application (`static/js/app.js`)

Main application logic:

```javascript
class EmailCampaignApp {
    constructor() {
        this.state = {
            campaignRunning: false,
            leads: [],
            progress: null,
            config: { daily_limit: 50, delay_seconds: 30 }
        };
        this.progressInterval = null;
        this.init();
    }
    
    init() {
        this.setupNavigation();
        this.setupEventListeners();
        this.checkAuthStatus();
        this.loadConfig();
    }
    
    setupNavigation() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchView(e.target.dataset.view);
            });
        });
    }
    
    switchView(viewName) {
        // Hide all views
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        
        // Show selected view
        document.getElementById(`${viewName}-view`).classList.add('active');
        document.querySelector(`[data-view="${viewName}"]`).classList.add('active');
        
        // Load view data
        if (viewName === 'history') {
            this.loadHistory();
        }
    }
    
    async uploadCSV(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            this.state.leads = data.preview;
            this.renderLeadPreview(data);
        } else {
            this.showError(data.error);
        }
    }
    
    async startCampaign() {
        const response = await fetch('/api/campaign/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(this.state.config)
        });
        
        const data = await response.json();
        
        if (data.success) {
            this.state.campaignRunning = true;
            this.startProgressPolling();
        } else {
            this.showError(data.error);
        }
    }
    
    async stopCampaign() {
        const response = await fetch('/api/campaign/stop', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            this.stopProgressPolling();
        }
    }
    
    startProgressPolling() {
        this.progressInterval = setInterval(() => {
            this.fetchProgress();
        }, 2000);
    }
    
    stopProgressPolling() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }
    
    async fetchProgress() {
        const response = await fetch('/api/progress');
        const data = await response.json();
        
        this.state.progress = data;
        this.renderProgress(data);
        
        if (data.state === 'completed' || data.state === 'stopped' || data.state === 'error') {
            this.stopProgressPolling();
            this.state.campaignRunning = false;
        }
    }
    
    renderProgress(progress) {
        // Update progress bar
        const percentage = progress.percentage || 0;
        document.getElementById('progress-bar').style.width = `${percentage}%`;
        
        // Update counters
        document.getElementById('sent-count').textContent = progress.sent_count;
        document.getElementById('failed-count').textContent = progress.failed_count;
        document.getElementById('skipped-count').textContent = progress.skipped_count;
        
        // Update current lead
        if (progress.current_lead) {
            document.getElementById('current-lead').textContent = 
                `${progress.current_lead.name} (${progress.current_lead.email})`;
        }
    }
    
    // Additional methods for history, settings, auth...
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new EmailCampaignApp();
});
```

## Data Models

### Lead Data Model

```python
@dataclass
class Lead:
    name: str
    username: str
    email: str
    phone: str
    category: str
    bio: str
    website: str
    followerCount: str
    pitch_type: str  # "Website" or "Management Tool"
    price: str       # Contains ₹ or $ symbol
    is_duplicate: bool = False
```

### Campaign Configuration Model

```python
@dataclass
class CampaignConfig:
    daily_limit: int  # 1-500
    delay_seconds: int  # 10-300
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        if not 1 <= self.daily_limit <= 500:
            return False, "daily_limit must be between 1 and 500"
        if not 10 <= self.delay_seconds <= 300:
            return False, "delay_seconds must be between 10 and 300"
        return True, None
```

### Progress Model

```python
@dataclass
class CampaignProgress:
    state: CampaignState  # IDLE, RUNNING, STOPPED, COMPLETED, ERROR
    total_leads: int
    sent_count: int
    failed_count: int
    skipped_count: int
    current_lead: Optional[Lead]
    error_message: Optional[str]
    
    @property
    def percentage(self) -> float:
        if self.total_leads == 0:
            return 0.0
        processed = self.sent_count + self.failed_count + self.skipped_count
        return (processed / self.total_leads) * 100
```

### Sent Log Model

The existing `sent_log.json` format is preserved:

```json
[
  "john@example.com",
  "jane@example.com",
  "bob@example.com"
]
```

### Configuration Persistence Model

Configuration is stored in `config.json`:

```json
{
  "daily_limit": 50,
  "delay_seconds": 30
}
```

## Error Handling

### Backend Error Handling

**File Upload Errors**
- Missing file: Return 400 with "No file provided"
- Invalid format: Return 400 with "Invalid CSV format"
- Missing columns: Return 400 with "Missing required columns: [list]"
- File too large: Return 413 with "File size exceeds limit"

**Campaign Errors**
- No leads uploaded: Return 400 with "No leads uploaded"
- Campaign already running: Return 400 with "Campaign already in progress"
- Authentication failed: Return 401 with "Gmail authentication required"

**Configuration Errors**
- Invalid daily_limit: Return 400 with "daily_limit must be between 1 and 500"
- Invalid delay_seconds: Return 400 with "delay_seconds must be between 10 and 300"

**Gmail API Errors**
- Authentication failure: Catch exception, return 401
- Send failure: Log error, increment failed_count, continue
- Rate limit exceeded: Log error, stop campaign

**Port Binding Errors**
- Port 3000 in use: Print error message and exit with code 1

### Frontend Error Handling

**Network Errors**
- Fetch timeout (10 seconds): Display "Connection error - server not responding"
- Network unavailable: Display "Network error - check connection"
- 500 errors: Display "Server error - please try again"

**Validation Errors**
- Empty file upload: Show "Please select a file"
- Invalid config values: Show inline validation messages
- Campaign start without leads: Show "Please upload leads first"

**User Feedback**
- Success messages: Green toast notifications
- Error messages: Red toast notifications
- Warning messages: Yellow toast notifications
- Loading states: Spinner overlays

## Testing Strategy

### Unit Tests

**Backend Unit Tests** (`tests/test_campaign_manager.py`)
- Test `CampaignManager.upload_leads()` with valid and empty lead lists
- Test `CampaignManager.start_campaign()` when already running
- Test `CampaignManager.stop_campaign()` sets stop flag
- Test `CampaignManager.get_progress()` returns correct state
- Test thread-safe access with concurrent reads/writes

**Backend Unit Tests** (`tests/test_email_adapter.py`)
- Test `EmailSenderAdapter.authenticate()` with valid/invalid credentials
- Test `EmailSenderAdapter.load_sent_log()` with existing/missing file
- Test progress callbacks are invoked correctly
- Test stop flag is checked between sends

**Backend Unit Tests** (`tests/test_api_routes.py`)
- Test `/api/upload` with valid CSV
- Test `/api/upload` with missing columns
- Test `/api/campaign/start` with no leads
- Test `/api/campaign/start` when already running
- Test `/api/config` validation for daily_limit and delay_seconds
- Test `/api/progress` returns correct JSON structure
- Test `/api/history` pagination

**Frontend Unit Tests** (`tests/test_frontend.js`)
- Test `uploadCSV()` sends correct FormData
- Test `startCampaign()` sends correct config
- Test `fetchProgress()` updates state correctly
- Test progress polling starts and stops
- Test view switching shows/hides correct elements

### Integration Tests

**End-to-End Flow Tests** (`tests/test_integration.py`)
- Test complete flow: upload CSV → start campaign → monitor progress → view history
- Test stop campaign mid-execution
- Test duplicate prevention across multiple uploads
- Test configuration persistence across restarts
- Test OAuth flow initiation and callback

**Gmail API Integration Tests** (`tests/test_gmail_integration.py`)
- Test authentication with valid credentials.json
- Test authentication with missing credentials.json
- Test token refresh when expired
- Test email sending with mocked Gmail API
- Test rate limiting behavior

### Manual Testing Checklist

**UI/UX Testing**
- [ ] All views render correctly in Chrome, Firefox, Safari
- [ ] Responsive layout works on mobile devices
- [ ] Progress bar animates smoothly
- [ ] Toast notifications appear and dismiss correctly
- [ ] File upload drag-and-drop works
- [ ] Buttons disable appropriately during operations

**Functional Testing**
- [ ] Upload CSV with 100+ leads
- [ ] Start campaign and verify emails send
- [ ] Stop campaign mid-execution
- [ ] Verify duplicates are skipped
- [ ] Verify daily limit stops campaign
- [ ] Verify delay is applied between sends
- [ ] Verify configuration persists after restart
- [ ] Verify history displays all sent emails

**Error Scenario Testing**
- [ ] Upload invalid CSV format
- [ ] Upload CSV with missing columns
- [ ] Start campaign without authentication
- [ ] Start campaign without uploaded leads
- [ ] Network disconnection during campaign
- [ ] Port 3000 already in use
- [ ] Gmail API quota exceeded

### Test Data

**Sample CSV Files**
- `test_leads_valid.csv`: 10 valid leads
- `test_leads_missing_columns.csv`: Missing email column
- `test_leads_duplicates.csv`: 5 leads, 3 duplicates
- `test_leads_large.csv`: 500 leads for performance testing

**Mock Responses**
- Mock Gmail API service for unit tests
- Mock sent_log.json with known email addresses
- Mock config.json with test values

### Performance Testing

**Load Testing**
- Test upload of 1000+ lead CSV file
- Test campaign execution with 500 leads
- Test progress polling with 10 concurrent clients
- Test history pagination with 10,000+ records

**Memory Testing**
- Monitor memory usage during large campaign
- Verify no memory leaks in background thread
- Test with multiple campaign executions

