import time
import random
import string

import motor.motor_asyncio

import config

client = motor.motor_asyncio.AsyncIOMotorClient(config.MONGO_URI)
db = client[config.DB_NAME]
files_col = db["files"]


def gen_short_id(length: int = 8) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


async def save_file(
    file_name: str,
    file_size: int,
    mime_type: str,
    channel_msg_id: int,
    uploader_id: int,
    magnet: str | None = None,
    info_hash: str | None = None,
) -> str:
    """Insert file metadata and return a short permanent id. Retries on id collision."""
    for _ in range(5):
        short_id = gen_short_id()
        doc = {
            "_id": short_id,
            "file_name": file_name,
            "file_size": file_size,
            "mime_type": mime_type,
            "channel_msg_id": channel_msg_id,
            "uploader_id": uploader_id,
            "upload_date": time.time(),
            "magnet": magnet,
            "info_hash": info_hash,
            "downloads": 0,
        }
        try:
            await files_col.insert_one(doc)
            return short_id
        except Exception:
            continue
    raise RuntimeError("Could not generate a unique short id")


async def get_file(short_id: str):
    return await files_col.find_one({"_id": short_id})


async def increment_downloads(short_id: str):
    await files_col.update_one({"_id": short_id}, {"$inc": {"downloads": 1}})
