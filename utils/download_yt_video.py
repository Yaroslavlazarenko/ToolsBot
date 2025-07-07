import os
import subprocess
import json

def download_yt_video(url: str) -> str:

    if not isinstance(url, str) or not url.strip():
        raise ValueError("url must be a non-empty string")
    
    save_dir = os.path.join(os.getcwd(), 'yt_videos')
    os.makedirs(save_dir, exist_ok=True)
    output_template = os.path.join(save_dir, '%(title)s.%(ext)s')
    
    cmd = [
        "yt-dlp",
        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
        "--merge-output-format", "mp4",
        "-o", output_template,
        "--print-json",
        "--no-warnings",
        url
    ]

    try:
        process = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
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
        error_message = e.stderr.strip()
        raise RuntimeError(f"yt-dlp failed to download video. Error: {error_message}")
    
    except Exception as e:
        raise RuntimeError(f"Unexpected error while downloading video: {e}")