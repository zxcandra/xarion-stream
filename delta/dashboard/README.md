# 📊 DeltaMusic Statistics Dashboard

> **Beautiful, Real-time Analytics Dashboard for DeltaMusic Bot**

![Dashboard](https://img.shields.io/badge/Status-Production%20Ready-success)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-blue)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4+-orange)

---

## 🎯 Quick Start

### 1️⃣ Install Dependencies

```bash
pip install -r dashboard/requirements.txt
```

### 2️⃣ Run Dashboard

**Option A: Quick Start Script** (Recommended)
```bash
python run_dashboard.py
```

**Option B: Direct Run**
```bash
python dashboard/server.py
```

### 3️⃣ Open Browser

Navigate to: **http://localhost:8000**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📈 **Live Charts** | Interactive play count trends |
| 🏆 **Top Tracks** | Most played songs (YouTube only) |
| 👥 **Active Users** | User leaderboard with avatars |
| 💬 **Group Rankings** | Most active groups |
| � **Telegram UI** | Native iOS-style grouped list design |
| 🔍 **Smart Filtering** | Auto-hides Live & Files from top lists |
| � **Scrollable** | Optimized lists for 100+ items |
| 🎨 **Modern Design** | Beautiful gradients & glassmorphism |
| 🔄 **Auto-Refresh** | Real-time updates |

---

## 🧠 Stats Logic & Filtering

The dashboard employs smart filtering to keep lists clean and relevant:

### 🎵 Top Tracks Logic
- **Music Only:** The main "Top Tracks" list **only** displays formatted music tracks (usually from YouTube).
- **Excluded Content:**
  - 🎥 **Live Streams:** Tracks with duration "Live" or "Unknown" are automatically hidden.
  - 📁 **Files:** Local Telegram audio files (which lack thumbnails) are excluded from the visual leaderboard.
  - ⚡ **Stream Type:** Database stores specific `stream_type` (`music`, `live`, `file`) for precise categorization.

### 👥 User & Group Logic
- **Avatars:** Uses a smart placeholder system with colored initials if no photo URL is available, ensuring fast load times.
- **Scrollable Lists:** "Top Tracks" supports infinite scrolling up to 100 items.

---

## 📸 Screenshot

```
┌─────────────────────────────────────────────────────────┐
│  Stats Dashboard                                        │
│  [ Header Gradient with Totals ]                        │
│                                                         │
│  [ Play Count Trend Chart ]                             │
│                                                         │
│  TOP TRACKS (Scrollable)                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │ 1. Attention                  420 plays [>]       │  │
│  │    3:33                                           │  │
│  │ ───────────────────────────────────────────────── │  │
│  │ 2. Blinding Lights            380 plays [>]       │  │
│  │    3:22                                           │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  TOP USERS                                              │
│  ┌───────────────────────────────────────────────────┐  │
│  │ [A] User A                    150 plays           │  │
│  │     ID: 12345                                     │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🌐 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard UI |
| `GET /docs` | API Documentation (Swagger) |
| `GET /api/overview` | Overall statistics |
| `GET /api/top-tracks` | Top played tracks |
| `GET /api/top-users` | Most active users |
| `GET /api/top-chats` | Most active groups |
| `GET /api/daily-stats` | Daily play counts |
| `GET /api/active-calls` | Current voice calls |
| `GET /api/group-stats/{id}` | Group-specific stats |

**Full API Documentation:** http://localhost:8000/docs

---

## 💻 Telegram Commands

### For Users
```
/stats              Get statistics for current group
```

### For Admins
```
/dashboard          Show dashboard info
/dashboard start    Start dashboard server
/dashboard stop     Stop dashboard server
```

---

## 🔧 Configuration

### Change Port

Edit `dashboard/server.py`:
```python
uvicorn.run(dashboard_app, host="0.0.0.0", port=8080)  # Change 8000 to 8080
```

### Change Refresh Interval

Edit `dashboard/index.html`:
```javascript
setInterval(loadAllData, 60000);  // Change 30000 to 60000 (60 seconds)
```

### Customize Colors

Edit `dashboard/index.html` CSS:
```css
background: linear-gradient(135deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%);
```

---

## 🚀 Deployment

### Development
```bash
python run_dashboard.py
```

### Production (with Gunicorn)
```bash
pip install gunicorn
gunicorn dashboard.server:dashboard_app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker
```bash
docker build -t deltamusic-dashboard .
docker run -p 8000:8000 deltamusic-dashboard
```

---

## 📊 Tech Stack

- **Backend:** FastAPI + Uvicorn
- **Frontend:** HTML5 + Vanilla JavaScript
- **Charts:** Chart.js 4.4
- **Database:** MongoDB (shared with bot)
- **Styling:** Pure CSS with Glassmorphism

---

## 🐛 Troubleshooting

### Dashboard won't start?
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Try different port
python dashboard/server.py --port 8080
```

### No data showing?
```bash
# Ensure bot is running and has processed some plays
# Check MongoDB connection
python -c "from delta import db; import asyncio; asyncio.run(db.connect())"
```

### Charts not rendering?
- Clear browser cache
- Check browser console for errors
- Ensure internet connection (for Chart.js CDN)

---

## 📝 Requirements

- Python 3.8+
- FastAPI 0.109+
- Uvicorn 0.27+
- Pydantic 2.5+
- MongoDB (via bot)

---

## 🎨 Customization Guide

### Add New Chart

```javascript
// In index.html
const myChart = new Chart(ctx, {
    type: 'bar',  // or 'pie', 'doughnut', etc.
    data: { /* your data */ },
    options: { /* your options */ }
});
```

### Add New API Endpoint

```python
# In dashboard/server.py
@dashboard_app.get("/api/my-endpoint")
async def my_endpoint():
    # Your logic here
    return {"message": "Hello"}
```

### Add Authentication

```python
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

@dashboard_app.get("/api/overview")
async def get_overview(credentials: HTTPBasicCredentials = Depends(security)):
    # Verify credentials
    return data
```

---

## 📚 Documentation

- **Full Guide:** See `dashboard_guide.md`
- **API Docs:** http://localhost:8000/docs (when running)
- **Redoc:** http://localhost:8000/redoc (alternative API docs)

---

## 🙏 Credits

Built with ❤️ for DeltaMusic Bot

- Dashboard Framework: [FastAPI](https://fastapi.tiangolo.com/)
- Charts: [Chart.js](https://www.chartjs.org/)
- Icons: Emoji (native)

---

## 📄 License

MIT License - Same as DeltaMusic Bot

---

## 🚧 Roadmap

- [ ] WebSocket for real-time updates
- [ ] Export data (CSV/JSON)
- [ ] User authentication system
- [ ] Dark/Light theme toggle
- [ ] Mobile app version
- [ ] Advanced analytics (genre, time-based)
- [ ] Notification system
- [ ] Multi-language support

---

**Enjoy your beautiful dashboard! 📊✨**

For issues or questions, check `dashboard_guide.md` or contact the bot admin.
