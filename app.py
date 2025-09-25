from flask import Flask, request, jsonify, render_template_string, send_from_directory
from datetime import datetime
from uuid import uuid4
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# ---------------- In-memory storage ----------------
users = {}       # phone -> {id, phone, verified}
messages = []    # [{id, user_id, text, ts}]
admin_webhook = os.getenv("ADMIN_WEBHOOK")  # optional webhook URL

def notify_admin(payload):
    if not admin_webhook:
        return
    try:
        import requests
        requests.post(admin_webhook, json=payload, timeout=3)
    except Exception:
        pass

# ---------------- API ----------------
@app.post("/api/register")
def register():
    data = request.get_json(force=True)
    phone = (data.get("phone") or "").strip()
    if not phone:
        return jsonify(error="phone_required"), 400
    user = users.get(phone)
    if not user:
        user = {"id": str(uuid4()), "phone": phone, "verified": False}
        users[phone] = user
        notify_admin({"type": "registration", "phone": phone, "ts": datetime.utcnow().isoformat()})
    code = "1111"  # автокод
    return jsonify(message="code_sent", code=code, user_id=user["id"])

@app.post("/api/verify")
def verify():
    data = request.get_json(force=True)
    phone = (data.get("phone") or "").strip()
    code = (data.get("code") or "").strip()
    user = users.get(phone)
    if not user:
        return jsonify(error="not_registered"), 404
    if code != "1111":
        return jsonify(error="invalid_code"), 400
    user["verified"] = True
    token = f"tok_{user['id']}"
    return jsonify(ok=True, token=token, user_id=user["id"])

@app.get("/api/messages")
def get_messages():
    return jsonify(messages=messages[-200:])

@app.post("/api/messages")
def post_message():
    data = request.get_json(force=True)
    token = data.get("token")
    text = (data.get("text") or "").strip()
    if not token or not text:
        return jsonify(error="bad_request"), 400
    user_id = token.replace("tok_", "")
    if not any(u["id"] == user_id and u["verified"] for u in users.values()):
        return jsonify(error="unauthorized"), 401
    msg = {"id": str(uuid4()), "user_id": user_id, "text": text[:2000], "ts": datetime.utcnow().isoformat()}
    messages.append(msg)
    return jsonify(ok=True, message=msg)

# ---------------- Shared CSS ----------------
CSS = """
:root {
  --bg-start: #1a0000; --bg-end: #5a0f0f;
  --text: #ff4444; --muted: #b33a3a; --error: #ff1a1a;
  --button-bg: #2a0000; --button-border: #aa2b2b;
}
html, body {
  height: 100%; margin: 0;
  background: linear-gradient(180deg, var(--bg-start), var(--bg-end));
  color: var(--text);
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, "Noto Sans", "Helvetica Neue", Arial, sans-serif;
}
.wrap { max-width: 720px; margin: 0 auto; padding: 28px; }
header { text-align: center; margin: 40px 0 24px; }
.brand { font-weight: 900; font-size: clamp(40px, 8vw, 84px); color: var(--error); text-transform: uppercase; }
.tagline { margin-top: 8px; font-size: clamp(16px, 2.5vw, 22px); color: var(--muted); }
.card { border: 1px solid rgba(255,68,68,0.2); background: rgba(0,0,0,0.2); border-radius: 12px; padding: 20px; backdrop-filter: blur(2px); }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 10px; padding: 12px 14px; border-radius: 10px; border: 1px solid var(--button-border); background: var(--button-bg); color: var(--text); text-decoration: none; font-weight: 700; }
.btn:hover { border-color: var(--error); }
footer { margin: 36px 0 20px; text-align: center; color: var(--muted); font-size: 13px; }
.progress { margin-top: 12px; height: 8px; background: rgba(255,68,68,0.15); border-radius: 8px; overflow: hidden; }
.bar { width: 0%; height: 100%; background: var(--error); transition: width 0.2s ease; }
.bad-signal { display: flex; align-items: center; gap: 16px; margin-bottom: 18px; color: var(--muted); }
.wifi { width: 36px; height: 36px; position: relative; opacity: 0.9; }
.wifi::before, .wifi::after { content: ""; position: absolute; inset: 0; border: 3px solid var(--muted); border-radius: 50%; transform: scale(1.2); filter: blur(0.2px); }
.wifi::after { border-color: var(--error); clip-path: polygon(0 0, 100% 0, 100% 55%, 0 55%); transform: scale(0.8); }
.features { display: grid; grid-template-columns: 1fr; gap: 12px; margin: 18px 0; }
.feature { display: flex; gap: 12px; align-items: flex-start; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--error); margin-top: 7px; flex-shrink: 0; }
"""

# ---------------- Pages ----------------
INDEX_HTML = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>СКАМ — медленное и тяжёлое приложение для общения</title>
  <style>{{ css }}</style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="brand">СКАМ</div>
      <div class="tagline">Медленное и тяжёлое приложение для общения. Связь теряется — настроение тоже.</div>
    </header>

    <main class="card" role="main">
      <div class="bad-signal" aria-live="polite">
        <div class="wifi" aria-hidden="true"></div>
        <div>Соединение потеряно… Повтор через 59 минут.</div>
      </div>

      <section class="features" aria-label="Анти-возможности">
        <div class="feature"><div class="dot"></div><div><b>Низкое качество связи:</b> разговоры рвутся даже рядом с роутером.</div></div>
        <div class="feature"><div class="dot"></div><div><b>Медленные сообщения:</b> текст доходит позже, чем вы передумали.</div></div>
        <div class="feature"><div class="dot"></div><div><b>Файлы до 4 МБ:</b> и то через раз, лучше не пытайтесь.</div></div>
        <div class="feature"><div class="dot"></div><div><b>Анимации без анимации:</b> стикеры зависают на первом кадре.</div></div>
      </section>

      <section aria-label="Скачать">
        <a class="btn" href="/download">Скачать на ПК (только Windows)</a>
      </section>
    </main>

    <footer>© 2025 СКАМ. Любые совпадения с реальностью случайны.</footer>
  </div>
</body>
</html>
"""

DOWNLOAD_HTML = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>СКАМ — скачивание для Windows</title>
  <style>{{ css }}</style>
  <script>
    let left = 5;
    function tick(){
      document.getElementById("sec").textContent = left;
      document.getElementById("bar").style.width = ((5-left)/5*100) + "%";
      if(left<=0){
        window.location.href="/files/ScamMessenger.exe";
      } else {
        left--;
        setTimeout(tick,1000);
      }
    }
    window.onload=tick;
  </script>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="brand">СКАМ</div>
      <div class="tagline">Скачивание начнётся через <span id="sec">5</span> сек…</div>
    </header>

    <main class="card">
      <p class="tagline">Если загрузка не началась — используйте кнопку ниже.</p>
      <div class="progress" aria-hidden="true"><div class="bar" id="bar"></div></div>
      <a class="btn" href="/files/ScamMessenger.exe" download>Скачать вручную (Windows)</a>
    </main>

    <footer>© 2025 СКАМ. Файл находится рядом со страницей.</footer>
  </div>
</body>
</html>
"""

@app.get("/")
def index_page():
    return render_template_string(INDEX_HTML, css=CSS)

@app.get("/download")
def download_page():
    return render_template_string(DOWNLOAD_HTML, css=CSS)

# ---------------- Serve installer ----------------
@app.get("/files/<path:filename>")
def files(filename):
    base = os.path.join(os.path.dirname(__file__), "files")
    return send_from_directory(base, filename, as_attachment=True)

# ---------------- Health ----------------
@app.get("/health")
def health():
    return "OK"

if __name__ == "__main__":
    # Для локального запуска; на Amvera будет использоваться gunicorn из Procfile
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
