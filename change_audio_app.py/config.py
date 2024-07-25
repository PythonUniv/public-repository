import os
import dotenv
from pydantic import BaseModel, Field


dotenv_values = dotenv.dotenv_values()


class Config(BaseModel):
    temporary_directory: str | None = Field(None, description='Directory where clips will be saved.')
    threads_on_spliting: int = Field(1, ge=1)
    device: str = Field('cuda')
    max_image_width: int = Field(1024, ge=1)


temporary_directory = dotenv_values['TEMPORARY_DIRECTORY']
if temporary_directory is None:
    temporary_directory = os.path.join(os.path.dirname(__file__), 'temporary')
os.makedirs(temporary_directory, exist_ok=True)

threads = dotenv_values['THREADS_ON_SPLITING']
device = dotenv_values['DEVICE']
max_image_width = dotenv_values['MAX_IMAGE_WIDTH']


config = Config(
    temporary_directory=temporary_directory,
    threads_on_spliting=threads,
    device=device,
    max_image_width=max_image_width
)
