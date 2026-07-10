(() => {
  const app = document.getElementById("app");
  let currentUser = null;
  let feedPage = 1;
  let feedMode = "latest";
  let editingId = null;

  const escapeHtml = (v) =>
    String(v)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const setStatus = (el, msg, type = "") => {
    if (!el) return;
    el.textContent = msg;
    el.classList.remove("is-error", "is-success");
    if (type) el.classList.add(`is-${type}`);
  };

  function parseRoute() {
    const hash = location.hash.replace(/^#\/?/, "") || "";
    const [path, query = ""] = hash.split("?");
    const parts = path.split("/").filter(Boolean);
    const params = Object.fromEntries(new URLSearchParams(query));
    return { parts, params };
  }

  function navigate(to) {
    location.hash = to.startsWith("#") ? to : `#${to}`;
  }

  function updateNav() {
    document.querySelectorAll("[data-auth='guest']").forEach((el) => {
      el.hidden = !!currentUser;
    });
    document.querySelectorAll("[data-auth='user']").forEach((el) => {
      el.hidden = !currentUser;
    });
    const userLink = document.querySelector(".nav-user");
    if (userLink && currentUser) {
      userLink.textContent = `@${currentUser.username}`;
      userLink.href = `#/u/${currentUser.username}`;
    }
  }

  async function refreshUser() {
    if (!API.token()) {
      currentUser = null;
      updateNav();
      return;
    }
    try {
      currentUser = await API.get("/auth/me");
    } catch {
      API.setToken(null);
      currentUser = null;
    }
    updateNav();
  }

  function memeCard(meme, index = 0) {
    const img = API.resolveUrl(meme.url);
    const author = meme.username || meme.name;
    const canEdit =
      currentUser && (!meme.user_id || meme.user_id === currentUser.id);
    return `
      <article class="meme-card" style="animation-delay:${Math.min(index, 12) * 40}ms">
        <a class="card-media" href="#/meme/${meme.id}">
          <img src="${escapeHtml(img)}" alt="${escapeHtml(meme.caption)}" loading="lazy"
            onerror="this.onerror=null;this.src='images/invalid_url.jpg'">
        </a>
        <div class="card-body">
          <p class="caption"><a href="#/meme/${meme.id}">${escapeHtml(meme.caption)}</a></p>
          <p class="author">
            ${meme.username ? `<a href="#/u/${escapeHtml(meme.username)}">@${escapeHtml(meme.username)}</a>` : escapeHtml(author)}
          </p>
          <div class="card-meta">
            <span>${meme.like_count || 0} likes</span>
            <span>${meme.comment_count || 0} comments</span>
          </div>
          <div class="card-actions">
            <button type="button" class="btn btn-ghost btn-sm" data-like="${meme.id}">
              ${meme.liked_by_me ? "Unlike" : "Like"}
            </button>
            <a class="btn btn-ghost btn-sm" href="#/meme/${meme.id}">Open</a>
            ${canEdit ? `<button type="button" class="btn btn-ghost btn-sm" data-edit="${meme.id}">Edit</button>` : ""}
            ${canEdit ? `<button type="button" class="btn btn-ghost btn-sm danger" data-delete="${meme.id}">Delete</button>` : ""}
          </div>
        </div>
      </article>`;
  }

  function pager(page, pages, baseHash) {
    if (!pages || pages <= 1) return "";
    return `
      <div class="pager">
        <button type="button" class="btn btn-ghost btn-sm" data-page="${page - 1}" ${page <= 1 ? "disabled" : ""}>Prev</button>
        <span>Page ${page} / ${pages}</span>
        <button type="button" class="btn btn-ghost btn-sm" data-page="${page + 1}" ${page >= pages ? "disabled" : ""}>Next</button>
      </div>`;
  }

  async function renderFeed(mode = "latest", page = 1) {
    feedMode = mode;
    feedPage = page;
    const title = mode === "trending" ? "Trending" : "Meme stream";
    app.innerHTML = `
      <section class="hero compact">
        <p class="hero-brand">XMeme</p>
        <h1>${mode === "trending" ? "What’s catching fire" : "Post it. Share it. Make it viral."}</h1>
        <p class="hero-sub">${mode === "trending" ? "Sorted by likes and views." : "Create memes, share links, and ride the stream."}</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="#/create">Create meme</a>
          <a class="btn btn-ghost" href="#/${mode === "trending" ? "" : "trending"}">${mode === "trending" ? "Latest" : "Trending"}</a>
        </div>
      </section>
      <section class="stream">
        <div class="stream-header">
          <h2>${title}</h2>
          <button type="button" class="btn btn-ghost btn-sm" id="refresh-btn">Refresh</button>
        </div>
        <div id="meme-grid" class="meme-grid"><p class="empty-state">Loading…</p></div>
        <div id="pager"></div>
      </section>`;

    document.getElementById("refresh-btn").onclick = () => renderFeed(mode, page);

    try {
      const path =
        mode === "trending"
          ? `/memes/trending?page=${page}&page_size=${window.XMEME_CONFIG.pageSize}`
          : `/memes?page=${page}&page_size=${window.XMEME_CONFIG.pageSize}`;
      const data = await API.get(path);
      const grid = document.getElementById("meme-grid");
      if (!data.items?.length) {
        grid.innerHTML = `<p class="empty-state">No memes yet — <a href="#/create">create one</a>.</p>`;
      } else {
        grid.innerHTML = data.items.map(memeCard).join("");
      }
      document.getElementById("pager").innerHTML = pager(data.page, data.pages);
      document.getElementById("pager").onclick = (e) => {
        const btn = e.target.closest("[data-page]");
        if (!btn || btn.disabled) return;
        renderFeed(mode, Number(btn.dataset.page));
      };
      bindCardActions(grid);
    } catch (err) {
      document.getElementById("meme-grid").innerHTML =
        `<p class="empty-state">Couldn’t reach the API (${escapeHtml(err.message)}).</p>`;
    }
  }

  function bindCardActions(root) {
    root.addEventListener("click", async (e) => {
      const likeBtn = e.target.closest("[data-like]");
      const editBtn = e.target.closest("[data-edit]");
      const delBtn = e.target.closest("[data-delete]");
      if (likeBtn) {
        if (!currentUser) return navigate("/login");
        try {
          await API.post(`/memes/${likeBtn.dataset.like}/like`, {});
          route();
        } catch (err) {
          alert(err.message);
        }
      }
      if (editBtn) openEdit(Number(editBtn.dataset.edit));
      if (delBtn) {
        if (!confirm("Delete this meme?")) return;
        try {
          await API.delete(`/memes/${delBtn.dataset.delete}`);
          route();
        } catch (err) {
          alert(err.message);
        }
      }
    });
  }

  function openEdit(id) {
    editingId = id;
    document.getElementById("edit-form").reset();
    setStatus(document.getElementById("edit-status"), "");
    document.getElementById("edit-dialog").showModal();
  }

  async function renderAuth(mode) {
    const isLogin = mode === "login";
    app.innerHTML = `
      <section class="panel">
        <h2>${isLogin ? "Log in" : "Create account"}</h2>
        <form id="auth-form" class="stack">
          <label><span>Username</span><input name="username" required autocomplete="username" pattern="[A-Za-z0-9_]+"></label>
          ${isLogin ? "" : `<label><span>Email</span><input type="email" name="email" required autocomplete="email"></label>`}
          <label><span>Password</span><input type="password" name="password" required minlength="6" autocomplete="${isLogin ? "current-password" : "new-password"}"></label>
          <div class="form-actions">
            <button class="btn btn-primary" type="submit">${isLogin ? "Log in" : "Sign up"}</button>
          </div>
          <p class="form-status" id="auth-status"></p>
          <p class="muted">${isLogin ? `No account? <a href="#/register">Sign up</a>` : `Have an account? <a href="#/login">Log in</a>`}</p>
        </form>
      </section>`;

    document.getElementById("auth-form").onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const status = document.getElementById("auth-status");
      try {
        if (isLogin) {
          await API.login(fd.get("username"), fd.get("password"));
        } else {
          await API.post("/auth/register", {
            username: fd.get("username"),
            email: fd.get("email"),
            password: fd.get("password"),
          });
          await API.login(fd.get("username"), fd.get("password"));
        }
        await refreshUser();
        navigate("/");
      } catch (err) {
        setStatus(status, err.message, "error");
      }
    };
  }

  async function renderCreate() {
    if (!currentUser) {
      app.innerHTML = `<section class="panel"><h2>Create meme</h2><p>Please <a href="#/login">log in</a> to upload and publish memes.</p></section>`;
      return;
    }

    app.innerHTML = `
      <section class="create-layout">
        <div class="panel">
          <h2>Meme editor</h2>
          <p class="muted">Pick a template or upload an image, add text, drag to position, then publish.</p>
          <div class="editor-toolbar">
            <label class="file-btn btn btn-ghost btn-sm">
              Upload image
              <input type="file" id="editor-file" accept="image/*" hidden>
            </label>
            <label class="inline">
              Font size
              <input type="range" id="font-size" min="24" max="72" value="42">
            </label>
          </div>
          <div class="editor-texts">
            <label><span>Top text</span><input id="top-text" value="TOP TEXT"></label>
            <label><span>Bottom text</span><input id="bottom-text" value="BOTTOM TEXT"></label>
            <label><span>Caption (feed)</span><input id="publish-caption" placeholder="How it appears in the stream" maxlength="280"></label>
          </div>
          <div class="form-actions">
            <button type="button" class="btn btn-primary" id="publish-btn">Publish meme</button>
          </div>
          <p class="form-status" id="create-status"></p>
        </div>
        <div class="editor-stage panel">
          <canvas id="meme-canvas" width="800" height="800"></canvas>
          <p class="muted tip">Drag text on the canvas to reposition.</p>
        </div>
        <div class="panel templates-panel">
          <h3>Templates</h3>
          <div id="template-grid" class="template-grid"><p class="muted">Loading…</p></div>
        </div>
        <div class="panel">
          <h3>Or post a URL</h3>
          <form id="url-form" class="stack">
            <label><span>Image URL</span><input type="url" id="url-input" required placeholder="https://…"></label>
            <label><span>Caption</span><input id="url-caption" required maxlength="280"></label>
            <button class="btn btn-ghost" type="submit">Post URL meme</button>
            <p class="form-status" id="url-status"></p>
          </form>
        </div>
      </section>`;

    MemeEditor.init(document.getElementById("meme-canvas"));

    const syncText = () =>
      MemeEditor.setTexts(
        document.getElementById("top-text").value,
        document.getElementById("bottom-text").value
      );
    document.getElementById("top-text").oninput = syncText;
    document.getElementById("bottom-text").oninput = syncText;
    document.getElementById("font-size").oninput = (e) =>
      MemeEditor.setFontSize(Number(e.target.value));

    document.getElementById("editor-file").onchange = async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const status = document.getElementById("create-status");
      try {
        const uploaded = await API.upload(file);
        await MemeEditor.loadImage(uploaded.url);
        setStatus(status, "Image loaded.", "success");
      } catch (err) {
        setStatus(status, err.message, "error");
      }
    };

    document.getElementById("publish-btn").onclick = async () => {
      const status = document.getElementById("create-status");
      const caption =
        document.getElementById("publish-caption").value.trim() ||
        `${document.getElementById("top-text").value} / ${document.getElementById("bottom-text").value}`.trim();
      try {
        setStatus(status, "Uploading…");
        const blob = await MemeEditor.toBlob();
        if (!blob) throw new Error("Nothing to export");
        const file = new File([blob], "meme.png", { type: "image/png" });
        const uploaded = await API.upload(file);
        const meme = await API.post("/memes", { url: uploaded.url, caption });
        setStatus(status, "Published!", "success");
        navigate(`/meme/${meme.id}`);
      } catch (err) {
        setStatus(status, err.message, "error");
      }
    };

    document.getElementById("url-form").onsubmit = async (e) => {
      e.preventDefault();
      const status = document.getElementById("url-status");
      try {
        const meme = await API.post("/memes", {
          url: document.getElementById("url-input").value.trim(),
          caption: document.getElementById("url-caption").value.trim(),
        });
        navigate(`/meme/${meme.id}`);
      } catch (err) {
        setStatus(status, err.message, "error");
      }
    };

    try {
      const templates = await API.get("/templates");
      const grid = document.getElementById("template-grid");
      grid.innerHTML = templates
        .map(
          (t) => `
        <button type="button" class="template-card" data-src="${escapeHtml(API.resolveUrl(t.image_url))}">
          <img src="${escapeHtml(API.resolveUrl(t.image_url))}" alt="${escapeHtml(t.name)}" loading="lazy"
            onerror="this.style.display='none'">
          <span>${escapeHtml(t.name)}</span>
        </button>`
        )
        .join("");
      grid.onclick = async (e) => {
        const btn = e.target.closest("[data-src]");
        if (!btn) return;
        try {
          await MemeEditor.loadImage(btn.dataset.src);
          setStatus(document.getElementById("create-status"), "Template loaded.", "success");
        } catch (err) {
          setStatus(document.getElementById("create-status"), err.message, "error");
        }
      };
    } catch {
      document.getElementById("template-grid").innerHTML =
        `<p class="muted">Templates unavailable.</p>`;
    }
  }

  async function renderMeme(id) {
    app.innerHTML = `<section class="panel"><p class="empty-state">Loading meme…</p></section>`;
    try {
      const meme = await API.get(`/memes/${id}?track_view=true`);
      const comments = await API.get(`/memes/${id}/comments`);
      const img = API.resolveUrl(meme.url);
      const shareApi = `${API.base}/share/${meme.id}`;
      const shareApp = `${location.origin}${location.pathname}#/meme/${meme.id}`;
      const author = meme.username || meme.name;
      const canEdit =
        currentUser && (!meme.user_id || meme.user_id === currentUser.id);

      app.innerHTML = `
        <section class="detail-layout">
          <div class="panel detail-media">
            <img src="${escapeHtml(img)}" alt="${escapeHtml(meme.caption)}"
              onerror="this.onerror=null;this.src='images/invalid_url.jpg'">
          </div>
          <div class="panel detail-info">
            <h1>${escapeHtml(meme.caption)}</h1>
            <p class="author">
              ${meme.username ? `<a href="#/u/${escapeHtml(meme.username)}">@${escapeHtml(meme.username)}</a>` : escapeHtml(author)}
            </p>
            <div class="card-meta">
              <span>${meme.like_count} likes</span>
              <span>${meme.comment_count} comments</span>
              <span>${meme.view_count} views</span>
            </div>
            <div class="form-actions wrap">
              <button type="button" class="btn btn-primary" id="like-btn">${meme.liked_by_me ? "Unlike" : "Like"}</button>
              <button type="button" class="btn btn-ghost" id="copy-link">Copy link</button>
              <a class="btn btn-ghost" target="_blank" rel="noopener"
                href="https://twitter.com/intent/tweet?text=${encodeURIComponent(meme.caption)}&url=${encodeURIComponent(shareApi)}">Share on X</a>
              <a class="btn btn-ghost" target="_blank" rel="noopener"
                href="https://www.reddit.com/submit?url=${encodeURIComponent(shareApi)}&title=${encodeURIComponent(meme.caption)}">Reddit</a>
              ${canEdit ? `<button type="button" class="btn btn-ghost" id="edit-detail">Edit</button>` : ""}
              ${canEdit ? `<button type="button" class="btn btn-ghost danger" id="delete-detail">Delete</button>` : ""}
            </div>
            <p class="form-status" id="share-status"></p>
            <p class="muted">OG share URL: <code>${escapeHtml(shareApi)}</code></p>

            <h3>Comments</h3>
            <div id="comments" class="comments">
              ${
                comments.length
                  ? comments
                      .map(
                        (c) => `
                <article class="comment">
                  <strong><a href="#/u/${escapeHtml(c.username)}">@${escapeHtml(c.username)}</a></strong>
                  <p>${escapeHtml(c.body)}</p>
                </article>`
                      )
                      .join("")
                  : `<p class="muted">No comments yet.</p>`
              }
            </div>
            ${
              currentUser
                ? `<form id="comment-form" class="stack">
                    <label><span>Add a comment</span><input name="body" maxlength="500" required placeholder="Say something…"></label>
                    <button class="btn btn-primary" type="submit">Comment</button>
                    <p class="form-status" id="comment-status"></p>
                  </form>`
                : `<p class="muted"><a href="#/login">Log in</a> to comment.</p>`
            }
          </div>
        </section>`;

      document.getElementById("like-btn").onclick = async () => {
        if (!currentUser) return navigate("/login");
        await API.post(`/memes/${id}/like`, {});
        renderMeme(id);
      };
      document.getElementById("copy-link").onclick = async () => {
        await navigator.clipboard.writeText(shareApp);
        setStatus(document.getElementById("share-status"), "Link copied.", "success");
      };
      const editDetail = document.getElementById("edit-detail");
      if (editDetail) editDetail.onclick = () => openEdit(Number(id));
      const deleteDetail = document.getElementById("delete-detail");
      if (deleteDetail) {
        deleteDetail.onclick = async () => {
          if (!confirm("Delete this meme?")) return;
          await API.delete(`/memes/${id}`);
          navigate("/");
        };
      }
      const commentForm = document.getElementById("comment-form");
      if (commentForm) {
        commentForm.onsubmit = async (e) => {
          e.preventDefault();
          const body = new FormData(commentForm).get("body");
          try {
            await API.post(`/memes/${id}/comments`, { body });
            renderMeme(id);
          } catch (err) {
            setStatus(document.getElementById("comment-status"), err.message, "error");
          }
        };
      }
    } catch (err) {
      app.innerHTML = `<section class="panel"><p class="empty-state">${escapeHtml(err.message)}</p></section>`;
    }
  }

  async function renderProfile(username) {
    app.innerHTML = `<section class="panel"><p class="empty-state">Loading profile…</p></section>`;
    try {
      const profile = await API.get(`/users/${username}`);
      const memes = await API.get(
        `/users/${username}/memes?page=1&page_size=${window.XMEME_CONFIG.pageSize}`
      );
      const isMe = currentUser?.username === username;
      app.innerHTML = `
        <section class="panel profile-head">
          <h1>@${escapeHtml(profile.username)}</h1>
          <p>${escapeHtml(profile.bio || "No bio yet.")}</p>
          <div class="card-meta">
            <span>${profile.meme_count} memes</span>
            <span>${profile.like_count} likes received</span>
          </div>
          ${
            isMe
              ? `<form id="bio-form" class="stack">
                  <label><span>Update bio</span><input name="bio" maxlength="280" value="${escapeHtml(profile.bio || "")}"></label>
                  <button class="btn btn-ghost btn-sm" type="submit">Save bio</button>
                  <p class="form-status" id="bio-status"></p>
                </form>`
              : ""
          }
        </section>
        <section class="stream">
          <h2>Memes by @${escapeHtml(profile.username)}</h2>
          <div id="meme-grid" class="meme-grid">
            ${
              memes.items?.length
                ? memes.items.map(memeCard).join("")
                : `<p class="empty-state">No memes yet.</p>`
            }
          </div>
        </section>`;
      const grid = document.getElementById("meme-grid");
      if (grid) bindCardActions(grid);
      const bioForm = document.getElementById("bio-form");
      if (bioForm) {
        bioForm.onsubmit = async (e) => {
          e.preventDefault();
          try {
            await API.patch("/auth/me", { bio: new FormData(bioForm).get("bio") });
            setStatus(document.getElementById("bio-status"), "Saved.", "success");
            await refreshUser();
          } catch (err) {
            setStatus(document.getElementById("bio-status"), err.message, "error");
          }
        };
      }
    } catch (err) {
      app.innerHTML = `<section class="panel"><p class="empty-state">${escapeHtml(err.message)}</p></section>`;
    }
  }

  async function route() {
    const { parts } = parseRoute();
    const [head, id] = parts;
    if (!head) return renderFeed("latest", 1);
    if (head === "trending") return renderFeed("trending", 1);
    if (head === "create") return renderCreate();
    if (head === "login") return renderAuth("login");
    if (head === "register") return renderAuth("register");
    if (head === "meme" && id) return renderMeme(id);
    if (head === "u" && id) return renderProfile(id);
    if (head === "profile" && currentUser) return renderProfile(currentUser.username);
    if (head === "profile") return navigate("/login");
    app.innerHTML = `<section class="panel"><p class="empty-state">Page not found. <a href="#/">Go home</a></p></section>`;
  }

  document.getElementById("logout-btn").onclick = () => {
    API.setToken(null);
    currentUser = null;
    updateNav();
    navigate("/");
  };

  const editDialog = document.getElementById("edit-dialog");
  document.getElementById("edit-close").onclick = () => editDialog.close();
  document.getElementById("edit-cancel").onclick = () => editDialog.close();
  document.getElementById("edit-form").onsubmit = async (e) => {
    e.preventDefault();
    if (!editingId) return;
    const url = document.getElementById("edit_url").value.trim();
    const caption = document.getElementById("edit_caption").value.trim();
    if (!url && !caption) {
      setStatus(document.getElementById("edit-status"), "Fill at least one field.", "error");
      return;
    }
    const body = {};
    if (url) body.url = url;
    if (caption) body.caption = caption;
    try {
      await API.patch(`/memes/${editingId}`, body);
      editDialog.close();
      route();
    } catch (err) {
      setStatus(document.getElementById("edit-status"), err.message, "error");
    }
  };

  window.addEventListener("hashchange", route);
  refreshUser().then(route);
})();
