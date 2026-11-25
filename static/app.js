const promptEl = document.getElementById("prompt");
const generateBtn = document.getElementById("generate-btn");
const outputEl = document.getElementById("output");
const copyBtn = document.getElementById("copy-btn");
const toastEl = document.getElementById("toast");
let currentOutput = "";

function toast(message) {
  toastEl.textContent = message;
  toastEl.classList.add("show");
  setTimeout(() => toastEl.classList.remove("show"), 2600);
}

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  })[char]);
}

function setOutput(text, model = "", time = "") {
  currentOutput = text;
  outputEl.innerHTML = `<div class="generated-text">${escapeHTML(text)}</div>`;
  copyBtn.disabled = false;
  document.getElementById("output-footer").classList.remove("hidden");
  document.getElementById("output-model").textContent = model;
  document.getElementById("output-time").textContent = time;
}

async function checkHealth() {
  const dot = document.getElementById("status-dot");
  const label = document.getElementById("status-text");
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    dot.className = "status-dot " + (response.ok ? "online" : "offline");
    label.textContent = response.ok ? "Model connected" : "Model offline";
    label.title = data.ollama;
  } catch {
    dot.className = "status-dot offline";
    label.textContent = "Server unavailable";
  }
}

async function loadHistory() {
  const list = document.getElementById("history-list");
  try {
    const response = await fetch("/api/history");
    const items = await response.json();
    if (!items.length) {
      list.innerHTML = '<p class="muted">Your generated responses will appear here.</p>';
      return;
    }
    list.innerHTML = items.map(item => `
      <div class="history-item">
        <div class="history-main" data-id="${item.id}">
          <div class="history-prompt">${escapeHTML(item.prompt)}</div>
          <div class="history-date">${new Date(item.created_at).toLocaleString()} · ${escapeHTML(item.model)}</div>
        </div>
        <button class="delete-btn" data-delete="${item.id}" title="Delete generation" aria-label="Delete generation">×</button>
      </div>`).join("");

    list.querySelectorAll(".history-main").forEach(element => {
      element.addEventListener("click", async () => {
        const itemResponse = await fetch("/api/history");
        const allItems = await itemResponse.json();
        const item = allItems.find(entry => String(entry.id) === element.dataset.id);
        if (item) {
          promptEl.value = item.prompt;
          updateCount();
          setOutput(item.output, item.model, new Date(item.created_at).toLocaleString());
          window.scrollTo({ top: 0, behavior: "smooth" });
        }
      });
    });

    list.querySelectorAll("[data-delete]").forEach(button => {
      button.addEventListener("click", async () => {
        const response = await fetch(`/api/history/${button.dataset.delete}`, { method: "DELETE" });
        if (response.ok) {
          toast("Generation deleted.");
          loadHistory();
        } else toast("Could not delete this item.");
      });
    });
  } catch {
    list.innerHTML = '<p class="muted">Could not load generation history.</p>';
  }
}

function updateCount() {
  document.getElementById("char-count").textContent = `${promptEl.value.length} / 5000`;
}
promptEl.addEventListener("input", updateCount);

document.getElementById("temperature").addEventListener("input", event => {
  document.getElementById("temperature-value").textContent = Number(event.target.value).toFixed(1);
});

document.querySelectorAll(".template-btn").forEach(button => {
  button.addEventListener("click", () => {
    promptEl.value = button.dataset.prompt;
    updateCount();
    promptEl.focus();
  });
});

document.getElementById("clear-prompt").addEventListener("click", () => {
  promptEl.value = "";
  updateCount();
  promptEl.focus();
});

generateBtn.addEventListener("click", async () => {
  const prompt = promptEl.value.trim();
  if (!prompt) {
    toast("Enter a prompt first.");
    promptEl.focus();
    return;
  }

  generateBtn.disabled = true;
  generateBtn.innerHTML = '<span>✦</span> Generating...';
  outputEl.innerHTML = '<div class="empty-state"><div class="sparkle">✧</div><h3>Creating your response...</h3><p>The local model is working. This can take a little while on the first run.</p></div>';
  copyBtn.disabled = true;
  document.getElementById("output-footer").classList.add("hidden");

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        temperature: Number(document.getElementById("temperature").value),
        max_tokens: Number(document.getElementById("max-tokens").value)
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Generation failed.");
    setOutput(data.output, data.model, new Date(data.created_at).toLocaleString());
    toast("Your response is ready.");
    loadHistory();
  } catch (error) {
    outputEl.innerHTML = `<div class="empty-state"><div class="sparkle">!</div><h3>Could not generate</h3><p>${escapeHTML(error.message)}</p></div>`;
    toast(error.message);
  } finally {
    generateBtn.disabled = false;
    generateBtn.innerHTML = '<span>✦</span> Generate response <span class="button-arrow">↗</span>';
    checkHealth();
  }
});

copyBtn.addEventListener("click", async () => {
  if (!currentOutput) return;
  try {
    await navigator.clipboard.writeText(currentOutput);
    toast("Copied to clipboard.");
  } catch {
    toast("Clipboard access was blocked by your browser.");
  }
});

document.getElementById("refresh-history").addEventListener("click", loadHistory);

checkHealth();
loadHistory();
