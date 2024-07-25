import os
import uuid

from utils import async_video_meta_data, async_split_on_parts, replace_audio, to_archive
import riffusion_inference
from config import config


async def split(
    video_path: str, num_clips: int, chosen_clip: int, prompt: str, additional: dict,
    exact: bool, paths: list[str] | None = None
) -> dict:
    if paths is None:
        paths = await async_split_on_parts(
            video_path, config.temporary_directory, num_clips, exact, config.threads_on_spliting)
    data = {
        'video_path': video_path,
        'num_clips': num_clips,
        'chosen_clip': chosen_clip,
        'prompt': prompt,
        'additional': additional,
        'archive': None,
        'clips': [
            {
                'original': path,
                'edited': None
            } for path in paths
        ]
    }
    return data


async def riffusuion_inference(data: dict) -> dict:
    audio_name = str(uuid.uuid4()) + '.wav'
    audio_path = os.path.join(config.temporary_directory, audio_name)
    chosen_clip = data['chosen_clip']
    video_path = data['clips'][chosen_clip - 1]['original']
    
    meta_data = await async_video_meta_data(video_path)
    duration = float(meta_data['streams'][0]['duration'])
    
    guidance_scale = data['additional']['guidance_scale']
    num_inference_steps = data['additional']['num_inference_steps']
    riffusion_inference.inference(data['prompt'], guidance_scale, num_inference_steps, duration, audio_path, format='wav')
    
    edited_path = await replace_audio(
        video_path, audio_path, dir=config.temporary_directory,
        threads=config.threads_on_spliting)
    data['clips'][chosen_clip - 1]['edited'] = edited_path
    print('Audio Replaced')
    return data


def create_archive(data: dict) -> str:
    archive_name = str(uuid.uuid4()) + '.zip'
    archive_path = os.path.join(config.temporary_directory, archive_name)
    clip_paths = [clip['edited'] or clip['original'] for clip in data['clips']]
    to_archive(archive_path, clip_paths)
    return archive_path
