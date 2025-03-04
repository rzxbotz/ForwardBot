from pyrogram import Client

API_ID = int(17427408)
API_HASH = "9699e632de895e7d566c241615a0e637"
BOT_TOKEN ="5919513919:AAFJq8uqhYJRpu_vx-QWjyW0D9X3vSTwfms"
DB_URI = "mongodb+srv://dudemusic111:dudemusic111@cluster0.df3yis2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DELETE_REGEX = r"s\d{1,2}[\.\s]?e[p]?\d{1,2}|season|\bepisode\b"
LOG_CHANNEL = "-1001930341741"
SESSION = "AQEJ69AAK_rj6Zrdaja6JnvjpLQ7u_5iX0Qx9f6cB0RkB736_6n6wIm1qLNI-Dq77XkdjVcW2mjh_9ruiTmcsFB5r43bZn3EPUCHH928eGDP3q7exJ216dWn3rIj_Fp0glzPiiqowq9OvzzHa3AGVT4piyfy7rf7tOjvV1nnhBZyvVl6OFi-1hK5-UVowvzaTDf4W44WPzMG12w797FR0Auh4_EqbK2azcXkJu6wEzxY7_6AAfDiYM-lXh_7102XhfyrMNDj1v4aDOy9DwtYNwpxObH7LbrV_R5kyRdJ6_f9M94vymdNZsnfQibiQLLb2cD3gBN47CRKlY2phFVkikphguxckwAAAAFM6o2iAA"

class temp(object):
    CANCEL=False

User = Client("Forward-user", session_string=SESSION)
