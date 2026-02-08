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

def delete_recursive(file_id):
    # Get children
    children = db.execute(
        "SELECT id FROM files WHERE parent_id = ?",
        file_id
    )

    for child in children:
        delete_recursive(child["id"])

    db.execute("DELETE FROM files WHERE id = ?", file_id)


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
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            flash("All fields are required!")
            return redirect("/register")

        if password != confirmation:
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
    output = ""

    if request.method == "POST":
        command = request.form.get("command").strip()
        parts = command.split()

        if len(parts) == 0:
            return render_template("terminal.html", output="")

        cmd = parts[0]

        # ---------------- LS ----------------
        if cmd == "ls":
            items = db.execute(
                "SELECT name, type FROM files WHERE owner_id = ? AND parent_id IS ? ORDER BY type DESC, name ASC",
                session["user_id"],
                session.get("cwd")
            )

            for item in items:
                if item["type"] == "folder":
                    output += item["name"] + "/\n"
                else:
                    output += item["name"] + "\n"

        # ---------------- MKDIR ----------------
        elif cmd == "mkdir" and len(parts) == 2:
            name = parts[1]

            existing = db.execute(
                "SELECT id FROM files WHERE owner_id = ? AND parent_id IS ? AND name = ?",
                session["user_id"],
                session.get("cwd"),
                name
            )

            if existing:
                output = "Folder already exists"
            else:
                db.execute(
                    "INSERT INTO files (name, type, parent_id, owner_id) VALUES (?, 'folder', ?, ?)",
                    name,
                    session.get("cwd"),
                    session["user_id"]
                )
                output = f"Folder '{name}' created"

        # ---------------- TOUCH ----------------
        elif cmd == "touch" and len(parts) == 2:
            name = parts[1]

            existing = db.execute(
                "SELECT id FROM files WHERE owner_id = ? AND parent_id IS ? AND name = ?",
                session["user_id"],
                session.get("cwd"),
                name
            )

            if existing:
                output = "File already exists"
            else:
                db.execute(
                    "INSERT INTO files (name, type, parent_id, owner_id, content) VALUES (?, 'file', ?, ?, '')",
                    name,
                    session.get("cwd"),
                    session["user_id"]
                )
                output = f"File '{name}' created"

        # ---------------- CD ----------------
        elif cmd == "cd" and len(parts) == 2:
            target = parts[1]

            if target == "/":
                session["cwd"] = None
                output = "Moved to root"

            elif target == "..":
                if session.get("cwd") is None:
                    output = "Already at root"
                else:
                    parent = db.execute(
                        "SELECT parent_id FROM files WHERE id = ?",
                        session["cwd"]
                    )
                    session["cwd"] = parent[0]["parent_id"]
                    output = "Moved up"

            else:
                folder = db.execute(
                    "SELECT id FROM files WHERE owner_id = ? AND parent_id IS ? AND name = ? AND type = 'folder'",
                    session["user_id"],
                    session.get("cwd"),
                    target
                )

                if not folder:
                    output = "Folder not found"
                else:
                    session["cwd"] = folder[0]["id"]
                    output = f"Entered '{target}'"

        # ---------------- PWD ----------------
        elif cmd == "pwd":
            current = session.get("cwd")

            if current is None:
                output = "/"
            else:
                path = []
                while current is not None:
                    row = db.execute(
                        "SELECT name, parent_id FROM files WHERE id = ?",
                        current
                    )[0]

                    path.append(row["name"])
                    current = row["parent_id"]

                path.reverse()
                output = "/" + "/".join(path)

        # ---------------- RM ----------------
        elif cmd == "rm" and len(parts) == 2:
            name = parts[1]

            target = db.execute(
                "SELECT id FROM files WHERE owner_id = ? AND parent_id IS ? AND name = ?",
                session["user_id"],
                session.get("cwd"),
                name
            )

            if not target:
                output = "File or folder not found"
            else:
                delete_recursive(target[0]["id"])
                output = f"'{name}' deleted"

        else:
            output = "Unknown or invalid command"

    items = db.execute(
    "SELECT id, name, type FROM files WHERE owner_id = ? AND parent_id IS ? ORDER BY type DESC, name ASC",
    session["user_id"],
    session.get("cwd")
)

    return render_template("terminal.html", output=output, items=items)



@app.route("/dashboard")
@login_required
def dashboard():
    """Analytics / process dashboard placeholder"""
    # TODO: fetch processes, file stats, etc.
    return render_template("dashboard.html")


@app.route("/folder/<int:folder_id>")
@login_required
def open_folder(folder_id):

    folder = db.execute(
        "SELECT id FROM files WHERE id = ? AND owner_id = ? AND type = 'folder'",
        folder_id,
        session["user_id"]
    )

    if not folder:
        return "Folder not found", 404

    session["cwd"] = folder_id
    return redirect("/terminal")


@app.route("/file/<int:file_id>", methods=["GET", "POST"])
@login_required
def open_file(file_id):

    file = db.execute(
        "SELECT * FROM files WHERE id = ? AND owner_id = ? AND type = 'file'",
        file_id,
        session["user_id"]
    )

    if not file:
        return "File not found"

    file = file[0]

    if request.method == "POST":
        content = request.form.get("content")
        db.execute(
            "UPDATE files SET content = ? WHERE id = ?",
            content,
            file_id
        )
        return redirect("/terminal")

    return render_template("editor.html", file=file)


# ----------------- Run Flask -----------------
if __name__ == "__main__":
    app.run(debug=True)