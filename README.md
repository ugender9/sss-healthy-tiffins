# 🌿 S.S.S Healthy Tiffins — Real-Time Morning Kitchen

A full-stack, real-time morning tiffin ordering and kitchen management system built with **Python FastAPI**, **WebSockets**, **SQLite**, and modern **vanilla HTML/CSS/JavaScript**.

---

## ⚡ Key Real-Time Features

1. **Bi-Directional Live Sync via WebSockets**:
   - When a customer places a booking, the **Admin Operations Center** receives it instantly without refreshing the page.
   - Synthesizer **audio chime alert** plays automatically for the kitchen staff upon new order arrival.
   - When the admin updates order status (*Confirmed* ➔ *Preparing* ➔ *Out for Delivery* ➔ *Delivered*), the customer's live order tracking stepper updates immediately in real-time.
   - Menu changes (adding dishes, toggling stock availability, deleting) broadcast live to all active customer screens.

2. **Python Backend for Easy Maintenance**:
   - **FastAPI**: Asynchronous, high-performance web framework.
   - **Native WebSockets**: `ConnectionManager` broadcasts events to all active clients.
   - **SQLite (`tiffins.db`)**: Zero-configuration, file-based database storing menu items and order histories with ACID guarantees.
   - **Interactive API Docs**: Built-in Swagger UI at `http://127.0.0.1:8000/docs`.

3. **Client UI & Aesthetics**:
   - Modern typography (`Outfit` and `Playfair Display`).
   - Warm organic aesthetic (Forest green `#145c48`, Sunny gold `#f6b84b`, Mint `#e2f4e4`, Coral `#e66b52`).
   - Live connection indicator (`🟢 Live Server Sync`) with automatic reconnection resilience.
   - Slide-out Cart drawer with instant price calculation.

---

## 🚀 How to Run

### Method 1: Using Python Launcher (Recommended)
```powershell
python run.py
```
*This initializes the database, starts the Uvicorn server, and opens `http://127.0.0.1:8000` in your default browser automatically.*

### Method 2: Double-click Windows Batch File
Double-click `start.bat` in the project folder.

### Method 3: Direct Uvicorn Command
```powershell
uvicorn main:app --reload --port 8000
```

### Method 4: Visual Studio Code
Press `F5` or go to the **Run & Debug** panel and choose:
- **Python: S.S.S Tiffins Real-Time Server**

---

## 📂 Project Architecture

```
sss-healthy-tiffins/
├── main.py              # FastAPI server, REST API endpoints, WebSocket connection manager
├── database.py          # SQLite database schema, seed data, and CRUD operations
├── run.py               # One-click startup script with browser launcher
├── start.bat            # Windows batch shortcut launcher
├── requirements.txt     # Python dependencies
├── tiffins.db           # SQLite database file (auto-created on first run)
├── index.html           # Real-time customer & admin web application
├── test_realtime.py     # End-to-end WebSocket and REST test suite
└── .vscode/
    └── launch.json      # VS Code debugging configurations
```

---

## 🛠️ REST API & WebSocket Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the single-page application |
| `GET` | `/api/health` | Health check & active client count |
| `GET` | `/api/stats` | Today's total bookings, revenue, and active orders |
| `GET` | `/api/menu` | List all menu items |
| `POST` | `/api/menu` | Add a new menu dish (broadcasts `MENU_UPDATED`) |
| `PATCH` | `/api/menu/{id}/toggle` | Toggle in-stock/sold-out status |
| `DELETE` | `/api/menu/{id}` | Delete menu dish |
| `GET` | `/api/bookings` | List all customer bookings |
| `POST` | `/api/bookings` | Create new booking (broadcasts `NEW_BOOKING`) |
| `PATCH` | `/api/bookings/{id}/status` | Update status (broadcasts `STATUS_UPDATED`) |
| `WS` | `/ws` | WebSocket endpoint for real-time live events |

---

## 🧪 Testing the Real-Time Sync

Run the automated integration test:
```powershell
python test_realtime.py
```
This tests WebSocket connection handshake, booking placement, event broadcast, and status update transitions end-to-end.
