"""
YouTube Thumbnail Generator — Flask backend
Flow:
  1. User pastes raw text/idea about their video       -> /api/start
  2. User answers quick clarifying questions (theme,     -> handled client-side
     style, mood, colors, face?, overlay text)
  3. Backend combines everything + calls Ollama (IBM     -> /api/refine
     Granite) to produce one polished image-gen prompt
  4. User confirms/edits, backend calls Stable Diffusion -> /api/generate
     (via diffusers) to render the thumbnail, then adds
     bold text overlay with Pillow
"""
import os
import uuid
import traceback
from flask import Flask, request, jsonify, send_from_directory, render_template

from modules.ollama_client import refine_prompt
from modules.image_generator import generate_image
from modules.text_overlay import add_title_text

app = Flask(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/refine", methods=["POST"])
def api_refine():
    """
    Expects JSON:
    {
      "raw_text": "user's original description of the video",
      "answers": {
          "theme": "Tech / Gaming / Vlog / Finance / Education / Motivational / Other",
          "style": "Bold & Bright / Minimal / Dark & Dramatic / Cartoon / Realistic photo",
          "mood": "Exciting / Calm / Serious / Funny / Shocking",
          "include_face": "Yes / No",
          "color_scheme": "free text, e.g. 'red and black, high contrast'",
          "overlay_text": "the short text/title to put on the thumbnail (or 'none')"
      }
    }
    Returns: { "refined_prompt": "...", "overlay_text": "..." }
    """
    try:
        data = request.get_json(force=True)
        raw_text = data.get("raw_text", "").strip()
        answers = data.get("answers", {})

        if not raw_text:
            return jsonify({"error": "raw_text is required"}), 400

        refined_prompt = refine_prompt(raw_text, answers)

        return jsonify({
            "refined_prompt": refined_prompt,
            "overlay_text": answers.get("overlay_text", "")
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """
    Expects JSON:
    { "final_prompt": "confirmed / user-edited prompt", "overlay_text": "optional title text" }
    Returns: { "image_url": "/outputs/<file>.png" }
    """
    try:
        data = request.get_json(force=True)
        final_prompt = data.get("final_prompt", "").strip()
        overlay_text = data.get("overlay_text", "").strip()

        if not final_prompt:
            return jsonify({"error": "final_prompt is required"}), 400

        # 1. Generate base image with Stable Diffusion
        image = generate_image(final_prompt)

        # 2. Optionally burn in bold YouTube-style title text
        if overlay_text and overlay_text.lower() != "none":
            image = add_title_text(image, overlay_text)

        filename = f"thumbnail_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        image.save(filepath)

        return jsonify({"image_url": f"/outputs/{filename}"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
