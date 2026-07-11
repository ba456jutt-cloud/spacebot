import os
import subprocess

def test_depthflow():
    img_path = "assets/scene_001.jpg"
    out_path = "assets/scene_001_animated.mp4"
    
    if not os.path.exists(img_path):
        print("Test image not found.")
        return
        
    print(f"Running DepthFlow on {img_path}...")
    try:
        cmd = [
            "./venv/bin/depthflow",
            img_path,
            "-o", out_path
        ]
        subprocess.run(cmd, check=True)
        print(f"Success! Saved to {out_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_depthflow()
