# README
### Application is build for a test task.

 App is intended for splitting input video on parts of equal duration and replacing the audio on the chosen part using Riffusion (Diffusion that works on spectrograms of audio instead of real-world images).
 # Visit https://huggingface.co/spaces/dima21232/change_audio
 # where I deployed model on GPU. Just trigger it!


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
# Engineering details:
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

# Run application
### Deploy guide on HuggingFace Spaces: https://huggingface.co/docs/hub/spaces-overview

### or 

### Using Virtual Environment:
    git clone https://huggingface.co/spaces/dima21232/change_audio
    cd change_audio
    pip install -r requirements.txt
    python app/app.py

### Template of Dockerfile used by HuggingFace for deployment:
    FROM docker.io/nvidia/cuda:12.3.2-cudnn9-devel-  
    ubuntu22.04@sha256:fb1ad20f2552f5b3aafb2c9c478ed57da95e2bb027d15218d7a55b3a0e4b4413

    RUN pyenv install 3.10 && 	pyenv global 3.10 && 	pyenv rehash
    RUN pip install --no-cache-dir pip==22.3.1 && 	pip install --no-cache-dir 	datasets 	"huggingface-hub>=0.19" "hf-transfer>=0.1.4" "protobuf<4" "click<8.1" 
    "pydantic~=1.0"

    COPY --chown=1000:1000 --from=root / /

    RUN apt-get update && apt-get install -y 	git rsync 	make build-essential libssl-dev zlib1g-dev 	libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm 	libncursesw5- 
    dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev git-lfs  	ffmpeg libsm6 libxext6 cmake libgl1-mesa-glx 	&& rm -rf /var/lib/apt/lists/* 	&& git lfs 
    install

    RUN apt-get update && apt-get install -y fakeroot &&     mv /usr/bin/apt-get /usr/bin/.apt-get &&     echo '#!/usr/bin/env sh\nfakeroot /usr/bin/.apt-get $@' > 
    /usr/bin/apt-get &&     chmod +x /usr/bin/apt-get && 	rm -rf /var/lib/apt/lists/* && 	useradd -m -u 1000 user


    RUN curl https://pyenv.run | bash

    RUN pip freeze > /tmp/freeze.txt


    WORKDIR /home/user/app

    RUN --mount=target=/tmp/requirements.txt,source=requirements.txt     pip install --no-cache-dir -r /tmp/requirements.txt

    RUN pip install --no-cache-dir 	gradio[oauth]==4.39.0 	"uvicorn>=0.14.0" 	spaces

    COPY --link --chown=1000 ./ /home/user/app

    COPY --from=pipfreeze --link --chown=1000 /tmp/freeze.txt /tmp/freeze.txt

    #--> Pushing image
    #DONE 1.0s
    #
    #--> Exporting cache
    #DONE 1.1s



#### Init your .env file inside /app folder!
Environment Variables
* TEMPORARY_DIRECTORY
* THREADS_ON_SPLITING
* DEVICE - cuda by default
* MAX_IMAGE_WIDTH - must be divisible by 8
