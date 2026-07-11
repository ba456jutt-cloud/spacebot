import os
import urllib.request
import onnxruntime as ort
import numpy as np
import cv2

MODEL_URL = "https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx"
MODEL_PATH = "assets/midas_small.onnx"

def download_model():
    if not os.path.exists(MODEL_PATH):
        print("[*] Downloading MiDaS ONNX model for 3D Depth estimation...")
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("[+] Model downloaded.")

def get_depth_map(img_path):
    # Load image
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Preprocess for MiDaS small
    # Input size: 256x256, normalize with mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
    img_resized = cv2.resize(img, (256, 256))
    img_input = img_resized.astype(np.float32) / 255.0
    
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    img_input = (img_input - mean) / std
    
    # Transpose to NCHW
    img_input = np.transpose(img_input, (2, 0, 1))
    img_input = np.expand_dims(img_input, axis=0)
    
    # Run inference
    session = ort.InferenceSession(MODEL_PATH, providers=['CPUExecutionProvider'])
    input_name = session.get_inputs()[0].name
    
    depth = session.run(None, {input_name: img_input})[0]
    
    # Normalize depth map to 0-1
    depth = depth[0]
    depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-6)
    
    # Resize back to original image size
    depth = cv2.resize(depth, (img.shape[1], img.shape[0]))
    return depth

def create_parallax_video(img_path, out_path, num_frames=120, fps=24):
    download_model()
    depth = get_depth_map(img_path)
    
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    
    # Grid
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h / 2
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    
    # 3D Dolly Zoom Effect
    max_zoom = 0.08 # 8% total zoom
    
    print(f"[*] Rendering {num_frames} frames of 3D Parallax...")
    for i in range(num_frames):
        progress = i / float(num_frames - 1)
        
        # Scale foreground more than background based on depth map
        # depth map is 1 for close objects, 0 for far objects
        scale = 1.0 + (max_zoom * progress * (0.3 + 0.7 * depth))
        
        map_x = (x - cx) / scale + cx
        map_y = (y - cy) / scale + cy
        
        frame = cv2.remap(img, map_x.astype(np.float32), map_y.astype(np.float32), interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        out.write(frame)
        
    out.release()
    print(f"[+] Parallax video saved to {out_path}")

if __name__ == "__main__":
    if os.path.exists("assets/scene_001.jpg"):
        create_parallax_video("assets/scene_001.jpg", "assets/scene_001_animated.mp4")
    else:
        print("No test image found.")
