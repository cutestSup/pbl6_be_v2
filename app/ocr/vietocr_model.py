import sys
import os
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from PIL import Image
import numpy as np

def load_vietocr(config_path, weights_path, device):
    # print(f"Loading VietOCR from {weights_path}...")
    config = Cfg.load_config_from_file(config_path)
    config['weights'] = weights_path
    config['device'] = str(device)
    config['cnn']['pretrained'] = False
    
    model = Predictor(config)
    # print("VietOCR loaded successfully.")
    return model

def recognize_text(predictor, image):
    """
    image: PIL Image or numpy array
    """
    try:
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
            
        txt = predictor.predict(image)
        
        if isinstance(txt, str):
            return txt.strip()
        else:
            return str(txt).strip()
    except Exception as e:
        print(f"VietOCR Error: {e}")
        return ""

def recognize_text_batch(predictor, images):
    """
    images: List of PIL Images or numpy arrays
    """
    if not images:
        return []
        
    pil_images = []
    for img in images:
        if isinstance(img, np.ndarray):
            pil_images.append(Image.fromarray(img))
        else:
            pil_images.append(img)
            
    try:
        texts = predictor.predict_batch(pil_images)
        return [t.strip() for t in texts]
    except Exception as e:
        print(f"VietOCR Batch Error: {e}")
        return [""] * len(images)
