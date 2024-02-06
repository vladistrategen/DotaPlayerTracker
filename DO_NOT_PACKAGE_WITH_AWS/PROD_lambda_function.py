import requests
import os
from datetime import datetime

DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
WEBHOOK_URL_CHAT = os.environ.get('WEBHOOK_URL_CHAT')  # Webhook URL for sending messages
WEBHOOK_URL_LOG = os.environ.get('WEBHOOK_URL_LOG')  # Webhook URL for sending messages
CHANNEL_ID = os.environ.get('CHANNEL_ID')  # Channel ID for updating channel settings
PLAYER_ID = os.environ.get('PLAYER_ID')  # Player ID for getting the leaderboard rank
PLAYER_NAME = os.environ.get('PLAYER_NAME')  # Player name for getting the leaderboard rank
TEAM_ID = os.environ.get('TEAM_ID')  # Team ID for getting the leaderboard rank
TEAM_TAG = os.environ.get('TEAM_TAG')  # Team tag for getting the leaderboard rank
COUNTRY_CODE = os.environ.get('COUNTRY_CODE')  # Country code for getting the leaderboard rank

# Headers for Discord API requests using the bot token
HEADERS = {
    "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
    "Content-Type": "application/json"
}

def send_message_via_webhook(content, webhook_url):
    # Payload with the message content
    payload = {
        "content": content
    }
    # POST request to the Discord webhook
    response = requests.post(webhook_url, json=payload)
    return response.status_code

def log_data(now, rank, webhook_url):
    log_message = f"{now.strftime('%d/%m/%Y-%H:%M:%S')} - Rank: {rank}"
    payload = {
        "content": log_message
    }
    response = requests.post(webhook_url, json=payload)
    return response.status_code

def update_channel_name(new_name):
    # Discord API endpoint to modify the channel
    url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}"
    payload = {
        "name": new_name  # New channel name
    }
    # PATCH request to update the channel name
    response = requests.patch(url, headers=HEADERS, json=payload)
    return response.status_code

def get_current_rank():
    api_url = f"https://www.dota2.com/webapi/ILeaderboard/GetDivisionLeaderboard/v0001?division=europe&leaderboard=0"
    response = requests.get(api_url)
    leaderboard = response.json()['leaderboard']
    # leaderboard is an  array of players, each player has a leaderboard_rank, get the rank of player with name == "legacy " and team_id == 9017851 and team_tag == "Plasma" and country_code == "ro"

    leaderboard_rank = None
    for player in leaderboard:
        if player['name'] == "legacy " and player['team_id'] == 9017851 and player['team_tag'] == "Plasma" and player['country'] == "ro":
            leaderboard_rank = player['rank']
            break
    
    if leaderboard_rank is None:
        print("Player not found")

    return int(leaderboard_rank)

def get_channel_message_and_name(leaderboard_rank: int, old_channel_name: str):
    message = f"Rankul lui andrei a fost actualizat"
    new_rank_message = f", acum este pe locul **{leaderboard_rank}**"
    old_rank_message = " de la "
    last_rank = int(old_channel_name.replace("-📈", "").replace("-📉", "").replace("-🔁", "").split('-')[-1].strip()) if old_channel_name is not None else None
    channel_name = "andrei-rank-" + str(leaderboard_rank)

    if last_rank is not None:
        old_rank_message += "**"+str(last_rank)+"**"
        if leaderboard_rank < last_rank:
            message += old_rank_message
            message += new_rank_message
            message += " 🏆 👑 💰 💰 🪙 💵 👙 🤤 🔥 💯 👆"
            channel_name+=' 📈'
        elif leaderboard_rank > last_rank:
            message += old_rank_message
            message += new_rank_message
            channel_name+=' 📉'
            message += " 🚫🏠😔 🚫🏠😔 💐💐"
        else:
            message += ", este tot pe locul **"+str(leaderboard_rank)+"**"
            message += " :neutral_face: :neutral_face: :neutral_face:"
            channel_name+=' 🔁'
    else:
        message += new_rank_message


    message+="\n"

    if leaderboard_rank <= 150:
        message += "Ai scapat de flori, you live to fight another day"
    elif leaderboard_rank <= 350:
        message += "Bravo, nu mai esti un gunoi"
    elif leaderboard_rank < 500:
        message += "Nu esti prost, dar nici bun nu esti"
    else:
        message += "Ai incerat sa joci cu monitorul pornit?"

    return message, channel_name

def lambda_handler(event, context):
    now = datetime.now()

    print("Starting the update...")

    if now.hour >= 0 and now.hour <= 8:
        print("Skipping the update because it's too early or too late")
        print(f"Current hour: {now.hour}")
        return

    leaderboard_rank = get_current_rank()

    if leaderboard_rank is None:
        return

    channel = requests.get(f"https://discord.com/api/v9/channels/{CHANNEL_ID}", headers=HEADERS).json()
    old_channel_name = channel['name']

    message, channel_name = get_channel_message_and_name(leaderboard_rank, old_channel_name)

    if channel:
        update_status = update_channel_name(channel_name)
        message_status = send_message_via_webhook(message, WEBHOOK_URL_CHAT)
        log_status = log_data(now, leaderboard_rank, WEBHOOK_URL_LOG)

        if update_status == 200:
            print("Channel name updated successfully.")
        else:
            print(f"Failed to update channel name. Status code: {update_status}")

        if log_status == 200:
            print("Message sent successfully via webhook.")
        else:
            print(f"Failed to send message via webhook. Status code: {log_status}")

        if message_status == 200:
            print("Message sent successfully via webhook.")
        else:
            print(f"Failed to send message via webhook. Status code: {message_status}")

    else:
        print("Channel not found")
