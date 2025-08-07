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
DB_HOST = os.getenv("POSTGRES_HOST", "postgres.tracker-ns")

def get_latest_commit_info():
    author = subprocess.check_output(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%an"]).decode().strip()
    timestamp = subprocess.check_output(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%aI"]).decode().strip()
    return author, timestamp

def file_has_changed():
    subprocess.check_call(["git", "-C", REPO_DIR, "fetch"])
    local_hash = subprocess.check_output(["git", "-C", REPO_DIR, "rev-parse", "HEAD"]).strip()
    remote_hash = subprocess.check_output(["git", "-C", REPO_DIR, "rev-parse", "@{u}"]).strip()
    return local_hash != remote_hash


def insert_change(author, timestamp, content):
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST
    )
    cur = conn.cursor()
    cur.execute("INSERT INTO changes (author, timestamp, content) VALUES (%s, %s, %s)", 
                (author, timestamp, content))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    if not os.path.exists(os.path.join(REPO_DIR, ".git")):
        print("Cloning repo into /repo...")
        result = subprocess.run(["git", "clone", GIT_REPO_URL, REPO_DIR], capture_output=True, text=True)
        print("Return code:", result.returncode)
        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr)
        subprocess.run(["git", "-C", REPO_DIR, "branch", "--set-upstream-to=origin/main"], check=True)
        print("Repo cloned successfully. Starting to monitor changes...")
    else:
        print("Repo already exists. Starting to monitor changes...")
    while True:
        try:
            if file_has_changed():
                subprocess.run(["git", "-C", REPO_DIR, "pull", "--rebase"],capture_output=True, text=True)
                author, timestamp = get_latest_commit_info()
                with open(os.path.join(REPO_DIR, FILE_TO_TRACK), 'r') as f:
                    content = f.read()
                print(f"Detected change by {author} at {timestamp}")
                insert_change(author, timestamp, content)
            else:
                print("No change detected.")
        except Exception:
            traceback.print_exc()
        time.sleep(30)
