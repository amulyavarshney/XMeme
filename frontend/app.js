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
    const canEdit = currentUser && (!meme.user_id || meme.user_id === currentUser.id);
    const tags = (meme.tags || [])
      .map((t) => `<a class="tag" href="#/tag/${escapeHtml(t)}">#${escapeHtml(t)}</a>`)
      .join(" ");
    const media =
      meme.media_type === "video"
        ? `<video src="${escapeHtml(img)}" muted loop playsinline></video>`
        : `<img src="${escapeHtml(img)}" alt="${escapeHtml(meme.caption)}" loading="lazy"
            onerror="this.onerror=null;this.src='images/invalid_url.jpg'">`;
    return `
      <article class="meme-card" style="animation-delay:${Math.min(index, 12) * 40}ms">
        <a class="card-media" href="#/meme/${meme.id}">${media}</a>
        <div class="card-body">
          <p class="caption"><a href="#/meme/${meme.id}">${escapeHtml(meme.caption)}</a></p>
          <p class="author">
            ${meme.username ? `<a href="#/u/${escapeHtml(meme.username)}">@${escapeHtml(meme.username)}</a>` : escapeHtml(author)}
            ${meme.status === "draft" ? " · draft" : ""}
          </p>
          <div class="card-meta">
            <span>${meme.like_count || 0} likes</span>
            <span>${meme.comment_count || 0} comments</span>
          </div>
          ${tags ? `<div class="tag-row">${tags}</div>` : ""}
          <div class="card-actions">
            <button type="button" class="btn btn-ghost btn-sm" data-like="${meme.id}">
              ${meme.liked_by_me ? "Unlike" : "Like"}
            </button>
            <a class="btn btn-ghost btn-sm" href="#/meme/${meme.id}">Open</a>
            ${canEdit ? `<a class="btn btn-ghost btn-sm" href="#/edit/${meme.id}">Studio</a>` : ""}
            ${canEdit ? `<button type="button" class="btn btn-ghost btn-sm" data-edit="${meme.id}">Quick edit</button>` : ""}
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

  async function renderFeed(mode = "latest", page = 1, extras = {}) {
    feedMode = mode;
    feedPage = page;
    const windowParam = extras.window || "all";
    const title =
      mode === "trending"
        ? `Trending (${windowParam})`
        : mode === "following"
          ? "Following"
          : extras.tag
            ? `#${extras.tag}`
            : extras.q
              ? `Search: ${extras.q}`
              : "Meme stream";
    app.innerHTML = `
      <section class="hero compact">
        <p class="hero-brand">XMeme</p>
        <h1>${mode === "trending" ? "What’s catching fire" : "Post it. Share it. Make it viral."}</h1>
        <p class="hero-sub">Studio editor, tags, reactions, drafts, and share pages — all in one stream.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="#/create">Create meme</a>
          <a class="btn btn-ghost" href="#/trending">Trending</a>
          <a class="btn btn-ghost" href="#/following">Following</a>
          <button type="button" class="btn btn-ghost" id="random-btn">Random</button>
        </div>
        <form id="search-form" class="search-bar">
          <input name="q" placeholder="Search captions & tags" value="${escapeHtml(extras.q || "")}">
          <button class="btn btn-ghost" type="submit">Search</button>
        </form>
        ${
          mode === "trending"
            ? `<div class="chip-row">
                <a class="chip ${windowParam === "today" ? "active" : ""}" href="#/trending?window=today">Today</a>
                <a class="chip ${windowParam === "week" ? "active" : ""}" href="#/trending?window=week">Week</a>
                <a class="chip ${windowParam === "all" ? "active" : ""}" href="#/trending">All time</a>
              </div>`
            : `<div class="chip-row" id="collection-chips"><span class="muted">Collections loading…</span></div>`
        }
      </section>
      <section class="stream">
        <div class="stream-header">
          <h2>${escapeHtml(title)}</h2>
          <button type="button" class="btn btn-ghost btn-sm" id="refresh-btn">Refresh</button>
        </div>
        <div id="meme-grid" class="meme-grid"><p class="empty-state">Loading…</p></div>
        <div id="pager"></div>
      </section>`;

    document.getElementById("refresh-btn").onclick = () => renderFeed(mode, page, extras);
    document.getElementById("random-btn").onclick = async () => {
      const meme = await API.get("/memes/random");
      navigate(`/meme/${meme.id}`);
    };
    document.getElementById("search-form").onsubmit = (e) => {
      e.preventDefault();
      const q = new FormData(e.target).get("q");
      navigate(`/search?q=${encodeURIComponent(q)}`);
    };

    if (mode !== "trending") {
      API.get("/collections")
        .then((cols) => {
          const el = document.getElementById("collection-chips");
          if (!el) return;
          el.innerHTML = cols
            .map((c) => `<a class="chip" href="#/collection/${escapeHtml(c.slug)}">${escapeHtml(c.name)}</a>`)
            .join("");
        })
        .catch(() => {
          const el = document.getElementById("collection-chips");
          if (el) el.innerHTML = "";
        });
    }

    try {
      let path;
      if (mode === "trending") {
        path = `/memes/trending?page=${page}&page_size=${window.XMEME_CONFIG.pageSize}&window=${windowParam}`;
      } else if (mode === "following") {
        path = `/memes?page=${page}&page_size=${window.XMEME_CONFIG.pageSize}&following=true`;
      } else if (extras.tag) {
        path = `/memes?page=${page}&page_size=${window.XMEME_CONFIG.pageSize}&tag=${encodeURIComponent(extras.tag)}`;
      } else if (extras.q) {
        path = `/memes?page=${page}&page_size=${window.XMEME_CONFIG.pageSize}&q=${encodeURIComponent(extras.q)}`;
      } else if (extras.collection) {
        path = `/collections/${extras.collection}/memes?page=${page}&page_size=${window.XMEME_CONFIG.pageSize}`;
      } else {
        path = `/memes?page=${page}&page_size=${window.XMEME_CONFIG.pageSize}`;
      }
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
        renderFeed(mode, Number(btn.dataset.page), extras);
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

  async function renderCreate(editingMemeId = null) {
    await CreatePage.render(app, {
      currentUser,
      navigate,
      setStatus,
      escapeHtml,
      editingMemeId,
    });
  }

  function renderComments(comments, depth = 0) {
    return comments
      .map(
        (c) => `
      <article class="comment" style="margin-left:${depth * 16}px">
        <strong><a href="#/u/${escapeHtml(c.username)}">@${escapeHtml(c.username)}</a></strong>
        <p>${escapeHtml(c.body)}</p>
        ${
          currentUser
            ? `<button type="button" class="btn btn-ghost btn-sm" data-reply="${c.id}">Reply</button>`
            : ""
        }
        ${c.replies?.length ? renderComments(c.replies, depth + 1) : ""}
      </article>`
      )
      .join("");
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
      const canEdit = currentUser && (!meme.user_id || meme.user_id === currentUser.id);
      const reactions = ["😂", "🔥", "💀", "👀", "✨"];
      const media =
        meme.media_type === "video"
          ? `<video controls src="${escapeHtml(img)}"></video>`
          : `<img src="${escapeHtml(img)}" alt="${escapeHtml(meme.caption)}"
              onerror="this.onerror=null;this.src='images/invalid_url.jpg'">`;

      app.innerHTML = `
        <section class="detail-layout">
          <div class="panel detail-media">${media}</div>
          <div class="panel detail-info">
            <h1>${escapeHtml(meme.caption)}</h1>
            <p class="author">
              ${meme.username ? `<a href="#/u/${escapeHtml(meme.username)}">@${escapeHtml(meme.username)}</a>` : escapeHtml(author)}
            </p>
            <div class="card-meta">
              <span>${meme.like_count} likes</span>
              <span>${meme.comment_count} comments</span>
              <span>${meme.view_count} views</span>
              <span>${meme.share_count || 0} shares</span>
              <span>${meme.download_count || 0} downloads</span>
            </div>
            <div class="tag-row">${(meme.tags || []).map((t) => `<a class="tag" href="#/tag/${escapeHtml(t)}">#${escapeHtml(t)}</a>`).join(" ")}</div>
            <div class="reaction-row">
              ${reactions
                .map(
                  (e) =>
                    `<button type="button" class="chip ${(meme.my_reactions || []).includes(e) ? "active" : ""}" data-react="${e}">${e} ${(meme.reactions || []).find((r) => r.emoji === e)?.count || ""}</button>`
                )
                .join("")}
            </div>
            <div class="form-actions wrap">
              <button type="button" class="btn btn-primary" id="like-btn">${meme.liked_by_me ? "Unlike" : "Like"}</button>
              <button type="button" class="btn btn-ghost" id="copy-link">Copy link</button>
              <button type="button" class="btn btn-ghost" id="download-meme">Download</button>
              <a class="btn btn-ghost" target="_blank" rel="noopener" href="${escapeHtml(shareApi)}">Share page</a>
              <a class="btn btn-ghost" target="_blank" rel="noopener"
                href="https://twitter.com/intent/tweet?text=${encodeURIComponent(meme.caption)}&url=${encodeURIComponent(shareApi)}">Share on X</a>
              ${canEdit ? `<a class="btn btn-ghost" href="#/edit/${meme.id}">Open in studio</a>` : ""}
              ${canEdit ? `<button type="button" class="btn btn-ghost" id="edit-detail">Quick edit</button>` : ""}
              ${canEdit ? `<button type="button" class="btn btn-ghost danger" id="delete-detail">Delete</button>` : ""}
              ${currentUser ? `<button type="button" class="btn btn-ghost" id="report-btn">Report</button>` : ""}
            </div>
            <p class="form-status" id="share-status"></p>
            <p class="muted">Embed: <code>&lt;a href="${escapeHtml(shareApp)}"&gt;${escapeHtml(meme.caption)}&lt;/a&gt;</code></p>
            <div id="analytics" class="muted"></div>

            <h3>Comments</h3>
            <div id="comments" class="comments">
              ${comments.length ? renderComments(comments) : `<p class="muted">No comments yet.</p>`}
            </div>
            ${
              currentUser
                ? `<form id="comment-form" class="stack">
                    <input type="hidden" name="parent_id" id="reply-parent" value="">
                    <label><span id="reply-label">Add a comment</span><input name="body" maxlength="500" required placeholder="Say something…"></label>
                    <button class="btn btn-primary" type="submit">Comment</button>
                    <p class="form-status" id="comment-status"></p>
                  </form>`
                : `<p class="muted"><a href="#/login">Log in</a> to comment.</p>`
            }
          </div>
        </section>`;

      if (canEdit) {
        API.get(`/memes/${id}/analytics`)
          .then((a) => {
            document.getElementById("analytics").textContent =
              `Analytics: ${a.views} views · ${a.shares} shares · ${a.downloads} downloads · CTR ${a.ctr}%`;
          })
          .catch(() => {});
      }

      document.querySelector(".reaction-row")?.addEventListener("click", async (e) => {
        const btn = e.target.closest("[data-react]");
        if (!btn) return;
        if (!currentUser) return navigate("/login");
        await API.post(`/memes/${id}/react?emoji=${encodeURIComponent(btn.dataset.react)}`, {});
        renderMeme(id);
      });

      document.getElementById("like-btn").onclick = async () => {
        if (!currentUser) return navigate("/login");
        await API.post(`/memes/${id}/like`, {});
        renderMeme(id);
      };
      document.getElementById("copy-link").onclick = async () => {
        await navigator.clipboard.writeText(shareApp);
        await API.post(`/memes/${id}/share`, {});
        setStatus(document.getElementById("share-status"), "Link copied.", "success");
      };
      document.getElementById("download-meme").onclick = async () => {
        const res = await API.post(`/memes/${id}/download`, {});
        const a = document.createElement("a");
        a.href = API.resolveUrl(res.url);
        a.download = `xmeme-${id}`;
        a.target = "_blank";
        a.click();
      };
      document.getElementById("report-btn")?.addEventListener("click", async () => {
        const reason = prompt("Why are you reporting this meme?");
        if (!reason) return;
        await API.post("/reports", { meme_id: Number(id), reason });
        setStatus(document.getElementById("share-status"), "Report submitted.", "success");
      });
      document.getElementById("edit-detail")?.addEventListener("click", () => openEdit(Number(id)));
      document.getElementById("delete-detail")?.addEventListener("click", async () => {
        if (!confirm("Delete this meme?")) return;
        await API.delete(`/memes/${id}`);
        navigate("/");
      });
      document.getElementById("comments")?.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-reply]");
        if (!btn) return;
        document.getElementById("reply-parent").value = btn.dataset.reply;
        document.getElementById("reply-label").textContent = `Reply to #${btn.dataset.reply}`;
      });
      const commentForm = document.getElementById("comment-form");
      if (commentForm) {
        commentForm.onsubmit = async (e) => {
          e.preventDefault();
          const fd = new FormData(commentForm);
          try {
            await API.post(`/memes/${id}/comments`, {
              body: fd.get("body"),
              parent_id: fd.get("parent_id") ? Number(fd.get("parent_id")) : null,
            });
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
      let draftsHtml = "";
      if (isMe) {
        const drafts = await API.get(
          `/users/${username}/memes?page=1&page_size=12&status=draft`
        );
        if (drafts.items?.length) {
          draftsHtml = `
            <section class="stream">
              <h2>Drafts</h2>
              <div class="meme-grid">${drafts.items.map(memeCard).join("")}</div>
            </section>`;
        }
      }
      app.innerHTML = `
        <section class="panel profile-head">
          <h1>@${escapeHtml(profile.username)}</h1>
          <p>${escapeHtml(profile.bio || "No bio yet.")}</p>
          <div class="card-meta">
            <span>${profile.meme_count} memes</span>
            <span>${profile.like_count} likes received</span>
            <span>${profile.follower_count || 0} followers</span>
            <span>${profile.following_count || 0} following</span>
            ${profile.is_private ? "<span>Private</span>" : ""}
          </div>
          ${
            currentUser && !isMe
              ? `<button type="button" class="btn btn-primary btn-sm" id="follow-btn">${profile.followed_by_me ? "Unfollow" : "Follow"}</button>`
              : ""
          }
          ${
            isMe
              ? `<form id="bio-form" class="stack">
                  <label><span>Update bio</span><input name="bio" maxlength="280" value="${escapeHtml(profile.bio || "")}"></label>
                  <label class="inline"><input type="checkbox" name="is_private" ${profile.is_private ? "checked" : ""}> Private profile</label>
                  <button class="btn btn-ghost btn-sm" type="submit">Save profile</button>
                  <p class="form-status" id="bio-status"></p>
                </form>`
              : ""
          }
        </section>
        ${draftsHtml}
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
      document.querySelectorAll(".meme-grid").forEach(bindCardActions);
      document.getElementById("follow-btn")?.addEventListener("click", async () => {
        await API.post(`/users/${username}/follow`, {});
        renderProfile(username);
      });
      const bioForm = document.getElementById("bio-form");
      if (bioForm) {
        bioForm.onsubmit = async (e) => {
          e.preventDefault();
          const fd = new FormData(bioForm);
          try {
            await API.patch("/auth/me", {
              bio: fd.get("bio"),
              is_private: fd.get("is_private") === "on",
            });
            setStatus(document.getElementById("bio-status"), "Saved.", "success");
            await refreshUser();
            renderProfile(username);
          } catch (err) {
            setStatus(document.getElementById("bio-status"), err.message, "error");
          }
        };
      }
    } catch (err) {
      app.innerHTML = `<section class="panel"><p class="empty-state">${escapeHtml(err.message)}</p></section>`;
    }
  }

  async function renderNotifications() {
    if (!currentUser) return navigate("/login");
    const rows = await API.get("/notifications");
    app.innerHTML = `
      <section class="panel">
        <div class="stream-header">
          <h2>Notifications</h2>
          <button type="button" class="btn btn-ghost btn-sm" id="mark-read">Mark all read</button>
        </div>
        <div class="comments">
          ${
            rows.length
              ? rows
                  .map(
                    (n) => `
            <article class="comment ${n.is_read ? "" : "unread"}">
              <p>${escapeHtml(n.message)}</p>
              <p class="muted">${n.meme_id ? `<a href="#/meme/${n.meme_id}">View meme</a>` : ""}</p>
            </article>`
                  )
                  .join("")
              : `<p class="muted">You're all caught up.</p>`
          }
        </div>
      </section>`;
    document.getElementById("mark-read").onclick = async () => {
      await API.post("/notifications/read", {});
      renderNotifications();
    };
  }

  async function route() {
    const { parts, params } = parseRoute();
    const [head, id] = parts;
    if (!head) return renderFeed("latest", 1);
    if (head === "trending") return renderFeed("trending", 1, { window: params.window || "all" });
    if (head === "following") return renderFeed("following", 1);
    if (head === "search") return renderFeed("latest", 1, { q: params.q || "" });
    if (head === "tag" && id) return renderFeed("latest", 1, { tag: id });
    if (head === "collection" && id) return renderFeed("latest", 1, { collection: id });
    if (head === "create") return renderCreate();
    if (head === "edit" && id) return renderCreate(Number(id));
    if (head === "notifications") return renderNotifications();
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

  document.getElementById("theme-btn").onclick = () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("xmeme_theme", next);
  };
  const savedTheme = localStorage.getItem("xmeme_theme");
  if (savedTheme) document.documentElement.dataset.theme = savedTheme;

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
