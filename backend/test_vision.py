import sys
import os
import asyncio

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.vision_service import get_vision_service
from PIL import Image
import io

async def test_yolo():
    print("Initializing VisionService...")
    vision = get_vision_service()
    
    # Create a small dummy image (red rectangle representing a potential target)
    img = Image.new('RGB', (320, 240), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    
    print("Running detection...")
    result = await vision.detect(img_bytes, conf_threshold=0.1)
    print("\nSUCCESS! Detection results:")
    print(f"Model used: {result['model']}")
    print(f"Resolution: {result['image_width']}x{result['image_height']}")
    print(f"Detections count: {len(result['detections'])}")
    print(f"Summary: {result['summary']}")

if __name__ == "__main__":
    asyncio.run(test_yolo())
