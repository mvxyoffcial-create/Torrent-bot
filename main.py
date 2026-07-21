import os
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId

# --- CONFIGURATION ---
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
SESSION_STRING = os.getenv("SESSION_STRING", "") # Telegram Premium String Session for 4GB uploads
BIN_CHANNEL_ID = int(os.getenv("BIN_CHANNEL_ID", "-100123456789"))
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
PORT = int(os.getenv("PORT", "8080")) # Required for Koyeb

# --- INITIALIZATION ---
app = Client("fast_store_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client["fast_file_store"]
files_collection = db["files"]


# --- KOYEB HEALTH CHECK ROUTE ---
async def health_check(request):
    """Responds to Koyeb health checks with 200 OK."""
    return web.Response(text="Bot is healthy and running!", status=200)

async def start_web_server():
    server = web.Application()
    server.router.add_get("/", health_check)
    server.router.add_get("/health", health_check)
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"🌐 Health check HTTP server running on port {PORT}")


# --- TELEGRAM BOT HANDLERS ---
@app.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def process_file_instantly(client: Client, message: Message):
    start_time = asyncio.get_event_loop().time()
    
    # Forward file to storage channel
    forwarded_msg = await message.forward(chat_id=BIN_CHANNEL_ID)
    
    media = forwarded_msg.document or forwarded_msg.video or forwarded_msg.audio
    file_id = media.file_id
    file_name = getattr(media, "file_name", "Telegram_File")
    file_size = getattr(media, "file_size", 0)
    file_unique_id = media.file_unique_id

    # Insert into Mongo
    db_record = {
        "file_name": file_name,
        "file_size": file_size,
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "bin_message_id": forwarded_msg.id,
        "user_id": message.from_user.id
    }
    insert_result = await files_collection.insert_one(db_record)
    mongo_id = str(insert_result.inserted_id)

    # Links
    bot_info = await client.get_me()
    direct_link = f"https://t.me/{bot_info.username}?start=file_{mongo_id}"
    trackers = "&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce"
    magnet_link = f"magnet:?xt=urn:btih:{file_unique_id}&dn={file_name}&xl={file_size}{trackers}"

    elapsed_time = round(asyncio.get_event_loop().time() - start_time, 2)

    response_text = (
        f"⚡ **Processed in {elapsed_time}s!**\n\n"
        f"📁 **Name:** `{file_name}`\n"
        f"📦 **Size:** `{round(file_size / (1024 * 1024), 2)} MB`\n\n"
        f"🔗 **Permanent Link:**\n`{direct_link}`\n\n"
        f"🧲 **Instant Magnet Link:**\n`{magnet_link}`"
    )

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Direct Link", url=direct_link)]
    ])

    await message.reply_text(response_text, reply_markup=reply_markup, disable_web_page_preview=True)


@app.on_message(filters.command("start") & filters.private)
async def serve_file(client: Client, message: Message):
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("file_"):
        mongo_id = args[1].replace("file_", "")
        file_record = await files_collection.find_one({"_id": ObjectId(mongo_id)})
        
        if file_record:
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=BIN_CHANNEL_ID,
                message_id=file_record["bin_message_id"]
            )
        else:
            await message.reply_text("❌ File not found in database or was removed.")
    else:
        await message.reply_text("Send any file up to 4GB to store permanently and get links instantly!")


# --- MAIN ENTRY POINT ---
async def main():
    await start_web_server()
    await app.start()
    print("🤖 Bot is active...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
