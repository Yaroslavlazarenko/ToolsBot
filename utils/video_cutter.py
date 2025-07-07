import os
import ffmpeg

def cut_video_to_segments(input_filename: str, segment_time: int, output_dir: str) -> list[str]:
    if not os.path.isfile(input_filename):
        raise FileNotFoundError(f"Input file not found: '{input_filename}'")
    
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_filename))[0]
    output_pattern = os.path.join(output_dir, f"{base_name}_%03d.mp4")

    try:
        ffmpeg.input(input_filename).output(
            output_pattern, c='copy', map='0', segment_time=segment_time, f='segment', reset_timestamps=1
        ).run(overwrite_output=True, quiet=True)
    except ffmpeg.Error as e:
        raise IOError(f"FFmpeg failed to cut video: {e.stderr.decode()}") from e

    return sorted([os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.startswith(base_name)])