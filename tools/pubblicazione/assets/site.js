(function () {
  const PWA_THEME_COLOR = "#12100d";
  const INTERACTIVE_ANCESTOR = "a, button, label, [role='button']";

  function initPwaSystemChrome() {
    const isInstalled =
      window.matchMedia("(display-mode: standalone)").matches ||
      window.matchMedia("(display-mode: fullscreen)").matches ||
      window.navigator.standalone === true;
    if (!isInstalled) {
      return;
    }

    document.documentElement.classList.add("pwa-installed");

    let meta = document.querySelector('meta[name="theme-color"]:not([media])');
    if (!meta) {
      meta = document.createElement("meta");
      meta.name = "theme-color";
      document.head.appendChild(meta);
    }
    meta.content = PWA_THEME_COLOR;
  }

  function initSalientMediaCards() {
    document.querySelectorAll(".salient-media-card__media img").forEach((img) => {
      const card = img.closest(".salient-media-card");
      if (!card) {
        return;
      }

      function applyOrientation() {
        if (!img.naturalWidth) {
          return;
        }
        const landscape = img.naturalWidth >= img.naturalHeight;
        card.classList.toggle("salient-media-card--landscape", landscape);
        card.classList.toggle("salient-media-card--portrait", !landscape);
      }

      if (img.complete) {
        applyOrientation();
      } else {
        img.addEventListener("load", applyOrientation, { once: true });
      }
    });
  }

  function isInteractiveContext(node) {
    return !!node.closest(INTERACTIVE_ANCESTOR);
  }

  function initImageLightbox() {
    document.querySelectorAll(".salient-media-card__media").forEach((media) => {
      if (!isInteractiveContext(media)) {
        media.classList.add("card-media-zoomable");
      }
    });

    const mediaNodes = document.querySelectorAll(".card-media-zoomable");
    if (!mediaNodes.length) {
      return;
    }

    let overlay = null;
    let viewport = null;
    let transformEl = null;
    let lightboxImg = null;
    let closeBtn = null;
    let lastFocused = null;

    let scale = 1;
    let translateX = 0;
    let translateY = 0;
    const minScale = 1;
    const maxScale = 5;

    let activePointers = new Map();
    let pinchStartDistance = 0;
    let pinchStartScale = 1;
    let panStartX = 0;
    let panStartY = 0;
    let panOriginX = 0;
    let panOriginY = 0;
    let lastTapTime = 0;

    function ensureOverlay() {
      if (overlay) {
        return;
      }
      overlay = document.createElement("div");
      overlay.className = "image-lightbox";
      overlay.hidden = true;
      overlay.setAttribute("role", "dialog");
      overlay.setAttribute("aria-modal", "true");
      overlay.innerHTML =
        '<button type="button" class="image-lightbox__close" aria-label="Chiudi immagine">×</button>' +
        '<div class="image-lightbox__viewport">' +
        '<div class="image-lightbox__transform">' +
        '<img class="image-lightbox__img" alt="" decoding="async">' +
        "</div>" +
        "</div>" +
        "</div>";
      document.body.appendChild(overlay);
      closeBtn = overlay.querySelector(".image-lightbox__close");
      viewport = overlay.querySelector(".image-lightbox__viewport");
      transformEl = overlay.querySelector(".image-lightbox__transform");
      lightboxImg = overlay.querySelector(".image-lightbox__img");

      closeBtn.addEventListener("click", closeLightbox);
      overlay.addEventListener("click", (event) => {
        if (event.target === overlay || event.target === viewport) {
          closeLightbox();
        }
      });
      document.addEventListener("keydown", onDocumentKeydown);

      viewport.addEventListener(
        "wheel",
        (event) => {
          if (overlay.hidden) {
            return;
          }
          event.preventDefault();
          const delta = event.deltaY < 0 ? 1.12 : 1 / 1.12;
          setScale(clamp(scale * delta, minScale, maxScale), event.clientX, event.clientY);
        },
        { passive: false }
      );

      viewport.addEventListener("pointerdown", onPointerDown);
      viewport.addEventListener("pointermove", onPointerMove);
      viewport.addEventListener("pointerup", onPointerUp);
      viewport.addEventListener("pointercancel", onPointerUp);

      viewport.addEventListener(
        "pointerup",
        (event) => {
          if (overlay.hidden || activePointers.size > 0) {
            return;
          }
          const now = Date.now();
          if (now - lastTapTime < 320) {
            if (scale > minScale * 1.15) {
              resetTransform();
            } else {
              setScale(2.5, event.clientX, event.clientY);
            }
            lastTapTime = 0;
            return;
          }
          lastTapTime = now;
        },
        { passive: true }
      );
    }

    function clamp(value, low, high) {
      return Math.min(high, Math.max(low, value));
    }

    function applyTransform() {
      transformEl.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
    }

    function resetTransform() {
      scale = 1;
      translateX = 0;
      translateY = 0;
      applyTransform();
    }

    function clampPan() {
      if (scale <= minScale + 0.001) {
        translateX = 0;
        translateY = 0;
        return;
      }
      const view = viewport.getBoundingClientRect();
      const box = transformEl.getBoundingClientRect();
      const maxX = Math.max(0, (box.width - view.width) / 2);
      const maxY = Math.max(0, (box.height - view.height) / 2);
      translateX = clamp(translateX, -maxX, maxX);
      translateY = clamp(translateY, -maxY, maxY);
    }

    function setScale(nextScale, focalX, focalY) {
      const prevScale = scale;
      scale = clamp(nextScale, minScale, maxScale);
      if (focalX != null && focalY != null && prevScale !== scale) {
        const rect = viewport.getBoundingClientRect();
        const cx = focalX - (rect.left + rect.width / 2);
        const cy = focalY - (rect.top + rect.height / 2);
        const ratio = scale / prevScale;
        translateX = cx - (cx - translateX) * ratio;
        translateY = cy - (cy - translateY) * ratio;
      }
      if (scale <= minScale) {
        translateX = 0;
        translateY = 0;
        scale = minScale;
      } else {
        clampPan();
      }
      applyTransform();
    }

    function pointerDistance(a, b) {
      return Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
    }

    function onPointerDown(event) {
      if (overlay.hidden) {
        return;
      }
      viewport.setPointerCapture(event.pointerId);
      activePointers.set(event.pointerId, event);
      if (activePointers.size === 2) {
        const pts = [...activePointers.values()];
        pinchStartDistance = pointerDistance(pts[0], pts[1]);
        pinchStartScale = scale;
      } else if (activePointers.size === 1 && scale > minScale) {
        panStartX = event.clientX;
        panStartY = event.clientY;
        panOriginX = translateX;
        panOriginY = translateY;
      }
    }

    function onPointerMove(event) {
      if (overlay.hidden || !activePointers.has(event.pointerId)) {
        return;
      }
      activePointers.set(event.pointerId, event);
      if (activePointers.size === 2) {
        event.preventDefault();
        const pts = [...activePointers.values()];
        const distance = pointerDistance(pts[0], pts[1]);
        if (pinchStartDistance > 0) {
          setScale(pinchStartScale * (distance / pinchStartDistance), null, null);
        }
        return;
      }
      if (activePointers.size === 1 && scale > minScale) {
        event.preventDefault();
        translateX = panOriginX + (event.clientX - panStartX);
        translateY = panOriginY + (event.clientY - panStartY);
        clampPan();
        applyTransform();
      }
    }

    function onPointerUp(event) {
      activePointers.delete(event.pointerId);
      if (activePointers.size < 2) {
        pinchStartDistance = 0;
      }
    }

    function onDocumentKeydown(event) {
      if (!overlay || overlay.hidden) {
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        closeLightbox();
      }
    }

    function openLightbox(sourceImg) {
      ensureOverlay();
      lastFocused = document.activeElement;
      const alt = sourceImg.getAttribute("alt") || "";
      lightboxImg.alt = alt;
      overlay.setAttribute("aria-label", alt || "Immagine ingrandita");
      resetTransform();
      activePointers.clear();
      lightboxImg.src = sourceImg.currentSrc || sourceImg.src;
      overlay.hidden = false;
      document.body.classList.add("image-lightbox-open");
      closeBtn.focus();
    }

    function closeLightbox() {
      if (!overlay || overlay.hidden) {
        return;
      }
      overlay.hidden = true;
      document.body.classList.remove("image-lightbox-open");
      lightboxImg.removeAttribute("src");
      resetTransform();
      activePointers.clear();
      if (lastFocused && typeof lastFocused.focus === "function") {
        lastFocused.focus();
      }
    }

    mediaNodes.forEach((media) => {
      if (isInteractiveContext(media)) {
        return;
      }
      const img = media.querySelector("img");
      if (!img || !img.src) {
        return;
      }

      media.setAttribute("role", "button");
      media.setAttribute("tabindex", "0");
      const alt = img.getAttribute("alt");
      media.setAttribute(
        "aria-label",
        alt && alt.trim() ? `Apri immagine: ${alt.trim()}` : "Apri immagine a schermo intero"
      );

      function openFromMedia() {
        openLightbox(img);
      }

      media.addEventListener("click", (event) => {
        event.preventDefault();
        openFromMedia();
      });

      media.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openFromMedia();
        }
      });
    });
  }

  function initPngHubFilters() {
    const hub = document.querySelector("[data-png-hub]");
    if (!hub) {
      return;
    }

    const searchInput = hub.querySelector("#png-hub-search");
    const regionSelect = hub.querySelector("#png-hub-region");
    const blocks = hub.querySelectorAll(".png-region-block");
    const emptyMessage = hub.querySelector(".png-hub-empty");

    function normalize(value) {
      return (value || "").trim().toLowerCase();
    }

    function applyFilters() {
      const query = normalize(searchInput && searchInput.value);
      const region = regionSelect ? regionSelect.value : "__all__";
      let anyVisible = false;

      blocks.forEach((block) => {
        const blockRegion = block.getAttribute("data-regione") || "";
        if (region && region !== "__all__" && blockRegion !== region) {
          block.hidden = true;
          return;
        }

        let blockHasVisible = false;
        block.querySelectorAll(".entity-card").forEach((card) => {
          const blob = card.getAttribute("data-search") || "";
          const match = !query || blob.includes(query);
          card.hidden = !match;
          if (match) {
            blockHasVisible = true;
          }
        });

        block.hidden = !blockHasVisible;
        if (blockHasVisible) {
          anyVisible = true;
        }
      });

      if (emptyMessage) {
        emptyMessage.hidden = anyVisible;
      }
    }

    let debounceTimer;
    if (searchInput) {
      searchInput.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(applyFilters, 150);
      });
    }
    if (regionSelect) {
      regionSelect.addEventListener("change", applyFilters);
    }
  }

  initPwaSystemChrome();
  initSalientMediaCards();
  initImageLightbox();
  initPngHubFilters();
})();
