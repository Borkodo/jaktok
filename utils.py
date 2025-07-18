import subprocess

import yt_dlp
import asyncio


def get_clean_filename(url: str):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        base = f"{info['id']}.mp4"
        base_temp = f"{info['id']}_temp.mp4"
        return base, base_temp

async def run_subprocess(cmd: list[str]):
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{stderr.decode()}")

def extract_preview(video_path):
    thumbnail_path = video_path.rsplit(".", 1)[0] + "_preview.jpg"
    subprocess.run([
        "ffmpeg",
        "-i", video_path,
        "-vf", "select=eq(n\\,0)" ,
        "-q:v", "3",
        thumbnail_path
    ], check=True)

