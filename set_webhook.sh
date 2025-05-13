
#!/bin/bash
TOKEN=$(grep BOT_TOKEN .env | cut -d '=' -f2)
curl -X POST https://api.telegram.org/bot$TOKEN/setWebhook -d "url=https://checker.gift/telegram"
