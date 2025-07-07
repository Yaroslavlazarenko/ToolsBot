import asyncio
import os
import re
from typing import Optional

from services.gemini_service import GeminiService
from core.enums import GeminiModel
from utils.video_cutter import cut_video_to_segments
from utils.download_yt_video import download_yt_video

from google import genai

client = genai.Client()

class FunctionHandler:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service

    async def get_hard_text_response(self, text_from_router: str) -> str:
        response = await self.gemini_service.generate_text(
            prompt=text_from_router,
            model=GeminiModel.GEMINI_2_5_PRO
        )
        return str(response)
    
    async def get_light_text_response(self, text_from_router: str) -> str:
        response = await self.gemini_service.generate_text(
            prompt=text_from_router,
            model=GeminiModel.GEMINI_2_5_FLASH_LITE
        )
        return str(response)

    async def analyze_video_content(self, text_from_router: str) -> str:
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^"&?\s]{11})'
        )
        match = youtube_regex.search(text_from_router)
        if not match:
            return None
        video_id = match.group(6)
        url = f"https://www.youtube.com/watch?v={video_id}"
        segments_dir = None
        segment_time = 600
        try:
            original_video_path = await asyncio.to_thread(download_yt_video, url)
            segments_dir = os.path.join(os.getcwd(), 'segments', os.path.basename(original_video_path).split('.')[0])
            video_segments_paths = await asyncio.to_thread(cut_video_to_segments, original_video_path, segment_time=segment_time, output_dir=segments_dir)
            tasks = []
            for i, path in enumerate(video_segments_paths):
                start_time = i * segment_time
                end_time = start_time + segment_time
                tasks.append(asyncio.create_task(
                    self._process_video_segment(path, i + 1, len(video_segments_paths), text_from_router, start_time, end_time)
                ))
            segment_descriptions = await asyncio.gather(*tasks)
            final_report_text = f"Full video analysis for request: '{text_from_router}'\n\n" + "\n\n---\n\n".join(filter(None, segment_descriptions))
            report_filename = f"report_{os.path.basename(original_video_path)}.txt"
            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(final_report_text)
            return report_filename
        except Exception as e:
            return f"A critical error occurred during video analysis: {e}"
        finally:
            if segments_dir and os.path.exists(segments_dir):
                import shutil
                try:
                    shutil.rmtree(segments_dir)
                except Exception:
                    pass

    async def _process_video_segment(self, segment_path: str, index: int, total: int, user_prompt: str, start_time: int, end_time: int) -> Optional[str]:
        uploaded_file = None
        try:
            uploaded_file = await asyncio.to_thread(client.files.upload, file=segment_path)
            while uploaded_file.state.name == "PROCESSING":
                await asyncio.sleep(5)
                uploaded_file = await asyncio.to_thread(client.files.get, name=uploaded_file.name)
            if uploaded_file.state.name == "FAILED":
                raise RuntimeError(f"Server failed to process segment: {uploaded_file.name}")
            prompt = f"""
            This is segment {index} of {total} from a large video. This segment covers time from {start_time} to {end_time} seconds.
            Analyze it and provide a description of what is happening on the video track.
            Consider the user's original request: "{user_prompt}"
            """
            response = await self.gemini_service.generate_text(
                prompt=prompt,
                model=GeminiModel.GEMINI_2_5_PRO,
                video_part=uploaded_file
            )
            description = str(response)
            return f"### Segment Analysis {index}/{total}\n\n{description}"
        except Exception as e:
            return f"### Segment Analysis {index}/{total}\n\nAn error occurred while analyzing this segment."
        finally:
            if uploaded_file:
                await asyncio.to_thread(client.files.delete, name=uploaded_file.name)
            if os.path.exists(segment_path):
                os.remove(segment_path)