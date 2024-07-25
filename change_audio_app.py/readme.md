# README
### Application is build for a test task.

 App is intended for splitting input video on parts of equal duration and replacing the audio on the chosen part using Riffusion (Diffusion that works on spectrograms of audio instead of real-world images).


# Functional
* Loading input video
* Information about:
    * applied prompt
    * number parts
    * chosen part for replacing the audio
    * duration of each part
    * timeline of chosen part
* Additional settings:
    * manage a guidance scale
    * number of diffusion steps
    * number of output columns with videos
    * 'exact split' - if True then using exact splitting of the video on equal parts (it slows down the application, though, because of rerendering the  video but may occur useful when interval of the video less than 5 seconds.)
* Possibility to change the prompt
* 'Split-n-Generate' button which splits video on parts, generate an audio and replace audio on the original part of the video into generated music.
* Download (archive of videos) button. 
### Caution!  
#### The 'Split-n-Generate' button works only when the video loaded and input field are fully correct (otherwise it is invisible)

---
# Engineer details:
#### Builded with:
    torch
    ffmpeg (for audio/video manipulation)
    gradio (interface, backend endpoints)
    diffusers (HF) - convenient pipelines

And, of course, using Riffusion repository for transforming spectrograms to audio.


#### Whenever it was reasonable I used async functions and multithreading for manipulating with recording and splitting the video to optimize the application (even it may be not the best idea to release this app into real production because of gradio)

### Structure of application
 * app.py - user interface with backend, very high level functions
 * audio_change.py - high level functions for manipulating of splitting the video, generating the audio and replacing it.
 * utils.py - help functions
 * riffusion_inference.py - running of the diffusion model
 * config.py - settings of the inference

# Start of the application 
### Deploy guide on HuggingFace Spaces: https://huggingface.co/docs/hub/spaces-overview

### or 

### Using Virtual Machine:
    git clone https://huggingface.co/spaces/dima21232/change_audio
    cd change_audio
    pip install -r requirements.txt
    python app/app.py


#### Init your .env file inside /app folder!
Environment Variables
* TEMPORARY_DIRECTORY
* THREADS_ON_SPLITING
* DEVICE - cuda by default
* MAX_IMAGE_WIDTH - must be divisible by 8
