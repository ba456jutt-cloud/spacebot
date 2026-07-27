import os
import requests
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
import textwrap

def get_bold_font(size=120):
    font_path = "assets/Anton-Regular.ttf"
    if not os.path.exists(font_path):
        return ImageFont.load_default()
    return ImageFont.truetype(font_path, size)

def overlay_text(img_path, overlay_text_str, out_path):
    img = Image.open(img_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    font = get_bold_font(180)
    width, height = img.size
    wrapped_text = textwrap.fill(overlay_text_str, width=12)
    
    try:
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align="center")
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        text_w, text_h = draw.textsize(wrapped_text, font=font)
    
    x = (width - text_w) / 2
    y = (height - text_h) / 2 + 50
    
    stroke_width = 8
    for adj_x in range(-stroke_width, stroke_width+1):
        for adj_y in range(-stroke_width, stroke_width+1):
            draw.multiline_text((x+adj_x+4, y+adj_y+4), wrapped_text, font=font, fill="black", align="center")
            
    draw.multiline_text((x, y), wrapped_text, font=font, fill="#FFFF00", align="center")
    img = img.convert("RGB")
    img.save(out_path, quality=95)

tests = [
    {
        "name": "style1_realism",
        "prompt": "A hyper-realistic cinematic shot of Earth cracking open, glowing magma from space, highly detailed, National Geographic documentary style, 8k, photorealistic",
        "model": "flux-realism",
        "text": "IT'S HAPPENING"
    },
    {
        "name": "style2_dark_mystery",
        "prompt": "A massive, terrifying, pitch black silhouette of an unknown structure looming near Jupiter, eerie, cosmic horror, cinematic lighting, 8k, masterpiece",
        "model": "flux",
        "text": "WHAT IS IT?"
    },
    {
        "name": "style3_sci_fi_art",
        "prompt": "Epic concept art of a futuristic megastructure in deep space, glowing neon lights, extremely detailed, trending on ArtStation, cinematic composition",
        "model": "flux-3d",
        "text": "ALIEN MEGASTRUCTURE"
    }
]

out_dir = "/home/ahmad/.gemini/antigravity/brain/8e43c054-ccae-4160-8f0c-6125a7646b43/"

for i, t in enumerate(tests):
    encoded = urllib.parse.quote(t["prompt"])
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed=12345&model={t['model']}"
    raw_img = os.path.join(out_dir, f"raw_{t['name']}.jpg")
    final_img = os.path.join(out_dir, f"{t['name']}.jpg")
    
    print(f"Downloading {t['name']}...")
    r = requests.get(url)
    with open(raw_img, "wb") as f:
        f.write(r.content)
        
    overlay_text(raw_img, t["text"], final_img)
    print(f"Saved to {final_img}")
