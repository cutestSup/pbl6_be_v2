import torch
import numpy as np
import cv2
import yaml
import os
from addict import Dict
from segmentation.models import build_model

def load_dbnet(model_path, cfg_path, device):
    # print(f"Loading DBNet from {model_path}...")
    with open(cfg_path, "r") as f:
        cfg = Dict(yaml.safe_load(f))

    if "in_channels" not in cfg["arch"]["backbone"]:
        cfg["arch"]["backbone"]["in_channels"] = 3

    model = build_model(cfg["arch"])
    
    # Load checkpoint
    checkpoint = torch.load(model_path, map_location=device)
    
    # Handle state_dict
    if 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']
    else:
        state_dict = checkpoint
        
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    
    # print("DBNet loaded successfully.")
    return model

def detect_boxes(dbnet_model, img):
    # This function is no longer used in the new pipeline 
    # because inference is done directly in pipeline.py
    pass

    # TODO: Implement actual detection logic
    # Placeholder: return whole image as single bbox
    h, w = img.shape[:2]
    return [(0, 0, w, h)]