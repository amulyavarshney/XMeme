#!/bin/sh
set -e

API_BASE="${XMEME_API_BASE:-/api}"
PAGE_SIZE="${XMEME_PAGE_SIZE:-12}"

cat > /usr/share/nginx/html/config.js <<EOF
window.XMEME_CONFIG = {
  apiBase: "${API_BASE}",
  pageSize: ${PAGE_SIZE},
};
EOF

echo "Wrote frontend config.js with apiBase=${API_BASE}"
