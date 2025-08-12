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
DB_HOST = os.getenv("POSTGRES_HOST")

def connect_db():
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST
    )

def get_latest_commit_info():
    result_files = subprocess.run(
        ["git", "-C", REPO_DIR, "diff", "--name-only", "HEAD~1", "HEAD"],
        capture_output=True, text=True, check=True
    )
    changed_files = result_files.stdout.strip().split("\n")
    if FILE_TO_TRACK not in changed_files:
        return None, None

    result_author = subprocess.run(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%an", "--", FILE_TO_TRACK],
        capture_output=True, text=True, check=True
    )
    author = result_author.stdout.strip()

    result_timestamp = subprocess.run(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%aI", "--", FILE_TO_TRACK],
        capture_output=True, text=True, check=True
    )
    timestamp = result_timestamp.stdout.strip()

    return author, timestamp

def track_changes():
    last_author, last_timestamp = None, None
    while True:
        try:
            subprocess.run(["git", "-C", REPO_DIR, "pull"], check=True)
            author, timestamp = get_latest_commit_info()
            if author and timestamp and (author != last_author or timestamp != last_timestamp):
                with connect_db() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO changes (timestamp, author) VALUES (%s, %s)",
                            (timestamp, author)
                        )
                        conn.commit()
                last_author, last_timestamp = author, timestamp
                print(f"Last Update\nAuthor: {author}\nTimestamp: {timestamp}")
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
        time.sleep(10)

if __name__ == "__main__":
    track_changes()
