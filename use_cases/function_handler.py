import asyncio
import os
import re
import logging
import shutil
import time
from typing import Optional, Dict
import ffmpeg
import math

from services.gemini_service import GeminiService
from core.enums import GeminiModel, RateLimits
from utils.download_yt_video import download_yt_video, get_yt_video_info
from google.genai.types import Part, VideoMetadata, FileData
from google import genai
from config import Config
from core.analysis_manager import analysis_manager, AnalysisStatus

config = Config()
client = genai.Client(api_key=config.gemini_api_key)

class FunctionHandler:
    logger = logging.getLogger("FunctionHandler")
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service

    async def estimate_and_propose_analysis(self, text_from_router: str, message=None) -> Dict:
        self.logger.info("Phase 1: Estimating video content analysis with time range")
        youtube_regex = re.compile(r'(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/(?:.*[?&]v=|embed/|v/|)([A-Za-z0-9_-]{11})')
        match = youtube_regex.search(text_from_router)
        if not match: return {'type': 'text', 'content': "Не найдена ссылка на YouTube в вашем запросе."}
        
        video_id = match.group(1)
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        try:
            video_info = await asyncio.to_thread(get_yt_video_info, url)
            if not video_info or not video_info.get('duration'):
                return {'type': 'text', 'content': "Не удалось получить информацию о видео."}

            duration = video_info.get('duration', 0)
            filesize = video_info.get('filesize', 0)
            duration_minutes = duration / 60

            internet_speed_mbps = 10
            speed_in_bytes = internet_speed_mbps * 1024 * 1024
            transfer_time_minutes = (filesize / speed_in_bytes) * 2 / 60 if filesize > 0 else 0
            analysis_time_minutes = duration_minutes / 60
            
            requests_per_minute = RateLimits.RATE_LIMIT_2_5_FLASH.value
            num_segments = math.ceil(duration_minutes / 10)
            gemini_wait_time_minutes = (num_segments / requests_per_minute) if requests_per_minute > 0 else 0

            remaining_duration = max(0, duration_minutes - (10 * requests_per_minute))
            token_processing_rate = RateLimits.RATE_LIMIT_2_5_FLASH_LITE.value
            gemini_wait_time_minutes1 = ((remaining_duration / token_processing_rate) + 1) if remaining_duration > 0 else 0

            base_time = transfer_time_minutes + analysis_time_minutes
            min_total_time = base_time + gemini_wait_time_minutes
            max_total_time = base_time + max(gemini_wait_time_minutes, gemini_wait_time_minutes1)

            self.logger.info(
                f"Time estimation for {video_id}: Total Range=[{min_total_time:.1f}m - {max_total_time:.1f}m]"
            )

            if max_total_time < 1:
                estimate_text = "Обработка займет меньше минуты.\n\nНачать?"
            elif (max_total_time - min_total_time) < 1:
                estimate_text = (f"Видео будет обрабатываться примерно {max_total_time:.1f} минут.\n\nНачать обработку?")
            else:
                estimate_text = (f"Видео будет обрабатываться от {min_total_time:.1f} до {max_total_time:.1f} минут.\n\nНачать обработку?")
            
            return {'type': 'confirmation', 'text': estimate_text, 'video_id': video_id}
        except Exception as e:
            self.logger.error(f"Error during estimation: {e}", exc_info=True)
            return {'type': 'text', 'content': f"Ошибка при получении данных о видео: {e}"}
        

    async def execute_video_analysis(self, video_id: str, original_user_prompt: str, language: str, message=None) -> str:
        self.logger.info(f"User {message.from_user.id} requested analysis for video_id: {video_id}")
        
        analysis_entry = await analysis_manager.get_or_create_analysis_entry(video_id)
        is_worker = analysis_entry["status"] == AnalysisStatus.IN_PROGRESS and not analysis_entry["event"].is_set()

        if not is_worker:
            self.logger.info(f"Task for {video_id} is a 'watcher'. Waiting for result...")
            await analysis_entry["event"].wait()
            
            self.logger.info(f"Watcher for {video_id} woke up. Status: {analysis_entry['status']}")
            if analysis_entry["status"] == AnalysisStatus.COMPLETED:
                return await self.get_user_copy_of_report(analysis_entry["result"], video_id, message.from_user.id)
            else:
                return analysis_entry["result"]

        self.logger.info(f"This process is the designated WORKER for {video_id}.")
        original_video_path = None
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            original_video_path = await asyncio.to_thread(download_yt_video, url)
            
            probe = ffmpeg.probe(original_video_path)
            duration = float(probe['format']['duration'])
            uploaded_file = await asyncio.to_thread(client.files.upload, file=original_video_path)
            
            max_wait = math.ceil(duration / 60) + 600; waited=0
            while uploaded_file.state.name == "PROCESSING" and waited < max_wait:
                await asyncio.sleep(5); waited+=5
                uploaded_file = await asyncio.to_thread(client.files.get, name=uploaded_file.name)
            if uploaded_file.state.name != "ACTIVE":
                raise RuntimeError(f"Видео не было обработано Gemini за {waited} секунд.")

            concurrency_limit = RateLimits.RATE_LIMIT_2_5_FLASH.value - 1
            semaphore = asyncio.Semaphore(concurrency_limit)
            num_segments = math.ceil(duration / 600)
            
            tasks = [ self._process_video_logical_segment(uploaded_file, i + 1, num_segments, original_user_prompt, language, i * 600, min((i + 1) * 600, int(duration)), semaphore) for i in range(num_segments) ]
            segment_descriptions = await asyncio.gather(*tasks)

            final_report_text = f"Full analysis for your request (in {language}): '{original_user_prompt}'\n\n" + "\n\n---\n\n".join(filter(None, segment_descriptions))
            report_filename = f"report_{os.path.basename(original_video_path)}.txt"
            with open(report_filename, "w", encoding="utf-8") as f: f.write(final_report_text)
            
            await analysis_manager.complete_analysis(video_id, report_filename)
            return await self.get_user_copy_of_report(report_filename, video_id, message.from_user.id)

        except Exception as e:
            error_message = f"Произошла критическая ошибка: {e}"
            await analysis_manager.fail_analysis(video_id, error_message)
            return error_message
        finally:
            if original_video_path and os.path.exists(original_video_path):
                os.remove(original_video_path)
            asyncio.create_task(self.schedule_cleanup(video_id, 600))

    async def get_hard_text_response(self, text_from_router: str) -> str:
        return await self.gemini_service.generate_text(prompt=text_from_router, model=GeminiModel.GEMINI_2_5_PRO)

    async def get_light_text_response(self, text_from_router: str) -> str:
        return await self.gemini_service.generate_text(prompt=text_from_router, model=GeminiModel.GEMINI_2_5_FLASH_LITE)
    
    async def _process_video_logical_segment(self, uploaded_file, index: int, total: int, user_prompt: str, language: str, start_time: int, end_time: int, semaphore: asyncio.Semaphore) -> Optional[str]:
        async with semaphore:
            try:
                self.logger.info(f"Processing segment {index}/{total}...")
                video_metadata = {"start_offset": f"{int(start_time)}s", "end_offset": f"{int(end_time)}s"}
                file_data_for_part = FileData(file_uri=uploaded_file.uri, mime_type=uploaded_file.mime_type)
                part = Part(file_data=file_data_for_part, video_metadata=VideoMetadata(**video_metadata))
                prompt = f"""This is segment {index} of {total} from a video. Analyze it based on the user's original request: "{user_prompt}". IMPORTANT: Your entire response MUST be in {language}."""
                response = await self.gemini_service.generate_text(prompt=prompt, model=GeminiModel.GEMINI_2_5_FLASH, video_part=part)
                return f"### Segment Analysis {index}/{total} ({start_time}s - {end_time}s)\n\n{str(response)}"
            except Exception as e:
                self.logger.error(f"Error processing segment {index}/{total}: {e}", exc_info=True)
                return f"### Segment Analysis {index}/{total}\n\nAn error occurred."

    async def schedule_cleanup(self, video_id: str, delay: int):
        await asyncio.sleep(delay)
        self.logger.info(f"Cleaning up cached analysis entry for video_id: {video_id}")
        await analysis_manager.cleanup_entry(video_id)

    async def get_user_copy_of_report(self, original_report_path: str, video_id: str, user_id: int) -> str:
        try:
            unique_report_name = f"report_{video_id}_{user_id}_{int(time.time())}.txt"
            shutil.copyfile(original_report_path, unique_report_name)
            return unique_report_name
        except Exception:
            return original_report_path
