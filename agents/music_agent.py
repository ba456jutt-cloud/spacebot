import os

def generate_music(prompt="cinematic dark space sci-fi background music, deep bass, ambient synth, 100 bpm", duration=30, output_path="assets/bgm.wav"):
    """
    Generates AI background music using Meta's MusicGen.
    Skips if audiocraft is not installed (e.g., running locally without a GPU).
    """
    print("[*] Music Agent: Attempting to generate AI Background Music...")
    
    try:
        import torch
        import scipy
        from audiocraft.models import MusicGen
    except ImportError:
        print("  [-] Music Agent skipped: 'audiocraft' is not installed. (This is normal for local runs without a Cloud GPU).")
        return None
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if os.path.exists(output_path):
        print(f"  [-] BGM already exists at {output_path}, skipping generation...")
        return output_path
        
    print(f"  [+] Loading MusicGen model... (This may take a moment)")
    try:
        model = MusicGen.get_pretrained('facebook/musicgen-small')
        model.set_generation_params(duration=duration)
        
        print(f"  [+] Generating {duration} seconds of AI music...")
        print(f"      Prompt: '{prompt}'")
        wav = model.generate([prompt])
        wav = wav[0].cpu().numpy()
        
        import scipy.io.wavfile
        scipy.io.wavfile.write(output_path, model.sample_rate, wav)
        print(f"  [+] Music successfully generated and saved to {output_path}!")
        return output_path
    except Exception as e:
        print(f"  [-] Error during Music Generation: {e}")
        return None

if __name__ == "__main__":
    pass
