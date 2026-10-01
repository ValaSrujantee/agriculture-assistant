/**
 * Agriculture Assistant Module for Smart Agriculture Assistant.
 * Connects the UI to the local curated knowledge base Q&A engine with quick prompt chips.
 */

document.addEventListener("DOMContentLoaded", () => {
  setupAssistant();
});

function setupAssistant() {
  const input = document.getElementById("assistantInput");
  const sendBtn = document.getElementById("assistantSendBtn");
  const chips = document.querySelectorAll(".prompt-chips .chip");

  if (!input || !sendBtn) return;

  sendBtn.addEventListener("click", () => handleUserQuestion());
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleUserQuestion();
  });

  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      input.value = chip.textContent.trim();
      handleUserQuestion();
    });
  });
}

async function handleUserQuestion() {
  const input = document.getElementById("assistantInput");
  const messagesBox = document.getElementById("assistantMessages");
  const sendBtn = document.getElementById("assistantSendBtn");

  const question = input.value.trim();
  if (!question) return;

  // Append user bubble
  appendMessage(question, "user");
  input.value = "";
  input.focus();

  // Show typing indicator
  const loadingId = "botLoadingMsg";
  const loadingBubble = document.createElement("div");
  loadingBubble.className = "message-bubble message-bot";
  loadingBubble.id = loadingId;
  loadingBubble.innerHTML = `<em>Agri-Assistant is searching knowledge base...</em>`;
  messagesBox.appendChild(loadingBubble);
  messagesBox.scrollTop = messagesBox.scrollHeight;

  try {
    sendBtn.disabled = true;

    const res = await fetch("/api/assistant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });

    const data = await res.json();
    document.getElementById(loadingId)?.remove();

    if (res.ok && data.status === "success") {
      appendMessage(data.answer, "bot");
    } else {
      appendMessage("Sorry, I could not retrieve information for that query. Please try asking about crops, rainfall, soil, or season.", "bot");
    }
  } catch (err) {
    document.getElementById(loadingId)?.remove();
    appendMessage("Connection error. Please ensure the backend is running.", "bot");
  } finally {
    sendBtn.disabled = false;
  }
}

function appendMessage(text, sender) {
  const messagesBox = document.getElementById("assistantMessages");
  if (!messagesBox) return;

  const bubble = document.createElement("div");
  bubble.className = `message-bubble message-${sender}`;
  bubble.innerHTML = formatSimpleMarkdown(text);

  messagesBox.appendChild(bubble);
  messagesBox.scrollTop = messagesBox.scrollHeight;
}
