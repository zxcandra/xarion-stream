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
logger = logging.getLogger(__name__)


__version__ = "3.0.1"

from config import Config

config = Config()
config.check()
tasks = []
boot = time.time()

from anony.core.bot import Bot
app = Bot()

from anony.core.dir import ensure_dirs
ensure_dirs()

from anony.core.userbot import Userbot
userbot = Userbot()

from anony.core.mongo import MongoDB
db = MongoDB()

from anony.core.telegram import Telegram
from anony.core.youtube import YouTube
tg = Telegram()
yt = YouTube()

# Import Queue directly to avoid any circular import issues
from anony.helpers._queue import Queue as QueueClass
queue = QueueClass()

from anony.core.calls import TgCall
anon = TgCall()

# Import utilities with lazy loading to avoid circular imports
from anony.helpers._cleanup import cleanup
from anony.helpers._lyrics import lyrics_searcher


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
    await lyrics_searcher.close()

    logger.info("Stopped.\n")
