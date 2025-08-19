import os
import subprocess
import json
from typing import Optional, Dict

def get_yt_video_info(url: str) -> Optional[Dict]:
    """
    Получает информацию о видео (длительность и размер) через yt-dlp, не скачивая файл.
    """
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--print-json",
        "--no-warnings",
        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
        url
    ]
    try:
        process = subprocess.run(
            cmd, check=True, capture_output=True, text=True, encoding='utf-8'
        )
        last_line = process.stdout.strip().split('\n')[-1]
        video_info = json.loads(last_line)
        filesize = video_info.get('filesize') or video_info.get('filesize_approx')
        return {'duration': video_info.get('duration'), 'filesize': filesize}
    except Exception as e:
        print(f"Error getting video info for {url}: {e}")
        return None

def download_yt_video(url: str) -> str:
    """
    Скачивает видео с YouTube, используя безопасные параметры для имени файла.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url must be a non-empty string")
    
    save_dir = os.path.join(os.getcwd(), 'yt_videos')
    os.makedirs(save_dir, exist_ok=True)
    output_template = os.path.join(save_dir, '%(title)s.%(ext)s')
    
    cmd = [
        "yt-dlp",
        
        # --- ЭТО САМАЯ ВАЖНАЯ СТРОКА ДЛЯ РЕШЕНИЯ ВАШЕЙ ПРОБЛЕМЫ ---
        "--restrict-filenames",
        # -------------------------------------------------------------
        
        # Остальные полезные флаги
        "--limit-rate", "15M",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        
        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
        "--merge-output-format", "mp4",
        "-o", output_template,
        "--print-json",
        "--no-warnings",
        url
    ]
    
    try:
        process = subprocess.run(
            cmd, check=True, capture_output=True, text=True, encoding='utf-8'
        )

        last_line = process.stdout.strip().split('\n')[-1]
        video_info = json.loads(last_line)
        filepath = video_info.get('_filename')
        
        if not filepath or not os.path.exists(filepath):
            raise RuntimeError("yt-dlp finished but could not find the downloaded file.")
            
        return filepath
        
    except FileNotFoundError:
        raise RuntimeError("'yt-dlp' command not found. Make sure it is installed and available in PATH.")
    
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"yt-dlp failed to download video. Error: {e.stderr.strip()}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error while downloading video: {e}")