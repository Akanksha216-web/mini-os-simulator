import sqlite3


conn = sqlite3.connect("mini_os.db")
c = conn.cursor()


with open("schema.sql") as f:
    c.executescript(f.read())

conn.commit()
conn.close()

print("Database created and initialized!")