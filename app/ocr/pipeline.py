import numpy as np
import torch
import cv2
import time
from PIL import Image
from app.ocr.preprocess import preprocess_image_bytes
from app.ocr.dbnet_model import load_dbnet, detect_boxes
from app.ocr.vietocr_model import load_vietocr, recognize_text

class OCRPipeline:
    def __init__(self, dbnet_weight, dbnet_cfg, vietocr_cfg, vietocr_weight):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.dbnet = load_dbnet(dbnet_weight, dbnet_cfg, self.device)
        self.vietocr = load_vietocr(vietocr_cfg, vietocr_weight, str(self.device))

    def process(self, image_bytes):
        start = time.time()
        img_resized, binary = preprocess_image_bytes(image_bytes)
        boxes = detect_boxes(self.dbnet, img_resized)  # list of boxes (x1,y1,x2,y2)
        results = []
        for (x1,y1,x2,y2) in boxes:
            crop = img_resized[y1:y2, x1:x2]
            import PIL.Image as Image
            crop_pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
            text = recognize_text(self.vietocr, crop_pil)
            results.append({"bbox":[x1,y1,x2,y2], "text": text})
        return {"results": results, "processing_time": time.time()-start}
