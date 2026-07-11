from moviepy import ImageClip, CompositeVideoClip

try:
    img = ImageClip("assets/scene_001.jpg").with_duration(1)
    
    # In MoviePy 2.x, some vfx functions are applied using .with_effects()
    # Let's see if .resized() takes a function
    animated = img.resized(lambda t: 1 + 0.05 * t)
    
    comp = CompositeVideoClip([animated.with_position('center')], size=(1920, 1080))
    print("Success with resized() and with_position()")
except Exception as e:
    print("Error:", e)
