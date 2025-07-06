import asyncio

from core.get_yt_video_subtitles import get_transcript_text

async def get_yt_video_summary(video_url: str, response_language: str = 'ru') -> str:
    """
    Создает краткое содержание (саммари) видео с YouTube по его субтитрам.
    Используй эту функцию, когда пользователь отправляет ссылку на YouTube и просит сделать пересказ или краткое содержание.

    Args:
        video_url (str): Полная ссылка на видео YouTube (например, 'https://www.youtube.com/watch?v=...').
        response_language (str): Язык ответа, например 'ru' для русского. Если не указан, будет использован 'ru' (русский).
    """
    print(f"[Tool Call] Вызов get_yt_video_suextract_video_id, get_transcript_textmmary с URL: {video_url} и языком ответа: {response_language}")

    from app.services import general_purpose_service

    try:
        # Для запуска синхронной функции в асинхронном коде
        loop = asyncio.get_running_loop()
        # Вызываем get_transcript_text в отдельном потоке, чтобы не блокировать event loop
        transcript = await loop.run_in_executor(
            None, get_transcript_text, video_url, response_language
        )
        
        # Обрезаем слишком длинный текст, чтобы не превышать лимиты модели
        if len(transcript) > 50000:
             transcript = transcript[:50000] + "... (Текст обрезан)"

    except ValueError as e:
        # Если get_transcript_text выбросил ValueError, возвращаем его сообщение
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

    response = await general_purpose_service.generate(final_prompt)
    return response