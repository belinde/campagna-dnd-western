(function () {
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

  initSalientMediaCards();

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
})();
