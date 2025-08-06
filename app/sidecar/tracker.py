import os
import time
import subprocess
import psycopg2
from datetime import datetime

REPO_DIR = "/repo"
FILE_TO_TRACK = "tracked-file.txt"
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")

def get_latest_commit_info():
    author = subprocess.check_output(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%an"]).decode().strip()
    timestamp = subprocess.check_output(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%aI"]).decode().strip()
    return author, timestamp

def file_has_changed():
    output = subprocess.check_output(["git", "-C", REPO_DIR, "pull"])
    return b'Already up to date' not in output

def insert_change(author, timestamp):
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST
    )
    cur = conn.cursor()
    cur.execute("INSERT INTO changes (author, timestamp) VALUES (%s, %s)", (author, timestamp))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    while True:
        try:
            if file_has_changed():
                author, timestamp = get_latest_commit_info()
                print(f"Detected change by {author} at {timestamp}")
                insert_change(author, timestamp)
            else:
                print("No change detected.")
        except Exception as e:
            print("Error:", e)
        time.sleep(30)
