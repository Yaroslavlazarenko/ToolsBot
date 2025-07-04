import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Регулярное выражение для извлечения ID видео из URL YouTube
YOUTUBE_REGEX = re.compile(
    r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
)

def extract_video_id(url: str) -> str | None:
    """Извлекает ID видео из URL YouTube."""
    match = YOUTUBE_REGEX.match(url)
    return match.group(1) if match else None

def get_transcript_text(video_url: str, preferred_lang: str = 'en') -> str:
    """
    Получает и возвращает полный текст субтитров для указанного YouTube видео.

    Args:
        video_id (str): ID видео YouTube.
        preferred_lang (str): Предпочтительный язык субтитров (например, 'ru', 'en').
                               По умолчанию 'en'.

    Raises:
        ValueError: Если субтитры отключены, не найдены или произошла другая ошибка.

    Returns:
        str: Сплошной текст субтитров.
    """
    video_id = extract_video_id(video_url)
    if not video_id:
        print("[Tool Call] Неверный формат ссылки на YouTube.")
        return "Неверный формат ссылки на YouTube. Убедитесь, что передана полная ссылка."

    try:
        # Получаем список всех доступных субтитров для видео
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Формируем список языков для поиска: сначала предпочтительный, потом английский (если он не был предпочтительным)
        search_langs = [preferred_lang]
        if 'en' not in search_langs:
            search_langs.append('en')

        transcript = None
        # Пытаемся найти субтитры на одном из языков из списка
        for lang_code in search_langs:
            try:
                transcript = transcript_list.find_transcript([lang_code])
                break  # Выходим из цикла, как только нашли подходящие субтитры
            except NoTranscriptFound:
                continue

        # Если не нашли субтитры на нужном языке, берем первые доступные
        if not transcript:
            # Преобразуем итератор в список, чтобы безопасно взять первый элемент
            available_transcripts = list(transcript_list)
            if not available_transcripts:
                raise NoTranscriptFound("Для этого видео не найдено вообще никаких субтитров.")
            transcript = available_transcripts[0]

        # Загружаем данные субтитров и объединяем их в одну строку
        srt_data = transcript.fetch()
        transcript_text = " ".join([entry['text'] for entry in srt_data])

        return transcript_text

    except (TranscriptsDisabled, NoTranscriptFound):
        raise ValueError("Субтитры для этого видео отключены или не найдены.")
    except Exception as e:
        # Перехватываем другие возможные ошибки и оборачиваем их в ValueError
        raise ValueError(f"Не удалось получить субтитры: {e}")