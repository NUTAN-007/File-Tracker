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
    timestamp = result_timestamp.stdout.strip()
    return author, timestamp

def file_has_changed():
    subprocess.run(["git", "-C", REPO_DIR, "fetch"], check=True)
    
    local_hash_result = subprocess.run(
        ["git", "-C", REPO_DIR, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True
    )
    local_hash = local_hash_result.stdout.strip()

    remote_hash_result = subprocess.run(
        ["git", "-C", REPO_DIR, "rev-parse", "@{u}"],
        capture_output=True,
        text=True,
        check=True
    )
    remote_hash = remote_hash_result.stdout.strip()

    print(f"[DEBUG] Local hash:  {local_hash}")
    print(f"[DEBUG] Remote hash: {remote_hash}")

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
        result = subprocess.run(
            ["git", "clone", GIT_REPO_URL, REPO_DIR],
            capture_output=True,
            text=True,
            check=True
        )
        print("Return code:", result.returncode)
        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr)

        subprocess.run(["git", "-C", REPO_DIR, "checkout", "main"], check=True)
        subprocess.run(["git", "-C", REPO_DIR, "branch", "--set-upstream-to=origin/main", "main"], check=True)

        print("Repo cloned successfully. Starting to monitor changes...")
    else:
        print("Repo already exists. Starting to monitor changes...")

    while True:
        try:
            if file_has_changed():
                print("[INFO] Change detected! Pulling latest changes...")
                subprocess.run(
                    ["git", "-C", REPO_DIR, "pull", "--rebase"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                author, timestamp = get_latest_commit_info()
                with open(os.path.join(REPO_DIR, FILE_TO_TRACK), 'r') as f:
                    content = f.read()
                print(f"[INFO] Change by {author} at {timestamp}")
                insert_change(author, timestamp, content)
            else:
                print("[INFO] No change detected.")
        except Exception as e:
            print("[ERROR] An exception occurred:")
            traceback.print_exc()
        time.sleep(30)
