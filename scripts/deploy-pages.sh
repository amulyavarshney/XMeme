#!/usr/bin/env bash
# Deploy frontend to origin/gh-pages (XMeme repo only — not amulyavarshney.github.io).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE="$(mktemp -d)"
trap 'rm -rf "$SITE"' EXIT

cp -R "$ROOT/frontend/api.js" "$ROOT/frontend/app.js" "$ROOT/frontend/create-page.js" \
  "$ROOT/frontend/editor.js" "$ROOT/frontend/embed.js" "$ROOT/frontend/style.css" \
  "$ROOT/frontend/images" "$SITE/"

python3 - <<PY
from pathlib import Path
root = Path("$ROOT")
site = Path("$SITE")
html = (root / "frontend/index.html").read_text()
if "<base " not in html:
    html = html.replace("<head>", '<head>\n  <base href="/XMeme/">', 1)
(site / "index.html").write_text(html)
(site / "config.js").write_text("""window.XMEME_CONFIG = {
  apiBase: window.XMEME_API_BASE || "http://localhost:8081",
  pageSize: 12,
  siteBase: "/XMeme",
};
""")
(site / ".nojekyll").write_text("")
print("Built site in", site)
PY

cd "$ROOT"
CURRENT="$(git branch --show-current)"
git fetch origin
git branch -D gh-pages 2>/dev/null || true
git checkout --orphan gh-pages
git rm -rf --quiet . 2>/dev/null || true
cp -R "$SITE"/. .
git add -A
git -c user.name='amulyavarshney' -c user.email='amulyavarshney7@gmail.com' \
  commit -m "Deploy XMeme frontend to GitHub Pages"
git push -u origin gh-pages --force
git checkout "$CURRENT"
git branch -D gh-pages
echo "Pushed gh-pages."
echo "GitHub → Settings → Pages → Deploy from branch: gh-pages / (root)"
echo "Site: https://amulyavarshney.github.io/XMeme/"
