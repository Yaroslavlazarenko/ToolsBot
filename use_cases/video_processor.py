import asyncio
import os
import re
import shutil

from google.genai import Client
from google.genai.types import Part

from services.gemini_service import GeminiService
from core.enums import GeminiModel
from core.exceptions import VideoProcessingError
from utils.video_cutter import cut_video_to_segments
from utils.download_yt_video import download_yt_video

class VideoProcessor:
    YOUTUBE_REGEX = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?(?P<id>[^"&?\s]{11})'
    )
    def __init__(self, gemini_service: GeminiService, file_client: Client, segment_duration: int):
        self.gemini_service = gemini_service
        self.file_client = file_client
        self.segment_duration = segment_duration

    async def analyze_video_from_prompt(self, user_prompt: str) -> str:
        match = self.YOUTUBE_REGEX.search(user_prompt)
        print(user_prompt)
        
        if not match:
            return "No valid YouTube link found in the request."
        
        video_id = match.group('id') 
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        original_video_path = None
        segments_dir = None

        try:
            original_video_path = await asyncio.to_thread(download_yt_video, url)
            
            base_name = os.path.basename(original_video_path).rsplit('.', 1)[0]
            segments_dir = os.path.join(os.getcwd(), 'segments', base_name)
            
            video_segments_paths = await asyncio.to_thread(
                cut_video_to_segments, original_video_path, self.segment_duration, segments_dir
            )
            
            tasks = [
                self._process_video_segment(path, i + 1, len(video_segments_paths), user_prompt)
                for i, path in enumerate(video_segments_paths)
            ]
            segment_descriptions = await asyncio.gather(*tasks)

            return self._generate_report(user_prompt, video_id, segment_descriptions)

        except Exception as e:
            raise VideoProcessingError(f"A critical error occurred during video analysis: {e}") from e
        
        finally:
            if original_video_path and os.path.exists(original_video_path):
                os.remove(original_video_path)
            if segments_dir and os.path.exists(segments_dir):
                shutil.rmtree(segments_dir, ignore_errors=True)

    async def _process_video_segment(self, segment_path: str, index: int, total: int, user_prompt: str) -> str:
        uploaded_file = None
        try:
            uploaded_file = await asyncio.to_thread(self.file_client.files.upload, file=segment_path)

            while uploaded_file.state and uploaded_file.state.name == "PROCESSING":
                await asyncio.sleep(5)
                uploaded_file = await asyncio.to_thread(self.file_client.files.get, name=uploaded_file.name)

            if uploaded_file.state and uploaded_file.state.name == "FAILED":
                raise RuntimeError(f"Server failed to process segment: {uploaded_file.name}")

            if not uploaded_file.uri or not uploaded_file.mime_type:
                raise RuntimeError(f"File {uploaded_file.name} is active but is missing a URI or MIME type.")


            video_part = Part.from_uri(file_uri=uploaded_file.uri, mime_type=uploaded_file.mime_type)
            
            start_time = (index - 1) * self.segment_duration
            end_time = start_time + self.segment_duration
            prompt = (
                f"This is segment {index} of {total} from a large video. This segment covers "
                f"the time from {start_time} to {end_time} seconds. Analyze its content based on "
                f"the user's original request: \"{user_prompt}\""
            )

            response = await self.gemini_service.generate_text(
                prompt=prompt, model=GeminiModel.GEMINI_2_5_PRO, video_part=video_part
            )
            return f"### Segment Analysis {index}/{total}\n\n{response}"

        except Exception as e:
            return f"### Segment Analysis {index}/{total}\n\nAn error occurred: {e}"
        
        finally:
            if uploaded_file and uploaded_file.name:
                try:
                    await asyncio.to_thread(self.file_client.files.delete, name=uploaded_file.name)
                except Exception:
                    pass
            if os.path.exists(segment_path):
                os.remove(segment_path)
    
    def _generate_report(self, user_prompt: str, video_id: str, descriptions: list[str]) -> str:
        final_report_text = f"Full video analysis for request: '{user_prompt}'\n\n" + "\n\n---\n\n".join(filter(None, descriptions))
        report_filename = f"report_{video_id}.txt"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(final_report_text)
        return report_filename