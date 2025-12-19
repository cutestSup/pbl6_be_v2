import os
import gdown
import sys

def download_weights():
    """Download model weights from Google Drive if not exists"""
    
    weights_dir = "app/weights"
    os.makedirs(weights_dir, exist_ok=True)
    
    dbnet_path = os.path.join(weights_dir, "model_best.pth")
    if not os.path.exists(dbnet_path):
        print("📥 Downloading DBNet weights...")
        dbnet_url = "https://drive.google.com/uc?id=1hyoxmkccDPndPvAU84Ct6M5JHF-EzKeC"
        gdown.download(dbnet_url, dbnet_path, quiet=False)
    
    vietocr_path = os.path.join(weights_dir, "myModelOCR.pth")
    if not os.path.exists(vietocr_path):
        print("📥 Downloading VietOCR weights...")
        vietocr_url = "https://drive.google.com/uc?id=1WKEH3xdXFiaxbtM7xLwGXkS2IJZNXxJ5"
        gdown.download(vietocr_url, vietocr_path, quiet=False)
    
    print("✅ All weights ready!")

if __name__ == "__main__":
    download_weights()
