import os
import sys
from PIL import Image
from google import genai
from google.genai import types
from huggingface_hub import InferenceClient

# --- Environment Setup ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ Warning: 'python-dotenv' is not installed.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

if not GEMINI_API_KEY or not HF_TOKEN:
    print("❌ ERROR: Please ensure GEMINI_API_KEY and HF_TOKEN are set in your .env file.")
    sys.exit(1)

# Initialize Clients
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
hf_client = InferenceClient(token=HF_TOKEN)

TEXT_MODEL = "gemini-2.5-flash"
HF_IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"


# --- Functions ---

def generate_enhanced_prompt(user_input: str) -> str:
    """Uses Gemini to expand the input prompt."""
    system_instruction = (
        "You are an expert AI image prompt engineer. Transform the user request "
        "into a highly detailed, visually descriptive prompt suitable for a text-to-image model. "
        "Include details on style, lighting, camera angle, texture, and composition. "
        "Return ONLY the enhanced prompt string without commentary or quote marks."
    )

    response = gemini_client.models.generate_content(
        model=TEXT_MODEL,
        contents=f"User idea: '{user_input}'. Expand this into a descriptive visual prompt.",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
        )
    )

    return response.text.strip().replace('"', '').replace("'", '')


def create_image(prompt: str, output_filename: str = "generated_image.png"):
    """Generates and saves the image via Hugging Face."""
    image = hf_client.text_to_image(
        prompt=prompt,
        model=HF_IMAGE_MODEL
    )
    image.save(output_filename)
    return os.path.abspath(output_filename)


# --- Main Execution Flow ---
if __name__ == "__main__":
    # Step 1: Ask prompt
    user_prompt = input("✍️ Step 1: Enter your prompt idea:\n> ")

    if not user_prompt.strip():
        print("Prompt cannot be empty. Exiting.")
        sys.exit(0)

    print("\nEnhancing prompt with Gemini...")
    
    # Step 2: Show enhanced prompt in terminal
    enhanced_prompt = generate_enhanced_prompt(user_prompt)
    print("\n✨ Step 2: Enhanced Prompt:")
    print(f"--------------------------------------------------")
    print(f"{enhanced_prompt}")
    print(f"--------------------------------------------------\n")

    # Step 3: Generate and display result message
    print("🎨 Step 3: Generating image using Hugging Face...")
    try:
        saved_location = create_image(enhanced_prompt)
        print(f"\n✅ Image Generated Successfully!")
        print(f"📁 Saved at: {saved_location}")
    except Exception as e:
        print(f"\n❌ Failed to generate image: {e}")