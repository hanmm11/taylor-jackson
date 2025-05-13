
import os
import logging
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters
import aiohttp

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = "/telegram"
WEBHOOK_PORT = 8443
WEBHOOK_URL = f"https://checker.gift{WEBHOOK_PATH}"
ADMIN_IDS = [6538167049]
API_BASE = "http://bot_web:5000/api"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_api(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.json()
            return ["接口请求失败"]

# 命令函数
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    url = f"{API_BASE}/history/{cid}?admin_id={update.effective_user.id}"
    result = await fetch_api(url)
    await update.message.reply_text("\n".join(result))

async def history_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        uid = context.args[0]
        url = f"{API_BASE}/history/user/{uid}?admin_id={update.effective_user.id}"
        result = await fetch_api(url)
        await update.message.reply_text("\n".join(result))

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    url = f"{API_BASE}/listusers/{cid}?admin_id={update.effective_user.id}"
    result = await fetch_api(url)
    await update.message.reply_text("用户列表：\n" + "\n".join(result))

async def bot_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    url = f"{API_BASE}/botmessages/{cid}?admin_id={update.effective_user.id}"
    result = await fetch_api(url)
    await update.message.reply_text("Bot 消息：\n" + "\n".join(result))

async def bot_messages_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        uid = context.args[0]
        url = f"{API_BASE}/botmessages/user/{uid}?admin_id={update.effective_user.id}"
        result = await fetch_api(url)
        await update.message.reply_text("Bot 发给该用户的消息：\n" + "\n".join(result))

# 权限装饰器
def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if uid in ADMIN_IDS:
            return await func(update, context)
        await update.message.reply_text("无权限，仅限管理员")
    return wrapper

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Message: {update.message.text}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("history", admin_only(history)))
    app.add_handler(CommandHandler("historyuser", admin_only(history_user)))
    app.add_handler(CommandHandler("listusers", admin_only(list_users)))
    app.add_handler(CommandHandler("botmessages", admin_only(bot_messages)))
    app.add_handler(CommandHandler("botmessagesuser", admin_only(bot_messages_user)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    await app.bot.set_webhook(url=WEBHOOK_URL)

    runner = web.AppRunner(app.web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    logger.info(f"Bot webhook running at {WEBHOOK_URL}")
    await site.start()
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
