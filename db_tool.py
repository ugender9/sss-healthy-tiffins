"""
Interactive Database CLI Tool for S.S.S Healthy Tiffins SQLite Database.
Run:
    python db_tool.py
"""
import sys
import sqlite3
from database import DB_FILE, get_stats

def show_summary():
    print("=" * 60)
    print(f" Database File: {DB_FILE}")
    print("=" * 60)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]

    print("\n--- Available Tables ---")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  • {table.ljust(20)}: {count} row(s)")

    print("\n--- Current App Stats ---")
    try:
        stats = get_stats()
        for k, v in stats.items():
            print(f"  • {k.replace('_', ' ').title().ljust(20)}: {v}")
    except Exception as e:
        print(f"  Error loading stats: {e}")

    conn.close()
    print("=" * 60)

def query_table(table_name: str, limit: int = 10):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
        rows = cursor.fetchall()
        if not rows:
            print(f"Table '{table_name}' is empty.")
            return

        headers = rows[0].keys()
        print(f"\n--- First {min(len(rows), limit)} rows of '{table_name}' ---")
        print(" | ".join(headers))
        print("-" * 60)
        for row in rows:
            print(" | ".join(str(row[h]) for h in headers))
    except Exception as e:
        print(f"Error querying {table_name}: {e}")
    finally:
        conn.close()

def interactive_shell():
    show_summary()
    print("\nType an SQL query (or 'tables', 'view <tablename>', 'quit'):")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    
    while True:
        try:
            cmd = input("\nsqlite> ").strip()
            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit", "q"):
                print("Exiting database shell.")
                break
            if cmd.lower() == "tables":
                show_summary()
                continue
            if cmd.lower().startswith("view "):
                tbl = cmd.split(" ", 1)[1].strip()
                query_table(tbl)
                continue

            # Execute SQL
            cursor = conn.cursor()
            cursor.execute(cmd)
            if cmd.strip().upper().startswith("SELECT") or cmd.strip().upper().startswith("PRAGMA"):
                rows = cursor.fetchall()
                if rows:
                    headers = rows[0].keys()
                    print(" | ".join(headers))
                    print("-" * 50)
                    for r in rows:
                        print(" | ".join(str(r[h]) for h in headers))
                else:
                    print("0 rows returned.")
            else:
                conn.commit()
                print(f"Executed successfully. Rows affected: {cursor.rowcount}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "summary":
            show_summary()
        elif arg == "view" and len(sys.argv) > 2:
            query_table(sys.argv[2])
        else:
            show_summary()
    else:
        show_summary()
