const API_BASE = "http://localhost:8081";

const els = {
  form: document.getElementById("meme-form"),
  formStatus: document.getElementById("form-status"),
  grid: document.getElementById("meme-grid"),
  refresh: document.getElementById("refresh-btn"),
  dialog: document.getElementById("edit-dialog"),
  editForm: document.getElementById("edit-form"),
  editUrl: document.getElementById("edit_url"),
  editCaption: document.getElementById("edit_caption"),
  editStatus: document.getElementById("edit-status"),
  editClose: document.getElementById("edit-close"),
  editCancel: document.getElementById("edit-cancel"),
  editSubmit: document.getElementById("edit-submit"),
};

let editingId = null;

function setStatus(el, message, type = "") {
  el.textContent = message;
  el.classList.remove("is-error", "is-success");
  if (type) el.classList.add(`is-${type}`);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function memeCard(meme, index) {
  const caption = escapeHtml(meme.caption);
  const name = escapeHtml(meme.name);
  const url = escapeHtml(meme.url);
  const id = Number(meme.id);

  return `
    <article class="meme-card" style="animation-delay: ${Math.min(index, 12) * 40}ms">
      <img src="${url}" alt="${caption}" loading="lazy"
        onerror="this.onerror=null;this.src='images/invalid_url.jpg';this.alt='Image unavailable'">
      <div class="card-body">
        <p class="caption">${caption}</p>
        <p class="author">Posted by <span>${name}</span></p>
        <button type="button" class="btn btn-ghost btn-sm" data-edit="${id}">Edit</button>
      </div>
    </article>
  `;
}

async function fetchMemes() {
  els.grid.setAttribute("aria-busy", "true");
  els.grid.innerHTML = `<p class="empty-state">Loading memes…</p>`;

  try {
    const res = await fetch(`${API_BASE}/memes`);
    if (!res.ok) throw new Error(`Server responded with ${res.status}`);

    const data = await res.json();
    const memes = Array.isArray(data) ? data.slice().reverse() : [];

    if (!memes.length) {
      els.grid.innerHTML = `<p class="empty-state">No memes yet — be the first to post.</p>`;
      return;
    }

    els.grid.innerHTML = memes.map(memeCard).join("");
  } catch (err) {
    els.grid.innerHTML = `
      <p class="empty-state">
        Couldn’t reach the API. Make sure the backend is running on port 8081, then refresh.
      </p>`;
    console.error(err);
  } finally {
    els.grid.setAttribute("aria-busy", "false");
  }
}

async function createMeme(event) {
  event.preventDefault();
  setStatus(els.formStatus, "");

  const payload = {
    name: document.getElementById("owner_name").value.trim(),
    url: document.getElementById("meme_url").value.trim(),
    caption: document.getElementById("caption").value.trim(),
  };

  if (!payload.name || !payload.url || !payload.caption) {
    setStatus(els.formStatus, "Please fill in all fields.", "error");
    return;
  }

  const submitBtn = els.form.querySelector('[type="submit"]');
  submitBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/memes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (res.status === 409) {
      setStatus(els.formStatus, "That exact meme already exists.", "error");
      return;
    }
    if (!res.ok) {
      setStatus(els.formStatus, "Couldn’t post meme. Check the URL and try again.", "error");
      return;
    }

    els.form.reset();
    setStatus(els.formStatus, "Meme posted!", "success");
    await fetchMemes();
  } catch (err) {
    setStatus(els.formStatus, "Network error — is the backend running?", "error");
    console.error(err);
  } finally {
    submitBtn.disabled = false;
  }
}

function openEdit(id) {
  editingId = id;
  els.editForm.reset();
  setStatus(els.editStatus, "");
  els.dialog.showModal();
}

function closeEdit() {
  editingId = null;
  els.dialog.close();
}

async function saveEdit(event) {
  event.preventDefault();
  if (editingId == null) return;

  const url = els.editUrl.value.trim();
  const caption = els.editCaption.value.trim();

  if (!url && !caption) {
    setStatus(els.editStatus, "Fill in at least one field.", "error");
    return;
  }

  const body = {};
  if (url) body.url = url;
  if (caption) body.caption = caption;

  els.editSubmit.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/memes/${editingId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (res.status === 404) {
      setStatus(els.editStatus, "Meme not found.", "error");
      return;
    }
    if (!res.ok) {
      setStatus(els.editStatus, "Update failed. Try again.", "error");
      return;
    }

    closeEdit();
    await fetchMemes();
  } catch (err) {
    setStatus(els.editStatus, "Network error — is the backend running?", "error");
    console.error(err);
  } finally {
    els.editSubmit.disabled = false;
  }
}

els.form.addEventListener("submit", createMeme);
els.refresh.addEventListener("click", fetchMemes);
els.editForm.addEventListener("submit", saveEdit);
els.editClose.addEventListener("click", closeEdit);
els.editCancel.addEventListener("click", closeEdit);

els.grid.addEventListener("click", (event) => {
  const btn = event.target.closest("[data-edit]");
  if (!btn) return;
  openEdit(Number(btn.dataset.edit));
});

els.dialog.addEventListener("click", (event) => {
  if (event.target === els.dialog) closeEdit();
});

fetchMemes();
