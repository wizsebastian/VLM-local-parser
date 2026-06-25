const dropZone = document.getElementById("drop-zone");
const resultBox = document.getElementById("result-box");
const resultEl = document.getElementById("result");
const statusEl = document.getElementById("status");
const copyBtn = document.getElementById("copy-btn");

const DEFAULT_INNER = dropZone.innerHTML;

// Paste from clipboard (Cmd+V)
document.addEventListener("paste", e => {
  for (const item of e.clipboardData.items) {
    if (item.type.startsWith("image/")) {
      processFile(item.getAsFile());
      break;
    }
  }
});

// Drag & drop
dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("active"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("active"));
dropZone.addEventListener("drop", e => {
  e.preventDefault();
  dropZone.classList.remove("active");
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith("image/")) processFile(file);
});

// Click to pick a file
dropZone.addEventListener("click", () => {
  if (dropZone.classList.contains("has-image")) return;
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "image/*";
  input.onchange = e => processFile(e.target.files[0]);
  input.click();
});

function processFile(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    const b64 = e.target.result;
    showPreview(b64);
    extractText(b64);
  };
  reader.readAsDataURL(file);
}

function showPreview(b64) {
  dropZone.classList.add("has-image");
  dropZone.innerHTML = `<img src="${b64}" alt="preview"><div class="scan-line"></div>`;
}

function extractText(b64) {
  setStatus("Extracting text…", "loading");
  dropZone.classList.add("processing");
  resultBox.classList.remove("success");
  resultEl.value = "";
  copyBtn.disabled = true;

  fetch("/parse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: b64 })
  })
    .then(r => r.json().then(data => ({ ok: r.ok, data })))
    .then(({ ok, data }) => {
      dropZone.classList.remove("processing");
      if (!ok || data.error) {
        setStatus(data.error || "Extraction failed", "error");
        return;
      }
      resultEl.value = data.text || "";
      copyBtn.disabled = false;
      resultBox.classList.add("success");
      setStatus("Done", "done");
    })
    .catch(() => {
      dropZone.classList.remove("processing");
      setStatus("Error connecting to server", "error");
    });
}

function copyText() {
  if (!resultEl.value) return;
  navigator.clipboard.writeText(resultEl.value);
  const label = copyBtn.lastChild;
  const prev = label.textContent;
  label.textContent = " Copied!";
  setTimeout(() => { label.textContent = prev; }, 1500);
}

function reset() {
  dropZone.classList.remove("has-image", "processing", "active");
  dropZone.innerHTML = DEFAULT_INNER;
  resultBox.classList.remove("success");
  resultEl.value = "";
  copyBtn.disabled = true;
  setStatus("", "");
}

function setStatus(msg, cls) {
  statusEl.textContent = msg;
  statusEl.className = "font-mono text-xs mt-3 min-h-[1rem] " + (cls || "text-ink-dim");
}
