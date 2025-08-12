import os
import time
import subprocess
import psycopg2
from datetime import datetime
import traceback

REPO_DIR = "/repo"
FILE_TO_TRACK = "tracked-file.txt"
GIT_REPO_URL = "https://github.com/NUTAN-007/File-Tracker.git"

DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")

CHECK_INTERVAL = 10  # seconds

def get_last_commit_files():
    """Return list of files changed in last commit."""
    try:
        result = subprocess.run(
            ["git", "-C", REPO_DIR, "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []

def get_latest_commit_info():
    """Get author and timestamp of latest commit."""
    try:
        author = subprocess.run(
            ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%an"],
            capture_output=True,
            text=True
        ).stdout.strip()

        timestamp = subprocess.run(
            ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%ci"],
            capture_output=True,
            text=True
        ).stdout.strip()

        return author, timestamp
    except Exception:
        return None, None

def read_tracked_file():
    """Read tracked file content."""
    try:
        with open(os.path.join(REPO_DIR, FILE_TO_TRACK), "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def save_to_db(content, author, timestamp):
    """Save update details to PostgreSQL."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO changes (content, author, timestamp) VALUES (%s, %s, %s)",
            (content, author, timestamp)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error saving to DB:", e)
        traceback.print_exc()

def main():
    # Clone repo if not present
    if not os.path.exists(REPO_DIR):
        subprocess.run(["git", "clone", GIT_REPO_URL, REPO_DIR])

    # Always ensure repo is updated
    subprocess.run(["git", "-C", REPO_DIR, "pull"])

    changed_files = get_last_commit_files()
    print("Changed files in last commit:", changed_files)

    if FILE_TO_TRACK in changed_files:
        content = read_tracked_file()
        author, timestamp = get_latest_commit_info()

        if content and author and timestamp:
            save_to_db(content, author, timestamp)
            print(f"Updated DB - {author} at {timestamp}")
        else:
            print("File change detected but missing commit info.")
    else:
        print(f"No changes in {FILE_TO_TRACK}, skipping DB update.")

if __name__ == "__main__":
    main()
