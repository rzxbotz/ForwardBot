from pyrogram import Client

API_ID = int(17427408)
API_HASH = "9699e632de895e7d566c241615a0e637"
BOT_TOKEN ="5919513919:AAFJq8uqhYJRpu_vx-QWjyW0D9X3vSTwfms"
DB_URI = "mongodb+srv://dudemusic111:dudemusic111@cluster0.df3yis2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
REGEX_PATTERN = r"s\d{1,2}[\.\s]?e[p]?\d{1,2}|season|\bepisode\b"
LOG_CHANNEL_ID = "-1001930341741"

class temp(object):
    CANCEL=False

User = Client("Forward-user", session_string=SESSION)
