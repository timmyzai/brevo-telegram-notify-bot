# Brevo Telegram Notify Bot

A serverless webhook service that monitors Brevo (formerly Sendinblue) email events and sends real-time notifications to Telegram. Perfect for teams that need instant visibility into email delivery performance.

## Features

- 📧 **Real-time Email Event Monitoring** - Track delivered, bounced, blocked, and spam emails
- 🔔 **Instant Telegram Notifications** - Get notified immediately when email events occur
- 🏷️ **Environment-based Filtering** - Separate notifications for staging and production
- 🚫 **Duplicate Prevention** - Smart tracking ensures each event is notified only once
- ⚡ **Serverless Architecture** - Runs on AWS Lambda for high availability and low cost
- 🔒 **Secure** - Environment variables for sensitive data, no email content exposed

## Supported Email Events

- ✅ **Delivered** & **Sent**
- ❌ **Hard Bounce** & **Soft Bounce**
- 🚫 **Blocked** & **Spam**
- ⚠️ **Invalid** & **Deferred**
- 📧 **Unsubscribed**
- 📖 **Opened** & **Clicked**

## Prerequisites

- Python 3.12
- AWS Account with configured credentials
- Telegram Bot Token (create via [@BotFather](https://t.me/botfather))
- Brevo Account with webhook access

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/brevo-telegram-notify-bot.git
cd brevo-telegram-notify-bot
```

### 2. Set Up Python Environment
```bash
# Install Python 3.12 (macOS)
brew install python@3.12

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask requests python-dotenv zappa
pip freeze > requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the project root:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
ENVIRONMENT=Production
PORT=6666
```

### 4. Configure Brevo Webhook
In your Brevo account:
1. Go to Transactional → Settings → Webhooks
2. Add webhook URL: `https://your-lambda-url/webhook`
3. Select events you want to monitor
4. Save and test

## Local Development

### Run the Server
```bash
python main.py
```
The server will start on `http://localhost:6666`

### Test Webhook Endpoint
```bash
curl -X POST http://localhost:6666/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event": "delivered",
    "email": "test@example.com",
    "subject": "Test Email",
    "tag": "Production"
  }'
```

## Deployment to AWS Lambda

### First-time Setup
```bash
# Configure AWS credentials
aws configure

# Initialize Zappa (only needed once)
zappa init
```

### Deploy Using Script
```bash
./deploy.sh
```
Then:
1. Select deployment stage: `staging` or `production`
2. Select action: `deploy` (first time) or `update` (subsequent deployments)

### Manual Deployment
```bash
# Inject environment variables
python initial_zappa.py production

# Deploy to AWS
zappa deploy production  # First deployment
# OR
zappa update production  # Update existing deployment

# Clean up
rm zappa_settings.json
```

## Configuration

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot authentication token | Yes |
| `TELEGRAM_CHAT_ID` | Target chat for notifications | Yes |
| `ENVIRONMENT` | Environment tag filter | Yes |
| `PORT` | Server port (default: 6666) | No |

### Zappa Settings
The `zappa_settings.template.json` provides the base configuration:
- Runtime: Python 3.12
- AWS Region: ap-southeast-1
- Memory: 128MB
- Timeout: 30 seconds

## How It Works

1. **Brevo sends webhook** → Your Lambda function receives POST request
2. **Filter by environment** → Only process events matching your environment tag
3. **Check if processed** → Prevent duplicate notifications using local JSON tracking
4. **Send to Telegram** → Format and send notification with event details
5. **Store for tracking** → Save email to prevent future duplicates

## Notification Format

```
📧 Email Delivered

Email: user@example.com
Subject: Welcome to our service
Time: 2024-01-15 10:30:45
Environment: Production
```

## Troubleshooting

### Common Issues

**Webhook not receiving events**
- Verify webhook URL in Brevo settings
- Check AWS Lambda logs: `zappa tail production`
- Ensure environment tag matches exactly (case-sensitive)

**Telegram notifications not sending**
- Verify bot token is correct
- Ensure bot has permission to send to chat ID
- Check if chat ID is correct (use [@userinfobot](https://t.me/userinfobot))

**Duplicate notifications**
- Check if JSON tracking files have write permissions
- Ensure Lambda has sufficient storage for tracking files

### Useful Commands

```bash
# View Lambda logs
zappa tail production

# Check deployment status
zappa status production

# Undeploy
zappa undeploy production

# Update Python packages
pip install --upgrade package-name
pip freeze > requirements.txt
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Brevo](https://www.brevo.com/) for their excellent email API
- [Zappa](https://github.com/zappa/Zappa) for seamless serverless deployment
- [python-telegram-bot](https://python-telegram-bot.org/) community for inspiration