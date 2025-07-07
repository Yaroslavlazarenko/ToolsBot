import asyncio
import os
import re
import shutil

from services.gemini_service import GeminiService
from core.enums import GeminiModel
from utils.video_cutter import cut_video_to_segments
from utils.download_yt_video import download_yt_video

from google import genai
from google.genai.types import Part

client = genai.Client()

class FunctionHandler:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service

    async def get_hard_text_response(self, text_from_router: str) -> str:
        return await self.gemini_service.generate_text(
            prompt=text_from_router,
            model=GeminiModel.GEMINI_2_5_PRO
        )
    
    async def get_light_text_response(self, text_from_router: str) -> str:
        return await self.gemini_service.generate_text(
            prompt=text_from_router,
            model=GeminiModel.GEMINI_2_5_FLASH_LITE
        )

    async def analyze_video_content(self, text_from_router: str) -> str:
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^"&?\s]{11})'
        )
        match = youtube_regex.search(text_from_router)

        if not match:
            return "No valid YouTube link found in the request."
        
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
            
            report_filename = f"report_{video_id}.txt"
            
            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(final_report_text)

            if os.path.exists(original_video_path):
                os.remove(original_video_path)

            return report_filename
        
        except Exception as e:
            return f"A critical error occurred during video analysis: {e}"
        
        finally:
            if segments_dir and os.path.exists(segments_dir):
                try:
                    shutil.rmtree(segments_dir)
                except Exception:
                    pass

    async def _process_video_segment(self, segment_path: str, index: int, total: int, user_prompt: str, start_time: int, end_time: int) -> str | None:
        uploaded_file = None

        try:
            uploaded_file = await asyncio.to_thread(client.files.upload, file=segment_path)

            if not uploaded_file:
                raise RuntimeError("Failed to upload segment file")

            while uploaded_file.state and uploaded_file.state.name == "PROCESSING":
                await asyncio.sleep(5)
                uploaded_file = await asyncio.to_thread(client.files.get, name=uploaded_file.name)

            if uploaded_file.state and uploaded_file.state.name == "FAILED":
                error_details = uploaded_file.error if hasattr(uploaded_file, 'error') else 'Unknown reason'
                raise RuntimeError(f"Server failed to process segment: {uploaded_file.name}. Reason: {error_details}")
            
            if not uploaded_file.uri or not uploaded_file.mime_type:
                raise RuntimeError(f"File {uploaded_file.name} is active but is missing a URI or MIME type.")

            video_part = Part.from_uri(
                file_uri=uploaded_file.uri,
                mime_type=uploaded_file.mime_type
            )

            prompt = f"""
            This is segment {index} of {total} from a large video. This segment covers time from {start_time} to {end_time} seconds.
            Analyze it and provide a description of what is happening on the video track.
            Consider the user's original request: "{user_prompt}"
            """

            response = await self.gemini_service.generate_text(
                prompt=prompt,
                model=GeminiModel.GEMINI_2_5_PRO,
                video_part=video_part
            )

            description = str(response)
            return f"### Segment Analysis {index}/{total}\n\n{description}"
        
        except Exception as e:
            return f"### Segment Analysis {index}/{total}\n\nAn error occurred while analyzing this segment: {e}"
        
        finally:

            if uploaded_file and uploaded_file.name:
                try:
                    await asyncio.to_thread(client.files.delete, name=uploaded_file.name)
                except Exception:
                    pass 

            if os.path.exists(segment_path):
                os.remove(segment_path)