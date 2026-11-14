import os
import requests

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
    res = requests.post(url, json=payload)
    print(f"Telegram API response ({res.status_code}): {res.text}")
    return res.status_code == 200

def scan_jobs():
    seen_jobs = load_seen_jobs()
    print(f"Loaded {len(seen_jobs)} seen jobs.")
    
    response = requests.get("https://remotive.com/api/remote-jobs?limit=50")
    jobs = response.json().get("jobs", [])
    print(f"Fetched {len(jobs)} jobs from Remotive.")

    matches_sent = 0
    for job in jobs:
        job_id = str(job["id"])
        title = job["title"].lower()
        
        if job_id not in seen_jobs and any(kw in title for kw in KEYWORDS):
            print(f"Match found: {job['title']} (ID: {job_id})")
            msg = (
                f"🚨 <b>New Job Match!</b>\n\n"
                f"<b>Role:</b> {job['title']}\n"
                f"<b>Company:</b> {job['company_name']}\n"
                f"<b>Location:</b> {job['candidate_required_location']}\n"
                f"🔗 <a href='{job['url']}'>Apply Here</a>"
            )
            if send_telegram_message(msg):
                save_seen_job(job_id)
                matches_sent += 1

    print(f"Total new matches sent: {matches_sent}")

if __name__ == "__main__":
    scan_jobs()
