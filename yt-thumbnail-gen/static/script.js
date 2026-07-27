const chatWindow = document.getElementById("chat-window");
const quickReplies = document.getElementById("quick-replies");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// Conversation state machine
const STATE = {
  AWAITING_IDEA: "AWAITING_IDEA",
  Q_THEME: "Q_THEME",
  Q_STYLE: "Q_STYLE",
  Q_MOOD: "Q_MOOD",
  Q_FACE: "Q_FACE",
  Q_COLOR: "Q_COLOR",
  Q_OVERLAY: "Q_OVERLAY",
  AWAITING_CONFIRM: "AWAITING_CONFIRM",
  DONE: "DONE"
};

let state = STATE.AWAITING_IDEA;
let answers = {};
let rawText = "";
let refinedPrompt = "";

const QUESTIONS = {
  [STATE.Q_THEME]: {
    text: "Got it! What category/theme is this thumbnail for?",
    options: ["Tech", "Gaming", "Vlog", "Finance", "Education", "Motivational", "Other"],
    key: "theme",
    next: STATE.Q_STYLE
  },
  [STATE.Q_STYLE]: {
    text: "What visual style do you want?",
    options: ["Bold & Bright", "Minimal", "Dark & Dramatic", "Cartoon/Illustrated", "Realistic Photo"],
    key: "style",
    next: STATE.Q_MOOD
  },
  [STATE.Q_MOOD]: {
    text: "What mood should it convey?",
    options: ["Exciting", "Calm", "Serious", "Funny", "Shocking/Surprised"],
    key: "mood",
    next: STATE.Q_FACE
  },
  [STATE.Q_FACE]: {
    text: "Should the thumbnail include a human face/expression?",
    options: ["Yes", "No"],
    key: "include_face",
    next: STATE.Q_COLOR
  },
  [STATE.Q_COLOR]: {
    text: "Any color scheme preference? (type freely, e.g. 'red and black, high contrast', or click Skip)",
    options: ["Skip (let AI choose)"],
    key: "color_scheme",
    next: STATE.Q_OVERLAY,
    freeText: true
  },
  [STATE.Q_OVERLAY]: {
    text: "Finally, what short title text (if any) should appear ON the thumbnail? Type it, or click None.",
    options: ["None"],
    key: "overlay_text",
    next: STATE.AWAITING_CONFIRM,
    freeText: true
  }
};

function addMessage(text, sender = "bot") {
  const div = document.createElement("div");
  div.className = `msg ${sender}`;
  div.innerText = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
}

function addImageMessage(url) {
  const div = document.createElement("div");
  div.className = "msg bot";
  const img = document.createElement("img");
  img.src = url;
  div.appendChild(img);
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function showQuickReplies(options) {
  quickReplies.innerHTML = "";
  options.forEach(opt => {
    const btn = document.createElement("button");
    btn.innerText = opt;
    btn.onclick = () => handleQuickReply(opt);
    quickReplies.appendChild(btn);
  });
}

function clearQuickReplies() {
  quickReplies.innerHTML = "";
}

function askCurrentQuestion() {
  const q = QUESTIONS[state];
  addMessage(q.text, "bot");
  showQuickReplies(q.options);
}

function handleQuickReply(value) {
  addMessage(value, "user");
  processAnswer(value);
}

function processAnswer(value) {
  const q = QUESTIONS[state];
  if (q) {
    if (value.startsWith("Skip")) value = "no preference, use best judgement";
    answers[q.key] = value;
    clearQuickReplies();
    state = q.next;
    advance();
  } else if (state === STATE.AWAITING_CONFIRM) {
    handleConfirmAnswer(value);
  }
}

function advance() {
  if (state === STATE.AWAITING_CONFIRM) {
    requestRefinedPrompt();
  } else {
    askCurrentQuestion();
  }
}

async function requestRefinedPrompt() {
  addMessage("Thinking of the perfect prompt for your thumbnail...", "bot").classList.add("spinner");
  try {
    const res = await fetch("/api/refine", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_text: rawText, answers })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    refinedPrompt = data.refined_prompt;
    addMessage("Here's the detailed prompt I'll use to generate your thumbnail:\n\n" + refinedPrompt, "bot");
    addMessage("Type 'confirm' to generate, or type an edited version of the prompt to use instead.", "bot");
  } catch (err) {
    addMessage("Error: " + err.message, "bot");
  }
}

function handleConfirmAnswer(value) {
  if (value.trim().toLowerCase() !== "confirm") {
    refinedPrompt = value; // user edited the prompt
  }
  generateThumbnail();
}

async function generateThumbnail() {
  addMessage("Generating your thumbnail now — this can take a bit on CPU...", "bot").classList.add("spinner");
  state = STATE.DONE;
  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ final_prompt: refinedPrompt, overlay_text: answers.overlay_text || "" })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    addImageMessage(data.image_url);
    addMessage("Done! Paste a new idea any time to make another thumbnail.", "bot");
    state = STATE.AWAITING_IDEA;
    rawText = "";
    answers = {};
  } catch (err) {
    addMessage("Error: " + err.message, "bot");
  }
}

function handleFreeTextSubmit() {
  const value = userInput.value.trim();
  if (!value) return;
  userInput.value = "";

  if (state === STATE.AWAITING_IDEA) {
    rawText = value;
    addMessage(value, "user");
    state = STATE.Q_THEME;
    advance();
  } else if (QUESTIONS[state]) {
    addMessage(value, "user");
    processAnswer(value);
  } else if (state === STATE.AWAITING_CONFIRM) {
    addMessage(value, "user");
    processAnswer(value);
  }
}

sendBtn.onclick = handleFreeTextSubmit;
userInput.addEventListener("keydown", e => {
  if (e.key === "Enter") handleFreeTextSubmit();
});

// initial greeting
addMessage("Hi! Paste your video idea/topic/description and I'll help you build a YouTube thumbnail for it.", "bot");
