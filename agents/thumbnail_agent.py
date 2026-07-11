import os
import requests
import urllib.parse
import json
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

def generate_custom_thumbnail(seo_title: str, topic: str, output_path: str = "assets/thumbnail.jpg") -> str:
    """
    Generates a clickbait YouTube thumbnail.
    Asks Gemini for a prompt and a short 3-word overlay text, downloads the image, and overlays the text.
    """
    print(f"[*] Thumbnail Agent: Generating custom thumbnail for '{seo_title}'...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    prompt_text = "A hyper-realistic cinematic deep space anomaly, bright glowing colors, highly detailed, 8k"
    overlay_text = "SHOCKING TRUTH"
    
    if api_key and api_key != "your_gemini_api_key_here":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        sys_prompt = f"""
        We need a viral YouTube thumbnail for a video titled: "{seo_title}" (Topic: {topic}).
        Provide JSON with two keys:
        1. "image_prompt": A highly detailed prompt for an AI image generator (Pollinations/Flux). Make it cinematic, extreme contrast, ultra-vibrant colors, and very mysterious to maximize click-through rate. NO TEXT IN PROMPT.
        2. "overlay_text": Extract the most shocking or compelling 3 to 4 words directly from the SEO Title to stamp on the thumbnail. It MUST be highly relevant to the title (e.g. if title is "The Truth About Black Holes", text could be "TRUTH ABOUT BLACK HOLES" or "NASA'S DARK SECRET").
        
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
            overlay_text = data.get("overlay_text", overlay_text).upper()
        except Exception as e:
            print(f"[-] Thumbnail Agent (Gemini Error): {e}. Using fallback.")
            
    # Download background image
    encoded_prompt = urllib.parse.quote(prompt_text)
    seed = random.randint(1000, 9999)
    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={seed}"
    
    try:
        r = requests.get(img_url, timeout=30)
        with open(output_path, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print(f"[-] Thumbnail Agent failed to download image: {e}")
        return None
        
    # Overlay Text using Pillow
    try:
        img = Image.open(output_path).convert("RGBA")
        draw = ImageDraw.Draw(img)
        
        # Try to use a large bold font
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 100)
        except:
            font = ImageFont.load_default()
            
        width, height = img.size
        # Wrap the clickbait text
        wrapped_text = textwrap.fill(overlay_text, width=15)
        
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align="center")
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        x = (width - text_w) / 2
        y = (height - text_h) / 2
        
        # Draw stroke/shadow (thick black outline)
        stroke_width = 5
        for adj_x in range(-stroke_width, stroke_width+1):
            for adj_y in range(-stroke_width, stroke_width+1):
                draw.multiline_text((x+adj_x, y+adj_y), wrapped_text, font=font, fill="black", align="center")
                
        # Draw main text in yellow
        draw.multiline_text((x, y), wrapped_text, font=font, fill="#FFE800", align="center")
        
        img = img.convert("RGB")
        img.save(output_path, quality=95)
        print(f"[+] Thumbnail saved successfully: {output_path}")
        return output_path
    except Exception as e:
        print(f"[-] Thumbnail Agent failed to overlay text: {e}")
        return output_path
