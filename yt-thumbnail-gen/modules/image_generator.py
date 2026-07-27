import os
import torch
from PIL import Image

# Load environment variables from .env if present
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

FLUX_MODE = os.environ.get("FLUX_MODE", "cloud").lower().strip()
HF_TOKEN = os.environ.get("HF_TOKEN", os.environ.get("HF_API_KEY", "")).strip()

print(f"--- IMAGE GENERATOR INITIALIZED ---")
print(f"FLUX Mode: {FLUX_MODE.upper()}")
if FLUX_MODE == "cloud":
    if HF_TOKEN:
        print("Hugging Face API Token: Found (using authenticated requests)")
    else:
        print("Hugging Face API Token: NOT FOUND (using public/unauthenticated requests; may experience rate limiting)")
print(f"-----------------------------------")

_pipe = None  # Lazy-loaded local pipeline singleton

def _get_local_pipe():
    global _pipe
    if _pipe is None:
        from diffusers import FluxPipeline
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.bfloat16 if device == "cuda" else torch.float32

        print(f"Loading FLUX.1-schnell locally on {device} ({dtype})... This may download ~24GB of weights.")
        _pipe = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-schnell",
            torch_dtype=dtype
        )
        if device == "cuda":
            _pipe.enable_model_cpu_offload()
        else:
            _pipe = _pipe.to("cpu")
    return _pipe

def generate_image(prompt: str, width: int = 1280, height: int = 720) -> Image.Image:
    """
    Generates a 16:9 YouTube-thumbnail-sized image from the given prompt.
    """
    if FLUX_MODE == "local":
        print(f"Generating image locally with prompt: {prompt}")
        pipe = _get_local_pipe()
        image = pipe(
            prompt=prompt,
            width=width,
            height=height,
            guidance_scale=0.0,
            num_inference_steps=4,
            max_sequence_length=256
        ).images[0]
        return image
    else:
        # Cloud mode using Hugging Face Serverless API
        print(f"Generating image via HF Serverless API with prompt: {prompt}")
        from huggingface_hub import InferenceClient
        
        client = InferenceClient(
            model="black-forest-labs/FLUX.1-schnell",
            token=HF_TOKEN if HF_TOKEN else None
        )
        
        # InferenceClient.text_to_image returns a PIL Image directly
        image = client.text_to_image(
            prompt=prompt,
            width=width,
            height=height,
            guidance_scale=0.0,
            num_inference_steps=4
        )
        return image
