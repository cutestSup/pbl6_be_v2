import sys
import os

vietocr_path = os.path.join(os.path.dirname(__file__), "..", "..", "vietocr")
if vietocr_path not in sys.path:
    sys.path.insert(0, vietocr_path)

from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from PIL import Image

def load_vietocr(config_path, weights_path, device):
    config = Cfg.load_config_from_file(config_path)
    config['weights'] = weights_path
    config['device'] = device
    config['cnn']['pretrained'] = False
    model = Predictor(config)
    return model

def recognize_text(predictor, pil_image_or_numpy):
    return predictor.predict(pil_image_or_numpy)