from flask import Flask, render_template, request, send_file, jsonify, abort
from db import SessionLocal, MessageRecord
from sqlalchemy import func
from io import StringIO
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
import csv
import math

app = Flask(__name__)
auth = HTTPBasicAuth()
PAGE_SIZE = 20
ADMIN_IDS = ["6538167049"]

users = {
    "admin": generate_password_hash("securepassword")
}

@auth.verify_password
def verify(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

@app.route('/')
@auth.login_required
def index():
    session = SessionLocal()
    groups = session.query(MessageRecord.chat_id, MessageRecord.chat_title).filter(
        MessageRecord.chat_type.in_(["group", "supergroup"])
    ).distinct().all()
    users_list = session.query(MessageRecord.user_id, MessageRecord.sender).filter(
        MessageRecord.chat_type == "private"
    ).distinct().all()
    session.close()
    return render_template("index.html", groups=groups, users=users_list)

@app.route('/messages/<chat_id>')
@auth.login_required
def messages(chat_id):
    page = int(request.args.get("page", 1))
    session = SessionLocal()
    total = session.query(MessageRecord).filter_by(chat_id=chat_id).count()
    messages = session.query(MessageRecord).filter_by(chat_id=chat_id).order_by(
        MessageRecord.date.desc()
    ).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()
    session.close()
    total_pages = math.ceil(total / PAGE_SIZE)
    return render_template("messages.html", chat_id=chat_id, messages=messages, page=page, total_pages=total_pages)

@app.route('/search')
@auth.login_required
def search():
    query = request.args.get("q", "")
    chat_id = request.args.get("chat_id")
    session = SessionLocal()
    q = session.query(MessageRecord).filter(MessageRecord.text.ilike(f"%{query}%"))
    if chat_id:
        q = q.filter(MessageRecord.chat_id == chat_id)
    results = q.order_by(MessageRecord.date.desc()).limit(100).all()
    session.close()
    return render_template("search.html", query=query, results=results, chat_id=chat_id)

@app.route('/user/<user_id>')
@auth.login_required
def user_detail(user_id):
    session = SessionLocal()
    messages = session.query(MessageRecord).filter_by(user_id=user_id).order_by(MessageRecord.date.desc()).limit(100).all()
    groups = session.query(MessageRecord.chat_id, MessageRecord.chat_title).filter_by(user_id=user_id).distinct().all()
    session.close()
    return render_template("user.html", user_id=user_id, messages=messages, groups=groups)

@app.route('/export/<chat_id>.<ext>')
@auth.login_required
def export(chat_id, ext):
    session = SessionLocal()
    messages = session.query(MessageRecord).filter_by(chat_id=chat_id).order_by(MessageRecord.date.asc()).all()
    session.close()
    if ext == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Sender", "Text"])
        for m in messages:
            writer.writerow([m.date, m.sender, m.text])
        output.seek(0)
        return send_file(output, mimetype='text/csv', download_name=f"chat_{chat_id}.csv", as_attachment=True)
    elif ext == "txt":
        lines = [f"[{m.date}] {m.sender}: {m.text}" for m in messages]
        output = StringIO("\n".join(lines))
        return send_file(output, mimetype='text/plain', download_name=f"chat_{chat_id}.txt", as_attachment=True)
    elif ext == "json":
        result = [{"date": str(m.date), "sender": m.sender, "text": m.text} for m in messages]
        return jsonify(result)
    return "Unsupported format", 400

@app.route('/stats')
@auth.login_required
def stats():
    session = SessionLocal()
    keywords = session.query(MessageRecord.text).filter(MessageRecord.source == "user").all()
    word_count = {}
    for t in keywords:
        for word in t.text.split():
            word = word.lower()
            word_count[word] = word_count.get(word, 0) + 1
    top_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:30]
    session.close()
    return render_template("stats.html", top_words=top_words)

# API 安全校验
def require_admin():
    telegram_id = request.args.get("admin_id")
    if telegram_id not in ADMIN_IDS:
        abort(403)

@app.route('/api/history/<chat_id>')
def api_history(chat_id):
    require_admin()
    session = SessionLocal()
    messages = session.query(MessageRecord).filter_by(chat_id=chat_id).order_by(MessageRecord.date.desc()).limit(10).all()
    session.close()
    return jsonify([f"[{m.date}] {m.sender}: {m.text}" for m in messages])

@app.route('/api/history/user/<user_id>')
def api_history_user(user_id):
    require_admin()
    session = SessionLocal()
    messages = session.query(MessageRecord).filter_by(user_id=user_id).order_by(MessageRecord.date.desc()).limit(10).all()
    session.close()
    return jsonify([f"[{m.date}] {m.sender}: {m.text}" for m in messages])

@app.route('/api/listusers/<chat_id>')
def api_list_users(chat_id):
    require_admin()
    session = SessionLocal()
    users = session.query(MessageRecord.user_id, MessageRecord.sender).filter_by(chat_id=chat_id).distinct().all()
    session.close()
    return jsonify([f"{u[1]} ({u[0]})" for u in users])

@app.route('/api/botmessages/<chat_id>')
def api_bot_messages(chat_id):
    require_admin()
    session = SessionLocal()
    messages = session.query(MessageRecord).filter_by(chat_id=chat_id, source="bot").order_by(MessageRecord.date.desc()).limit(10).all()
    session.close()
    return jsonify([f"[{m.date}] Bot: {m.text}" for m in messages])

@app.route('/api/botmessages/user/<user_id>')
def api_bot_messages_user(user_id):
    require_admin()
    session = SessionLocal()
    messages = session.query(MessageRecord).filter_by(related_user_id=user_id).order_by(MessageRecord.date.desc()).limit(10).all()
    session.close()
    return jsonify([f"[{m.date}] Bot: {m.text}" for m in messages])

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
