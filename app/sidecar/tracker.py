import os, time, subprocess
import psycopg2
from datetime import datetime

REPO_DIR = "/repo"
GIT_URL = os.getenv("GIT_REPO_URL")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "trackdb")
DB_USER = os.getenv("DB_USER", "tracker")
DB_PASS = os.getenv("DB_PASS", "trackerpass")

def git_clone():
    subprocess.run(["git", "clone", GIT_URL, REPO_DIR])

def get_latest_commit():
    author = subprocess.check_output(["git", "log", "-1", "--pretty=format:%an"], cwd=REPO_DIR).decode()
    return author

def push_to_db(author):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor()
    cur.execute("INSERT INTO changes (author) VALUES (%s)", (author,))
    conn.commit()
    conn.close()

def run():
    last_commit = ""
    git_clone()
    while True:
        subprocess.run(["git", "pull"], cwd=REPO_DIR)
        current_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_DIR).decode().strip()
        if current_commit != last_commit:
            author = get_latest_commit()
            push_to_db(author)
            last_commit = current_commit
        time.sleep(10)

if __name__ == "__main__":
    run()
