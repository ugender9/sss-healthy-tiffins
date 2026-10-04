"""
FastAPI Server with Real-Time WebSockets for S.S.S Healthy Tiffins.
Handles live bidirectional updates between Customers and Admin Dashboard.
"""
import os
import sys
import json
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sss-tiffins")

# Initialize database
database.init_db()

app = FastAPI(
    title="S.S.S Healthy Tiffins - Real-Time Service",
    description="Python FastAPI backend powering real-time order tracking and admin management.",
    version="1.0.0"
)

# Enable CORS for local development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket Connection Manager ---
class ConnectionManager:
    """Manages active WebSocket connections and handles real-time broadcasting."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast event to all connected clients."""
        logger.info(f"Broadcasting event: {message.get('event')} to {len(self.active_connections)} clients")
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending message to client: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

# --- Pydantic Request Models ---
class MenuItemCreate(BaseModel):
    name: str
    price: int
    icon: str = "🥣"
    desc: str = ""
    category: str = "Tiffins"

class BookingItem(BaseModel):
    name: str
    qty: int
    price: int

class BookingCreate(BaseModel):
    customer_name: str
    phone: str
    address: str = ""
    items: List[Dict[str, Any]]
    total_amount: int

class StatusUpdate(BaseModel):
    status: str

class AdminLoginRequest(BaseModel):
    phone: str
    password: str

class AdminOtpVerify(BaseModel):
    phone: str
    otp: str

class SendOtpRequest(BaseModel):
    phone: str
    role: str = "user"  # "user" or "admin"
    name: Optional[str] = ""
    password: Optional[str] = None

class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str
    role: str = "user"  # "user" or "admin"
    name: Optional[str] = ""
    password: Optional[str] = None

class AdminProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    pin: Optional[str] = None
    upi_id: Optional[str] = None
    whatsapp: Optional[str] = None
    timings: Optional[str] = None

class DirectLoginRequest(BaseModel):
    role: Optional[str] = "admin"  # "user" or "admin"
    username: Optional[str] = None
    phone: Optional[str] = None
    password: str

class DirectRegisterRequest(BaseModel):
    role: str = "user"  # "user" or "admin"
    username: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    password: str
    secret_pin: Optional[str] = None
    address: Optional[str] = None

def get_admin_token(request: Request) -> str:
    """Extract admin session token from Authorization header."""
    auth = request.headers.get("Authorization", "")
    return auth.replace("Bearer ", "").strip()

def get_auth_token(request: Request) -> str:
    """Extract general auth session token from Authorization header."""
    auth = request.headers.get("Authorization", "")
    return auth.replace("Bearer ", "").strip()

# --- WebSocket Endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Real-time WebSocket endpoint for instant synchronization across all browser tabs:
    - New bookings alert
    - Live order status transitions (Confirmed -> Preparing -> Out for Delivery -> Delivered)
    - Live menu updates
    - Real-time active counter
    """
    await manager.connect(websocket)
    try:
        # Send initial handshake with current stats
        await websocket.send_json({
            "event": "CONNECTED",
            "message": "Connected to S.S.S Tiffins Real-Time Engine",
            "stats": database.get_stats(),
            "connected_clients": len(manager.active_connections)
        })
        while True:
            # Keep connection open and receive any client heartbeats
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                if parsed.get("action") == "ping":
                    await websocket.send_json({"event": "PONG"})
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# --- REST API Endpoints ---

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "S.S.S Healthy Tiffins Python Engine",
        "active_clients": len(manager.active_connections)
    }

@app.get("/api/stats")
async def get_stats():
    return database.get_stats()

@app.get("/api/menu")
async def get_menu():
    return database.get_all_menu_items()

@app.post("/api/menu")
async def add_menu(item: MenuItemCreate):
    created = database.add_menu_item(
        name=item.name,
        price=item.price,
        icon=item.icon,
        desc=item.desc,
        category=item.category
    )
    # Broadcast real-time event to all connected customers & admin
    await manager.broadcast({
        "event": "MENU_UPDATED",
        "action": "added",
        "item": created,
        "menu": database.get_all_menu_items(),
        "stats": database.get_stats()
    })
    return created

@app.delete("/api/menu/{item_id}")
async def delete_menu(item_id: int):
    success = database.delete_menu_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    await manager.broadcast({
        "event": "MENU_UPDATED",
        "action": "deleted",
        "item_id": item_id,
        "menu": database.get_all_menu_items(),
        "stats": database.get_stats()
    })
    return {"success": True, "deleted_id": item_id}

@app.patch("/api/menu/{item_id}/toggle")
async def toggle_menu_availability(item_id: int):
    updated = database.toggle_menu_item_availability(item_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    await manager.broadcast({
        "event": "MENU_UPDATED",
        "action": "toggled",
        "item": updated,
        "menu": database.get_all_menu_items(),
        "stats": database.get_stats()
    })
    return updated

@app.get("/api/bookings")
async def get_bookings(phone: Optional[str] = None):
    all_b = database.get_all_bookings()
    if phone:
        clean = phone.strip()
        return [b for b in all_b if clean in str(b.get("phone", ""))]
    return all_b

@app.get("/api/bookings/{order_id}")
async def get_booking(order_id: str):
    booking = database.get_booking_by_id(order_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@app.post("/api/bookings")
async def create_booking(booking: BookingCreate):
    # Enforce Taking Orders status
    store_open = database.get_setting("store_open", "1") == "1"
    if not store_open:
        raise HTTPException(
            status_code=403,
            detail="The kitchen is currently closed and not taking orders right now. Please try again later."
        )

    if not booking.items or len(booking.items) == 0:
        raise HTTPException(status_code=400, detail="Order items cannot be empty")
    if not booking.customer_name or not booking.phone:
        raise HTTPException(status_code=400, detail="Name and mobile number are required")

    created = database.create_booking(
        customer_name=booking.customer_name,
        phone=booking.phone,
        address=booking.address,
        items=booking.items,
        total_amount=booking.total_amount
    )

    # Real-time broadcast to Admin and other connected screens
    await manager.broadcast({
        "event": "NEW_BOOKING",
        "booking": created,
        "stats": database.get_stats()
    })

    return created

@app.patch("/api/bookings/{order_id}/status")
@app.post("/api/bookings/{order_id}/status")
@app.patch("/api/admin/bookings/{order_id}/status")
@app.post("/api/admin/bookings/{order_id}/status")
async def update_booking_status(order_id: str, update: StatusUpdate):
    valid_statuses = ["Confirmed", "Preparing", "Out for Delivery", "Delivered", "Cancelled"]
    clean_id = (order_id or "").strip()
    status_str = (update.status or "").strip()

    matched_status = None
    for s in valid_statuses:
        if s.lower() == status_str.lower():
            matched_status = s
            break

    if not matched_status:
        raise HTTPException(status_code=400, detail=f"Invalid status '{update.status}'. Must be one of: {valid_statuses}")

    updated = database.update_booking_status(clean_id, matched_status)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Booking '{clean_id}' not found")

    # Broadcast real-time order status update to customer & admin
    await manager.broadcast({
        "event": "STATUS_UPDATED",
        "order_id": updated["id"],
        "status": matched_status,
        "booking": updated,
        "stats": database.get_stats()
    })

    return updated

# --- Unified Role-Based Authentication & OTP API ---

@app.post("/api/auth/send-otp")
async def auth_send_otp(req: SendOtpRequest):
    """Generate and dispatch OTP for either User or Admin role."""
    phone = req.phone.strip()
    role = (req.role or "user").strip().lower()

    if role == "admin":
        # Admin can authenticate via password or directly if registered admin phone/user
        if req.password:
            if not database.verify_admin_credentials(phone, req.password):
                raise HTTPException(status_code=401, detail="Invalid admin credentials (phone or password)")
        else:
            # Direct OTP mode for admin
            reg_phone = database.get_setting("admin_phone", "9876543210")
            clean_p = "".join(filter(str.isalnum, phone.lower()))
            clean_reg = "".join(filter(str.isalnum, reg_phone.lower()))
            if clean_p not in ["admin", "chef", "manager"] and not clean_p.endswith(clean_reg[-10:]):
                raise HTTPException(status_code=401, detail="Phone number not registered as Admin. Use 9876543210 or enter password.")
        
        # Standardize admin phone for OTP storage
        if phone.lower() in ["admin", "chef", "manager"]:
            phone = database.get_setting("admin_phone", "9876543210")
    else:
        # User validation
        clean_p = "".join(filter(str.isdigit, phone))
        if len(clean_p) < 10:
            raise HTTPException(status_code=400, detail="Please enter a valid 10-digit mobile number")
        phone = clean_p[-10:]

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    database.save_otp(phone, otp, role=role, ttl_seconds=300)

    display_mask = phone[-4:].rjust(len(phone), "*")
    logger.info(f"🔐 [{role.upper()}] Generated OTP for {phone}: {otp}")

    return {
        "success": True,
        "role": role,
        "phone": phone,
        "message": f"OTP sent to {display_mask}",
        "otp_preview": otp  # Shown for easy testing and SMS simulation
    }

@app.post("/api/auth/verify-otp")
async def auth_verify_otp(req: VerifyOtpRequest):
    """Verify OTP and return token and profile for role."""
    phone = req.phone.strip()
    role = (req.role or "user").strip().lower()
    otp = req.otp.strip()

    if role == "admin" and phone.lower() in ["admin", "chef", "manager"]:
        phone = database.get_setting("admin_phone", "9876543210")
    elif role == "user":
        clean_p = "".join(filter(str.isdigit, phone))
        if len(clean_p) >= 10:
            phone = clean_p[-10:]

    if not database.verify_otp(phone, otp, role=role):
        raise HTTPException(status_code=401, detail="Invalid or expired OTP. Please try again.")

    if role == "admin":
        token = database.create_admin_session(phone, ttl_hours=24)
        profile = database.get_admin_profile()
        return {
            "success": True,
            "role": "admin",
            "token": token,
            "admin": profile,
            "message": "Admin login successful! Welcome back, Chef."
        }
    else:
        session = database.create_user_session(phone, name=req.name or "", ttl_hours=72)
        if req.password:
            database.update_user_password(phone, req.password)
        return {
            "success": True,
            "role": "user",
            "token": session["token"],
            "user": {
                "name": session["name"],
                "phone": session["phone"],
                "role": "user"
            },
            "message": f"Welcome, {session['name']}! Dynamic phone OTP verified successfully."
        }

@app.get("/api/auth/session")
async def auth_check_session(request: Request):
    """Validate current session token for admin or customer."""
    token = get_auth_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="No session token provided")

    # Check admin session
    admin_sess = database.verify_admin_session(token)
    if admin_sess:
        return {
            "valid": True,
            "role": "admin",
            "admin": database.get_admin_profile(),
            "session": admin_sess
        }

    # Check customer user session
    user_sess = database.verify_user_session(token)
    if user_sess:
        return {
            "valid": True,
            "role": "user",
            "user": user_sess
        }

    raise HTTPException(status_code=401, detail="Session expired or invalid")

@app.post("/api/auth/logout")
async def auth_logout(request: Request):
    """Revoke session token for admin or user."""
    token = get_auth_token(request)
    if token:
        database.revoke_admin_session(token)
        database.revoke_user_session(token)
    return {"success": True, "message": "Logged out successfully"}

# --- Static Direct Login & Account Creation Endpoints ---

@app.post("/api/admin/login")
@app.post("/api/auth/login")
async def auth_direct_login(req: DirectLoginRequest):
    """Direct login for admin strictly matching name 'ugender' and password '5201314'."""
    role = (req.role or "admin").strip().lower()
    username = (req.username or req.phone or "").strip()
    password = req.password.strip()

    if not username or not password:
        raise HTTPException(status_code=400, detail="Admin username and password are required")

    if role == "admin" or username.lower() in ["ugender", "admin", "chef", "manager"]:
        result = database.authenticate_admin_password(username, password)
        if not result:
            raise HTTPException(
                status_code=401,
                detail="❌ Access denied. Invalid admin credentials."
            )
        return {
            "success": True,
            "role": "admin",
            "token": result["token"],
            "admin": result["admin"],
            "message": f"Welcome back, {result['admin'].get('name', 'ugender')}! Admin login successful."
        }
    else:
        session = database.authenticate_user_password(username, password)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid user credentials. Check mobile/username and password.")
        return {
            "success": True,
            "role": "user",
            "token": session["token"],
            "user": {
                "name": session["name"],
                "phone": session["phone"],
                "role": "user"
            },
            "message": f"Welcome back, {session['name']}! Login successful."
        }

@app.post("/api/auth/register")
async def auth_direct_register(req: DirectRegisterRequest):
    """Direct account creation for user or admin. Statically saved once created."""
    role = (req.role or "user").strip().lower()
    password = req.password.strip()

    if not password or len(password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters long")

    if role == "admin":
        user_id = (req.username or req.phone or "").strip()
        if not user_id:
            raise HTTPException(status_code=400, detail="Admin username or phone is required")
        
        # Verify secret PIN (master default 1234 or existing admin credentials)
        pin = (req.secret_pin or "").strip()
        master_pin = database.get_setting("admin_pin", "1234")
        master_pass = database.get_setting("admin_password", "Admin@123")
        if pin not in [master_pin, master_pass, "1234", "Admin@123", "admin"]:
            raise HTTPException(status_code=401, detail="Invalid Secret Admin Verification PIN. Enter 1234 to authorize admin creation.")

        name = (req.name or "Kitchen Chef").strip()
        result = database.register_admin(user_id, password, name=name, phone=req.phone or "")
        return {
            "success": True,
            "role": "admin",
            "token": result["token"],
            "admin": result["admin"],
            "message": f"Admin account '{name}' created successfully! Statically saved."
        }
    else:
        phone = (req.phone or req.username or "").strip()
        clean_p = "".join(filter(str.isdigit, phone))
        if len(clean_p) < 10 and not phone.isalnum():
            raise HTTPException(status_code=400, detail="Please enter a valid 10-digit mobile number")
        
        phone_num = clean_p[-10:] if len(clean_p) >= 10 else phone
        name = (req.name or f"User-{phone_num[-4:]}").strip()
        session = database.register_user(phone_num, name=name, password=password)
        return {
            "success": True,
            "role": "user",
            "token": session["token"],
            "user": {
                "name": session["name"],
                "phone": session["phone"],
                "role": "user"
            },
            "message": f"Account for {session['name']} created successfully! Statically saved."
        }

# --- Legacy Admin Endpoints (Maintained for Backward Compatibility) ---

@app.post("/api/admin/request-otp")
async def admin_login(req: AdminLoginRequest):
    """Validate phone/user + password, then generate and store OTP."""
    phone = req.phone.strip()
    if not database.verify_admin_credentials(phone, req.password):
        raise HTTPException(status_code=401, detail="Invalid phone number, username, or password")

    if phone.lower() in ["admin", "chef", "manager"]:
        phone = database.get_setting("admin_phone", "9876543210")

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    database.save_admin_otp(phone, otp, ttl_seconds=300)

    logger.info(f"🔐 Admin OTP for {phone}: {otp}")
    display_mask = phone[-4:].rjust(len(phone), "*")

    return {
        "success": True,
        "message": f"OTP sent to {display_mask}",
        "otp_preview": otp,
        "phone": phone
    }

@app.post("/api/admin/verify-otp")
async def admin_verify_otp(req: AdminOtpVerify):
    """Verify admin OTP and issue session token."""
    phone = req.phone.strip()
    if phone.lower() in ["admin", "chef", "manager"]:
        phone = database.get_setting("admin_phone", "9876543210")

    if not database.verify_admin_otp(phone, req.otp):
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    # Create 24-hour session
    token = database.create_admin_session(phone, ttl_hours=24)
    profile = database.get_admin_profile()

    return {
        "success": True,
        "token": token,
        "admin": profile,
        "message": "Login successful! Welcome back, Chef."
    }

@app.get("/api/admin/session")
async def check_admin_session(request: Request):
    """Validate current admin session token."""
    token = get_admin_token(request)
    session = database.verify_admin_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    profile = database.get_admin_profile()
    return {
        "valid": True,
        "admin": profile,
        "session": session
    }

@app.post("/api/admin/logout")
async def admin_logout(request: Request):
    """Revoke admin session."""
    token = get_admin_token(request)
    database.revoke_admin_session(token)
    return {"success": True, "message": "Logged out successfully"}

@app.get("/api/admin/profile")
async def get_admin_profile(request: Request):
    """Get admin profile (protected)."""
    token = get_admin_token(request)
    if not database.verify_admin_session(token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return database.get_admin_profile()

@app.patch("/api/admin/profile")
async def update_admin_profile(req: AdminProfileUpdate, request: Request):
    """Update admin profile settings (protected)."""
    token = get_admin_token(request)
    if not database.verify_admin_session(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    updated = database.update_admin_profile(
        name=req.name, phone=req.phone, password=req.password,
        pin=req.pin, upi_id=req.upi_id, whatsapp=req.whatsapp,
        timings=req.timings
    )

    await manager.broadcast({
        "event": "ADMIN_PROFILE_UPDATED",
        "admin": updated
    })

    return updated

@app.post("/api/admin/store-toggle")
async def toggle_store(request: Request):
    """Toggle store open/close status (protected)."""
    token = get_admin_token(request)
    if not database.verify_admin_session(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    new_state = database.toggle_store_status()
    stats = database.get_stats()

    await manager.broadcast({
        "event": "STORE_STATUS_CHANGED",
        "store_open": new_state,
        "stats": stats
    })

    return {"store_open": new_state, "stats": stats}

@app.get("/api/admin/bookings")
async def get_admin_bookings(request: Request, status: str = None, search: str = None):
    """Get bookings with optional filter/search (protected)."""
    token = get_admin_token(request)
    if not database.verify_admin_session(token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return database.get_all_bookings(status_filter=status, search=search)

@app.delete("/api/admin/bookings/{order_id}")
async def delete_booking(order_id: str, request: Request):
    """Delete a booking record (protected)."""
    token = get_admin_token(request)
    if not database.verify_admin_session(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    database.delete_booking(order_id)

    await manager.broadcast({
        "event": "BOOKING_DELETED",
        "order_id": order_id,
        "stats": database.get_stats()
    })

    return {"success": True, "deleted_id": order_id}

@app.get("/api/admin/export")
async def export_bookings(request: Request):
    """Export all bookings as CSV (protected)."""
    token = get_admin_token(request)
    if not database.verify_admin_session(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    csv_data = database.export_bookings_to_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sss_bookings_export.csv"}
    )

@app.get("/api/admin/settings")
async def get_settings(request: Request):
    """Get all settings (protected)."""
    token = get_admin_token(request)
    if not database.verify_admin_session(token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    settings = database.get_all_settings()
    # Don't expose password in response
    settings.pop("admin_password", None)
    settings.pop("admin_pin", None)
    return settings

# --- Static Frontend Serving ---
CURRENT_DIR = Path(__file__).parent

def find_html_file() -> Path:
    candidates = [
        CURRENT_DIR / "index.html",
        CURRENT_DIR / "sss-healthy-tiffins" / "index.html",
        CURRENT_DIR / "static" / "index.html"
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]

@app.get("/")
@app.get("/index.html")
async def serve_index():
    html_file = find_html_file()
    if html_file.exists():
        return FileResponse(html_file, media_type="text/html")
    return JSONResponse({"error": "Frontend index.html not found"}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    is_prod = bool(os.environ.get("PORT"))
    print("\n" + "=" * 65)
    print(" S.S.S Healthy Tiffins - Real-Time Python Server Running ")
    print(f" Local URL: http://127.0.0.1:{port}")
    print(f" WebSocket: ws://127.0.0.1:{port}/ws")
    print(f" API Docs:  http://127.0.0.1:{port}/docs")
    print("=" * 65 + "\n")
    uvicorn.run("main:app", host=host, port=port, reload=not is_prod)

