import os
import time
import subprocess
import psycopg2
from datetime import datetime, timezone, timedelta
import traceback

REPO_DIR = "/repo"
FILE_TO_TRACK = "tracked-file.txt"
GIT_REPO_URL = "https://github.com/NUTAN-007/File-Tracker.git"

DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

# Function to get commit info (author, timestamp, commit hash)
def get_latest_commit_info():
    try:
        result_author = subprocess.run(
            ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%an"],
            capture_output=True,
            text=True,
            check=True
        )
        author = result_author.stdout.strip()

        result_timestamp = subprocess.run(
            ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%aI"],
            capture_output=True,
            text=True,
            check=True
        )
        utc_timestamp_str = result_timestamp.stdout.strip()
        utc_time = datetime.fromisoformat(utc_timestamp_str.replace("Z", "+00:00"))

        # Convert UTC to IST (UTC+5:30)
        ist_time = utc_time.astimezone(timezone(timedelta(hours=5, minutes=30)))

        result_hash = subprocess.run(
            ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%H"],
            capture_output=True,
            text=True,
            check=True
        )
        commit_hash = result_hash.stdout.strip()

        return author, ist_time, commit_hash

    except subprocess.CalledProcessError:
        print("Error retrieving git commit info")
        return None, None, None

# Function to clone or pull repo
def clone_or_pull_repo():
    if not os.path.exists(REPO_DIR):
        print("Cloning repository...")
        subprocess.run(["git", "clone", GIT_REPO_URL, REPO_DIR], check=True)
    else:
        print("Pulling latest changes...")
        subprocess.run(["git", "-C", REPO_DIR, "pull"], check=True)

# Function to store commit info in DB
def store_commit_info(author, timestamp, commit_hash):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO changes (timestamp, author, commit_hash)
            VALUES (%s, %s, %s)
        """, (timestamp, author, commit_hash))
        conn.commit()
        cur.close()
        conn.close()
        print(f"Stored commit: {commit_hash} by {author} at {timestamp}")
    except Exception as e:
        print("Error inserting into database:", e)
        traceback.print_exc()

# Main loop
if __name__ == "__main__":
    last_commit = None
    while True:
        try:
            clone_or_pull_repo()
            author, timestamp, commit_hash = get_latest_commit_info()

            if commit_hash and commit_hash != last_commit:
                store_commit_info(author, timestamp, commit_hash)
                last_commit = commit_hash

        except Exception as e:
            print("Error in main loop:", e)
            traceback.print_exc()

        time.sleep(10)
