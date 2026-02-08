import os
import hashlib
from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
from cs50 import SQL
from helpers import login_required

# ----------------- Flask setup -----------------
app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connect to SQLite
db = SQL("sqlite:///mini_os.db")

# ----------------- Password helpers -----------------
def hash_password(password):
    """Return SHA-256 hash of the password"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed):
    """Check if password matches hashed"""
    return hashlib.sha256(password.encode()).hexdigest() == hashed

# ----------------- Routes -----------------

@app.route("/")
def index():
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if not username or not password or not confirm:
            flash("All fields are required!")
            return redirect("/register")

        if password != confirm:
            flash("Passwords do not match!")
            return redirect("/register")

        if db.execute("SELECT * FROM users WHERE username = ?", username):
            flash("Username already exists!")
            return redirect("/register")

        # Insert new user with hashed password
        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            username, hash_password(password)
        )

        # Auto-login
        user = db.execute("SELECT * FROM users WHERE username = ?", username)[0]
        session["user_id"] = user["id"]
        session["role"] = "user"

        return redirect("/terminal")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Username and password required!")
            return redirect("/login")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 1 or not check_password(password, rows[0]["hash"]):
            flash("Invalid username or password!")
            return redirect("/login")

        session["user_id"] = rows[0]["id"]
        session["role"] = rows[0]["role"]

        return redirect("/terminal")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/terminal", methods=["GET", "POST"])
@login_required
def terminal():
    """Terminal interface"""
    output = ""
    current_dir_id = session.get("current_dir_id")  # track current folder
    if current_dir_id is None:
        current_dir_id = None  # root directory

    if request.method == "POST":
        command_input = request.form.get("command").strip()
        parts = command_input.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == "ls":
            # list files in current directory
            rows = db.execute(
                "SELECT name, type FROM files WHERE parent_id IS ? AND owner_id = ?",
                current_dir_id, session["user_id"]
            )
            output = "\n".join(f"{r['name']}/" if r["type"]=="folder" else r["name"] for r in rows)

        elif cmd == "mkdir":
            if len(args) != 1:
                output = "Usage: mkdir <folder_name>"
            else:
                folder_name = args[0]
                # check if folder already exists
                exists = db.execute(
                    "SELECT * FROM files WHERE name=? AND parent_id IS ? AND owner_id=? AND type='folder'",
                    folder_name, current_dir_id, session["user_id"]
                )
                if exists:
                    output = "Folder already exists"
                else:
                    db.execute(
                        "INSERT INTO files (name, type, parent_id, owner_id) VALUES (?, 'folder', ?, ?)",
                        folder_name, current_dir_id, session["user_id"]
                    )
                    output = f"Folder '{folder_name}' created"

        elif cmd == "touch":
            if len(args) != 1:
                output = "Usage: touch <file_name>"
            else:
                file_name = args[0]
                exists = db.execute(
                    "SELECT * FROM files WHERE name=? AND parent_id IS ? AND owner_id=? AND type='file'",
                    file_name, current_dir_id, session["user_id"]
                )
                if exists:
                    output = "File already exists"
                else:
                    db.execute(
                        "INSERT INTO files (name, type, parent_id, owner_id, content) VALUES (?, 'file', ?, ?, '')",
                        file_name, current_dir_id, session["user_id"]
                    )
                    output = f"File '{file_name}' created"

        else:
            output = f"Unknown command: {cmd}"

    return render_template("terminal.html", output=output)


@app.route("/dashboard")
@login_required
def dashboard():
    """Analytics / process dashboard placeholder"""
    # TODO: fetch processes, file stats, etc.
    return render_template("dashboard.html")


# ----------------- Run Flask -----------------
if __name__ == "__main__":
    app.run(debug=True)