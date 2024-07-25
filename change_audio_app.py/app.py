import torch
import gradio as gr

from utils import (async_video_meta_data,
                   seconds_to_str,
                   timeline)
from audio_change import split, riffusuion_inference, create_archive


print(f'cuda: {torch.cuda.is_available()}')


initial_caution = '# !!!'


def caution(num_clips: float | int, chosen_clip: int | float) -> gr.Markdown:
    initial_length = len(initial_caution)
    caution = initial_caution
    
    if not isinstance(num_clips, int) or num_clips < 1:
        caution += '\n ### Number of parts should be only integer greater or equal 1.'
    elif chosen_clip < 1 or num_clips < chosen_clip:
        caution += f'\n ### Chosen clip should be less or equal {num_clips}'
    elif not isinstance(chosen_clip, int):
        caution += '\n ### Number of chosen clip should be integer.'
    visible = initial_length < len(caution)
    return gr.Markdown(caution, visible=visible)


async def change_status(video_path: str | None, num_clips: int, chosen_clip: int, prompt_state: str) -> str:
    if video_path is not None:
        meta_data = await async_video_meta_data(video_path)
        duration = float(meta_data['streams'][0]['duration'])
    else:
        meta_data = None
    
    status = f'''
        # Status
        ### Video duration: {seconds_to_str(duration) if meta_data is not None else None}
        ### Current prompt: {prompt_state}
        ### Number of parts to divide into: {num_clips}
        ### Chosen clip: {chosen_clip}
        {f"### Part duration: {seconds_to_str(duration / num_clips)} seconds/part" if meta_data is not None else ""}
        {f"### Chosen part timeline: {timeline(num_clips, chosen_clip, duration)}" if meta_data is not None and 0 < chosen_clip <= num_clips else ""}
    '''
    return status


def generate_comp_visibility(video_path: str | None, warning: str) -> gr.Button:
    global video_comp, warning_comp
    if video_path is not None and warning == initial_caution:
        return gr.Button(visible=True)
    else:
        return gr.Button(visible=False)
    
    
async def split_video(
    video_path: str, num_clips: int, chosen_clip: str, prompt: str,
    guidance_scale: float, num_inference_steps: int, data: dict | None, exact: bool
) -> dict:
    if (
        data is not None and
        video_path == data['video_path'] and
        num_clips == data['num_clips']
    ):
        paths = [clip['original'] for clip in data['clips']]
    else:
        paths = None
    
    additional = {'guidance_scale': guidance_scale, 'num_inference_steps': num_inference_steps}
    data = await split(video_path, num_clips, chosen_clip, prompt, additional, exact=exact, paths=paths)
    return data


def download_archive(data: dict) -> tuple[dict, gr.DownloadButton]:
    if data['archive'] is not None:
        archive = data['archive']
    else:
        archive = create_archive(data)
    data['archive'] = archive
    return data, gr.DownloadButton(value=archive)


def download_visibility(data: dict | None) -> gr.DownloadButton:
    if data is None:
        return gr.DownloadButton(visible=False)
    return gr.DownloadButton(visible=True)
    

with gr.Blocks(theme=gr.themes.Monochrome()) as demo:
    greeting_comp = gr.Markdown(
        '''
            # Replace Audio on Your Video ✨✨✨
            ### Load the video, specify number of equal parts to separate video into
        ''', show_label=False)
    
    with gr.Row():
        video_comp = gr.Video(sources='upload', label='Input Video', scale=1, width=345, height=345)
        
        num_clips_comp = gr.Number(
            value=1, minimum=1, precision=1, label='Number of Clips',
            info='Number of clips to separate video into.',
            interactive=True, scale=1)
        
        chosen_clip_comp = gr.Number(
            value=1, minimum=1, label='Chosen Clip', interactive=True, scale=1)
        
        status_comp = gr.Markdown(
            '''
            # Status
            ### Video duration:
            ### Current prompt:
            ### Number of parts: 1
            ### Chosen clip: 1
            ''', visible=True)
    
    warning_comp = gr.Markdown(initial_caution, visible=False, show_label=False)
    gr.on(fn=caution, inputs=[num_clips_comp, chosen_clip_comp], outputs=warning_comp)
    
    prompt_state_comp = gr.State(value='')
    gr.on(
        fn=change_status,
        inputs=[video_comp, num_clips_comp, chosen_clip_comp, prompt_state_comp],
        outputs=status_comp)
    
    prompt_comp = gr.Textbox(placeholder='Your prompt', label='Prompt', interactive=True, lines=3)
    submit_comp = gr.Button('Submit Prompt', size='sm')
    submit_comp.click(lambda new_prompt: new_prompt, inputs=prompt_comp, outputs=prompt_state_comp)
    
    with gr.Accordion(label='Additional Settings', open=False, render=False) as additional_settings_comp:
        num_columns_comp = gr.Number(label='Number of Columns', value=3, minimum=1, maximum=21)

        exact_comp = gr.Checkbox(label='Exact Split', value=False, info='Exact splitting works much more accurately but slower.')
        guidance_scale_comp = gr.Number(label='Guidance Scale', value=6.5, minimum=0, maximum=45)
        num_inference_steps_comp = gr.Number(label='Steps', value=50, minimum=1, maximum=100)
            
    generate_comp = gr.Button(value='Split-n-Generate', size='sm', visible=False, scale=1)
    gr.on(fn=generate_comp_visibility, inputs=[video_comp, warning_comp], outputs=generate_comp)
    generated_state_comp = gr.State(value=None)
    generate_comp.click(
        split_video,
        inputs=[
            video_comp, num_clips_comp, chosen_clip_comp, prompt_state_comp,
            guidance_scale_comp, num_inference_steps_comp, generated_state_comp, exact_comp
        ],
        outputs=generated_state_comp).then(riffusuion_inference, generated_state_comp, generated_state_comp, show_progress=True)

    processing_comp = gr.Markdown(visible=False, show_label=False)
    generate_comp.click(
        lambda: gr.Markdown('# Wait! 🕒\n\n # Task is processing now! 😎', visible=True),
        outputs=processing_comp)
    generated_state_comp.change(
        lambda data: gr.Markdown(visible=False) if any(clip['edited'] for clip in data['clips']) else gr.Markdown(visible=True),
        inputs=generated_state_comp, outputs=processing_comp)
    
    additional_settings_comp.render()
    
    @gr.render([generated_state_comp, num_columns_comp])
    def update_clips(data: dict | None, num_columns: int):
        if data is not None:
            num_clips = data['num_clips']
            for idx in range(0, num_clips, num_columns):
                clips = data['clips'][idx: idx + num_columns]
                with gr.Row():
                    for clip in clips:
                        original_path = clip['original']
                        edited_path = clip['edited']
                        
                        with gr.Column():
                            path = edited_path or original_path
                            gr.Video(path, interactive=False, width=235, height=175)
    
    download_comp = gr.DownloadButton(visible=False)
    generated_state_comp.change(download_visibility, generated_state_comp, download_comp)
    download_comp.click(download_archive, generated_state_comp, [generated_state_comp, download_comp])


if __name__ == '__main__':
    demo.launch(share=True)
