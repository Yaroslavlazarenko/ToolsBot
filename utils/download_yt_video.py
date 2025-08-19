import os
import subprocess
import json
import sys
from typing import Optional, Dict

# Определяем полный путь к yt-dlp, чтобы избежать конфликтов
python_executable_path = sys.executable
venv_bin_path = os.path.dirname(python_executable_path)
YT_DLP_EXECUTABLE = os.path.join(venv_bin_path, 'yt-dlp')
COOKIES_FILE_PATH = os.path.join(os.getcwd(), 'cookies.txt')

def get_yt_video_info(url: str) -> Optional[Dict]:
    """
    Получает метаданные видео, используя файл cookies для аутентификации.
    """
    cmd = [
        YT_DLP_EXECUTABLE,
        "--cookies", COOKIES_FILE_PATH,
        "--skip-download", "--print-json", "--no-warnings",
        url
    ]
    try:
        process = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        video_info = json.loads(process.stdout.strip().split('\n')[-1])
        filesize = video_info.get('filesize') or video_info.get('filesize_approx') or 0
        return {'duration': video_info.get('duration'), 'filesize': filesize}
    except subprocess.CalledProcessError as e:
        print(f"Error getting video info for {url}. Stderr: {e.stderr.strip()}")
        if not os.path.exists(COOKIES_FILE_PATH):
            print("CRITICAL: cookies.txt file not found!")
        return None
    except Exception as e:
        print(f"Unexpected error getting video info for {url}: {e}")
        return None

def download_yt_video(url: str) -> str:
    """
    Скачивает видео с YouTube, используя надежный одноэтапный подход с --print-json.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url must be a non-empty string")
    
    save_dir = os.path.join(os.getcwd(), 'yt_videos')
    os.makedirs(save_dir, exist_ok=True)
    output_template = os.path.join(save_dir, '%(title)s.%(ext)s')
    
    cmd = [
        YT_DLP_EXECUTABLE,
        "--restrict-filenames",
        "--cookies", COOKIES_FILE_PATH,
        "--limit-rate", "15M",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", output_template,
        "--print-json", # Возвращаем JSON, но будем парсить его умнее
        "--no-warnings",
        url
    ]
    
    try:
        # Запускаем yt-dlp и ждем его полного завершения
        process = subprocess.run(
            cmd, check=True, capture_output=True, text=True, encoding='utf-8'
        )
        
        # Парсим JSON из вывода
        video_info = json.loads(process.stdout.strip().split('\n')[-1])
        
        # --- УМНЫЙ ПОИСК ФИНАЛЬНОГО ПУТИ ---
        # yt-dlp помещает финальный путь в 'filepath' после слияния,
        # а в '_filename' может быть путь к временному файлу.
        # Мы проверяем оба для максимальной надежности.
        filepath = video_info.get('filepath') or video_info.get('_filename')

        if not filepath or not os.path.exists(filepath):
            # Если мы здесь, значит, произошла очень серьезная и редкая ошибка
            raise RuntimeError(f"yt-dlp finished, but its output JSON did not contain a valid final filepath.")
            
        return filepath
        
    except FileNotFoundError:
        raise RuntimeError(f"'yt-dlp' command not found at path: {YT_DLP_EXECUTABLE}")
    except subprocess.CalledProcessError as e:
        # Если yt-dlp упал, его ошибка будет в stderr
        if not os.path.exists(COOKIES_FILE_PATH):
             raise RuntimeError(f"yt-dlp failed. CRITICAL: cookies.txt file not found at {COOKIES_FILE_PATH}")
        raise RuntimeError(f"yt-dlp failed to download video. Error: {e.stderr.strip()}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error while downloading video: {e}")