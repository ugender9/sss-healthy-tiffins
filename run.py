"""
Convenient one-click launcher for S.S.S Healthy Tiffins Python Engine.
Run with: python run.py
"""
import sys
import time
import webbrowser
import threading
import uvicorn
import database

def open_browser():
    """Wait for server startup, then open the browser automatically."""
    time.sleep(1.2)
    url = "http://127.0.0.1:8000"
    print(f"🌐 Opening {url} in your default browser...")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Could not open browser automatically: {e}")

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("\n" + "=" * 65)
    print(" S.S.S Healthy Tiffins - Real-Time Python Kitchen ")
    print("=" * 65)
    
    # Initialize SQLite database
    database.init_db()
    stats = database.get_stats()
    print(f" Database Ready: {stats['total_menu_items']} menu items, {stats['total_bookings']} bookings.")
    print(" Real-Time WebSockets: Active")
    print(" Server starting at: http://127.0.0.1:8000")
    print(" API Documentation: http://127.0.0.1:8000/docs")
    print("=" * 65 + "\n")

    # Start browser opener in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Launch FastAPI with Uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

