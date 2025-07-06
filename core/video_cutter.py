import subprocess
import os

def cut_video_to_segments(input_filename: str, segment_time: int = 600, output_dir: str = None) -> list:
    if not os.path.isfile(input_filename):
        raise FileNotFoundError(f"File '{input_filename}' not found.")

    if output_dir is None:
        output_dir = os.getcwd()
    else:
        os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(input_filename))[0]
    output_pattern = os.path.join(output_dir, f"{base_name}_%03d.mp4")

    cmd = [
        "ffmpeg",
        "-i", input_filename,
        "-c", "copy",
        "-map", "0",
        "-segment_time", str(segment_time),
        "-f", "segment",
        "-reset_timestamps", "1",
        output_pattern
    ]

    subprocess.run(cmd, check=True)

    output_files = []
    idx = 0
    while True:
        segment_file = os.path.join(output_dir, f"{base_name}_{idx:03d}.mp4")
        if os.path.exists(segment_file):
            output_files.append(segment_file)
            idx += 1
        else:
            break
    return output_files
