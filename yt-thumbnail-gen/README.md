# YouTube Thumbnail Generator (Chatbot-style, Local)

A chatbot-style web app: paste your video idea → answer a few quick style
questions → confirm the AI-refined prompt → get a generated YouTube
thumbnail (with optional bold title text burned in).

## Architecture (important — read this first)

Ollama **only runs text LLMs**, it does not do image generation. So this
project splits the work:

| Stage | Tool | Model |
|---|---|---|
| Ask clarifying questions | Frontend JS (no model needed) | — |
| Turn your idea + answers into a detailed image prompt | **Ollama**, local | **IBM Granite** (`granite3.1:8b`) |
| Generate the actual thumbnail image | **Hugging Face `diffusers`**, local | `stabilityai/sdxl-turbo` |
| Burn in title text | Pillow | — |

If you were hoping to run the *image* model through Ollama too — that's
not currently possible for any provider (Ollama's model format doesn't
support diffusion models). IBM also doesn't publish an open-weights local
text-to-image model comparable to SDXL, so Stable Diffusion is the
practical local choice here.

---

## 1. Install & run Ollama (for prompt refinement)

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: download installer from https://ollama.com/download
```

Start the server (if it isn't already running as a service):
```bash
ollama serve
```

### Pull IBM Granite
```bash
ollama pull granite3.1:8b
```
This is IBM's open-weight Granite 3.1 8B model, published directly to the
Ollama library (IBM maintains it there — no separate IBM account or key
needed). If your machine is low on RAM/VRAM, use the smaller
`granite3.1:2b` instead:
```bash
ollama pull granite3.1:2b
```
and change `OLLAMA_MODEL` in `modules/ollama_client.py` (or set the env
var, see below) to `granite3.1:2b`.

Quick test:
```bash
ollama run granite3.1:8b "Say hello in one sentence."
```

### Alternative: use IBM models via Hugging Face instead of Ollama
IBM also publishes Granite on Hugging Face (e.g.
`ibm-granite/granite-3.1-8b-instruct`). You'd only do this if you want to
run it through `transformers` directly instead of Ollama — for this
project, sticking with Ollama is simpler (no GPU code to manage for the
text model), so the code here uses the Ollama route by default.

---

## 2. Set up the image generation model (Hugging Face)

```bash
pip install -U huggingface_hub
huggingface-cli login
```
Paste a Hugging Face access token (create one free at
https://huggingface.co/settings/tokens — "Read" access is enough).

The first time you generate an image, `diffusers` will auto-download
`stabilityai/sdxl-turbo` (~7GB) and cache it locally
(`~/.cache/huggingface`). No further setup needed after that.

**If you don't have a GPU:** it'll still work on CPU, just slower
(a couple of minutes per image instead of seconds). If that's too slow,
swap `SD_MODEL_ID` to `"runwayml/stable-diffusion-v1-5"` and bump
`num_inference_steps` to ~25 in `modules/image_generator.py`.

---

## 3. Install Python dependencies

```bash
cd yt-thumbnail-gen
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> Note: `torch` install size/command varies by OS/GPU. If the plain
> `pip install torch` from requirements.txt doesn't give you GPU support,
> get the right command for your CUDA version from
> https://pytorch.org/get-started/locally/ and re-install torch with that.

---

## 4. Run the app

Make sure Ollama is running (`ollama serve`, or it's already running as a
background service), then:

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 5. How the conversation flows

1. You paste your video idea/topic as free text.
2. Bot asks, one at a time (with clickable quick-reply buttons):
   - Theme/category (Tech, Gaming, Vlog, Finance, Education, Motivational, Other)
   - Visual style (Bold & Bright, Minimal, Dark & Dramatic, Cartoon, Realistic)
   - Mood (Exciting, Calm, Serious, Funny, Shocking)
   - Include a human face? (Yes/No)
   - Color scheme (free text or skip)
   - Overlay title text (free text or none)
3. Backend sends everything to Granite (via Ollama) → gets back one
   detailed image-generation prompt → shows it to you in chat.
4. You type `confirm` to proceed as-is, or type an edited prompt to use
   instead.
5. Backend generates the image with SDXL-Turbo, overlays your title text
   (if provided), and posts the final PNG in the chat.

---

## Project structure

```
yt-thumbnail-gen/
├── app.py                     # Flask routes
├── requirements.txt
├── modules/
│   ├── ollama_client.py       # Prompt refinement via IBM Granite (Ollama)
│   ├── image_generator.py     # Stable Diffusion (diffusers) image gen
│   └── text_overlay.py        # Pillow-based bold title text overlay
├── templates/index.html       # Chat UI shell
├── static/style.css           # Chat bubble styling
├── static/script.js           # Conversation state machine + fetch calls
└── outputs/                   # Generated thumbnails land here
```

## Customizing

- **Change the text model:** set env var `OLLAMA_MODEL` before running,
  e.g. `export OLLAMA_MODEL=llama3.2` (any Ollama-pulled model works).
- **Change the image model:** set env var `SD_MODEL_ID`, e.g.
  `export SD_MODEL_ID=stabilityai/stable-diffusion-xl-base-1.0` for
  higher quality (slower) output.
- **Change clarifying questions:** edit the `QUESTIONS` object in
  `static/script.js`.
