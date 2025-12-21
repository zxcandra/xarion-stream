# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import time
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=10485760, backupCount=5),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.CRITICAL)
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)
logging.getLogger("yt_dlp").setLevel(logging.CRITICAL)
logger = logging.getLogger(__name__)


__version__ = "3.0.1"

from config import Config

config = Config()
config.check()
tasks = []
boot = time.time()

from delta.core.bot import Bot
app = Bot()

from delta.core.dir import ensure_dirs
ensure_dirs()

from delta.core.userbot import Userbot
userbot = Userbot()

from delta.core.mongo import MongoDB
db = MongoDB()

from delta.core.telegram import Telegram
from delta.core.youtube import YouTube
tg = Telegram()
yt = YouTube()

# Import Queue directly - NO DEPENDENCY on delta package
from delta.helpers._queue import Queue
queue = Queue()

from delta.core.calls import TgCall
anon = TgCall()


# These are initialized lazily in __main__.py to avoid circular imports
# cleanup = None
# lyrics_searcher = None


async def stop() -> None:
    logger.info("Stopping...")
    for task in tasks:
        task.cancel()
        try:
            await task
        except:
            pass

    await app.exit()
    await userbot.exit()
    await db.close()

    logger.info("Stopped.\n")
