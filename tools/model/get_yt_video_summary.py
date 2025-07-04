import asyncio
import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from models.gemini_core import generate_content

YOUTUBE_REGEX = re.compile(
    r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
)

def extract_video_id(url: str) -> str | None:
    """Извлекает ID видео из URL YouTube."""
    match = YOUTUBE_REGEX.match(url)
    return match.group(1) if match else None

def get_transcript_text(video_id: str, preferred_lang: str = 'en') -> str:
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        search_langs = [preferred_lang]
        if 'en' not in search_langs: 
            search_langs.append('en')

        transcript = None
        for lang_code in search_langs:
            try:
                transcript = transcript_list.find_transcript([lang_code])
                break
            except NoTranscriptFound:
                continue

        if not transcript:
            first_available_transcript = list(transcript_list)[0]
            transcript = first_available_transcript

        srt_data = transcript.fetch()
        transcript_text = " ".join([entry.text for entry in srt_data])
        
        return transcript_text
        
    except (TranscriptsDisabled, NoTranscriptFound):
        raise ValueError("Субтитры для этого видео отключены или не найдены.")
    except Exception as e:
        raise ValueError(f"Не удалось получить субтитры: {e}")

 

# --- Измененная функция ---
async def get_yt_video_summary(video_url: str, response_language: str = 'en', ) -> str:
    """
    Создает краткое содержание (саммари) видео с YouTube по его субтитрам.
    Используй эту функцию, когда пользователь отправляет ссылку на YouTube и просит сделать пересказ или краткое содержание.

    Args:
        video_url (str): Полная ссылка на видео YouTube (например, 'https://www.youtube.com/watch?v=...').
        response_language (str): Язык ответа, например 'ru' для русского. Если не указан, будет использован 'en' (английский).
    """
    print(f"[Tool Call] Вызов get_yt_video_summary с URL: {video_url} и языком ответа: {response_language}")

    video_id = extract_video_id(video_url)
    
    if not video_id:
        print("[Tool Call] Неверный формат ссылки на YouTube.")
        return "Неверный формат ссылки на YouTube. Убедитесь, что передана полная ссылка."

    try:
        loop = asyncio.get_running_loop()
        transcript = await loop.run_in_executor(None, get_transcript_text, video_id, response_language)
        
        if len(transcript) > 50000:
             transcript = transcript[:50000] + "... (Текст обрезан)"

    except ValueError as e:
        return str(e)

    user_task = "Сделай подробное краткое содержание (саммари) этого видео. Опиши его главную идею и ключевые моменты."
    
    final_prompt = (
        "Ты — продвинутый ИИ-ассистент, который анализирует текст субтитров из YouTube видео, чтобы сделать его краткое содержание.\n"
        "Проанализируй текст субтитров ниже и выполни следующую задачу.\n\n"
        "--- ТЕКСТ СУБТИТРОВ ---\n"
        f"{transcript}\n"
        "--- КОНЕЦ ТЕКСТА СУБТИТРОВ ---\n\n"
        f"ЗАДАЧА: \"{user_task}\"\n\n"
        f"ЯЗЫК ОТВЕТА: \"{response_language}\"\n\n"
        "ТВОЙ ОТВЕТ:"
    )

    response = await generate_content(final_prompt)
    return response

