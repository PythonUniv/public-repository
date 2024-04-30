from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import torch
from pydantic import BaseModel
from fastapi import UploadFile
from transformers import YolosImageProcessor, YolosForObjectDetection


class ObjectDetected(BaseModel):
    box: list[float]
    label_id: int
    label: str
    
    
class ObjectsDetected(BaseModel):
    objects_detected: list[ObjectDetected]


class ObjectDetectionModel:
    def __init__(
        self,
        model_name: str = 'hustvl/yolos-tiny'
    ) -> None:
        """Instantiate model detection named mode_name on HuggingFace."""
        
        self.model_name = model_name
        self.image_processor = None
        self.model = None
    
    def load_model(
        self
    ) -> None: 
        """Loads model."""
        
        self.image_processor = YolosImageProcessor.from_pretrained(self.model_name)
        self.model = YolosForObjectDetection.from_pretrained(self.model_name)
    
    def predict(
        self,
        image: Image.Image,
        score_confidence: float = 0.75
    ) -> list[dict]:
        """Makes prediction."""
        
        if self.image_processor is None or self.model is None:
            raise RuntimeError('Model is not loaded.')
        
        processed = self.image_processor(image, return_tensors='pt')
        predicted = self.model(**processed)
        
        width, height = image.size
        target_sizes = torch.tensor([[height, width]])
        
        detected = self.image_processor.post_process_object_detection(
            predicted,
            target_sizes=target_sizes,
        )[0]
        
        output = []
        for score, label_id, box in zip(*detected.values()):
            if score > score_confidence:
                output.append(
                    {
                        'box': box.tolist(),
                        'label_id': label_id.item(),
                        'label': self.model.config.id2label[label_id.item()],
                        'score': score.item()
                    }
                )
        return output
    
    @staticmethod
    def draw_detected_object(
        image: Image.Image,
        prediction: list[dict]
    ) -> Image.Image:
        """Draw predicted objects in image."""
        
        image_draw = ImageDraw.ImageDraw(image)
        font = ImageFont.truetype(r'C:\Users\Ноутбук\Desktop\enviroment\object_detection_app\Nicolast.ttf', 18)
        
        for detection in prediction:
            x_1, y_1, x_2, y_2 = detection['box']
            score, label = detection['score'], detection['label']
            
            image_draw.rectangle((x_1, y_1, x_2, y_2), outline='red', width=5)
            image_draw.text((x_1, y_1), text=label + f' ({score:.2f})', font=font)
        return image
    
    @staticmethod
    def bytes_to_pil_image(
        bytes: bytes
    ) -> Image.Image:
        """Converts bytes of image into PIL Image."""
        
        return Image.open(BytesIO(bytes))
    
    @staticmethod
    def pil_image_to_bytes(
        image: Image.Image
    ) -> tuple[bytes, str]:
        """Converts PIL Image into bytes and format string."""
        
        image.seek(0)
        buffer = BytesIO()
        image.save(buffer, format=image.format)
        buffer.seek(0)
        return buffer.read(), image.format.lower() 
        
        
async def async_file_to_pil_image(
    image: UploadFile
):
    return ObjectDetectionModel.bytes_to_pil_image(await image.read())
    
        
if __name__ == '__main__':
    object_detection_model = ObjectDetectionModel()
