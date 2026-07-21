# ==== Telegram API credentials (from https://my.telegram.org) ====
API_ID = 36282056                       # your api_id
API_HASH = "3a948acece533f362b4c90b2b3c14b60"      # your api_hash

# ==== Bot ====
BOT_TOKEN = "8955122333:AAEqVijtClBjLLY-rFFsQZWN5wXRFfwmXVs"

# ==== Bin channel (private channel where all files are stored) ====
# Bot AND userbot must both be admins here.
BIN_CHANNEL = -1004393509819

# ==== MongoDB ====
MONGO_URI = "mongodb+srv://cloudnestoffcail_db_user:Venura8907@cluster0.hjqkg75.mongodb.net/?appName=Cluster0"
DB_NAME = "filestore"

# ==== Local Bot API server ====
# Required to receive files >20MB and send up to 2000MB (2GB) as a bot.
# Run via: https://github.com/tdlib/telegram-bot-api (see Dockerfile)
LOCAL_SERVER = True
LOCAL_API_URL = "http://localhost:8081"

# ==== Userbot (for files between 2GB and 4GB) ====
# Session string/name for a logged-in USER account (not a bot).
# That account needs Telegram Premium to send files >2GB (up to 4GB).
USE_USERBOT_FOR_LARGE = True
USERBOT_SESSION = "userbot"          # pyrogram session name, generated once via login

# ==== Local storage ====
DOWNLOAD_DIR = "./downloads"
TORRENT_DIR = "./torrents"

# ==== Torrent / libtorrent ====
SEED_PORT_MIN = 6881
SEED_PORT_MAX = 6891
TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.tracker.cl:1337/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
    "udp://exodus.desync.com:6969/announce",
]

TWO_GB = 2 * 1024 * 1024 * 1024
FOUR_GB = 4 * 1024 * 1024 * 1024
