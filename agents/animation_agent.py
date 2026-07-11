import os
import subprocess

def generate_3d_animations(scenes: list) -> list:
    """
    Takes the generated images and uses OpenCV to create a smooth 2D Ken Burns
    Zoom animation. Falls back gracefully if any error occurs.
    DepthFlow requires a display (GLFW), so we use a robust pure-Python fallback.
    """
    print(f"[*] Animation Agent: Generating animations for {len(scenes)} scenes...")
    
    for idx, scene in enumerate(scenes):
        img_path = scene.get("image_path")
        if not img_path or not os.path.exists(img_path):
            continue
            
        anim_path = img_path.replace(".jpg", "_animated.mp4")
        scene["animated_path"] = anim_path
        
        if os.path.exists(anim_path):
            print(f"  [-] Animation already exists for Scene {scene['scene_id']}, skipping...")
            continue
            
        print(f"  [+] Animating Scene {scene['scene_id']} ({idx+1}/{len(scenes)})...")
        
        try:
            import cv2
            import numpy as np

            img = cv2.imread(img_path)
            if img is None:
                raise ValueError(f"Could not read image: {img_path}")
            
            h, w = img.shape[:2]
            fps = 24
            num_frames = fps * 5  # 5 second clip per scene
            max_zoom = 0.06       # 6% zoom-in (Ken Burns effect)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(anim_path, fourcc, fps, (w, h))

            for i in range(num_frames):
                progress = i / float(num_frames - 1)
                scale = 1.0 + (max_zoom * progress)

                new_w = int(w / scale)
                new_h = int(h / scale)
                x1 = (w - new_w) // 2
                y1 = (h - new_h) // 2
                x2 = x1 + new_w
                y2 = y1 + new_h

                cropped = img[y1:y2, x1:x2]
                frame = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
                out.write(frame)

            out.release()
            print(f"  [+] Scene {scene['scene_id']} animation done.")
        except Exception as e:
            print(f"  [-] Animation Error on Scene {scene['scene_id']}: {e}")
            scene["animated_path"] = img_path  # fallback to static image
            
    return scenes

if __name__ == "__main__":
    pass
