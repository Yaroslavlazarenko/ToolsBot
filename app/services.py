from services.gemini_service import GeminiService

from model_tools.get_yt_video_summary import get_yt_video_summary

general_purpose_service = GeminiService(tools=None)

youtube_tool_service = GeminiService(tools=[get_yt_video_summary])

