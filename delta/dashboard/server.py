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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from delta import app as telegram_app
from delta import config, db, logger

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


@dashboard_app.get("/api/overview", response_model=StatsOverview)
async def get_overview():
    """Get overall statistics overview"""
    try:
        users = await db.get_users()
        chats = await db.get_chats()
        total_plays = await db.get_queries()
        active_calls = len(db.active_calls)

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


@dashboard_app.get("/api/active-calls")
async def get_active_calls():
    """Get currently active voice calls"""
    try:
        active = []
        for chat_id in db.active_calls.keys():
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(dashboard_app, host="0.0.0.0", port=8000)
