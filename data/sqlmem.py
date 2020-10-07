# === SQL MEMORY CONTROLLER ===
# Database Ver : 1.002
# Last modified: 04308
# Base Memory  : 16 Kb
import os
import sqlite3
from platform import system

# Set Database Path
if system() == "Windows":
    database = os.getenv('LOCALAPPDATA') + '\\lite-vi'

    if not os.path.exists(database):
        os.makedirs(database)
    database = database + '\\lite-vi.db'

else:
    database = './data/lite-vi.db'


# === RUN SQL QUERY ===
# SQL Query Functions
# query for multiple items within the database
def query(sql):
    # CONNECT TO DATABASE
    conn = sqlite3.connect(database)
    c = conn.cursor()

    # ATTEMPT QUERY
    try:
        c.execute(sql)
    #   IF QUERY FAILED
    except Exception as e:
        print(e)
        return False
    # STORE QUERY RESULT
    i = c.fetchall()
    # COMMIT CONNECTION
    conn.commit()
    c.close()
    conn.close()
    # COMMIT RESULT
    return i


# query for a single item within the database
def queryFor(sql):
    # CONNECT TO DATABASE
    conn = sqlite3.connect(database)
    c = conn.cursor()

    # ATTEMPT QUERY
    try:
        c.execute(sql)
    #   IF QUERY FAILED
    except Exception as e:
        print(e)
        return False
    # STORE QUERY RESULT
    i = c.fetchone()
    # COMMIT CONNECTION
    conn.commit()
    c.close()
    conn.close()
    # COMMIT RESULT
    return i


def close_database():
    return


# CLEAN DATABASE PROTOCOL ==============================================================================================
# Cleans the database of old and unused tables
tables = query("SELECT name FROM sqlite_master WHERE type='table'")
ttd = ["current_pnl", ""]

for table in tables:
    if table[0] in ttd:
        print("Deleting", table[0], "...")
        query("DROP TABLE " + table[0] + ";")


# CREATE TABLES FUNCTION ===============================================================================================
# CT is run on start-up to assure tables always exist and avoids possible code failure if the database is corrupted

# Utility Functions
query("CREATE TABLE IF NOT EXISTS smart_devices(name TEXT, ip TEXT)")
query("CREATE TABLE IF NOT EXISTS bookmarks(name TEXT, url TEXT, content TEXT, confirmed INT)")
query("CREATE TABLE IF NOT EXISTS triggers(type TEXT, info TEXT, time TIMEDATE)")
query("CREATE TABLE IF NOT EXISTS self(pid INT, f_name TEXT, l_name TEXT, email TEXT, password TEXT)")
# Hard Storage
query("CREATE TABLE IF NOT EXISTS variable_table(name TEXT, value TEXT)")
# People
query("CREATE TABLE IF NOT EXISTS master(uid INT, f_name TEXT, l_name TEXT, password TEXT, "
      "auto_login INT, wloc TEXT)")
query("CREATE TABLE IF NOT EXISTS people(uid INT, f_name TEXT, l_name TEXT, info TEXT, weather INT, tmsg TEXT)")
query("CREATE TABLE IF NOT EXISTS processes("
      "process TEXT DEFAULT 'unknown',"
      "type TEXT DEFAULT 'exe', "
      "when_found TEXT DEFAULT '0', "
      "active TEXT DEFAULT '0')")

# END OF FILE [sqlmem.py]
