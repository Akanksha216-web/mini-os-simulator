CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    hash TEXT NOT NULL,
    role TEXT DEFAULT 'user'
);

CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL, 
    content TEXT,
    parent_id INTEGER,
    owner_id INTEGER,
    FOREIGN KEY(owner_id) REFERENCES users(id)
);