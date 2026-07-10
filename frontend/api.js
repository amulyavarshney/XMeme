const API = {
  get base() {
    return window.XMEME_CONFIG.apiBase;
  },

  token() {
    return localStorage.getItem("xmeme_token");
  },

  setToken(token) {
    if (token) localStorage.setItem("xmeme_token", token);
    else localStorage.removeItem("xmeme_token");
  },

  headers(json = true) {
    const h = {};
    if (json) h["Content-Type"] = "application/json";
    const token = this.token();
    if (token) h.Authorization = `Bearer ${token}`;
    return h;
  },

  async request(path, options = {}) {
    const res = await fetch(`${this.base}${path}`, options);
    if (res.status === 204) return null;
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }
    if (!res.ok) {
      const detail = data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((d) => d.msg || d).join(", ")
        : detail || res.statusText || "Request failed";
      const err = new Error(message);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  },

  get(path) {
    return this.request(path, { headers: this.headers(false) });
  },

  post(path, body) {
    return this.request(path, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(body),
    });
  },

  patch(path, body) {
    return this.request(path, {
      method: "PATCH",
      headers: this.headers(),
      body: JSON.stringify(body),
    });
  },

  delete(path) {
    return this.request(path, {
      method: "DELETE",
      headers: this.headers(false),
    });
  },

  async login(username, password) {
    const body = new URLSearchParams({ username, password });
    const res = await fetch(`${this.base}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Login failed");
    this.setToken(data.access_token);
    return data;
  },

  async upload(file) {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${this.base}/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${this.token()}` },
      body: form,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");
    return data;
  },

  resolveUrl(url) {
    if (!url) return "";
    if (url.startsWith("http") || url.startsWith("data:")) return url;
    if (url.startsWith("/")) return `${this.base}${url}`;
    return url;
  },
};
