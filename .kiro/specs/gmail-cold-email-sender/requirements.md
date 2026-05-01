# Requirements Document

## Introduction

The Gmail Cold Email Sender is a Python script that automates personalized cold email outreach via the Gmail API. The system reads lead information from CSV files, generates customized email content based on lead characteristics (pitch type and location), and sends emails while respecting rate limits and preventing duplicates.

## Glossary

- **Email_Sender**: The Python script that orchestrates the email sending process
- **Gmail_API_Client**: The component that authenticates and communicates with Gmail API
- **CSV_Reader**: The component that reads and parses lead data from CSV files
- **Email_Generator**: The component that creates personalized email content based on templates
- **Duplicate_Tracker**: The component that maintains sent_log.json to prevent duplicate sends
- **Rate_Limiter**: The component that enforces daily limits and delays between sends
- **Lead**: A potential customer record from the CSV file
- **Pitch_Type**: The type of service being offered (Website or Management Tool)
- **Location_Type**: Whether the lead is Indian (₹) or International ($)

## Requirements

### Requirement 1: CSV Data Input

**User Story:** As a user, I want to load lead data from CSV files, so that I can send personalized emails to multiple prospects.

#### Acceptance Criteria

1. THE CSV_Reader SHALL read data from files named "indian_leads_FINAL.csv" or "international_leads_part1.csv"
2. THE CSV_Reader SHALL parse columns: name, username, email, phone, category, bio, website, followerCount, pitch_type, price
3. WHEN a CSV row is missing the email field, THE CSV_Reader SHALL skip that row
4. THE CSV_Reader SHALL extract Location_Type by detecting ₹ symbol for Indian leads and $ symbol for international leads from the price column

### Requirement 2: Gmail API Authentication

**User Story:** As a user, I want to authenticate with Gmail API using OAuth2, so that I can send emails from my Gmail account.

#### Acceptance Criteria

1. THE Gmail_API_Client SHALL authenticate using OAuth2 with credentials.json file
2. THE Gmail_API_Client SHALL store authentication tokens in token.pickle file for reuse
3. IF credentials.json is missing, THEN THE Email_Sender SHALL print setup instructions and exit without error
4. WHEN token.pickle exists and is valid, THE Gmail_API_Client SHALL reuse the stored authentication
5. WHEN token.pickle is invalid or expired, THE Gmail_API_Client SHALL prompt for re-authentication via browser

### Requirement 3: Email Content Generation

**User Story:** As a user, I want emails to be personalized based on pitch type and location, so that recipients receive relevant offers.

#### Acceptance Criteria

1. WHEN pitch_type is "Website" AND Location_Type is Indian, THE Email_Generator SHALL create an email with subject "Quick question about your online presence" and price range ₹12,000-15,000
2. WHEN pitch_type is "Management Tool" AND Location_Type is Indian, THE Email_Generator SHALL create an email with subject "Are you still managing your operations manually?" and price ₹40,000+
3. WHEN pitch_type is "Website" AND Location_Type is International, THE Email_Generator SHALL create an email with subject "Your business deserves a better website" and price starting $100
4. WHEN pitch_type is "Management Tool" AND Location_Type is International, THE Email_Generator SHALL create an email with subject "Are you managing your business with spreadsheets?" and price starting $600
5. THE Email_Generator SHALL use the Lead's first name in the greeting, or "there" if name is missing
6. THE Email_Generator SHALL include project references: dental clinic, law firm, and ecommerce projects in Mumbai for all email types
7. WHERE pitch_type is "Management Tool", THE Email_Generator SHALL mention Legal Management System and Business Dashboard for Mumbai clients
8. THE Email_Generator SHALL append signature with sender name "Rishi Rohan Sawant", title "Full-Stack Developer | Mumbai", phone "+91 86938 52452", and portfolio link "https://inforishi.netlify.app"

### Requirement 4: Duplicate Prevention

**User Story:** As a user, I want to avoid sending duplicate emails to the same recipient, so that I maintain professional communication.

#### Acceptance Criteria

1. THE Duplicate_Tracker SHALL maintain a sent_log.json file containing all previously sent email addresses
2. WHEN processing a Lead, THE Duplicate_Tracker SHALL check if the email address exists in sent_log.json
3. IF the email address exists in sent_log.json, THEN THE Email_Sender SHALL skip that Lead
4. WHEN an email is successfully sent, THE Duplicate_Tracker SHALL add the email address to sent_log.json immediately
5. THE Duplicate_Tracker SHALL persist sent_log.json to disk after every successful send

### Requirement 5: Rate Limiting

**User Story:** As a user, I want to respect Gmail's sending limits, so that my account remains in good standing.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL enforce a daily limit of 50 emails per execution
2. THE Rate_Limiter SHALL be configurable via a DAILY_LIMIT variable at the top of the script
3. WHEN an email is successfully sent, THE Rate_Limiter SHALL wait 30 seconds before processing the next Lead
4. THE Rate_Limiter SHALL be configurable via a DELAY_SECONDS variable at the top of the script
5. WHEN the daily limit is reached, THE Email_Sender SHALL stop processing and display the summary

### Requirement 6: Progress Reporting

**User Story:** As a user, I want to see real-time progress of email sending, so that I can monitor the script's execution.

#### Acceptance Criteria

1. WHEN an email is successfully sent, THE Email_Sender SHALL print "[sent_count/total_count] ✅ Lead_name (email_address)"
2. WHEN an email fails to send, THE Email_Sender SHALL print "[sent_count/total_count] ❌ Lead_name (email_address) - failure_reason"
3. WHEN all processing is complete, THE Email_Sender SHALL print a summary containing: emails sent in current run, emails failed in current run, and total emails ever sent
4. THE Email_Sender SHALL display progress messages in real-time during execution

### Requirement 7: Error Handling

**User Story:** As a user, I want the script to handle errors gracefully, so that one failure doesn't stop the entire process.

#### Acceptance Criteria

1. WHEN an individual email send fails, THE Email_Sender SHALL log the error, skip that Lead, and continue processing
2. THE Email_Sender SHALL wrap all email send operations in try-except blocks
3. IF credentials.json is missing, THEN THE Email_Sender SHALL display setup instructions and exit cleanly without raising an exception
4. WHEN an error occurs, THE Email_Sender SHALL include the error reason in the progress output

### Requirement 8: Configuration Management

**User Story:** As a user, I want to easily modify script settings, so that I can adapt the behavior without editing code logic.

#### Acceptance Criteria

1. THE Email_Sender SHALL define all configuration variables at the top of the script file
2. THE Email_Sender SHALL include these configurable variables: DAILY_LIMIT, DELAY_SECONDS, sender name, sender email, sender phone, and sender portfolio URL
3. THE Email_Sender SHALL label each configuration variable with clear comments
4. THE Email_Sender SHALL use these configuration variables throughout the script instead of hardcoded values

### Requirement 9: Setup Instructions Display

**User Story:** As a user, I want clear setup instructions when credentials are missing, so that I can configure the Gmail API correctly.

#### Acceptance Criteria

1. IF credentials.json is missing, THEN THE Email_Sender SHALL print step-by-step instructions for creating OAuth credentials
2. THE Email_Sender SHALL include in instructions: Google Cloud Console URL, project creation steps, Gmail API enablement, OAuth credential creation for Desktop App, and required pip packages
3. THE Email_Sender SHALL specify that credentials should be downloaded as credentials.json
4. THE Email_Sender SHALL instruct the user to sign in with rishi.sawant2005@gmail.com during OAuth flow

### Requirement 10: Multi-File Support

**User Story:** As a user, I want to process different CSV files without code changes, so that I can handle both Indian and international leads.

#### Acceptance Criteria

1. THE Email_Sender SHALL accept CSV filename as a configurable parameter
2. THE Email_Sender SHALL work correctly with both "indian_leads_FINAL.csv" and "international_leads_part1.csv"
3. THE Email_Sender SHALL automatically detect Location_Type from the price column format regardless of filename
