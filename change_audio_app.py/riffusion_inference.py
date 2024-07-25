import os
import sys
from math import floor, ceil
import PIL
import pydub
from diffusers import DiffusionPipeline, StableDiffusionImg2ImgPipeline

sys.path.append(os.path.join(os.path.dirname(__file__), 'riffusion'))
from riffusion.spectrogram_image_converter import SpectrogramImageConverter
from riffusion.spectrogram_params import SpectrogramParams

from config import config


print(f'File location: {__file__}')


init_image = PIL.Image.open(os.path.join(os.path.dirname(__file__), 'riffusion', 'seed_images', 'og_beat.png')).convert('RGB')


pipeline = DiffusionPipeline.from_pretrained('riffusion/riffusion-model-v1').to(config.device)
diffusion_img_to_img = StableDiffusionImg2ImgPipeline.from_pipe(pipeline)
spectrogram_params = SpectrogramParams()
spectrogram_image_converter = SpectrogramImageConverter(spectrogram_params)


def inference(prompt: str, guidance_scale: float, num_inference_steps: int, duration: float, save_path: str, format: str):
    default_width = 512
    default_duration = 5.12
    
    print(duration)
    print(type(duration))
    
    total_width = floor(default_width / default_duration * duration)
    width = config.max_image_width
    iters = ceil(total_width / width)
    
    spectrograms = []
    for idx in range(iters):
        if idx == 0:
            spectrogram = pipeline(
                prompt, width=width, init_image=init_image, guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps
            )['images'][0]
        else:
            spectrogram = diffusion_img_to_img(prompt, image=spectrograms[-1], strength=0.9, guidance_scale=guidance_scale).images[0]
        spectrograms.append(spectrogram)
        
    audio = pydub.AudioSegment.empty()
    for spectrogram in spectrograms:
        audio += spectrogram_image_converter.audio_from_spectrogram_image(spectrogram)
    audio.export(save_path, format=format)
