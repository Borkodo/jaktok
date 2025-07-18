import discord
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from utils import *

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.dm_messages = True
client = discord.Client(intents=intents)

VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), "video_inbox")
INDEX_JSON = os.path.join(os.path.dirname(__file__), "index.json")
os.makedirs(VIDEO_FOLDER, exist_ok=True)

async def download_video_480p(url, folder):
    clean_filename, temp_filename = get_clean_filename(url)
    full_path = os.path.join(folder, clean_filename)

    try:
        await run_subprocess([
            "yt-dlp",
            "-f", "bv[height<=480]+ba/b[height<=480]",
            "-o", full_path,
            url
        ])
        print("✅ Downloaded native 480p.")
        record_video(os.path.basename(full_path))
        return True
    except Exception:
        print("⚠️ 480p not available. Downloading best and re-encoding...")

        temp_path = os.path.join(folder, temp_filename)
        await run_subprocess([
            "yt-dlp",
            "-f", "b",
            "-o", temp_path,
            url
        ])

        await run_subprocess([
            "ffmpeg",
            "-i", temp_path,
            "-vf", "scale=-2:480",
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "64k",
            "-ac", "1",
            full_path
        ])

        os.remove(temp_path)
        print(f"✅ Re-encoded: {os.path.basename(full_path)}")
        record_video(os.path.basename(full_path))
        return True


def record_video(filename: str):
    timestamp = datetime.now().isoformat(timespec="seconds")
    index_path = Path(INDEX_JSON)

    if index_path.exists() and index_path.stat().st_size > 0:
        with open(index_path, "r") as f:
            try:
                videos = json.load(f)
            except json.JSONDecodeError:
                print("⚠️ index.json is corrupt. Starting fresh.")
                videos = []
    else:
        videos = []

    videos.append({
        "filename": filename,
        "timestamp": timestamp
    })

    with open(index_path, "w") as f:
        json.dump(videos, f, indent=2)



@client.event
async def on_ready():
    print(f"🤖 Bot is ready: {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mention = client.user in message.mentions

    if not (is_dm or is_mention):
        return

    url = message.content.strip()
    if not url.startswith("http"):
        return

    await message.channel.send("📥 Downloading video...")
    try:
        result = await download_video_480p(url, VIDEO_FOLDER)
        if result:
            await message.channel.send("📩 Video sent to Jack's feed.")
        else:
            await message.channel.send("⚠️ Something went wrong.")
    except Exception as e:
        await message.channel.send("❌ Download failed.")
        print(f"Error: {e}")

if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if token:
        client.run(token)
    else:
        print("❌ Bot token not found. Set DISCORD_BOT_TOKEN env variable.")
