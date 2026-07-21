import asyncio
import os

from pyrogram import Client, filters, idle
from pyrogram.types import Message

import config
import db
import torrent as torrent_mod
from health import start_health_server

bot = Client(
    "filebot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    base_url=config.LOCAL_API_URL if config.LOCAL_SERVER else None,
)

userbot = (
    Client(config.USERBOT_SESSION, api_id=config.API_ID, api_hash=config.API_HASH)
    if config.USE_USERBOT_FOR_LARGE
    else None
)


@bot.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    if len(message.command) > 1:
        short_id = message.command[1]
        doc = await db.get_file(short_id)
        if not doc:
            await message.reply("That link is invalid or the file no longer exists.")
            return
        await client.copy_message(
            chat_id=message.chat.id,
            from_chat_id=config.BIN_CHANNEL,
            message_id=doc["channel_msg_id"],
        )
        await db.increment_downloads(short_id)
        return

    await message.reply(
        "Send me any file (up to 4GB).\n"
        "I'll store it permanently and give you a Telegram link plus a magnet link."
    )


@bot.on_message(filters.document | filters.video | filters.audio)
async def file_handler(client: Client, message: Message):
    media = message.document or message.video or message.audio
    file_name = media.file_name or f"file_{media.file_unique_id}"
    file_size = media.file_size
    mime_type = getattr(media, "mime_type", None)

    if file_size > config.FOUR_GB:
        await message.reply("File is larger than 4GB, sorry — I can't store that.")
        return

    status = await message.reply("⬇️ Downloading...")

    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
    local_path = os.path.join(config.DOWNLOAD_DIR, file_name)
    await message.download(file_name=local_path)

    await status.edit("🧲 Building torrent / magnet link...")
    magnet, info_hash = None, None
    try:
        magnet, info_hash, _ = torrent_mod.create_torrent_and_seed(local_path)
    except Exception as e:
        magnet, info_hash = None, None
        await status.edit(f"⚠️ Torrent step failed ({e}), continuing with upload...")

    await status.edit("⬆️ Uploading to storage channel...")
    if file_size <= config.TWO_GB or userbot is None:
        # Bot can handle this size directly, and copy_message avoids a re-upload
        # when the file is still small enough to just reference the original message.
        sent = await client.copy_message(
            chat_id=config.BIN_CHANNEL,
            from_chat_id=message.chat.id,
            message_id=message.id,
        )
    else:
        # 2GB-4GB: requires a Premium user account session.
        # userbot is already running (started once in main()), reuse it directly.
        sent = await userbot.send_document(
            chat_id=config.BIN_CHANNEL,
            document=local_path,
            file_name=file_name,
        )
    channel_msg_id = sent.id

    short_id = await db.save_file(
        file_name,
        file_size,
        mime_type,
        channel_msg_id,
        message.from_user.id,
        magnet,
        info_hash,
    )

    me = await client.get_me()
    perm_link = f"https://t.me/{me.username}?start={short_id}"

    text = f"✅ **{file_name}**\n\n🔗 Permanent link:\n{perm_link}"
    if magnet:
        text += f"\n\n🧲 Magnet link:\n`{magnet}`"

    await status.edit(text)

    # cleanup local copy — torrent session keeps seeding from TORRENT_DIR/DOWNLOAD_DIR,
    # so don't delete local_path if you want the swarm to keep working.


async def main():
    await start_health_server()
    print(f"Health server up on port {os.environ.get('PORT', 8000)}")

    await bot.start()
    print("Bot started.")

    if userbot is not None:
        await userbot.start()
        print("Userbot started.")

    await idle()

    await bot.stop()
    if userbot is not None:
        await userbot.stop()


if __name__ == "__main__":
    asyncio.run(main())
