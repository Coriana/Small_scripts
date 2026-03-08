import requests
import sqlite3
from datetime import datetime, timedelta
from apikey import GITHUB

REPO = "org\repo"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO}/commits"
DATABASE = "recent_commits.db"
NEW_COMMITS_FILE = "new_commits.txt"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS commits (
                        sha TEXT PRIMARY KEY,
                        message TEXT,
                        author TEXT,
                        date TEXT
                    )''')
    conn.commit()
    conn.close()

def get_recent_commits(since, per_page=500):
    headers = {
        "Authorization": f"Bearer {GITHUB}",
        "Accept": "application/vnd.github.v3+json"
    }
    params = {
        "since": since.isoformat(),
        "per_page": per_page
    }
    response = requests.get(GITHUB_API_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def save_new_commits(commits):
    with open(NEW_COMMITS_FILE, 'w') as f:
        for commit in reversed(commits):
            message = commit['commit']['message']
            if not message.startswith("Merge branch "):         
               f.write(f"{commit['commit']['message']}\n")

def store_commits_in_db(commits):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    new_commits = []
    for commit in commits:
        cursor.execute('SELECT sha FROM commits WHERE sha=?', (commit['sha'],))
        if cursor.fetchone() is None:
            cursor.execute('INSERT INTO commits (sha, message, author, date) VALUES (?, ?, ?, ?)',
                           (commit['sha'], commit['commit']['message'], commit['commit']['author']['name'], commit['commit']['author']['date']))
            new_commits.append(commit)
    conn.commit()
    conn.close()
    return new_commits

def main():
    init_db()
    # Check for commits in the last 24 hours
    since = datetime.utcnow() - timedelta(days=200)
    commits = get_recent_commits(since)
    print(f"Found {len(commits)} commits since {since}.")
    new_commits = store_commits_in_db(commits)
    if new_commits:
        save_new_commits(new_commits)
        print(f"Found and saved {len(new_commits)} new commits.")
    else:
        print("No new commits found.")

if __name__ == "__main__":
    main()
