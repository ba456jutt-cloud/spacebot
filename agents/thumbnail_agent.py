import os
import requests
import urllib.parse
import json
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

def get_bold_font(size=120):
    """Downloads a bold Google Font (Anton) if not present to ensure high CTR text."""
    os.makedirs("assets", exist_ok=True)
    font_path = "assets/Anton-Regular.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
        try:
            r = requests.get(url)
            with open(font_path, "wb") as f:
                f.write(r.content)
        except:
            return ImageFont.load_default()
    return ImageFont.truetype(font_path, size)

def generate_custom_thumbnail(seo_title: str, topic: str, output_path: str = "assets/thumbnail.jpg") -> str:
    """
    Generates a viral YouTube thumbnail.
    """
    print(f"[*] Thumbnail Agent: Generating viral thumbnail for '{seo_title}'...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    prompt_text = "A hyper-realistic cinematic deep space anomaly, MrBeast style, bright glowing neon colors, extreme contrast, highly detailed, 8k"
    overlay_text = "SHOCKING!"
    
    if api_key and api_key != "your_gemini_api_key_here":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        sys_prompt = f"""
        We need a VIRAL YouTube thumbnail for a video titled: "{seo_title}" (Topic: {topic}).
        Provide JSON with two keys:
        1. "image_prompt": A highly detailed prompt for an AI image generator. Create a "Split-Screen Composition" tailored EXACTLY to the video title.
        - Left Side: A hyper-realistic close-up of a relevant subject (e.g., if the video is about the deep sea, show a shocked diver; if about space, an astronaut or scientist).
        - Right Side: The core mystery of the video (e.g., if deep sea, a terrifying glowing sea creature; if space, a black hole or alien).
        Make it extremely vibrant, hyper-saturated colors, cinematic lighting, and extreme contrast to maximize click-through rate. NO TEXT IN PROMPT.
        2. "overlay_text": Extract the most shocking or compelling 2 to 3 words max directly from the title. Must be extremely punchy (e.g., "SHOCKING TRUTH", "NASA LIED?", "THEY EXIST!").
        
        Strict JSON only.
        """
        payload = {"contents": [{"parts": [{"text": sys_prompt}]}]}
        try:
            resp = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            resp.raise_for_status()
            res_text = resp.json()['candidates'][0]['content']['parts'][0]['text']
            res_text = res_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(res_text)
            prompt_text = data.get("image_prompt", prompt_text)
            # Add a style enhancer suffix
            prompt_text += ", MrBeast style thumbnail, highly saturated, glowing elements, 8k resolution, masterpiece"
            overlay_text = data.get("overlay_text", overlay_text).upper()
        except Exception as e:
            print(f"[-] Thumbnail Agent (Gemini Error): {e}. Using fallback.")
            
    # Download background image
    encoded_prompt = urllib.parse.quote(prompt_text)
    seed = random.randint(1000, 99999)
    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={seed}"
    
    try:
        r = requests.get(img_url, timeout=45)
        with open(output_path, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print(f"[-] Thumbnail Agent failed to download image: {e}")
        return None
        
    # Overlay Text using Pillow
    try:
        img = Image.open(output_path).convert("RGBA")
        draw = ImageDraw.Draw(img)
        
        font = get_bold_font(130)
            
        width, height = img.size
        wrapped_text = textwrap.fill(overlay_text, width=12)
        
        try:
            bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align="center")
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = draw.textsize(wrapped_text, font=font)
        
        # Center horizontally, place slightly below center vertically
        x = (width - text_w) / 2
        y = (height - text_h) / 2 + 50
        
        # Draw stroke/shadow (Thick black outline for MrBeast style)
        stroke_width = 8
        for adj_x in range(-stroke_width, stroke_width+1):
            for adj_y in range(-stroke_width, stroke_width+1):
                # Make the shadow slightly darker and shifted down for 3D effect
                draw.multiline_text((x+adj_x+4, y+adj_y+4), wrapped_text, font=font, fill="black", align="center")
                
        # Draw main text in bright yellow
        draw.multiline_text((x, y), wrapped_text, font=font, fill="#FFFF00", align="center")
        
        img = img.convert("RGB")
        img.save(output_path, quality=95)
        print(f"[+] Thumbnail saved successfully: {output_path}")
        return output_path
    except Exception as e:
        print(f"[-] Thumbnail Agent failed to overlay text: {e}")
        return output_path
