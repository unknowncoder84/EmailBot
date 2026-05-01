# Requirements Document

## Introduction

This document specifies requirements for a web-based user interface for the existing Gmail Cold Email Sender Python script. The Web_Application will provide a browser-based interface for managing email campaigns, uploading lead data, monitoring sending progress, and viewing email history. The application will run on port 3000 and integrate with the existing email_sender.py functionality.

## Glossary

- **Web_Application**: The Flask-based web server that provides the user interface and API endpoints
- **Frontend**: The browser-based user interface built with HTML, CSS, and JavaScript
- **Backend**: The Python Flask server that handles HTTP requests and integrates with Email_Sender
- **Email_Sender**: The existing Python module (email_sender.py) that sends emails via Gmail API
- **Campaign**: A batch email sending operation triggered by the user
- **Lead**: A recipient record containing name, email, and other contact information
- **CSV_File**: A comma-separated values file containing lead data
- **Sent_Log**: The persistent storage (sent_log.json) tracking previously contacted email addresses
- **Progress_Monitor**: The component that tracks and reports real-time campaign execution status
- **Configuration_Settings**: User-adjustable parameters including daily_limit and delay_seconds
- **Email_History**: The record of all sent emails with timestamps and recipient details

## Requirements

### Requirement 1: Web Server Initialization

**User Story:** As a user, I want the web application to start on port 3000, so that I can access the interface through my browser.

#### Acceptance Criteria

1. WHEN the application is started, THE Web_Application SHALL bind to port 3000
2. WHEN the application is started, THE Web_Application SHALL serve the Frontend on http://localhost:3000
3. IF port 3000 is already in use, THEN THE Web_Application SHALL display an error message and exit gracefully
4. THE Web_Application SHALL initialize the Backend before accepting HTTP requests

### Requirement 2: CSV File Upload

**User Story:** As a user, I want to upload CSV files with lead data, so that I can import recipients for email campaigns.

#### Acceptance Criteria

1. THE Frontend SHALL provide a file upload interface for CSV files
2. WHEN a CSV file is uploaded, THE Backend SHALL validate the file format
3. WHEN a CSV file is uploaded, THE Backend SHALL verify the presence of required columns: name, email, pitch_type, price
4. IF the CSV file is missing required columns, THEN THE Backend SHALL return an error message listing the missing columns
5. WHEN a valid CSV file is uploaded, THE Backend SHALL parse the file and store the lead data
6. WHEN a valid CSV file is uploaded, THE Backend SHALL return the count of leads imported

### Requirement 3: Email Campaign Execution

**User Story:** As a user, I want to trigger email sending campaigns, so that I can send personalized emails to my leads.

#### Acceptance Criteria

1. THE Frontend SHALL provide a button to start an email campaign
2. WHEN the start campaign button is clicked, THE Backend SHALL invoke the Email_Sender with the uploaded leads
3. WHILE a campaign is running, THE Backend SHALL prevent starting additional campaigns
4. WHEN a campaign is running, THE Email_Sender SHALL check each lead against the Sent_Log for duplicates
5. WHEN a campaign is running, THE Email_Sender SHALL skip leads that exist in the Sent_Log
6. WHEN a campaign is running, THE Email_Sender SHALL generate personalized email content for each lead
7. WHEN a campaign is running, THE Email_Sender SHALL send emails via the Gmail API
8. WHEN a campaign is running, THE Email_Sender SHALL apply the configured delay between sends
9. WHEN the daily limit is reached, THE Email_Sender SHALL stop sending and mark the campaign as complete
10. WHEN a campaign completes, THE Backend SHALL update the campaign status to completed

### Requirement 4: Real-Time Progress Monitoring

**User Story:** As a user, I want to see real-time progress of email sending, so that I can monitor campaign execution.

#### Acceptance Criteria

1. WHILE a campaign is running, THE Progress_Monitor SHALL track the count of emails sent
2. WHILE a campaign is running, THE Progress_Monitor SHALL track the count of emails failed
3. WHILE a campaign is running, THE Progress_Monitor SHALL track the count of emails skipped due to duplicates
4. WHILE a campaign is running, THE Progress_Monitor SHALL track the current lead being processed
5. WHEN the Frontend requests progress updates, THE Backend SHALL return the current campaign status
6. THE Frontend SHALL poll the Backend for progress updates every 2 seconds
7. THE Frontend SHALL display the sent count, failed count, and skipped count
8. THE Frontend SHALL display the name and email of the current lead being processed
9. THE Frontend SHALL display a progress bar showing percentage completion

### Requirement 5: Email History Display

**User Story:** As a user, I want to view the history of sent emails, so that I can track my outreach efforts.

#### Acceptance Criteria

1. THE Frontend SHALL provide a view for displaying email history
2. WHEN the email history view is loaded, THE Backend SHALL read the Sent_Log
3. WHEN the email history view is loaded, THE Backend SHALL return a list of sent email addresses with timestamps
4. THE Frontend SHALL display each sent email address in a table format
5. THE Frontend SHALL display the timestamp for each sent email
6. THE Frontend SHALL display the total count of emails ever sent
7. THE Frontend SHALL support pagination when more than 50 records exist

### Requirement 6: Configuration Settings Management

**User Story:** As a user, I want to configure sending parameters, so that I can control the rate and volume of email sending.

#### Acceptance Criteria

1. THE Frontend SHALL provide input fields for daily_limit and delay_seconds
2. THE Frontend SHALL display the current values of daily_limit and delay_seconds
3. WHEN the user modifies daily_limit, THE Backend SHALL validate the value is between 1 and 500
4. WHEN the user modifies delay_seconds, THE Backend SHALL validate the value is between 10 and 300
5. IF a configuration value is invalid, THEN THE Backend SHALL return an error message with the valid range
6. WHEN valid configuration values are submitted, THE Backend SHALL update the Configuration_Settings
7. WHEN valid configuration values are submitted, THE Backend SHALL persist the settings for future sessions

### Requirement 7: Gmail API Authentication Status

**User Story:** As a user, I want to see my Gmail authentication status, so that I know if the application can send emails.

#### Acceptance Criteria

1. WHEN the Frontend loads, THE Backend SHALL check for the presence of credentials.json
2. WHEN the Frontend loads, THE Backend SHALL check for the presence of token.pickle
3. IF credentials.json is missing, THEN THE Frontend SHALL display setup instructions
4. IF token.pickle is missing, THEN THE Frontend SHALL display a button to initiate OAuth authentication
5. WHEN the OAuth button is clicked, THE Backend SHALL initiate the Gmail OAuth flow
6. WHEN OAuth authentication succeeds, THE Backend SHALL save token.pickle
7. WHEN OAuth authentication succeeds, THE Frontend SHALL display authentication status as connected
8. THE Frontend SHALL display the authenticated email address

### Requirement 8: Error Handling and User Feedback

**User Story:** As a user, I want to see clear error messages, so that I can understand and resolve issues.

#### Acceptance Criteria

1. WHEN an error occurs during CSV upload, THE Frontend SHALL display the error message
2. WHEN an error occurs during campaign execution, THE Backend SHALL log the error details
3. WHEN an error occurs during campaign execution, THE Frontend SHALL display the error message
4. WHEN Gmail API authentication fails, THE Frontend SHALL display the authentication error
5. WHEN the daily limit is reached, THE Frontend SHALL display a notification that the limit was reached
6. IF the Backend becomes unresponsive, THEN THE Frontend SHALL display a connection error message after 10 seconds

### Requirement 9: Campaign Statistics Dashboard

**User Story:** As a user, I want to see summary statistics, so that I can understand my campaign performance.

#### Acceptance Criteria

1. THE Frontend SHALL display the total number of leads uploaded
2. THE Frontend SHALL display the total number of emails sent in the current session
3. THE Frontend SHALL display the total number of emails ever sent
4. THE Frontend SHALL display the number of remaining sends before reaching the daily limit
5. WHEN a campaign completes, THE Frontend SHALL update all statistics
6. THE Frontend SHALL display the success rate as a percentage

### Requirement 10: Duplicate Prevention Verification

**User Story:** As a user, I want to ensure no duplicate emails are sent, so that I don't spam recipients.

#### Acceptance Criteria

1. WHEN a campaign starts, THE Email_Sender SHALL load the Sent_Log into memory
2. WHEN processing each lead, THE Email_Sender SHALL check if the email address exists in the Sent_Log
3. WHEN a duplicate email address is detected, THE Email_Sender SHALL skip the lead
4. WHEN a duplicate email address is detected, THE Progress_Monitor SHALL increment the skipped count
5. WHEN an email is successfully sent, THE Email_Sender SHALL add the email address to the Sent_Log
6. WHEN an email is successfully sent, THE Email_Sender SHALL persist the updated Sent_Log to disk

### Requirement 11: Campaign Control

**User Story:** As a user, I want to stop a running campaign, so that I can halt email sending if needed.

#### Acceptance Criteria

1. WHILE a campaign is running, THE Frontend SHALL display a stop button
2. WHEN the stop button is clicked, THE Backend SHALL set a stop flag
3. WHEN the stop flag is set, THE Email_Sender SHALL stop processing new leads
4. WHEN the stop flag is set, THE Email_Sender SHALL complete sending the current email
5. WHEN a campaign is stopped, THE Backend SHALL update the campaign status to stopped
6. WHEN a campaign is stopped, THE Frontend SHALL display a notification that the campaign was stopped

### Requirement 12: Lead Preview

**User Story:** As a user, I want to preview uploaded leads before sending, so that I can verify the data is correct.

#### Acceptance Criteria

1. WHEN a CSV file is uploaded, THE Frontend SHALL display a preview of the first 10 leads
2. THE Frontend SHALL display the name, email, pitch_type, and price for each previewed lead
3. THE Frontend SHALL indicate which leads are duplicates based on the Sent_Log
4. THE Frontend SHALL display the count of new leads versus duplicate leads
5. THE Frontend SHALL display the estimated campaign duration based on lead count and delay settings
