# 🚀 Deployment Guide — S.S.S Healthy Tiffins

This project is a real-time full-stack application built with **FastAPI**, **WebSockets**, and **SQLite**.

All necessary production deployment files are configured:
- `Dockerfile` & `docker-compose.yml` (Container deployment)
- `render.yaml` & `Procfile` (Render deployment)
- `railway.json` (Railway deployment)
- `fly.toml` (Fly.io deployment)

---

## Option 1: Render.com (Recommended Free/Easy Cloud Hosting)

Render provides free/inexpensive web services with native WebSocket support.

### Steps:
1. Initialize Git and push your repository to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for S.S.S Healthy Tiffins"
   git branch -M main
   # Add your github remote:
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** ➔ **Web Service**.
3. Connect your GitHub repository.
4. Settings:
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variable**: `PYTHON_VERSION` = `3.11.1`
5. Click **Create Web Service**. Your app and live WebSockets will be running on your `onrender.com` URL!

---

## Option 2: Railway.app (Zero-Config 1-Click Deploy)

Railway supports Python, WebSockets, and SQLite out of the box.

### Steps:
1. Push your code to GitHub (as shown above).
2. Go to [Railway.app](https://railway.app/).
3. Click **New Project** ➔ **Deploy from GitHub repo**.
4. Select this repository. Railway automatically detects `requirements.txt` and `Procfile`.
5. Under Settings ➔ Networking, click **Generate Domain** to get your public HTTPS/WSS URL.

---

## Option 3: Docker / Self-Hosted VPS

If you have a Linux server (DigitalOcean, Hetzner, AWS EC2, Linode, etc.):

```bash
# Clone the repository
git clone <repo-url>
cd sss-healthy-tiffins

# Run with Docker Compose
docker compose up -d --build
```
Your service will be live on port `8000`.

---

## Option 4: Instant Public Live URL from Local Machine (Demo / Quick Share)

If you want an immediate live link accessible from any smartphone, customer, or remote device without cloud signups:

```powershell
# 1. Start your local server in one terminal
python run.py

# 2. In another terminal, create an instant tunnel using npx:
npx localtunnel --port 8000
```
This generates an instant HTTPS URL connected directly to your local live kitchen.
