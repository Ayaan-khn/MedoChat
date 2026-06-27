import os
import sqlite3

# Folder containing app.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Go one level up (to Medo_chat)
PROJECT_DIR = os.path.dirname(CURRENT_DIR)

# Path to Medo_chat/database
DATABASE_DIR = os.path.join(PROJECT_DIR, "database")
os.makedirs(DATABASE_DIR, exist_ok=True)

# Database file
DB_PATH = os.path.join(DATABASE_DIR, "medochat.db")

# Create the database
conn = sqlite3.connect(DB_PATH)
conn.close()

print("Database created successfully!")
print(DB_PATH)

from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)