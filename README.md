# EmailBot

A Flask-based web application for managing Gmail cold email campaigns with custom templates, duplicate tracking, and real-time progress monitoring.

## Features

- 📧 **Email Templates** - Create and manage custom email templates with variable placeholders
- 📊 **Real-time Dashboard** - Monitor campaign progress with live statistics
- 📂 **CSV Upload** - Drag & drop lead files with duplicate detection
- 📜 **Email History** - Track all sent emails with pagination
- ⚙️ **Configurable Settings** - Adjust daily limits and sending delays
- 🔐 **Gmail OAuth** - Secure authentication with Gmail API
- 🎯 **Smart Duplicate Prevention** - Never send to the same email twice

## Setup

### Prerequisites

- Python 3.7+
- Gmail API credentials (credentials.json)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/unknowncoder84/EmailBot.git
cd EmailBot
```

2. Install dependencies:
```bash
pip install flask flask-cors google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

3. Add your Gmail API credentials:
   - Place `credentials.json` in the project root
   - Run the app and authenticate via the Settings tab

### Running the Application

```bash
python app.py
```

Open your browser and navigate to: **http://localhost:3000**

## Usage

1. **Email Templates** - Create custom email templates with placeholders like `{name}`, `{sender_name}`, etc.
2. **Upload Leads** - Upload a CSV file with columns: name, email, pitch_type, price, etc.
3. **Start Campaign** - Click "Start Campaign" on the dashboard to begin sending
4. **Monitor Progress** - Watch real-time statistics and progress bar
5. **View History** - Check all sent emails in the History tab

## CSV Format

Your CSV file should include these columns:
- `name` - Recipient's full name
- `email` - Recipient's email address (required)
- `pitch_type` - Type of pitch (e.g., Website, Management Tool)
- `price` - Price with currency symbol (₹ or $)
- Other columns: username, phone, category, bio, website, followerCount

## Configuration

- **Daily Limit**: Maximum emails per campaign (1-500)
- **Delay**: Seconds between each email (10-300)
- **Templates**: Manage email templates in the Email Templates tab

## Project Structure

```
EmailBot/
├── app.py                  # Flask web server
├── campaign_manager.py     # Campaign state management
├── email_adapter.py        # Email sending adapter
├── email_sender.py         # Core email logic
├── template_manager.py     # Template management
├── config_manager.py       # Configuration persistence
├── templates/
│   └── index.html         # Web UI
├── static/
│   ├── css/styles.css     # Styling
│   └── js/app.js          # Frontend logic
└── test_leads.csv         # Sample CSV file
```

## License

MIT License

## Author

Rishi Rohan Sawant
