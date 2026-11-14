import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

KEYWORDS = ["python", "backend", "ai", "data analyst"]
SEEN_FILE = "seen_jobs.txt"

def load_seen_jobs():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(f.read().splitlines())

def save_seen_job(job_id):
    with open(SEEN_FILE, "a") as f:
        f.write(f"{job_id}\n")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload)

def scan_jobs():
    seen_jobs = load_seen_jobs()
    # Fetching from Remotive's free public API
    response = requests.get("https://remotive.com/api/remote-jobs?limit=50")
    jobs = response.json().get("jobs", [])

    for job in jobs:
        job_id = str(job["id"])
        title = job["title"].lower()
        
        if job_id not in seen_jobs and any(kw in title for kw in KEYWORDS):
            msg = (
                f"🚨 <b>New Job Match!</b>\n\n"
                f"<b>Role:</b> {job['title']}\n"
                f"<b>Company:</b> {job['company_name']}\n"
                f"<b>Location:</b> {job['candidate_required_location']}\n"
                f"🔗 <a href='{job['url']}'>Apply Here</a>"
            )
            send_telegram_message(msg)
            save_seen_job(job_id)

if __name__ == "__main__":
    scan_jobs()
