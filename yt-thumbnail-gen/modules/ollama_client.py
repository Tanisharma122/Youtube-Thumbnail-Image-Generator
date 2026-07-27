"""
Talks to a locally running Ollama server to turn the user's raw idea +
their answers to the clarifying questions into one polished, detailed
image-generation prompt.

Default model: IBM Granite (text-only), pulled via:
    ollama pull granite3.1:8b

If you'd rather use a different local model (e.g. llama3.2, mistral),
just change OLLAMA_MODEL below — no other code changes needed.
"""
import os
import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

SYSTEM_INSTRUCTIONS = """You are a professional YouTube thumbnail art director.
You take a creator's raw video idea plus their style preferences and turn it
into ONE detailed, vivid, production-ready image-generation prompt for a
diffusion model (like Stable Diffusion).

Rules:
- Output ONLY the final image prompt. No preamble, no explanation, no markdown.
- Describe: subject/focal point, composition, facial expression (if a person
  is included), lighting, color palette, background, art style, and the kind
  of "click-bait energy" typical of high-CTR YouTube thumbnails (high
  contrast, bold framing, rule-of-thirds, dramatic lighting).
- Do NOT put any literal text/words to render inside the image description —
  text overlay is handled separately.
- Keep it to 2-4 dense sentences, comma-separated descriptors are fine.
"""


def refine_prompt(raw_text: str, answers: dict) -> str:
    theme = answers.get("theme", "General")
    style = answers.get("style", "Bold & Bright")
    mood = answers.get("mood", "Exciting")
    include_face = answers.get("include_face", "No")
    color_scheme = answers.get("color_scheme", "high contrast, vivid colors")

    user_message = f"""Video idea from creator: "{raw_text}"

Preferences:
- Thumbnail theme/category: {theme}
- Visual style: {style}
- Mood: {mood}
- Include a human face/expression: {include_face}
- Color scheme: {color_scheme}

Write the final image-generation prompt now."""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{SYSTEM_INSTRUCTIONS}\n\n{user_message}",
        "stream": False,
        "options": {"temperature": 0.7}
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        return result.get("response", "").strip()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Could not reach Ollama at " + OLLAMA_URL +
            ". Make sure Ollama is installed and running (`ollama serve`), "
            f"and that you've pulled the model with `ollama pull {OLLAMA_MODEL}`."
        )
