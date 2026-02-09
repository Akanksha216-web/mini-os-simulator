import os
import hashlib
from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
from cs50 import SQL
from helpers import login_required

# ----------------- Flask setup -----------------
app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///mini_os.db")

# ----------------- Utility Functions -----------------

def delete_recursive(file_id):
    children = db.execute(
        "SELECT id FROM files WHERE parent_id = ?",
        file_id
    )

    for child in children:
        delete_recursive(child["id"])

    db.execute("DELETE FROM files WHERE id = ?", file_id)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(password, hashed):
    return hashlib.sha256(password.encode()).hexdigest() == hashed


def build_path():
    current = session.get("cwd")

    if current is None:
        return "/"

    path = []
    while current is not None:
        row = db.execute(
            "SELECT name, parent_id FROM files WHERE id = ?",
            current
        )[0]

        path.append(row["name"])
        current = row["parent_id"]

    path.reverse()
    return "/" + "/".join(path)


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

        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            username, hash_password(password)
        )

        user = db.execute("SELECT * FROM users WHERE username = ?", username)[0]
        session["user_id"] = user["id"]
        session["role"] = "user"
        session["cwd"] = None

        return redirect("/terminal")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password(password, rows[0]["hash"]):
            flash("Invalid username or password!")
            return redirect("/login")

        session["user_id"] = rows[0]["id"]
        session["role"] = rows[0]["role"]
        session["cwd"] = None

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

        if parts:
            cmd = parts[0]

            # -------- LS --------
            if cmd == "ls":
                items_ls = db.execute(
                    "SELECT name, type FROM files WHERE owner_id = ? AND parent_id IS ? ORDER BY type DESC, name ASC",
                    session["user_id"],
                    session.get("cwd")
                )

                for item in items_ls:
                    if item["type"] == "folder":
                        output += item["name"] + "/\n"
                    else:
                        output += item["name"] + "\n"

            # -------- MKDIR --------
            elif cmd == "mkdir" and len(parts) == 2:
                name = parts[1]

                if db.execute(
                    "SELECT id FROM files WHERE owner_id = ? AND parent_id IS ? AND name = ?",
                    session["user_id"],
                    session.get("cwd"),
                    name
                ):
                    output = "Folder already exists"
                else:
                    db.execute(
                        "INSERT INTO files (name, type, parent_id, owner_id) VALUES (?, 'folder', ?, ?)",
                        name,
                        session.get("cwd"),
                        session["user_id"]
                    )

            # -------- TOUCH --------
            elif cmd == "touch" and len(parts) == 2:
                name = parts[1]

                if db.execute(
                    "SELECT id FROM files WHERE owner_id = ? AND parent_id IS ? AND name = ?",
                    session["user_id"],
                    session.get("cwd"),
                    name
                ):
                    output = "File already exists"
                else:
                    db.execute(
                        "INSERT INTO files (name, type, parent_id, owner_id, content) VALUES (?, 'file', ?, ?, '')",
                        name,
                        session.get("cwd"),
                        session["user_id"]
                    )

            # -------- CD --------
            elif cmd == "cd" and len(parts) == 2:
                target = parts[1]

                if target == "/":
                    session["cwd"] = None

                elif target == "..":
                    if session.get("cwd") is not None:
                        parent = db.execute(
                            "SELECT parent_id FROM files WHERE id = ?",
                            session["cwd"]
                        )[0]
                        session["cwd"] = parent["parent_id"]

                else:
                    folder = db.execute(
                        "SELECT id FROM files WHERE owner_id = ? AND parent_id IS ? AND name = ? AND type = 'folder'",
                        session["user_id"],
                        session.get("cwd"),
                        target
                    )

                    if folder:
                        session["cwd"] = folder[0]["id"]
                    else:
                        output = "Folder not found"

            # -------- RM --------
            elif cmd == "rm" and len(parts) == 2:
                name = parts[1]

                target = db.execute(
                    "SELECT id FROM files WHERE owner_id = ? AND parent_id IS ? AND name = ?",
                    session["user_id"],
                    session.get("cwd"),
                    name
                )

                if target:
                    delete_recursive(target[0]["id"])
                else:
                    output = "Not found"

            else:
                output = "Invalid command"

    items = db.execute(
        "SELECT id, name, type FROM files WHERE owner_id = ? AND parent_id IS ? ORDER BY type DESC, name ASC",
        session["user_id"],
        session.get("cwd")
    )

    current_path = build_path()

    return render_template(
        "terminal.html",
        items=items,
        output=output,
        current_path=current_path
    )


@app.route("/folder/<int:folder_id>")
@login_required
def open_folder(folder_id):
    folder = db.execute(
        "SELECT id FROM files WHERE id = ? AND owner_id = ? AND type = 'folder'",
        folder_id,
        session["user_id"]
    )

    if folder:
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


if __name__ == "__main__":
    app.run(debug=True)
