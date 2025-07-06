import os
import ffmpeg

def cut_video_to_segments(input_filename: str, segment_time: int = 600, output_dir: str = None) -> list:
    yt_dir = os.path.join(os.getcwd(), 'yt_videos')
    yt_file_path = os.path.join(yt_dir, input_filename) if not os.path.isabs(input_filename) else input_filename
    if not os.path.isfile(yt_file_path):
        raise FileNotFoundError(f"File '{yt_file_path}' not found in yt_videos folder.")
    if output_dir is None:
        output_dir = os.getcwd()
    else:
        os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(yt_file_path))[0]
    output_pattern = os.path.join(output_dir, f"{base_name}_%03d.mp4")
    (
        ffmpeg
        .input(yt_file_path)
        .output(output_pattern, c='copy', map='0', segment_time=segment_time, f='segment', reset_timestamps=1)
        .run(overwrite_output=True)
    )
    output_files = []
    idx = 0
    while True:
        segment_file = os.path.join(output_dir, f"{base_name}_{idx:03d}.mp4")
        if os.path.exists(segment_file):
            output_files.append(segment_file)
            idx += 1
        else:
            break
    try:
        os.remove(yt_file_path)
    except Exception:
        pass
    return output_files
