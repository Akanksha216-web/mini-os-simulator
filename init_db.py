import sqlite3

# Connect (this will create the database if it doesn't exist)
conn = sqlite3.connect("mini_os.db")
c = conn.cursor()

# Read schema.sql and execute it
with open("schema.sql") as f:
    c.executescript(f.read())

conn.commit()
conn.close()

print("Database created and initialized!")