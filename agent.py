import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Expanded keywords covering AI/ML, Data, QA, Annotation & Tech roles
KEYWORDS = [
    "python", "backend", "ai", "data analyst", "data",
    "annotation", "annotator", "rlhf", "llm", "trainer",
    "evaluation", "evaluator", "quality", "qa", "agent",
    "operations", "analyst", "prompt"
]
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

def fetch_remotive():
    try:
        res = requests.get("https://remotive.com/api/remote-jobs", timeout=15)
        jobs = res.json().get("jobs", [])
        return [
            {
                "id": f"remotive_{j['id']}",
                "title": j.get("title", ""),
                "company": j.get("company_name", "Unknown"),
                "location": j.get("candidate_required_location", "Remote"),
                "url": j.get("url", ""),
                "source": "Remotive"
            }
            for j in jobs
        ]
    except Exception as e:
        print(f"Remotive error: {e}")
        return []

def fetch_remoteok():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get("https://remoteok.com/api", headers=headers, timeout=15)
        jobs = res.json()[1:]  # First element is metadata
        return [
            {
                "id": f"remoteok_{j['id']}",
                "title": j.get("position", ""),
                "company": j.get("company", "Unknown"),
                "location": j.get("location", "Worldwide") or "Worldwide",
                "url": j.get("url", ""),
                "source": "RemoteOK"
            }
            for j in jobs if j.get("position")
        ]
    except Exception as e:
        print(f"RemoteOK error: {e}")
        return []

def fetch_arbeitnow():
    try:
        res = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=15)
        jobs = res.json().get("data", [])
        return [
            {
                "id": f"arbeitnow_{j['slug']}",
                "title": j.get("title", ""),
                "company": j.get("company_name", "Unknown"),
                "location": j.get("location", "Remote"),
                "url": j.get("url", ""),
                "source": "Arbeitnow"
            }
            for j in jobs if j.get("remote")
        ]
    except Exception as e:
        print(f"Arbeitnow error: {e}")
        return []

def scan_jobs():
    seen_jobs = load_seen_jobs()
    print(f"Loaded {len(seen_jobs)} seen jobs.")

    all_jobs = fetch_remotive() + fetch_remoteok() + fetch_arbeitnow()
    print(f"Fetched {len(all_jobs)} total jobs across all sources.")

    matches_sent = 0
    for job in all_jobs:
        job_id = str(job["id"])
        title_lower = job["title"].lower()

        if job_id not in seen_jobs and any(kw in title_lower for kw in KEYWORDS):
            print(f"Match found [{job['source']}]: {job['title']} (ID: {job_id})")
            msg = (
                f"🚨 <b>New Job Match ({job['source']})!</b>\n\n"
                f"<b>Role:</b> {job['title']}\n"
                f"<b>Company:</b> {job['company']}\n"
                f"<b>Location:</b> {job['location']}\n"
                f"🔗 <a href='{job['url']}'>Apply Here</a>"
            )
            if send_telegram_message(msg):
                save_seen_job(job_id)
                seen_jobs.add(job_id)
                matches_sent += 1

    print(f"Total new matches sent: {matches_sent}")

if __name__ == "__main__":
    scan_jobs()
