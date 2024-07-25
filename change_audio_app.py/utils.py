import asyncio.runners
import os
from os import PathLike
import json
import asyncio
import time
import uuid
from ffmpeg.asyncio import FFmpeg
import zipfile


async def async_video_meta_data(path: PathLike) -> dict:
    ffprobe = FFmpeg(executable='ffprobe').input(
        path,
        print_format='json',
        show_streams=None
    )
    ffprobe_executed = await ffprobe.execute()
    meta_data = json.loads(ffprobe_executed)
    return meta_data


def seconds_to_str(seconds: float) -> str:
    return time.strftime('%H:%M:%S', time.gmtime(seconds))


def timeline(num_clips: int, chosen_clip: int, duration: float) -> str:
    part_duration = duration / num_clips
    beginning = seconds_to_str((chosen_clip - 1) * part_duration)
    end = seconds_to_str(chosen_clip * part_duration)
    return f'{beginning} - {end}'


def get_all_paths(unique_name: str, dir: PathLike) -> list[str]:
    return sorted(os.path.join(dir, path) for path in os.listdir(dir) if unique_name in path)


async def async_split_on_parts(path: PathLike, dir: PathLike, num_parts: int, exact: bool = False, threads: int = 1) -> list[str]:
    duration = float((await async_video_meta_data(path))['streams'][0]['duration'])
    part_duration = duration / num_parts
    
    extension = str(path)[str(path).rfind('.'):]
    unique_name = str(uuid.uuid4())
    path_template = os.path.join(dir, f'{unique_name}_%09d{extension}')
    
    if exact:
        cmd = f'ffmpeg -i {path} -c:v libx264 -crf 22 -map 0 -segment_time {part_duration} -g {part_duration} -reset_timestamps 1 '\
              f'-sc_threshold 0 -force_key_frames "expr:gte(t, n_forced * {part_duration})" -threads {threads} -f segment {path_template}'
    else:
        cmd = f'ffmpeg -i {path} -c copy -map 0 -segment_time {part_duration} -f segment -reset_timestamps 1 -threads {threads} {path_template}'
        
    process = await asyncio.create_subprocess_shell(cmd)
    await process.wait()
    if process.returncode != 0:
        raise RuntimeError('Something went wrong during spliting video on parts.')
    all_paths = get_all_paths(unique_name, dir)
    return all_paths


async def replace_audio(video_path: PathLike, audio_path: PathLike, dir: PathLike, threads: int) -> str:
    extension = str(video_path)[str(video_path).rfind('.'):]
    name = str(uuid.uuid4()) + extension
    path = os.path.join(dir, name)
    cmd = f'ffmpeg -i {video_path} -i {audio_path} -c:v copy -map 0:v:0 -map 1:a:0 -shortest {path}'
    process = await asyncio.subprocess.create_subprocess_shell(cmd)
    await process.wait()
    if process.returncode != 0:
        raise RuntimeError('Something went wrong during replacing the audio on the video.')
    return path


def to_archive(archive_path: PathLike, files_paths: list[PathLike]):
    with zipfile.ZipFile(archive_path, mode='w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in files_paths:
            zip_file.write(file_path)


if __name__ == '__main__':
    path = r'C:\Users\Ноутбук\Desktop\enviroment\change_audio\videoplayback.mp4'
    dir = r'C:\Users\Ноутбук\Desktop\enviroment\change_audio\temporary'
    print(asyncio.run(async_split_on_parts(path, dir, num_parts=10, threads=4)))
