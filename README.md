
# Telegram Bot with Webhook + Flask 控制台

## 功能
- 支持群组/私聊消息监听
- 自动记录、搜索、导出聊天内容
- 提供 Web 控制台（Flask）
- Webhook 模式监听 Telegram
- Docker 一键部署 + Nginx + HTTPS + Certbot

## 快速启动
```bash
cp .env.example .env
# 编辑 .env 填入你的 BOT_TOKEN
docker compose up -d --build
```

## 设置 webhook
```bash
chmod +x set_webhook.sh
./set_webhook.sh
```

## 访问路径
- Web 控制台：https://checker.gift
- Webhook 接收端：https://checker.gift/telegram
