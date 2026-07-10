const MemeEditor = (() => {
  let canvas;
  let ctx;
  let image = null;
  let texts = [
    { id: "top", value: "TOP TEXT", x: 0.5, y: 0.08, dragging: false },
    { id: "bottom", value: "BOTTOM TEXT", x: 0.5, y: 0.92, dragging: false },
  ];
  let dragTarget = null;
  let fontSize = 42;

  function init(canvasEl) {
    canvas = canvasEl;
    ctx = canvas.getContext("2d");
    canvas.width = 800;
    canvas.height = 800;
    draw();

    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", onPointerUp);
    canvas.addEventListener("pointerleave", onPointerUp);
  }

  function setTexts(top, bottom) {
    texts[0].value = top || "";
    texts[1].value = bottom || "";
    draw();
  }

  function setFontSize(size) {
    fontSize = size;
    draw();
  }

  function loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        image = img;
        const max = 800;
        const scale = Math.min(max / img.width, max / img.height, 1);
        canvas.width = Math.round(img.width * scale);
        canvas.height = Math.round(img.height * scale);
        texts[0].x = 0.5;
        texts[0].y = 0.08;
        texts[1].x = 0.5;
        texts[1].y = 0.92;
        draw();
        resolve();
      };
      img.onerror = () => reject(new Error("Could not load image (CORS or invalid URL)"));
      img.src = src;
    });
  }

  function drawText(item) {
    if (!item.value) return;
    const x = item.x * canvas.width;
    const y = item.y * canvas.height;
    const size = Math.max(18, Math.round(fontSize * (canvas.width / 800)));
    ctx.font = `bold ${size}px Impact, Haettenschweiler, "Arial Black", sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.lineJoin = "round";
    ctx.lineWidth = Math.max(3, size / 12);
    ctx.strokeStyle = "#000";
    ctx.fillStyle = "#fff";
    const lines = wrapText(item.value.toUpperCase(), canvas.width * 0.9);
    const lineHeight = size * 1.1;
    const startY = y - ((lines.length - 1) * lineHeight) / 2;
    lines.forEach((line, i) => {
      const ly = startY + i * lineHeight;
      ctx.strokeText(line, x, ly);
      ctx.fillText(line, x, ly);
    });
  }

  function wrapText(text, maxWidth) {
    const words = text.split(/\s+/);
    const lines = [];
    let current = "";
    words.forEach((word) => {
      const test = current ? `${current} ${word}` : word;
      if (ctx.measureText(test).width > maxWidth && current) {
        lines.push(current);
        current = word;
      } else {
        current = test;
      }
    });
    if (current) lines.push(current);
    return lines.length ? lines : [""];
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (image) {
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    } else {
      ctx.fillStyle = "#1a1f2b";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#6b7280";
      ctx.font = "24px Outfit, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Load a template or upload an image", canvas.width / 2, canvas.height / 2);
    }
    texts.forEach(drawText);
  }

  function pointerPos(e) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) / rect.width,
      y: (e.clientY - rect.top) / rect.height,
    };
  }

  function hitTest(pos) {
    return texts.find((t) => Math.hypot(t.x - pos.x, t.y - pos.y) < 0.08) || null;
  }

  function onPointerDown(e) {
    const pos = pointerPos(e);
    dragTarget = hitTest(pos);
    if (dragTarget) {
      canvas.setPointerCapture(e.pointerId);
    }
  }

  function onPointerMove(e) {
    if (!dragTarget) return;
    const pos = pointerPos(e);
    dragTarget.x = Math.min(0.95, Math.max(0.05, pos.x));
    dragTarget.y = Math.min(0.95, Math.max(0.05, pos.y));
    draw();
  }

  function onPointerUp() {
    dragTarget = null;
  }

  function toBlob() {
    return new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  }

  return { init, loadImage, setTexts, setFontSize, toBlob, draw };
})();
