# Copyright (c) 2025 DeltaMusic
# Licensed under the MIT License.
# This file is part of DeltaMusic

"""
Advanced Statistics Dashboard - FastAPI Backend
"""

import asyncio
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from delta import app as telegram_app
from delta import config, db, logger

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                continue

manager = ConnectionManager()

# Create FastAPI app
dashboard_app = FastAPI(
    title="DeltaMusic Statistics Dashboard",
    description="Real-time statistics and analytics for DeltaMusic Bot",
    version="1.0.0"
)

# Enable CORS
dashboard_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response Models
class StatsOverview(BaseModel):
    total_users: int
    total_chats: int
    total_plays: int
    active_calls: int


class TopTrack(BaseModel):
    id: str
    title: str
    play_count: int
    duration: str
    image: Optional[str] = None


class TopUser(BaseModel):
    user_id: int
    username: Optional[str]
    play_count: int
    image: Optional[str] = None


class TopChat(BaseModel):
    chat_id: int
    chat_name: Optional[str]
    play_count: int
    image: Optional[str] = None


class DailyStats(BaseModel):
    date: str
    play_count: int


# API Routes
@dashboard_app.get("/")
async def read_root():
    """Serve the dashboard HTML"""
    index_path = Path(__file__).parent / "index.html"
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@dashboard_app.get("/miniapp")
async def read_miniapp():
    """Serve the Telegram Mini App HTML"""
    miniapp_path = Path(__file__).parent / "miniapp.html"
    with open(miniapp_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@dashboard_app.get("/manifest.json")
async def read_manifest():
    """Serve the PWA Manifest"""
    manifest_path = Path(__file__).parent / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), media_type="application/json")


@dashboard_app.get("/api/overview", response_model=StatsOverview)
async def get_overview():
    """Get overall statistics overview"""
    try:
        users = await db.get_users()
        chats = await db.get_chats()
        total_plays = await db.get_queries()
        active_calls = await db.active_callsdb.count_documents({})

        return StatsOverview(
            total_users=len(users),
            total_chats=len(chats),
            total_plays=total_plays,
            active_calls=active_calls
        )
    except Exception as e:
        logger.error(f"Error getting overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@dashboard_app.get("/api/top-tracks")
async def get_top_tracks(limit: int = 10):
    """Get top played tracks globally"""
    try:
        tracks = await db.get_global_tops(limit=limit)
        
        result = []
        for track_id, data in tracks.items():
            result.append({
                "id": track_id,
                "title": data["title"],
                "play_count": data["spot"],
                "duration": data["duration"],
                "image": data.get("thumbnail")
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting top tracks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@dashboard_app.get("/api/top-users")
async def get_top_users(limit: int = 10):
    """Get most active users globally"""
    try:
        # Identify excluded IDs (Bot and Assistants)
        excluded_ids = {telegram_app.id}
        from delta import userbot
        for client in userbot.clients:
            if hasattr(client, 'id'):
                excluded_ids.add(client.id)
            elif hasattr(client, 'me') and client.me:
                excluded_ids.add(client.me.id)
        
        # Fetch more users to allow for filtering
        users_data = await db.get_top_users(limit=limit + 5)
        
        result = []
        for user_id, count in users_data.items():
            if user_id in excluded_ids:
                continue
            
            # Try to get username from Telegram
            try:
                user = await telegram_app.get_users(user_id)
                username = user.username or user.first_name or f"User {user_id}"
            except:
                username = f"User {user_id}"
            
            result.append({
                "user_id": user_id,
                "username": username,
                "play_count": count,
                "image": None # Placeholder handled by frontend
            })
            
            if len(result) >= limit:
                break
        
        return result
    except Exception as e:
        logger.error(f"Error getting top users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@dashboard_app.get("/api/top-chats")
async def get_top_chats(limit: int = 10):
    """Get most active groups globally"""
    try:
        chats_data = await db.get_top_chats(limit=limit)
        
        result = []
        for chat_id, count in chats_data.items():
            # Try to get chat name from Telegram
            try:
                chat = await telegram_app.get_chat(chat_id)
                chat_name = chat.title or f"Chat {chat_id}"
            except:
                chat_name = f"Chat {chat_id}"
            
            result.append({
                "chat_id": chat_id,
                "chat_name": chat_name,
                "play_count": count,
                "image": None # Placeholder handled by frontend
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting top chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@dashboard_app.get("/api/daily-stats")
async def get_daily_stats(days: int = 7):
    """Get daily statistics for the last N days"""
    try:
        # Get daily play counts from database
        result = await db.get_daily_play_count(days=days)
        return result
    except Exception as e:
        logger.error(f"Error getting daily stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@dashboard_app.get("/api/peak-hours")
async def get_peak_hours(days: int = 7):
    """Get peak activity hours"""
    try:
        data = await db.get_peak_hours(days=days)
        return {"data": data}
    except Exception as e:
        logger.error(f"Error getting peak hours: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@dashboard_app.get("/api/platform-distribution")
async def get_platform_distribution():
    """Get platform distribution statistics"""
    try:
        data = await db.get_platform_stats()
        return {"data": data}
    except Exception as e:
        logger.error(f"Error getting platform distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@dashboard_app.get("/api/active-calls")
async def get_active_calls():
    """Get currently active voice calls"""
    try:
        active = []
        active_chats = await db.get_active_calls()
        for chat_id in active_chats:
            try:
                chat = await telegram_app.get_chat(chat_id)
                active.append({
                    "chat_id": chat_id,
                    "chat_name": chat.title or f"Chat {chat_id}",
                    "is_playing": await db.playing(chat_id)
                })
            except:
                active.append({
                    "chat_id": chat_id,
                    "chat_name": f"Chat {chat_id}",
                    "is_playing": await db.playing(chat_id)
                })
        
        return active
    except Exception as e:
        logger.error(f"Error getting active calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@dashboard_app.get("/api/group-stats/{chat_id}")
async def get_group_stats(chat_id: int, limit: int = 10):
    """Get statistics for a specific group"""
    try:
        # Get top tracks for this group
        tracks = await db.get_group_stats(chat_id, limit=limit)
        
        # Get top users for this group
        users = await db.get_group_top_users(chat_id, limit=limit)
        
        return {
            "chat_id": chat_id,
            "top_tracks": [
                {
                    "id": track_id,
                    "title": data["title"],
                    "play_count": data["spot"],
                    "duration": data["duration"]
                }
                for track_id, data in tracks.items()
            ],
            "top_users": [
                {
                    "user_id": int(user_id),
                    "play_count": count
                }
                for user_id, count in users.items()
            ]
        }
    except Exception as e:
        logger.error(f"Error getting group stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files
try:
    static_path = Path(__file__).parent / "static"
    if not static_path.exists():
        static_path.mkdir(exist_ok=True)
        logger.warning(f"Created missing directory: {static_path}")
    dashboard_app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


# Run server function
async def run_dashboard_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the dashboard server"""
    import uvicorn
    
    config_uvicorn = uvicorn.Config(
        dashboard_app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config_uvicorn)
    
    logger.info(f"📊 Dashboard server starting on http://{host}:{port}")
    await server.serve()


@dashboard_app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


async def broadcast_stats():
    """Background task to broadcast stats to connected clients"""
    last_data = {}
    import time
    
    # Try importing psutil
    try:
        import psutil
    except ImportError:
        psutil = None
        logger.warning("psutil not installed, server stats will be unavailable")

    boot_time = psutil.boot_time() if psutil else time.time()
    
    # Network tracking
    last_network_io = psutil.net_io_counters() if psutil else None
    last_network_time = time.time()

    while True:
        try:
            # 1. Overview Stats
            users_count = len(await db.get_users())
            chats_count = len(await db.get_chats())
            plays_count = await db.get_queries()
            active_calls = await db.active_callsdb.count_documents({})
            
            # System Stats
            sys_stats = None
            if psutil:
                try:
                    cpu = psutil.cpu_percent(interval=None)
                    ram = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    uptime_seconds = int(time.time() - boot_time)
                    
                    # Network speed calculation
                    current_network_io = psutil.net_io_counters()
                    current_time = time.time()
                    time_delta = current_time - last_network_time
                    
                    upload_speed = 0
                    download_speed = 0
                    if last_network_io and time_delta > 0:
                        upload_speed = (current_network_io.bytes_sent - last_network_io.bytes_sent) / time_delta
                        download_speed = (current_network_io.bytes_recv - last_network_io.bytes_recv) / time_delta
                    
                    last_network_io = current_network_io
                    last_network_time = current_time
                    
                    sys_stats = {
                        "cpu": cpu,
                        "ram": ram.percent,
                        "disk": disk.percent,
                        "uptime": uptime_seconds,
                        "network": {
                            "upload_speed": upload_speed,
                            "download_speed": download_speed,
                            "total_sent": current_network_io.bytes_sent,
                            "total_recv": current_network_io.bytes_recv
                        }
                    }
                except Exception as ex:
                    logger.error(f"Error getting sys stats: {ex}")

            overview = {
                "type": "overview",
                "data": {
                    "total_users": users_count,
                    "total_chats": chats_count,
                    "total_plays": plays_count,
                    "active_calls": active_calls,
                    "system": sys_stats
                }
            }
            
            # Broadcast if changed (simplistic check, ideally check diff)
            # For now, just broadcast every 5s to keep alive and ensure sync
            await manager.broadcast(overview)
            
            # 2. Lists (Top Tracks, etc) - Broadcast less frequently or on change?
            # For simplicity, let's assume lists are heavy and clients can fetch them 
            # or we broadcast a "refresh" signal
            
        except Exception as e:
            logger.error(f"Error in broadcast task: {e}")
        
        await asyncio.sleep(5)


@dashboard_app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_stats())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(dashboard_app, host="0.0.0.0", port=8000)
