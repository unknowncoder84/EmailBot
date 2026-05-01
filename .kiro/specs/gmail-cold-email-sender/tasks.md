# Implementation Plan: Gmail Cold Email Sender

## Overview

This implementation plan breaks down the Gmail Cold Email Sender into discrete coding tasks. The system will be built incrementally, starting with core data structures and utilities, then adding email generation logic, Gmail API integration, duplicate tracking, and finally the main orchestration logic. Each task builds on previous work to ensure a cohesive, testable implementation.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create project directory structure (email_sender.py, tests/, requirements.txt, README.md)
  - Define requirements.txt with all dependencies (google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client, hypothesis, pytest)
  - Create .gitignore to exclude credentials.json, token.pickle, sent_log.json, and CSV files
  - _Requirements: 2.1, 8.1_

- [ ] 2. Implement CSV_Reader component
  - [x] 2.1 Implement read_leads function to parse CSV files
    - Read CSV file and extract all required columns (name, username, email, phone, category, bio, website, followerCount, pitch_type, price)
    - Skip rows with missing or empty email fields
    - Return list of lead dictionaries
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 2.2 Write property test for CSV column parsing completeness
    - **Property 1: CSV Column Parsing Completeness**
    - **Validates: Requirements 1.2**

  - [x] 2.3 Write property test for email field filtering
    - **Property 2: Email Field Filtering**
    - **Validates: Requirements 1.3**

  - [x] 2.4 Implement extract_location_type function
    - Detect ₹ symbol and return "Indian"
    - Detect $ symbol and return "International"
    - _Requirements: 1.4, 10.3_

  - [x] 2.5 Write property test for location type detection
    - **Property 3: Location Type Detection**
    - **Validates: Requirements 1.4, 10.3**

- [ ] 3. Implement Email_Generator component
  - [x] 3.1 Implement get_greeting function
    - Extract first name from full name string
    - Return "there" if name is missing or empty
    - _Requirements: 3.5_

  - [x] 3.2 Write property test for greeting name extraction
    - **Property 5: Greeting Name Extraction**
    - **Validates: Requirements 3.5**

  - [x] 3.3 Implement generate_email function with all four template combinations
    - Create template for Website + Indian (subject: "Quick question about your online presence", price: ₹12,000-15,000)
    - Create template for Management Tool + Indian (subject: "Are you still managing your operations manually?", price: ₹40,000+)
    - Create template for Website + International (subject: "Your business deserves a better website", price: starting $100)
    - Create template for Management Tool + International (subject: "Are you managing your business with spreadsheets?", price: starting $600)
    - Include project references (dental clinic, law firm, ecommerce in Mumbai) in all templates
    - Include Legal Management System and Business Dashboard mentions for Management Tool templates
    - Append signature block with sender details (name, title, phone, portfolio)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6, 3.7, 3.8_

  - [x] 3.4 Write property test for email content generation correctness
    - **Property 4: Email Content Generation Correctness**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

  - [x] 3.5 Write property test for email content completeness
    - **Property 6: Email Content Completeness**
    - **Validates: Requirements 3.6, 3.7, 3.8**

- [ ] 4. Implement Duplicate_Tracker component
  - [x] 4.1 Implement load_sent_log function
    - Load sent_log.json file if it exists
    - Return empty set if file doesn't exist
    - Parse JSON array into Python set
    - _Requirements: 4.1_

  - [x] 4.2 Implement is_duplicate function
    - Check if email address exists in sent log set
    - Return boolean result
    - _Requirements: 4.2_

  - [x] 4.3 Write property test for duplicate detection
    - **Property 7: Duplicate Detection**
    - **Validates: Requirements 4.2**

  - [x] 4.4 Implement mark_as_sent function
    - Add email address to sent log set
    - Persist updated set to sent_log.json file
    - Write JSON array format
    - _Requirements: 4.4, 4.5_

- [ ] 5. Implement Rate_Limiter component
  - [x] 5.1 Implement should_continue function
    - Compare sent count against daily limit
    - Return true if under limit, false if at or over limit
    - _Requirements: 5.1_

  - [x] 5.2 Write property test for rate limit enforcement
    - **Property 8: Rate Limit Enforcement**
    - **Validates: Requirements 5.1**

  - [x] 5.3 Implement apply_delay function
    - Use time.sleep to wait specified seconds
    - _Requirements: 5.3_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement Gmail_API_Client component
  - [x] 7.1 Implement authenticate function
    - Check for credentials.json file existence
    - Load token.pickle if it exists and is valid
    - Trigger OAuth flow if token is missing or expired
    - Save refreshed token to token.pickle
    - Return authenticated Gmail API service resource
    - _Requirements: 2.1, 2.2, 2.4, 2.5_

  - [x] 7.2 Implement create_message function
    - Create MIME message with to, subject, and body
    - Encode message in base64
    - Return dictionary format for Gmail API
    - _Requirements: 2.1_

  - [x] 7.3 Implement send_email function
    - Call Gmail API service.users().messages().send()
    - Handle API errors gracefully
    - Return boolean success/failure
    - _Requirements: 2.1, 7.1, 7.2_

  - [x] 7.4 Write unit tests for Gmail_API_Client
    - Test missing credentials.json handling
    - Test MIME message creation format
    - Mock Gmail API calls for send_email
    - _Requirements: 2.3, 7.3_

- [ ] 8. Implement progress reporting and error handling utilities
  - [x] 8.1 Implement display_setup_instructions function
    - Print Google Cloud Console URL
    - Print project creation steps
    - Print Gmail API enablement instructions
    - Print OAuth credential creation steps for Desktop App
    - Print credentials.json filename specification
    - Print required pip packages
    - Print email address to use (rishi.sawant2005@gmail.com)
    - _Requirements: 2.3, 9.1, 9.2, 9.3, 9.4_

  - [x] 8.2 Write property test for setup instructions completeness
    - **Property 11: Setup Instructions Completeness**
    - **Validates: Requirements 9.2, 9.3, 9.4**

  - [x] 8.3 Implement progress message printing functions
    - Create function to print success message with format "[sent_count/total_count] ✅ Lead_name (email_address)"
    - Create function to print failure message with format "[sent_count/total_count] ❌ Lead_name (email_address) - failure_reason"
    - _Requirements: 6.1, 6.2, 6.4_

  - [x] 8.4 Write property test for progress message formatting
    - **Property 9: Progress Message Formatting**
    - **Validates: Requirements 6.1, 6.2**

  - [x] 8.5 Implement summary statistics printing function
    - Print emails sent in current run
    - Print emails failed in current run
    - Print total emails ever sent (from sent_log.json size)
    - _Requirements: 6.3_

  - [x] 8.6 Write property test for summary statistics formatting
    - **Property 10: Summary Statistics Formatting**
    - **Validates: Requirements 6.3**

- [ ] 9. Implement main orchestration logic
  - [x] 9.1 Define configuration constants at module level
    - DAILY_LIMIT = 50
    - DELAY_SECONDS = 30
    - SENDER_NAME = "Rishi Rohan Sawant"
    - SENDER_EMAIL = "rishi.sawant2005@gmail.com"
    - SENDER_PHONE = "+91 86938 52452"
    - SENDER_PORTFOLIO = "https://inforishi.netlify.app"
    - CSV_FILENAME = "indian_leads_FINAL.csv"
    - Add clear comments for each configuration variable
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 9.2 Implement main function initialization phase
    - Check for credentials.json existence
    - If missing, call display_setup_instructions and exit cleanly
    - Call authenticate to get Gmail API service
    - Call load_sent_log to get sent email set
    - Call read_leads to parse CSV file
    - Initialize counters (sent_count, failed_count)
    - _Requirements: 2.3, 4.1, 1.1, 7.3_

  - [x] 9.3 Implement main function processing loop
    - Iterate through each lead from CSV
    - Extract location_type using extract_location_type
    - Check for duplicate using is_duplicate, skip if duplicate
    - Generate email content using generate_email
    - Wrap send_email call in try-except block
    - On success: call mark_as_sent, print success message, increment sent_count, apply delay
    - On failure: print failure message with error reason, increment failed_count, continue to next lead
    - Check should_continue after each send, break if daily limit reached
    - _Requirements: 1.4, 4.2, 4.3, 3.1, 7.1, 7.2, 4.4, 6.1, 6.2, 5.3, 5.1, 5.5_

  - [x] 9.4 Implement main function completion phase
    - Print summary statistics (sent_count, failed_count, total ever sent)
    - Exit cleanly
    - _Requirements: 6.3_

- [x] 10. Final checkpoint and integration verification
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Write integration tests
  - Test end-to-end flow with mock Gmail API
  - Test CSV file reading with actual test CSV files
  - Test sent_log.json persistence across multiple runs
  - Test duplicate prevention by running twice with same leads
  - Test rate limiting with mock time.sleep
  - _Requirements: 1.1, 4.5, 5.3_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end behavior with external services
- The main function is broken into three phases (initialization, processing, completion) for clarity
- All error handling follows the fail-safe principle: individual failures don't halt the batch process
