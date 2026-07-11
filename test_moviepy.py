from moviepy import ImageClip, CompositeVideoClip
try:
    img = ImageClip("assets/scene_001.jpg").with_duration(1)
    if hasattr(img, 'resized'):
        print("Has resized()")
    elif hasattr(img, 'resize'):
        print("Has resize()")
    else:
        print("No resize method")
except Exception as e:
    print("Error:", e)
