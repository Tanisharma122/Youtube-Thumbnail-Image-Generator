import os
import sys
from PIL import Image
from google import genai
from google.genai import types
from huggingface_hub import InferenceClient

# ==============================================================================
# 1. ENVIRONMENT & API SETUP
# ==============================================================================
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

# Initialize API Clients
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
hf_client = InferenceClient(token=HF_TOKEN)

TEXT_MODEL = "gemini-2.5-flash"
HF_TEXT_TO_IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"
HF_IMAGE_TO_IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"


# ==============================================================================
# 2. UNIVERSAL MENU OPTIONS (TECH, VLOG, BEAUTY, FINANCE)
# ==============================================================================
PLATFORM_PRESETS = {
    "1": {"name": "YouTube Video Thumbnail", "width": 1280, "height": 720, "ratio": "16:9"},
    "2": {"name": "YouTube Shorts / Instagram Reels / TikTok", "width": 1080, "height": 1920, "ratio": "9:16"},
    "3": {"name": "Instagram / LinkedIn Square Post", "width": 1080, "height": 1080, "ratio": "1:1"},
    "4": {"name": "Twitter / LinkedIn Banner", "width": 1200, "height": 675, "ratio": "16:9"}
}

CATEGORY_OPTIONS = [
    "Tech & AI", 
    "Beauty, Fashion & Skincare", 
    "Design & Art", 
    "Vlog & Lifestyle", 
    "Gaming", 
    "Finance & Business", 
    "Motivational", 
    "Other"
]

STYLE_OPTIONS = [
    "Minimalist & Aesthetic Premium", 
    "Dark & Dramatic (Cinematic)", 
    "Bold, Bright & High-Contrast", 
    "Iman Gadzhi Luxury Style (Clean Dark Studio)",
    "Realistic Photo / Editorial", 
    "Cartoon / Illustrated", 
    "Other"
]

BACKGROUND_OPTIONS = [
    "Aesthetic Pastel & Soft Sunlight (Great for Beauty/Design)",
    "Clean Blurred Modern Studio / Bookshelf",
    "Dark Minimalist Gradient with Soft Accent Light",
    "Sleek High-Tech Desk Setup",
    "Abstract Glowing Grid / Matrix",
    "Pure Solid Color Background (Pop Art style)",
    "Other"
]

GRAPHIC_ELEMENTS = [
    "Split Screen Comparison (Before vs After)",
    "Floating Sparkles / Glowing Aura (Beauty/Magic)",
    "Highlighted Text Box Banner (Yellow/Cyan Background)",
    "Red Curved Arrow pointing to Subject",
    "Glowing App/Product Icon floating on side",
    "Clean & Minimal (No extra graphics)",
    "Other"
]

MOOD_OPTIONS = [
    "Aesthetic, Calm & Luxurious",
    "Shocking / Surprised", 
    "Excited / High-Energy", 
    "Intense & Serious", 
    "Urgent / FOMO", 
    "Other"
]

FACE_EXPRESSION_OPTIONS = [
    "Confident Smile with direct eye contact", 
    "Applying product / Creative focus pose",
    "Jaw-dropped Open Mouth Shock", 
    "Pointing at floating object/text", 
    "No Face (Pure Object/UI focus)", 
    "Other"
]


# ==============================================================================
# 3. INTERACTIVE CHOICE SELECTOR UTILITIES
# ==============================================================================

def select_from_options(prompt_title: str, options: list) -> str:
    """Displays a numbered list of options and supports custom entry."""
    print(f"\n❓ {prompt_title}")
    for idx, opt in enumerate(options, 1):
        print(f"   [{idx}] {opt}")
    
    choice = input(f"Select option (1-{len(options)}) [Default: 1]:\n> ").strip()
    
    if not choice:
        return options[0]
    
    if choice.isdigit() and 1 <= int(choice) <= len(options):
        selected = options[int(choice) - 1]
        if selected == "Other":
            custom_val = input("👉 Enter your custom choice:\n> ").strip()
            return custom_val if custom_val else "Custom Preference"
        return selected
    else:
        return choice


def ask_text_question(question_text: str, default_val: str = "") -> str:
    """Standard text input collector."""
    if default_val:
        user_input = input(f"\n✍️ {question_text} [Default: {default_val}]:\n> ").strip()
        return user_input if user_input else default_val
    else:
        user_input = input(f"\n✍️ {question_text}:\n> ").strip()
        return user_input


# ==============================================================================
# 4. GEMINI PROMPT SYNTHESIS 
# ==============================================================================

def get_genai_creative_boost(title: str, description: str, category: str) -> str:
    """Asks Gemini for a high-CTR visual prop idea based on niche."""
    prompt = (
        f"Category: {category}\nTitle: {title}\nDescription: {description}\n"
        "Suggest ONE viral visual prop or graphic hook for a thumbnail "
        "(e.g., 'A glowing skin-care bottle', 'A 3D $0 to $1M arrow', 'A floating UI dashboard'). "
        "Return only 1 concise sentence."
    )
    response = gemini_client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt
    )
    return response.text.strip()


def generate_high_ctr_prompt(video_data: dict) -> str:
    """
    Synthesizes user selections into a high-production-value YouTube thumbnail prompt.
    Adapts perfectly whether the user wants a hardcore Tech bro thumbnail or a soft Beauty vlog thumbnail.
    """
    system_instruction = (
        "You are an elite YouTube Thumbnail Designer and Prompt Engineer.\n"
        "Your goal is to write a highly detailed image prompt that generates a realistic, high-CTR thumbnail.\n\n"
        "STRICT DESIGN RULES:\n"
        "1. SUBJECT: Ensure the human subject or core object matches the requested mood and expression perfectly.\n"
        "2. BACKGROUND: Render the background strictly according to the user's setup preference, utilizing cinematic depth of field (bokeh) to separate the subject from the background.\n"
        "3. GRAPHICS & TEXT OVERLAY: Seamlessly integrate the requested graphic elements (split screens, arrows, sparkles) and visualize the text overlay as bold, legible typography.\n"
        "4. LIGHTING: Adapt lighting to the theme—soft natural light for beauty/vlogs, and dramatic high-contrast studio lighting for tech/finance.\n"
        "Output ONLY the final descriptive visual prompt string. Do not use quotes."
    )

    prompt = (
        f"Category/Niche: {video_data['category']}\n"
        f"Video Title: {video_data['title']}\n"
        f"Video Concept: {video_data['description']}\n"
        f"Target Aspect Ratio: {video_data['ratio']}\n"
        f"Overall Aesthetic: {video_data['style']}\n"
        f"Background Setup: {video_data['background']}\n"
        f"Graphic Elements: {video_data['graphic_element']}\n"
        f"Subject Pose & Emotion: {video_data['expression']} with a {video_data['mood']} mood\n"
        f"Text Overlay Request: '{video_data['text_overlay']}'\n"
        f"GenAI Creative Hook: {video_data['genai_boost']}\n\n"
        "Synthesize these instructions into a single ultra-detailed, photorealistic image generation prompt."
    )

    response = gemini_client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.75,
        )
    )

    return response.text.strip().replace('"', '').replace("'", '')


# ==============================================================================
# 5. IMAGE GENERATION ENGINE
# ==============================================================================

def generate_thumbnail_image(
    prompt: str, 
    width: int, 
    height: int, 
    user_image_path: str = "", 
    output_filename: str = "final_thumbnail.png"
) -> str:
    """Generates the image using Hugging Face API."""
    if user_image_path and os.path.exists(user_image_path):
        print("\n📸 User Image Detected! Blending avatar via Image-to-Image pipeline...")
        with open(user_image_path, "rb") as img_file:
            input_image_bytes = img_file.read()

        image = hf_client.image_to_image(
            image=input_image_bytes,
            prompt=prompt,
            model=HF_IMAGE_TO_IMAGE_MODEL,
            height=height,
            width=width
        )
    else:
        print("\n🎨 Generating pure Text-to-Image thumbnail...")
        image = hf_client.text_to_image(
            prompt=prompt,
            model=HF_TEXT_TO_IMAGE_MODEL,
            height=height,
            width=width
        )

    image.save(output_filename)
    return os.path.abspath(output_filename)


# ==============================================================================
# 6. MAIN EXECUTION WORKFLOW
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🎬 CREATECT AI — ULTIMATE THUMBNAIL STUDIO")
    print("="*70)

    # Step 1: Select Platform
    print("\n📌 Step 1: Select Target Platform & Resolution")
    for key, val in PLATFORM_PRESETS.items():
        print(f"   [{key}] {val['name']} ({val['width']}x{val['height']} | {val['ratio']})")
    
    preset_choice = input("Choose option (1-4) [Default: 1]:\n> ").strip()
    selected_preset = PLATFORM_PRESETS.get(preset_choice, PLATFORM_PRESETS["1"])
    print(f"👉 Selected: {selected_preset['name']} ({selected_preset['width']}x{selected_preset['height']})")

    # Step 2: Core Video Inputs
    print("\n📌 Step 2: Video Details")
    title = ask_text_question("What is your Video Title?")
    if not title:
        print("❌ Video title is required.")
        sys.exit(0)

    description = ask_text_question("Brief video summary / script concept")

    # Step 3: Design Preferences
    print("\n📌 Step 3: Thumbnail Design Preferences")
    category = select_from_options("What category/niche is this for?", CATEGORY_OPTIONS)
    style = select_from_options("Select Overall Aesthetic Style:", STYLE_OPTIONS)
    background = select_from_options("What background setup do you want?", BACKGROUND_OPTIONS)
    graphic_element = select_from_options("What graphical annotations / callouts to include?", GRAPHIC_ELEMENTS)
    mood = select_from_options("What mood should the thumbnail convey?", MOOD_OPTIONS)
    expression = select_from_options("What pose / facial expression for the subject?", FACE_EXPRESSION_OPTIONS)

    text_overlay = ask_text_question(
        "Text Callout Overlay? (e.g., 'BEAUTY RESET', 'AUTOMATE LIFE', '$0 ➔ $1M')", 
        default_val="WATCH THIS"
    )

    # Step 4: Personal Avatar
    print("\n📌 Step 4: Personal Avatar / Face Image (Optional)")
    include_face_choice = select_from_options("Do you want to upload your own photo to place in the thumbnail?", ["No", "Yes"])
    
    user_image_path = ""
    if include_face_choice == "Yes":
        user_image_path = ask_text_question("Enter local image file path (e.g. my_photo.jpg)").strip('"').strip("'")
        if not os.path.exists(user_image_path):
            print("⚠️ Image path not found. Proceeding without custom photo.")
            user_image_path = ""

    # Step 5: Gemini Synthesis
    print("\n" + "-"*70)
    print("🧠 Step 5: Synthesizing Thumbnail Strategy with Gemini...")
    print("-"*70)

    genai_boost = get_genai_creative_boost(title, description, category)
    print(f"💡 GenAI Creative Prop Suggested:\n-> {genai_boost}")

    video_data = {
        "category": category,
        "title": title,
        "description": description,
        "ratio": selected_preset["ratio"],
        "style": style,
        "background": background,
        "graphic_element": graphic_element,
        "mood": mood,
        "expression": expression,
        "text_overlay": text_overlay,
        "genai_boost": genai_boost
    }

    enhanced_prompt = generate_high_ctr_prompt(video_data)

    print("\n✨ Enhanced High-CTR Prompt:")
    print("-" * 60)
    print(enhanced_prompt)
    print("-" * 60)

    # Step 6: Render
    print(f"\n🎨 Step 6: Rendering {selected_preset['name']} ({selected_preset['width']}x{selected_preset['height']})...")
    
    try:
        saved_path = generate_thumbnail_image(
            prompt=enhanced_prompt,
            width=selected_preset["width"],
            height=selected_preset["height"],
            user_image_path=user_image_path,
            output_filename="final_thumbnail.png"
        )
        
        print("\n✅ THUMBNAIL GENERATED SUCCESSFULLY!")
        print(f"📁 Output Resolution: {selected_preset['width']} x {selected_preset['height']} pixels")
        print(f"📁 Saved at: {saved_path}\n")

    except Exception as e:
        print(f"\n❌ Failed to generate thumbnail: {e}")