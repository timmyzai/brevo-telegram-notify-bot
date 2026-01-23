# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Brevo (formerly Sendinblue) webhook service that sends Telegram notifications for email events. It's deployed as a serverless application on AWS Lambda using Zappa.

## Common Development Commands

### Initial Setup
```bash
# Create virtual environment with Python 3.12
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies (needs to be populated in requirements.txt)
pip install flask requests python-dotenv zappa
```

### Running Locally
```bash
# Activate virtual environment
source venv/bin/activate

# Run the Flask application
python main.py
```

### Deployment
```bash
# Deploy to AWS Lambda
./deploy.sh
# Then select stage (staging/production) and action (deploy/update)
```

### Testing Webhooks Locally
```bash
# The service runs on port 6666 by default
# Test endpoint: POST http://localhost:6666/webhook
```

## Architecture

### Core Components
- **main.py**: Flask server with `/webhook` endpoint that filters events by environment tag
- **brevo_service.py**: Processes Brevo events, manages email tracking, sends Telegram notifications
- **config.py**: Loads environment variables from `.env` or AWS environment
- **initial_zappa.py**: Injects environment variables into Zappa configuration during deployment

### Environment Variables Required
- `TELEGRAM_BOT_TOKEN`: Bot authentication token
- `TELEGRAM_CHAT_ID`: Target chat ID for notifications
- `ENVIRONMENT`: Tag for filtering events (e.g., "Staging", "Production")
- `PORT`: Server port (default: 6666)

### Event Processing Flow
1. Brevo sends webhook POST to `/webhook`
2. Flask filters events by environment tag
3. BrevoService checks if email was already processed
4. If new, stores email and sends Telegram notification
5. Prevents duplicate notifications via JSON file tracking

## Important Notes

- **requirements.txt is empty**: You need to add dependencies when setting up
- Email tracking files (*.json) are created automatically in the project root
- The bot filters events by exact environment tag match (case-sensitive)
- Zappa deployment requires AWS credentials configured locally