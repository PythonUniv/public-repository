import contextlib
from PIL import Image
import uvicorn
from fastapi import FastAPI, Depends, Body
from fastapi.responses import Response


from object_detection import (ObjectsDetected,
                              ObjectDetectionModel,
                              async_file_to_pil_image)


model = ObjectDetectionModel()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    model.load_model()    
    yield
    
    
app = FastAPI(lifespan=lifespan)


@app.post('/predict', response_model=ObjectsDetected)
def predict(
    image: Image.Image = Depends(async_file_to_pil_image),
    score_confidence: float = Body(0.75, ge=0, le=1)
) -> list[dict]:
    """Returns detected objects in json."""
    
    return {'objects_detected': model.predict(image=image, score_confidence=score_confidence)}


@app.post('/detect', response_class=Response)
def detect(
    image: Image.Image = Depends(async_file_to_pil_image),
    score_confidence: float = Body(0.75, ge=0, le=1)
) -> Response:
    """Draws detected object in image."""
    
    prediction = model.predict(image, score_confidence=score_confidence)
    model.draw_detected_object(image, prediction=prediction)
    image_bytes, format = model.pil_image_to_bytes(image)
    return Response(content=image_bytes, media_type=f'image/{format}')


if __name__ == '__main__':
    uvicorn.run('app:app')
