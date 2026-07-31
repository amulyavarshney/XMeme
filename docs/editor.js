const MemeEditor = (() => {
  const FONTS = [
    "Impact, Haettenschweiler, 'Arial Black', sans-serif",
    "Arial Black, Gadget, sans-serif",
    "'Comic Sans MS', 'Comic Sans', cursive",
    "Georgia, serif",
    "'Courier New', monospace",
    "Outfit, system-ui, sans-serif",
  ];

  const STICKERS = ["😂", "🔥", "💀", "👀", "✨", "💯", "🤡", "😭", "😎", "🧠", "📈", "📉", "🫡", "🫶", "⚡"];

  const FILTER_PRESETS = {
    none: { brightness: 100, contrast: 100, blur: 0, saturate: 100, sepia: 0 },
    vivid: { brightness: 105, contrast: 125, blur: 0, saturate: 140, sepia: 0 },
    noir: { brightness: 95, contrast: 130, blur: 0, saturate: 0, sepia: 0 },
    warm: { brightness: 108, contrast: 110, blur: 0, saturate: 120, sepia: 25 },
    cold: { brightness: 100, contrast: 105, blur: 0, saturate: 80, sepia: 0 },
    soft: { brightness: 110, contrast: 90, blur: 1.2, saturate: 95, sepia: 0 },
  };

  let canvas;
  let ctx;
  let image = null;
  let imageUrl = "";
  let layers = [];
  let selectedId = null;
  let filters = { ...FILTER_PRESETS.none, preset: "none" };
  let crop = null; // { x, y, w, h } normalized 0-1
  let history = [];
  let future = [];
  let interaction = null; // { mode, id, start, orig }
  let onChange = null;
  let uid = 1;

  function init(canvasEl, changeCb) {
    canvas = canvasEl;
    ctx = canvas.getContext("2d");
    onChange = changeCb || null;
    canvas.width = 800;
    canvas.height = 800;
    if (!layers.length) resetLayersDefault();
    bind();
    draw();
    pushHistory(true);
  }

  function bind() {
    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", onPointerUp);
    canvas.addEventListener("pointercancel", onPointerUp);
    canvas.addEventListener("wheel", onWheel, { passive: false });
  }

  function notify() {
    if (onChange) onChange(getState());
  }

  function nextId() {
    return `L${uid++}`;
  }

  function defaultText(partial = {}) {
    return {
      id: nextId(),
      type: "text",
      text: "NEW TEXT",
      x: 0.5,
      y: 0.5,
      scale: 1,
      rotation: 0,
      fontFamily: FONTS[0],
      fontSize: 42,
      color: "#ffffff",
      outlineColor: "#000000",
      outlineWidth: 4,
      shadow: true,
      allCaps: true,
      align: "center",
      locked: false,
      ...partial,
    };
  }

  function defaultSticker(emoji, partial = {}) {
    return {
      id: nextId(),
      type: "sticker",
      emoji,
      x: 0.5,
      y: 0.5,
      scale: 1,
      rotation: 0,
      fontSize: 64,
      locked: false,
      ...partial,
    };
  }

  function resetLayersDefault() {
    layers = [
      defaultText({ text: "TOP TEXT", y: 0.1, id: nextId() }),
      defaultText({ text: "BOTTOM TEXT", y: 0.9, id: nextId() }),
    ];
    selectedId = layers[0]?.id || null;
  }

  function cloneState() {
    return JSON.parse(
      JSON.stringify({
        imageUrl,
        layers,
        selectedId,
        filters,
        crop,
      })
    );
  }

  function pushHistory(silent = false) {
    history.push(cloneState());
    if (history.length > 50) history.shift();
    future = [];
    if (!silent) notify();
  }

  function restore(snapshot) {
    imageUrl = snapshot.imageUrl || "";
    layers = snapshot.layers || [];
    selectedId = snapshot.selectedId;
    filters = snapshot.filters || { ...FILTER_PRESETS.none, preset: "none" };
    crop = snapshot.crop;
    if (imageUrl && (!image || image.src !== imageUrl)) {
      return loadImage(imageUrl, true).then(() => {
        draw();
        notify();
      });
    }
    draw();
    notify();
    return Promise.resolve();
  }

  function undo() {
    if (history.length <= 1) return;
    future.push(history.pop());
    return restore(history[history.length - 1]);
  }

  function redo() {
    if (!future.length) return;
    const snap = future.pop();
    history.push(snap);
    return restore(snap);
  }

  function reset(clearImage = false) {
    if (clearImage) {
      image = null;
      imageUrl = "";
      canvas.width = 800;
      canvas.height = 800;
    }
    layers = [];
    resetLayersDefault();
    filters = { ...FILTER_PRESETS.none, preset: "none" };
    crop = null;
    pushHistory();
    draw();
  }

  function getState() {
    return {
      imageUrl,
      layers: JSON.parse(JSON.stringify(layers)),
      selectedId,
      filters: { ...filters },
      crop: crop ? { ...crop } : null,
      fonts: FONTS,
      stickers: STICKERS,
      filterPresets: Object.keys(FILTER_PRESETS),
      canUndo: history.length > 1,
      canRedo: future.length > 0,
    };
  }

  function loadState(state, skipHistory = false) {
    if (!state) return Promise.resolve();
    imageUrl = state.imageUrl || "";
    layers = state.layers || [];
    selectedId = state.selectedId || layers[0]?.id || null;
    filters = { ...FILTER_PRESETS.none, ...(state.filters || {}) };
    crop = state.crop || null;
    const p = imageUrl ? loadImage(imageUrl, true) : Promise.resolve();
    return p.then(() => {
      if (!skipHistory) pushHistory(true);
      draw();
      notify();
    });
  }

  function selected() {
    return layers.find((l) => l.id === selectedId) || null;
  }

  function select(id) {
    selectedId = id;
    draw();
    notify();
  }

  function updateSelected(patch, record = true) {
    const layer = selected();
    if (!layer || layer.locked) return;
    Object.assign(layer, patch);
    draw();
    if (record) pushHistory();
    else notify();
  }

  function addText() {
    const layer = defaultText({ y: 0.35 + Math.random() * 0.3 });
    layers.push(layer);
    selectedId = layer.id;
    pushHistory();
    draw();
  }

  function addSticker(emoji) {
    const layer = defaultSticker(emoji, {
      x: 0.3 + Math.random() * 0.4,
      y: 0.3 + Math.random() * 0.4,
    });
    layers.push(layer);
    selectedId = layer.id;
    pushHistory();
    draw();
  }

  function removeSelected() {
    if (!selectedId) return;
    const layer = selected();
    if (layer?.locked) return;
    layers = layers.filter((l) => l.id !== selectedId);
    selectedId = layers[layers.length - 1]?.id || null;
    pushHistory();
    draw();
  }

  function bringForward() {
    const i = layers.findIndex((l) => l.id === selectedId);
    if (i < 0 || i === layers.length - 1) return;
    [layers[i], layers[i + 1]] = [layers[i + 1], layers[i]];
    pushHistory();
    draw();
  }

  function sendBackward() {
    const i = layers.findIndex((l) => l.id === selectedId);
    if (i <= 0) return;
    [layers[i], layers[i - 1]] = [layers[i - 1], layers[i]];
    pushHistory();
    draw();
  }

  function toggleLock() {
    const layer = selected();
    if (!layer) return;
    layer.locked = !layer.locked;
    pushHistory();
    draw();
  }

  function setFilters(patch, record = true) {
    Object.assign(filters, patch);
    if (patch.preset && FILTER_PRESETS[patch.preset]) {
      Object.assign(filters, FILTER_PRESETS[patch.preset], { preset: patch.preset });
    }
    draw();
    if (record) pushHistory();
    else notify();
  }

  function setCrop(next) {
    crop = next;
    pushHistory();
    draw();
  }

  function clearCrop() {
    crop = null;
    pushHistory();
    draw();
  }

  function applyFilterCss() {
    return `brightness(${filters.brightness}%) contrast(${filters.contrast}%) saturate(${filters.saturate}%) sepia(${filters.sepia}%) blur(${filters.blur}px)`;
  }

  function loadImage(src, keepLayers = false) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        image = img;
        imageUrl = src;
        const max = 900;
        const scale = Math.min(max / img.width, max / img.height, 1);
        canvas.width = Math.max(1, Math.round(img.width * scale));
        canvas.height = Math.max(1, Math.round(img.height * scale));
        if (!keepLayers) {
          resetLayersDefault();
          filters = { ...FILTER_PRESETS.none, preset: "none" };
          crop = null;
          pushHistory();
        }
        draw();
        notify();
        resolve();
      };
      img.onerror = () => reject(new Error("Could not load image (CORS or invalid URL)"));
      img.src = src;
    });
  }

  function displayText(layer) {
    return layer.allCaps ? String(layer.text || "").toUpperCase() : String(layer.text || "");
  }

  function wrapText(text, font, maxWidth) {
    ctx.font = font;
    const words = text.split(/\s+/);
    const lines = [];
    let current = "";
    words.forEach((word) => {
      const test = current ? `${current} ${word}` : word;
      if (ctx.measureText(test).width > maxWidth && current) {
        lines.push(current);
        current = word;
      } else current = test;
    });
    if (current) lines.push(current);
    return lines.length ? lines : [""];
  }

  function drawLayer(layer, withHandles = false) {
    const x = layer.x * canvas.width;
    const y = layer.y * canvas.height;
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate((layer.rotation || 0) * Math.PI / 180);
    ctx.scale(layer.scale || 1, layer.scale || 1);

    if (layer.type === "sticker") {
      const size = layer.fontSize || 64;
      ctx.font = `${size}px serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(layer.emoji || "⭐", 0, 0);
    } else {
      const size = layer.fontSize || 42;
      const font = `bold ${size}px ${layer.fontFamily || FONTS[0]}`;
      ctx.font = font;
      ctx.textAlign = layer.align || "center";
      ctx.textBaseline = "middle";
      ctx.lineJoin = "round";
      ctx.lineWidth = layer.outlineWidth ?? 4;
      ctx.strokeStyle = layer.outlineColor || "#000";
      ctx.fillStyle = layer.color || "#fff";
      if (layer.shadow) {
        ctx.shadowColor = "rgba(0,0,0,0.55)";
        ctx.shadowBlur = 6;
        ctx.shadowOffsetX = 2;
        ctx.shadowOffsetY = 2;
      }
      const lines = wrapText(displayText(layer), font, canvas.width * 0.85);
      const lineHeight = size * 1.1;
      const startY = -((lines.length - 1) * lineHeight) / 2;
      lines.forEach((line, i) => {
        const ly = startY + i * lineHeight;
        if ((layer.outlineWidth ?? 4) > 0) ctx.strokeText(line, 0, ly);
        ctx.fillText(line, 0, ly);
      });
    }

    if (withHandles && layer.id === selectedId) {
      ctx.shadowColor = "transparent";
      ctx.strokeStyle = "#0f9f8a";
      ctx.lineWidth = 2 / (layer.scale || 1);
      ctx.setLineDash([6, 4]);
      const box = 70;
      ctx.strokeRect(-box, -box * 0.55, box * 2, box * 1.1);
      ctx.setLineDash([]);
      ctx.fillStyle = "#0f9f8a";
      ctx.beginPath();
      ctx.arc(box, -box * 0.55, 7 / (layer.scale || 1), 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  function draw() {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.filter = applyFilterCss();

    if (image) {
      if (crop) {
        const sx = crop.x * image.naturalWidth;
        const sy = crop.y * image.naturalHeight;
        const sw = crop.w * image.naturalWidth;
        const sh = crop.h * image.naturalHeight;
        ctx.drawImage(image, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
      } else {
        ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
      }
    } else {
      ctx.filter = "none";
      ctx.fillStyle = "#1a1f2b";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#6b7280";
      ctx.font = "22px Outfit, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Load a template or upload an image", canvas.width / 2, canvas.height / 2);
    }
    ctx.restore();

    layers.forEach((layer) => drawLayer(layer, true));
  }

  function pointerPos(e) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) / rect.width,
      y: (e.clientY - rect.top) / rect.height,
      px: e.clientX - rect.left,
      py: e.clientY - rect.top,
    };
  }

  function hitTest(pos) {
    for (let i = layers.length - 1; i >= 0; i--) {
      const layer = layers[i];
      const dx = (layer.x - pos.x) * canvas.width;
      const dy = (layer.y - pos.y) * canvas.height;
      const hitR = 48 * (layer.scale || 1);
      if (Math.hypot(dx, dy) <= hitR) return layer;
    }
    return null;
  }

  function onPointerDown(e) {
    const pos = pointerPos(e);
    const layer = hitTest(pos);
    if (!layer) {
      selectedId = null;
      draw();
      notify();
      return;
    }
    selectedId = layer.id;
    if (layer.locked) {
      draw();
      notify();
      return;
    }
    const mode = e.shiftKey ? "rotate" : e.altKey ? "scale" : "drag";
    interaction = {
      mode,
      id: layer.id,
      start: pos,
      orig: { x: layer.x, y: layer.y, rotation: layer.rotation || 0, scale: layer.scale || 1 },
    };
    canvas.setPointerCapture(e.pointerId);
    draw();
    notify();
  }

  function onPointerMove(e) {
    if (!interaction) return;
    const layer = layers.find((l) => l.id === interaction.id);
    if (!layer || layer.locked) return;
    const pos = pointerPos(e);
    if (interaction.mode === "drag") {
      layer.x = Math.min(0.98, Math.max(0.02, interaction.orig.x + (pos.x - interaction.start.x)));
      layer.y = Math.min(0.98, Math.max(0.02, interaction.orig.y + (pos.y - interaction.start.y)));
    } else if (interaction.mode === "rotate") {
      const a0 = Math.atan2(interaction.start.y - interaction.orig.y, interaction.start.x - interaction.orig.x);
      const a1 = Math.atan2(pos.y - interaction.orig.y, pos.x - interaction.orig.x);
      layer.rotation = interaction.orig.rotation + ((a1 - a0) * 180) / Math.PI;
    } else if (interaction.mode === "scale") {
      const d0 = Math.hypot(interaction.start.x - interaction.orig.x, interaction.start.y - interaction.orig.y) || 0.01;
      const d1 = Math.hypot(pos.x - interaction.orig.x, pos.y - interaction.orig.y);
      layer.scale = Math.min(4, Math.max(0.3, interaction.orig.scale * (d1 / d0)));
    }
    draw();
  }

  function onPointerUp() {
    if (interaction) {
      interaction = null;
      pushHistory();
    }
  }

  function onWheel(e) {
    const layer = selected();
    if (!layer || layer.locked) return;
    e.preventDefault();
    layer.scale = Math.min(4, Math.max(0.3, (layer.scale || 1) * (e.deltaY < 0 ? 1.05 : 0.95)));
    draw();
  }

  function toBlob(type = "image/png", quality = 0.92) {
    // redraw without handles
    const prev = selectedId;
    selectedId = null;
    draw();
    return new Promise((resolve) => {
      canvas.toBlob(
        (blob) => {
          selectedId = prev;
          draw();
          resolve(blob);
        },
        type,
        quality
      );
    });
  }

  function download(filename = "xmeme.png") {
    return toBlob().then((blob) => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    });
  }

  return {
    init,
    loadImage,
    loadState,
    getState,
    select,
    updateSelected,
    addText,
    addSticker,
    removeSelected,
    bringForward,
    sendBackward,
    toggleLock,
    setFilters,
    setCrop,
    clearCrop,
    undo,
    redo,
    reset,
    toBlob,
    download,
    draw,
    FONTS,
    STICKERS,
    FILTER_PRESETS,
  };
})();
