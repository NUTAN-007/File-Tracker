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
    try:
        subprocess.check_call(["git", "-C", REPO_DIR, "fetch"])
        local_hash = subprocess.check_output(
            ["git", "-C", REPO_DIR, "rev-parse", "HEAD"]).strip()
        remote_hash = subprocess.check_output(
            ["git", "-C", REPO_DIR, "rev-parse", "@{u}"]).strip()
        print(f"[DEBUG] Local hash: {local_hash.decode()}", flush=True)
        print(f"[DEBUG] Remote hash: {remote_hash.decode()}", flush=True)
        return local_hash != remote_hash
    except subprocess.CalledProcessError as e:
        print("[ERROR] Failed to compare hashes or fetch from remote:", flush=True)
        traceback.print_exc()
        return False

def insert_change(author, timestamp, content):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST
        )
        cur = conn.cursor()
        cur.execute("INSERT INTO changes (author, timestamp, content) VALUES (%s, %s, %s)", 
                    (author, timestamp, content))
        conn.commit()
        conn.close()
        print("[INFO] Change inserted into DB.", flush=True)
    except Exception:
        print("[ERROR] Failed to insert change into DB.", flush=True)
        traceback.print_exc()

if __name__ == "__main__":
    if not os.path.exists(os.path.join(REPO_DIR, ".git")):
        print("[INFO] Cloning repo into /repo...", flush=True)
        subprocess.check_call([
            "git", "clone", "--branch", "main", "--single-branch", GIT_REPO_URL, REPO_DIR
        ])
        # Set upstream branch explicitly
        subprocess.check_call([
            "git", "-C", REPO_DIR, "branch", "--set-upstream-to=origin/main", "main"
        ])
    else:
        print("[INFO] Repo already cloned. Skipping clone step.", flush=True)

    print("[INFO] Starting tracker loop...", flush=True)

    while True:
        try:
            print("[INFO] Checking for file changes...", flush=True)
            if file_has_changed():
                print("[INFO] Change detected. Pulling latest...", flush=True)
                subprocess.check_call(["git", "-C", REPO_DIR, "pull", "--rebase"])
                author, timestamp = get_latest_commit_info()
                with open(os.path.join(REPO_DIR, FILE_TO_TRACK), 'r') as f:
                    content = f.read()
                print(f"[INFO] Detected change by {author} at {timestamp}", flush=True)
                insert_change(author, timestamp, content)
            else:
                print("[INFO] No change detected.", flush=True)
        except Exception:
            print("[ERROR] Exception in main loop:", flush=True)
            traceback.print_exc()
        time.sleep(30)
