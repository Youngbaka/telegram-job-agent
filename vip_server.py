import os
import time
import hmac
import hashlib
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ["TELEGRAM_TOKEN"]
VIP_CHAT_ID = os.environ["VIP_CHAT_ID"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])
PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET", "")


def create_one_time_invite(label: str = "VIP Pass", hours_valid: int = 48) -> str:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createChatInviteLink"
    payload = {
        "chat_id": VIP_CHAT_ID,
        "member_limit": 1,
        "expire_date": int(time.time()) + (hours_valid * 3600),
        "name": label[:32],
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    return data["result"]["invite_link"]


def send_dm(chat_id: int, text: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )


@app.post("/telegram-webhook")
def telegram_webhook():
    update = request.get_json(silent=True) or {}
    msg = update.get("message") or {}
    sender = msg.get("from") or {}
    text = (msg.get("text") or "").strip()

    if sender.get("id") != ADMIN_USER_ID:
        return jsonify({"ok": True}), 200

    if text.startswith("/vip"):
        parts = text.split(maxsplit=1)
        buyer_label = parts[1].strip() if len(parts) > 1 else "VIP Buyer"
        try:
            link = create_one_time_invite(label=buyer_label)
            send_dm(sender["id"], f"One-time VIP link for <b>{buyer_label}</b>:\n{link}")
        except Exception as exc:
            send_dm(sender["id"], f"Failed to create link: {exc}")

    return jsonify({"ok": True}), 200


@app.post("/webhook/paystack")
def paystack_webhook():
    raw_body = request.get_data()
    signature = request.headers.get("x-paystack-signature", "")

    if not PAYSTACK_SECRET:
        return jsonify({"error": "Missing webhook secret"}), 400

    computed = hmac.new(
        PAYSTACK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()

    if not hmac.compare_digest(computed, signature):
        return jsonify({"error": "Invalid signature"}), 401

    event = request.get_json(silent=True) or {}
    if event.get("event") == "charge.success":
        customer_email = (event.get("data") or {}).get("customer", {}).get("email", "Buyer")
        link = create_one_time_invite(label=customer_email)
        send_dm(ADMIN_USER_ID, f"Paid ({customer_email}):\n{link}")

    return jsonify({"ok": True}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
