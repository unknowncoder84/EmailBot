#!/usr/bin/env python3
"""
Gmail Cold Email Sender

Automates personalized cold email outreach via Gmail API.
Reads lead data from CSV files, generates customized emails, and sends them
while respecting rate limits and preventing duplicates.
"""

import csv
import json
import os
import pickle
from typing import List, Dict, Set, Tuple

# Configuration Constants
DAILY_LIMIT = 50  # Maximum emails to send per execution
DELAY_SECONDS = 30  # Delay between email sends (in seconds)
SENDER_NAME = "Rishi Rohan Sawant"
SENDER_EMAIL = "rishi.sawant2005@gmail.com"
SENDER_PHONE = "+91 86938 52452"
SENDER_PORTFOLIO = "https://inforishi.netlify.app"
CSV_FILENAME = "indian_leads_FINAL.csv"  # or "international_leads_part1.csv"


# CSV_Reader Component
def read_leads(filename: str) -> List[Dict[str, str]]:
    """
    Read and parse CSV file containing lead data
    
    Args:
        filename: Path to CSV file
        
    Returns:
        List of lead dictionaries with keys: name, username, email, phone,
        category, bio, website, followerCount, pitch_type, price
        
    Skips rows with missing email field
    """
    leads = []
    
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Skip rows with missing or empty email field
            if not row.get('email') or not row.get('email').strip():
                continue
            
            # Extract all required columns
            lead = {
                'name': row.get('name', ''),
                'username': row.get('username', ''),
                'email': row.get('email', ''),
                'phone': row.get('phone', ''),
                'category': row.get('category', ''),
                'bio': row.get('bio', ''),
                'website': row.get('website', ''),
                'followerCount': row.get('followerCount', ''),
                'pitch_type': row.get('pitch_type', ''),
                'price': row.get('price', '')
            }
            
            leads.append(lead)
    
    return leads


def extract_location_type(price: str) -> str:
    """
    Determine location type from price column
    
    Args:
        price: Price string containing ₹ or $ symbol
        
    Returns:
        "Indian" if ₹ symbol present, "International" if $ symbol present
    """
    if '₹' in price:
        return "Indian"
    elif '$' in price:
        return "International"
    else:
        # Default to International if no currency symbol found
        return "International"


# Email_Generator Component
def get_greeting(name: str) -> str:
    """
    Extract first name for greeting, or return "there" if name is missing
    
    Args:
        name: Full name from lead data
        
    Returns:
        First name or "there"
    """
    # Handle None, empty string, or whitespace-only names
    if not name or not name.strip():
        return "there"
    
    # Extract first name (first word before any space)
    first_name = name.strip().split()[0]
    
    # Return "there" if first name is empty after extraction
    if not first_name:
        return "there"
    
    return first_name


def generate_email(lead: Dict[str, str], location_type: str) -> tuple:
    """
    Generate personalized email subject and body
    
    Args:
        lead: Dictionary containing lead data (name, pitch_type, etc.)
        location_type: "Indian" or "International"
        
    Returns:
        Tuple of (subject, body)
    """
    pitch_type = lead.get('pitch_type', '')
    greeting = get_greeting(lead.get('name', ''))
    
    # Determine subject and price based on pitch_type and location_type
    if pitch_type == "Website" and location_type == "Indian":
        subject = "Quick question about your online presence"
        price_info = "₹12,000-15,000"
        service_description = "a professional website"
        
    elif pitch_type == "Management Tool" and location_type == "Indian":
        subject = "Are you still managing your operations manually?"
        price_info = "₹40,000+"
        service_description = "a custom management system"
        
    elif pitch_type == "Website" and location_type == "International":
        subject = "Your business deserves a better website"
        price_info = "starting $100"
        service_description = "a professional website"
        
    elif pitch_type == "Management Tool" and location_type == "International":
        subject = "Are you managing your business with spreadsheets?"
        price_info = "starting $600"
        service_description = "a custom management system"
        
    else:
        # Default fallback (should not happen with valid data)
        subject = "Quick question about your business"
        price_info = "competitive rates"
        service_description = "a custom solution"
    
    # Build email body
    body = f"Hi {greeting},\n\n"
    
    # Main pitch content
    if pitch_type == "Website":
        body += f"I noticed your business and wanted to reach out. I'm a full-stack developer based in Mumbai, and I specialize in building {service_description}s that help businesses grow their online presence.\n\n"
        body += "I've recently completed projects for:\n"
        body += "- A dental clinic in Mumbai (modern booking system and patient portal)\n"
        body += "- A law firm in Mumbai (professional website with case management features)\n"
        body += "- An ecommerce business in Mumbai (full online store with payment integration)\n\n"
        body += f"I'd love to discuss how I can help your business with {service_description}. My rates start at {price_info}.\n\n"
        
    elif pitch_type == "Management Tool":
        body += f"I noticed your business and wanted to reach out. I'm a full-stack developer based in Mumbai, and I specialize in building {service_description}s that streamline operations and eliminate manual processes.\n\n"
        body += "I've recently completed projects for:\n"
        body += "- A dental clinic in Mumbai (modern booking system and patient portal)\n"
        body += "- A law firm in Mumbai (Legal Management System for case tracking and client management)\n"
        body += "- An ecommerce business in Mumbai (Business Dashboard for inventory and order management)\n\n"
        body += f"I'd love to discuss how I can help automate your business operations with {service_description}. My rates start at {price_info}.\n\n"
    
    else:
        # Default fallback content
        body += f"I noticed your business and wanted to reach out. I'm a full-stack developer based in Mumbai, and I specialize in building custom solutions for businesses.\n\n"
        body += "I've recently completed projects for:\n"
        body += "- A dental clinic in Mumbai\n"
        body += "- A law firm in Mumbai\n"
        body += "- An ecommerce business in Mumbai\n\n"
        body += f"I'd love to discuss how I can help your business. My rates are {price_info}.\n\n"
    
    # Signature block
    body += "Best regards,\n"
    body += f"{SENDER_NAME}\n"
    body += "Full-Stack Developer | Mumbai\n"
    body += f"Phone: {SENDER_PHONE}\n"
    body += f"Portfolio: {SENDER_PORTFOLIO}\n"
    
    return (subject, body)


# Duplicate_Tracker Component
def load_sent_log() -> Set[str]:
    """
    Load sent email addresses from sent_log.json
    
    Returns:
        Set of email addresses that have been sent to
    """
    sent_log_file = "sent_log.json"
    
    # Check if file exists
    if not os.path.exists(sent_log_file):
        return set()
    
    try:
        # Read and parse JSON file
        with open(sent_log_file, 'r', encoding='utf-8') as f:
            email_list = json.load(f)
            
        # Convert list to set
        if isinstance(email_list, list):
            return set(email_list)
        else:
            # If file format is unexpected, return empty set
            return set()
            
    except (json.JSONDecodeError, IOError):
        # If file is corrupted or unreadable, return empty set
        return set()


def is_duplicate(email: str, sent_log: Set[str]) -> bool:
    """
    Check if email address has already been sent to
    
    Args:
        email: Email address to check
        sent_log: Set of previously sent email addresses
        
    Returns:
        True if duplicate, False otherwise
    """
    return email in sent_log


def mark_as_sent(email: str, sent_log: Set[str]) -> None:
    """
    Add email address to sent log and persist to disk
    
    Args:
        email: Email address to mark as sent
        sent_log: Set of sent email addresses (modified in place)
        
    Side effects:
        Updates sent_log.json file
    """
    sent_log_file = "sent_log.json"
    
    # Add email to the set (modifies in place)
    sent_log.add(email)
    
    # Convert set to list for JSON serialization
    email_list = list(sent_log)
    
    # Write to file in JSON array format
    with open(sent_log_file, 'w', encoding='utf-8') as f:
        json.dump(email_list, f, indent=2)


# Rate_Limiter Component
def should_continue(sent_count: int, daily_limit: int) -> bool:
    """
    Check if daily limit has been reached
    
    Args:
        sent_count: Number of emails sent in current run
        daily_limit: Maximum emails per run
        
    Returns:
        True if can continue sending, False if limit reached
    """
    return sent_count < daily_limit


def apply_delay(delay_seconds: int) -> None:
    """
    Wait between email sends
    
    Args:
        delay_seconds: Number of seconds to wait
    """
    import time
    time.sleep(delay_seconds)


# Gmail_API_Client Component
def authenticate():
    """
    Authenticate with Gmail API using OAuth2
    
    Returns:
        Gmail API service resource
        
    Raises:
        FileNotFoundError: If credentials.json is missing
    """
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    
    # Gmail API scope for sending emails
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        raise FileNotFoundError("credentials.json not found")
    
    creds = None
    
    # Load token.pickle if it exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh the expired token
            creds.refresh(Request())
        else:
            # Trigger OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    # Build and return the Gmail API service
    service = build('gmail', 'v1', credentials=creds)
    return service


def create_message(to: str, subject: str, body: str) -> Dict:
    """
    Create a MIME message for Gmail API
    
    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content
        
    Returns:
        Dictionary with base64-encoded message
    """
    from email.mime.text import MIMEText
    import base64
    
    # Create MIME message
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    
    # Encode message in base64
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    # Return dictionary format for Gmail API
    return {'raw': raw_message}


def send_email(service, to: str, subject: str, body: str) -> bool:
    """
    Send an email via Gmail API
    
    Args:
        service: Authenticated Gmail API service
        to: Recipient email address
        subject: Email subject line
        body: Email body content (plain text)
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Create the message
        message = create_message(to, subject, body)
        
        # Send the message
        service.users().messages().send(userId='me', body=message).execute()
        
        return True
    except Exception as e:
        # Log error and return False
        print(f"Error sending email: {e}")
        return False


def display_setup_instructions():
    """
    Print OAuth setup instructions when credentials.json is missing
    
    Displays step-by-step instructions for:
    - Creating a Google Cloud project
    - Enabling Gmail API
    - Creating OAuth credentials
    - Downloading credentials.json
    - Installing required packages
    """
    print("\n" + "=" * 70)
    print("SETUP REQUIRED: credentials.json not found")
    print("=" * 70)
    print("\nTo use this script, you need to set up Gmail API credentials.")
    print("Follow these steps:\n")
    
    print("1. Go to Google Cloud Console:")
    print("   https://console.cloud.google.com/")
    print()
    
    print("2. Create a new project:")
    print("   - Click 'Select a project' at the top")
    print("   - Click 'New Project'")
    print("   - Enter a project name (e.g., 'Gmail Cold Email Sender')")
    print("   - Click 'Create'")
    print()
    
    print("3. Enable Gmail API:")
    print("   - In the search bar, type 'Gmail API'")
    print("   - Click on 'Gmail API' in the results")
    print("   - Click 'Enable'")
    print()
    
    print("4. Create OAuth credentials:")
    print("   - Go to 'Credentials' in the left sidebar")
    print("   - Click 'Create Credentials' at the top")
    print("   - Select 'OAuth client ID'")
    print("   - If prompted, configure the OAuth consent screen:")
    print("     * Select 'External' user type")
    print("     * Fill in app name and your email")
    print("     * Add rishi.sawant2005@gmail.com as a test user")
    print("   - For 'Application type', select 'Desktop app'")
    print("   - Enter a name (e.g., 'Gmail Email Sender')")
    print("   - Click 'Create'")
    print()
    
    print("5. Download credentials:")
    print("   - Click the download icon next to your newly created OAuth client")
    print("   - Save the file as 'credentials.json' in this directory")
    print()
    
    print("6. Install required packages (if not already installed):")
    print("   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    print()
    
    print("7. Sign in with the correct account:")
    print("   - When you run this script, it will open a browser")
    print("   - Sign in with: rishi.sawant2005@gmail.com")
    print("   - Grant the requested permissions")
    print()
    
    print("=" * 70)
    print("Once you've completed these steps, run this script again.")
    print("=" * 70 + "\n")


def print_success_message(lead: Dict[str, str], sent_count: int, total_count: int):
    """
    Print success message for sent email
    
    Args:
        lead: Lead dictionary containing name and email
        sent_count: Number of emails sent so far
        total_count: Total number of leads to process
    """
    name = lead.get('name', 'Unknown')
    if not name or not name.strip():
        name = 'Unknown'
    email = lead.get('email', 'unknown@example.com')
    print(f"[{sent_count}/{total_count}] ✅ {name} ({email})")


def print_failure_message(lead: Dict[str, str], sent_count: int, total_count: int, failure_reason: str):
    """
    Print failure message for failed email
    
    Args:
        lead: Lead dictionary containing name and email
        sent_count: Number of emails sent so far (includes failed attempts)
        total_count: Total number of leads to process
        failure_reason: Reason for failure
    """
    name = lead.get('name', 'Unknown')
    if not name or not name.strip():
        name = 'Unknown'
    email = lead.get('email', 'unknown@example.com')
    print(f"[{sent_count}/{total_count}] ❌ {name} ({email}) - {failure_reason}")


def print_summary_statistics(sent_current_run: int, failed_current_run: int, total_ever_sent: int):
    """
    Print summary statistics at the end of execution
    
    Args:
        sent_current_run: Number of emails successfully sent in current run
        failed_current_run: Number of emails that failed in current run
        total_ever_sent: Total number of emails ever sent (from sent_log.json)
    """
    print("\n" + "=" * 70)
    print("EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Emails sent in current run: {sent_current_run}")
    print(f"Emails failed in current run: {failed_current_run}")
    print(f"Total emails ever sent: {total_ever_sent}")
    print("=" * 70 + "\n")


def main():
    """Main entry point for the email sender script"""
    print("Gmail Cold Email Sender")
    print("=" * 50)
    
    # ===== INITIALIZATION PHASE =====
    
    # Check for credentials.json existence
    if not os.path.exists('credentials.json'):
        display_setup_instructions()
        return  # Exit cleanly without error
    
    # Authenticate with Gmail API
    try:
        service = authenticate()
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return
    
    # Load sent log for duplicate tracking
    sent_log = load_sent_log()
    
    # Read leads from CSV file
    try:
        leads = read_leads(CSV_FILENAME)
    except FileNotFoundError:
        print(f"\n❌ Error: CSV file '{CSV_FILENAME}' not found")
        return
    except Exception as e:
        print(f"\n❌ Error reading CSV file: {e}")
        return
    
    # Initialize counters
    sent_count = 0
    failed_count = 0
    total_leads = len(leads)
    
    print(f"\nLoaded {total_leads} leads from {CSV_FILENAME}")
    print(f"Already sent to {len(sent_log)} recipients")
    print(f"Daily limit: {DAILY_LIMIT} emails\n")
    
    # ===== PROCESSING LOOP =====
    
    for lead in leads:
        email = lead.get('email', '')
        
        # Check for duplicate
        if is_duplicate(email, sent_log):
            continue  # Skip duplicate, don't count as processed
        
        # Extract location type from price
        location_type = extract_location_type(lead.get('price', ''))
        
        # Generate email content
        subject, body = generate_email(lead, location_type)
        
        # Attempt to send email
        try:
            success = send_email(service, email, subject, body)
            
            if success:
                # Mark as sent and update log
                mark_as_sent(email, sent_log)
                
                # Print success message
                sent_count += 1
                print_success_message(lead, sent_count, total_leads)
                
                # Check if daily limit reached
                if not should_continue(sent_count, DAILY_LIMIT):
                    print(f"\n⚠️  Daily limit of {DAILY_LIMIT} emails reached. Stopping.")
                    break
                
                # Apply delay before next send
                apply_delay(DELAY_SECONDS)
            else:
                # Send failed
                failed_count += 1
                print_failure_message(lead, sent_count + failed_count, total_leads, "Send failed")
                
        except Exception as e:
            # Handle any unexpected errors during send
            failed_count += 1
            print_failure_message(lead, sent_count + failed_count, total_leads, str(e))
            continue  # Continue to next lead
    
    # ===== COMPLETION PHASE =====
    
    # Print summary statistics
    total_ever_sent = len(sent_log)
    print_summary_statistics(sent_count, failed_count, total_ever_sent)


if __name__ == "__main__":
    main()
