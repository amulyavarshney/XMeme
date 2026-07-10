window.CreatePage = {
  async render(root, ctx) {
    const { currentUser, navigate, setStatus, escapeHtml, editingMemeId } = ctx;
    if (!currentUser) {
      root.innerHTML = `<section class="panel"><h2>Create meme</h2><p>Please <a href="#/login">log in</a> to use the editor.</p></section>`;
      return;
    }

    root.innerHTML = `
      <section class="create-layout advanced">
        <div class="panel editor-controls">
          <div class="stream-header">
            <h2>${editingMemeId ? "Re-edit meme" : "Meme studio"}</h2>
            <div class="form-actions">
              <button type="button" class="btn btn-ghost btn-sm" id="undo-btn">Undo</button>
              <button type="button" class="btn btn-ghost btn-sm" id="redo-btn">Redo</button>
              <button type="button" class="btn btn-ghost btn-sm" id="reset-btn">Reset</button>
            </div>
          </div>
          <p class="muted tip">Drag to move · Shift-drag rotate · Alt-drag or scroll to scale · ⌘/Ctrl+Z undo</p>

          <div class="toolbar-row">
            <label class="file-btn btn btn-ghost btn-sm">Upload<input type="file" id="editor-file" accept="image/*,video/mp4,video/webm,image/gif" hidden></label>
            <button type="button" class="btn btn-ghost btn-sm" id="add-text">+ Text</button>
            <button type="button" class="btn btn-ghost btn-sm" id="del-layer">Delete layer</button>
            <button type="button" class="btn btn-ghost btn-sm" id="fwd-layer">Forward</button>
            <button type="button" class="btn btn-ghost btn-sm" id="back-layer">Back</button>
            <button type="button" class="btn btn-ghost btn-sm" id="lock-layer">Lock</button>
          </div>

          <div id="layer-panel" class="layer-panel muted">Select a layer</div>

          <div class="editor-section">
            <h3>Stickers</h3>
            <div id="sticker-bar" class="sticker-bar"></div>
          </div>

          <div class="editor-section">
            <h3>Filters</h3>
            <div class="filter-row" id="filter-presets"></div>
            <label class="inline">Brightness <input type="range" id="f-bright" min="50" max="150" value="100"></label>
            <label class="inline">Contrast <input type="range" id="f-contrast" min="50" max="150" value="100"></label>
            <label class="inline">Blur <input type="range" id="f-blur" min="0" max="8" step="0.1" value="0"></label>
            <div class="toolbar-row">
              <button type="button" class="btn btn-ghost btn-sm" id="crop-center">Crop center</button>
              <button type="button" class="btn btn-ghost btn-sm" id="crop-clear">Clear crop</button>
            </div>
          </div>

          <div class="editor-section">
            <label><span>Caption</span><input id="publish-caption" maxlength="280" placeholder="Feed caption"></label>
            <label><span>Tags</span><input id="publish-tags" placeholder="funny, work, reaction"></label>
            <label class="inline"><input type="checkbox" id="unlisted"> Unlisted</label>
            <div class="form-actions">
              <button type="button" class="btn btn-ghost" id="draft-btn">Save draft</button>
              <button type="button" class="btn btn-primary" id="publish-btn">Publish</button>
              <button type="button" class="btn btn-ghost" id="download-btn">Download PNG</button>
            </div>
            <p class="form-status" id="create-status"></p>
          </div>
        </div>

        <div class="editor-stage panel">
          <canvas id="meme-canvas" width="800" height="800"></canvas>
          <p class="muted tip" id="onboarding-tip" hidden>Tip: add text, style it, then publish. You can re-open any of your memes in the editor later.</p>
        </div>

        <div class="panel templates-panel">
          <div class="stream-header">
            <h3>Templates & stock</h3>
            <input id="template-q" placeholder="Search templates" style="max-width:180px">
          </div>
          <div class="chip-row" id="category-chips">
            <button type="button" class="chip active" data-cat="all">All</button>
            <button type="button" class="chip" data-cat="blank">Blank</button>
            <button type="button" class="chip" data-cat="reaction">Reaction</button>
            <button type="button" class="chip" data-cat="workplace">Workplace</button>
            <button type="button" class="chip" data-cat="politics">Politics</button>
            <button type="button" class="chip" data-cat="favorites">Favorites</button>
          </div>
          <div id="template-grid" class="template-grid"></div>
          <div class="editor-section">
            <h3>Stock search</h3>
            <div class="toolbar-row">
              <input id="stock-q" placeholder="Search Giphy / curated…">
              <button type="button" class="btn btn-ghost btn-sm" id="stock-btn">Search</button>
            </div>
            <div id="stock-grid" class="template-grid"></div>
          </div>
          <div class="editor-section">
            <h3>Upload as template</h3>
            <div class="toolbar-row">
              <input id="tmpl-name" placeholder="Template name">
              <label class="file-btn btn btn-ghost btn-sm">Image<input type="file" id="tmpl-file" accept="image/*" hidden></label>
              <button type="button" class="btn btn-ghost btn-sm" id="tmpl-save">Save template</button>
            </div>
          </div>
        </div>
      </section>`;

    const status = document.getElementById("create-status");
    const canvas = document.getElementById("meme-canvas");
    let category = "all";
    let mediaType = "image";
    let activeMemeId = editingMemeId || null;

    const syncLayerPanel = () => {
      const state = MemeEditor.getState();
      const layer = state.layers.find((l) => l.id === state.selectedId);
      const panel = document.getElementById("layer-panel");
      if (!layer) {
        panel.innerHTML = `<span class="muted">Select a layer</span>`;
        return;
      }
      if (layer.type === "sticker") {
        panel.innerHTML = `
          <strong>Sticker ${escapeHtml(layer.emoji)}</strong>
          <label class="inline">Size <input type="range" data-patch="fontSize" min="24" max="160" value="${layer.fontSize || 64}"></label>
          <p class="muted">Locked: ${layer.locked ? "yes" : "no"}</p>`;
      } else {
        panel.innerHTML = `
          <label><span>Text</span><textarea data-patch="text" rows="2">${escapeHtml(layer.text || "")}</textarea></label>
          <label><span>Font</span>
            <select data-patch="fontFamily">
              ${MemeEditor.FONTS.map((f) => `<option value="${escapeHtml(f)}" ${f === layer.fontFamily ? "selected" : ""}>${escapeHtml(f.split(",")[0].replace(/'/g, ""))}</option>`).join("")}
            </select>
          </label>
          <label class="inline">Size <input type="range" data-patch="fontSize" min="16" max="96" value="${layer.fontSize || 42}"></label>
          <label class="inline">Color <input type="color" data-patch="color" value="${layer.color || "#ffffff"}"></label>
          <label class="inline">Outline <input type="color" data-patch="outlineColor" value="${layer.outlineColor || "#000000"}"></label>
          <label class="inline">Outline width <input type="range" data-patch="outlineWidth" min="0" max="12" value="${layer.outlineWidth ?? 4}"></label>
          <label class="inline"><input type="checkbox" data-patch="shadow" ${layer.shadow ? "checked" : ""}> Shadow</label>
          <label class="inline"><input type="checkbox" data-patch="allCaps" ${layer.allCaps ? "checked" : ""}> ALL CAPS</label>
          <label><span>Align</span>
            <select data-patch="align">
              ${["left", "center", "right"].map((a) => `<option value="${a}" ${layer.align === a ? "selected" : ""}>${a}</option>`).join("")}
            </select>
          </label>`;
      }
    };

    MemeEditor.init(canvas, syncLayerPanel);
    document.getElementById("sticker-bar").innerHTML = MemeEditor.STICKERS.map(
      (e) => `<button type="button" class="sticker" data-emoji="${e}">${e}</button>`
    ).join("");
    document.getElementById("filter-presets").innerHTML = Object.keys(MemeEditor.FILTER_PRESETS)
      .map((p) => `<button type="button" class="chip" data-preset="${p}">${p}</button>`)
      .join("");

    if (!currentUser.onboarding_done) {
      document.getElementById("onboarding-tip").hidden = false;
    }

    if (activeMemeId) {
      try {
        const meme = await API.get(`/memes/${activeMemeId}`);
        document.getElementById("publish-caption").value = meme.caption || "";
        document.getElementById("publish-tags").value = (meme.tags || []).join(", ");
        document.getElementById("unlisted").checked = meme.visibility === "unlisted" || meme.status === "unlisted";
        mediaType = meme.media_type || "image";
        if (meme.editor_state) {
          await MemeEditor.loadState(JSON.parse(meme.editor_state));
        } else {
          await MemeEditor.loadImage(API.resolveUrl(meme.url));
        }
      } catch (err) {
        setStatus(status, err.message, "error");
      }
    }

    document.getElementById("layer-panel").addEventListener("input", (e) => {
      const el = e.target.closest("[data-patch]");
      if (!el) return;
      const key = el.dataset.patch;
      let value;
      if (el.type === "checkbox") value = el.checked;
      else if (el.type === "range" || key === "fontSize" || key === "outlineWidth") value = Number(el.value);
      else value = el.value;
      MemeEditor.updateSelected({ [key]: value }, key === "text" ? false : true);
    });
    document.getElementById("layer-panel").addEventListener("change", (e) => {
      const el = e.target.closest("[data-patch]");
      if (!el) return;
      if (el.dataset.patch === "text") MemeEditor.updateSelected({ text: el.value }, true);
    });

    document.getElementById("sticker-bar").onclick = (e) => {
      const btn = e.target.closest("[data-emoji]");
      if (btn) MemeEditor.addSticker(btn.dataset.emoji);
    };
    document.getElementById("add-text").onclick = () => MemeEditor.addText();
    document.getElementById("del-layer").onclick = () => MemeEditor.removeSelected();
    document.getElementById("fwd-layer").onclick = () => MemeEditor.bringForward();
    document.getElementById("back-layer").onclick = () => MemeEditor.sendBackward();
    document.getElementById("lock-layer").onclick = () => MemeEditor.toggleLock();
    document.getElementById("undo-btn").onclick = () => MemeEditor.undo();
    document.getElementById("redo-btn").onclick = () => MemeEditor.redo();
    document.getElementById("reset-btn").onclick = () => MemeEditor.reset();
    document.getElementById("download-btn").onclick = () => MemeEditor.download();
    document.getElementById("crop-center").onclick = () => MemeEditor.setCrop({ x: 0.1, y: 0.1, w: 0.8, h: 0.8 });
    document.getElementById("crop-clear").onclick = () => MemeEditor.clearCrop();

    document.getElementById("filter-presets").onclick = (e) => {
      const btn = e.target.closest("[data-preset]");
      if (btn) MemeEditor.setFilters({ preset: btn.dataset.preset });
    };
    const liveFilter = () =>
      MemeEditor.setFilters(
        {
          brightness: Number(document.getElementById("f-bright").value),
          contrast: Number(document.getElementById("f-contrast").value),
          blur: Number(document.getElementById("f-blur").value),
          preset: "custom",
        },
        false
      );
    ["f-bright", "f-contrast", "f-blur"].forEach((id) => {
      document.getElementById(id).oninput = liveFilter;
      document.getElementById(id).onchange = () => MemeEditor.setFilters({}, true);
    });

    document.getElementById("editor-file").onchange = async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      try {
        const uploaded = await API.upload(file);
        mediaType = uploaded.media_type || "image";
        if (mediaType === "video") {
          setStatus(status, "Video saved. Overlay editor uses a poster frame — publish uses the video file.", "success");
          // still try to load as image may fail; keep url for publish
          window.__videoUrl = uploaded.url;
        } else {
          window.__videoUrl = null;
          await MemeEditor.loadImage(uploaded.url);
        }
        setStatus(status, "Media loaded.", "success");
      } catch (err) {
        setStatus(status, err.message, "error");
      }
    };

    const publish = async (asDraft) => {
      try {
        setStatus(status, asDraft ? "Saving draft…" : "Publishing…");
        let url = window.__videoUrl;
        let type = mediaType;
        if (!url) {
          const blob = await MemeEditor.toBlob();
          const file = new File([blob], "meme.png", { type: "image/png" });
          const uploaded = await API.upload(file);
          url = uploaded.url;
          type = "image";
        }
        const tags = document
          .getElementById("publish-tags")
          .value.split(",")
          .map((t) => t.trim())
          .filter(Boolean);
        const caption =
          document.getElementById("publish-caption").value.trim() || "Untitled meme";
        const unlisted = document.getElementById("unlisted").checked;
        const payload = {
          url,
          caption,
          tags,
          editor_state: JSON.stringify(MemeEditor.getState()),
          media_type: type,
          status: asDraft ? "draft" : unlisted ? "unlisted" : "published",
          visibility: asDraft || unlisted ? "unlisted" : "public",
        };
        let meme;
        if (activeMemeId) {
          meme = await API.patch(`/memes/${activeMemeId}`, payload);
        } else {
          meme = await API.post("/memes", payload);
          activeMemeId = meme.id;
        }
        if (!currentUser.onboarding_done) {
          await API.patch("/auth/me", { onboarding_done: true });
          currentUser.onboarding_done = true;
        }
        setStatus(status, asDraft ? "Draft saved." : "Published!", "success");
        if (!asDraft) navigate(`/meme/${meme.id}`);
      } catch (err) {
        setStatus(status, err.message, "error");
      }
    };

    document.getElementById("publish-btn").onclick = () => publish(false);
    document.getElementById("draft-btn").onclick = () => publish(true);

    const loadTemplates = async () => {
      const q = document.getElementById("template-q").value.trim();
      const favorites = category === "favorites";
      const cat = favorites || category === "all" ? null : category;
      const params = new URLSearchParams();
      if (cat) params.set("category", cat);
      if (q) params.set("q", q);
      if (favorites) params.set("favorites", "true");
      const templates = await API.get(`/templates?${params}`);
      const grid = document.getElementById("template-grid");
      grid.innerHTML = templates
        .map(
          (t) => `
        <div class="template-card-wrap">
          <button type="button" class="template-card" data-id="${t.id}" data-src="${escapeHtml(API.resolveUrl(t.image_url))}">
            <img src="${escapeHtml(API.resolveUrl(t.image_url))}" alt="${escapeHtml(t.name)}" loading="lazy">
            <span>${escapeHtml(t.name)}</span>
          </button>
          <button type="button" class="btn btn-ghost btn-sm fav-btn" data-fav="${t.id}">${t.favorited ? "★" : "☆"}</button>
        </div>`
        )
        .join("") || `<p class="muted">No templates</p>`;
    };

    document.getElementById("category-chips").onclick = (e) => {
      const chip = e.target.closest("[data-cat]");
      if (!chip) return;
      category = chip.dataset.cat;
      document.querySelectorAll("#category-chips .chip").forEach((c) => c.classList.toggle("active", c === chip));
      loadTemplates().catch((err) => setStatus(status, err.message, "error"));
    };
    document.getElementById("template-q").oninput = () => loadTemplates().catch(() => {});
    document.getElementById("template-grid").onclick = async (e) => {
      const fav = e.target.closest("[data-fav]");
      if (fav) {
        await API.post(`/templates/${fav.dataset.fav}/favorite`, {});
        return loadTemplates();
      }
      const btn = e.target.closest("[data-src]");
      if (!btn) return;
      try {
        await MemeEditor.loadImage(btn.dataset.src);
        window.__videoUrl = null;
        mediaType = "image";
        if (btn.dataset.id) await API.post(`/templates/${btn.dataset.id}/use`, {});
        setStatus(status, "Template loaded.", "success");
      } catch (err) {
        setStatus(status, err.message, "error");
      }
    };

    document.getElementById("stock-btn").onclick = async () => {
      const q = document.getElementById("stock-q").value.trim() || "meme";
      const items = await API.get(`/stock/search?q=${encodeURIComponent(q)}`);
      document.getElementById("stock-grid").innerHTML = items
        .map(
          (i) => `
        <button type="button" class="template-card" data-src="${escapeHtml(i.url)}">
          <img src="${escapeHtml(i.preview_url)}" alt="${escapeHtml(i.title)}" loading="lazy">
          <span>${escapeHtml(i.title)}</span>
        </button>`
        )
        .join("");
    };
    document.getElementById("stock-grid").onclick = async (e) => {
      const btn = e.target.closest("[data-src]");
      if (!btn) return;
      try {
        await MemeEditor.loadImage(btn.dataset.src);
        window.__videoUrl = null;
        setStatus(status, "Stock image loaded.", "success");
      } catch (err) {
        setStatus(status, err.message, "error");
      }
    };

    let pendingTmplFile = null;
    document.getElementById("tmpl-file").onchange = (e) => {
      pendingTmplFile = e.target.files?.[0] || null;
    };
    document.getElementById("tmpl-save").onclick = async () => {
      try {
        if (!pendingTmplFile) throw new Error("Choose an image first");
        const name = document.getElementById("tmpl-name").value.trim() || "My template";
        const uploaded = await API.upload(pendingTmplFile);
        await API.post("/templates", {
          name,
          image_url: uploaded.url,
          category: "custom",
          is_public: true,
          description: "Community template",
        });
        setStatus(status, "Template saved.", "success");
        loadTemplates();
      } catch (err) {
        setStatus(status, err.message, "error");
      }
    };

    window.addEventListener(
      "keydown",
      (e) => {
        if (!location.hash.includes("/create") && !location.hash.includes("/edit/")) return;
        const meta = e.metaKey || e.ctrlKey;
        if (meta && e.key.toLowerCase() === "z") {
          e.preventDefault();
          if (e.shiftKey) MemeEditor.redo();
          else MemeEditor.undo();
        }
        if (e.key === "Delete" || e.key === "Backspace") {
          if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) return;
          MemeEditor.removeSelected();
        }
      },
      { once: false }
    );

    await loadTemplates();
    syncLayerPanel();
  },
};
