(function () {
  const root = document.querySelector("[data-prompt-tool]");
  if (!root) {
    return;
  }

  const REGION_ORDER = [
    "La East Coast",
    "Gli Appalacchi",
    "Il Middle West",
    "Le Pianure del Sud",
    "La Frontiera",
    "Le Montagne Rocciose",
    "Le Terre Selvagge",
    "Itinerante",
    "Varie",
    "Altro",
  ];

  const statusEl = document.getElementById("prompt-status");
  const luoghiGrid = document.getElementById("prompt-luoghi-grid");
  const luoghiSearch = document.getElementById("prompt-luoghi-search");
  const luoghiRegion = document.getElementById("prompt-luoghi-region");
  const luoghiEmpty = document.getElementById("prompt-luoghi-empty");
  const pgGrid = document.getElementById("prompt-pg-grid");
  const pgSearch = document.getElementById("prompt-pg-search");
  const pgEmpty = document.getElementById("prompt-pg-empty");
  const pngRegions = document.getElementById("prompt-png-regions");
  const pngSearch = document.getElementById("prompt-png-search");
  const pngRegion = document.getElementById("prompt-png-region");
  const pngEmpty = document.getElementById("prompt-png-empty");
  const scenaInput = document.getElementById("prompt-scena");
  const generaBtn = document.getElementById("prompt-genera");
  const copiaTuttoBtn = document.getElementById("prompt-copia-tutto");
  const outputPanel = document.getElementById("prompt-output-panel");
  const outputEl = document.getElementById("prompt-output");

  let catalog = null;

  function setStatus(message, isError) {
    if (!statusEl) {
      return;
    }
    if (!message) {
      statusEl.hidden = true;
      statusEl.textContent = "";
      statusEl.classList.remove("prompt-tool-status--error");
      return;
    }
    statusEl.hidden = false;
    statusEl.textContent = message;
    statusEl.classList.toggle("prompt-tool-status--error", Boolean(isError));
  }

  function normalize(value) {
    return (value || "").trim().toLowerCase();
  }

  function isEmptyRefValue(value) {
    const trimmed = (value || "").trim();
    return !trimmed || trimmed === "_None._";
  }

  function dedupeLines(lines) {
    const seen = new Set();
    const out = [];
    for (const line of lines) {
      const key = line.trim().toLowerCase();
      if (!key || seen.has(key)) {
        continue;
      }
      seen.add(key);
      out.push(line.trim());
    }
    return out;
  }

  function bulletLines(values) {
    return dedupeLines(
      values
        .filter((v) => !isEmptyRefValue(v))
        .flatMap((v) =>
          v
            .split(/\n+/)
            .map((line) => line.replace(/^[-*]\s*/, "").trim())
            .filter(Boolean)
        )
    ).map((line) => `- ${line}`);
  }

  function regionSortIndex(region) {
    const key = (region || "").trim();
    const idx = REGION_ORDER.findIndex(
      (r) => r.toLowerCase() === key.toLowerCase()
    );
    return idx >= 0 ? idx : REGION_ORDER.length;
  }

  function sortByLabel(items) {
    return [...items].sort((a, b) =>
      (a.label || "").localeCompare(b.label || "", "it", { sensitivity: "base" })
    );
  }

  function uniqueRegions(items) {
    const regions = new Set();
    for (const item of items) {
      if (item.regione) {
        regions.add(item.regione);
      }
    }
    return [...regions].sort((a, b) => {
      const diff = regionSortIndex(a) - regionSortIndex(b);
      return diff !== 0 ? diff : a.localeCompare(b, "it", { sensitivity: "base" });
    });
  }

  function fillRegionSelect(selectEl, items) {
    if (!selectEl) {
      return;
    }
    const current = selectEl.value;
    selectEl.innerHTML = '<option value="__all__">Tutte</option>';
    for (const region of uniqueRegions(items)) {
      const opt = document.createElement("option");
      opt.value = region;
      opt.textContent = region;
      selectEl.appendChild(opt);
    }
    if ([...selectEl.options].some((opt) => opt.value === current)) {
      selectEl.value = current;
    }
  }

  function matchesFilters(item, query, region) {
    const blob = item.search || "";
    if (query && !blob.includes(query)) {
      return false;
    }
    if (region && region !== "__all__" && item.regione !== region) {
      return false;
    }
    return true;
  }

  function thumbMarkup(item) {
    if (item.thumbPath) {
      return `<img class="prompt-small-card-thumb" src="${item.thumbPath}" alt="" loading="lazy">`;
    }
    return '<span class="prompt-small-card-thumb prompt-small-card-thumb--placeholder" aria-hidden="true"></span>';
  }

  function createSmallCard(item, options) {
    const { inputType, inputName, portrait } = options;
    const label = document.createElement("label");
    label.className = "prompt-small-card";
    if (portrait) {
      label.classList.add("prompt-small-card--portrait");
    }
    label.dataset.search = item.search || "";
    if (item.regione) {
      label.dataset.regione = item.regione;
    }

    const input = document.createElement("input");
    input.type = inputType;
    input.name = inputName;
    input.value = item.id;
    input.className = "prompt-small-card-input";

    const inner = document.createElement("span");
    inner.className = "prompt-small-card-inner";
    inner.innerHTML = `${thumbMarkup(item)}<span class="prompt-small-card-body"><span class="prompt-small-card-title">${escapeHtml(
      item.label
    )}</span><span class="prompt-small-card-desc">${escapeHtml(
      item.description || item.subtitle || ""
    )}</span></span>`;

    label.appendChild(input);
    label.appendChild(inner);

    function syncSelected() {
      label.classList.toggle("prompt-small-card--selected", input.checked);
    }

    input.addEventListener("change", syncSelected);
    if (inputType === "radio") {
      input.addEventListener("click", () => {
        if (input.dataset.wasChecked === "true") {
          input.checked = false;
          input.dataset.wasChecked = "false";
          syncSelected();
        } else {
          const group = root.querySelectorAll(
            `input[name="${inputName}"]`
          );
          for (const peer of group) {
            peer.dataset.wasChecked = "false";
          }
          input.dataset.wasChecked = "true";
        }
      });
    }

    syncSelected();
    return label;
  }

  function escapeHtml(text) {
    return (text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function applyCardVisibility(cards, visible) {
    let shown = 0;
    for (const card of cards) {
      const show = visible(card);
      card.hidden = !show;
      if (show) {
        shown += 1;
      }
    }
    return shown;
  }

  function renderLuoghiGrid() {
    if (!luoghiGrid || !catalog) {
      return;
    }
    const items = sortByLabel(catalog.luoghi || []);
    luoghiGrid.innerHTML = "";
    for (const item of items) {
      luoghiGrid.appendChild(
        createSmallCard(item, {
          inputType: "radio",
          inputName: "prompt-luogo",
          portrait: false,
        })
      );
    }
    filterLuoghi();
  }

  function renderPgGrid() {
    if (!pgGrid || !catalog) {
      return;
    }
    const items = sortByLabel(catalog.personaggi || []);
    pgGrid.innerHTML = "";
    for (const item of items) {
      pgGrid.appendChild(
        createSmallCard(item, {
          inputType: "checkbox",
          inputName: "prompt-pg",
          portrait: true,
        })
      );
    }
    filterPg();
  }

  function renderPngRegions() {
    if (!pngRegions || !catalog) {
      return;
    }
    const items = sortByLabel(catalog.png || []);
    pngRegions.innerHTML = "";

    const byRegion = new Map();
    for (const item of items) {
      const region = item.regione || "Altro";
      if (!byRegion.has(region)) {
        byRegion.set(region, []);
      }
      byRegion.get(region).push(item);
    }

    const regions = [...byRegion.keys()].sort((a, b) => {
      const diff = regionSortIndex(a) - regionSortIndex(b);
      return diff !== 0 ? diff : a.localeCompare(b, "it", { sensitivity: "base" });
    });

    for (const region of regions) {
      const block = document.createElement("section");
      block.className = "prompt-png-region-block";
      block.dataset.regione = region;

      const heading = document.createElement("h3");
      heading.className = "prompt-png-region-title";
      heading.textContent = region;
      block.appendChild(heading);

      const grid = document.createElement("div");
      grid.className = "prompt-small-card-grid";
      for (const item of byRegion.get(region)) {
        grid.appendChild(
          createSmallCard(item, {
            inputType: "checkbox",
            inputName: "prompt-png",
            portrait: true,
          })
        );
      }
      block.appendChild(grid);
      pngRegions.appendChild(block);
    }
    filterPng();
  }

  function filterLuoghi() {
    const query = normalize(luoghiSearch && luoghiSearch.value);
    const region = luoghiRegion ? luoghiRegion.value : "__all__";
    const cards = luoghiGrid
      ? luoghiGrid.querySelectorAll(".prompt-small-card")
      : [];
    const shown = applyCardVisibility(cards, (card) => {
      const blob = card.dataset.search || "";
      const cardRegion = card.dataset.regione || "";
      if (query && !blob.includes(query)) {
        return false;
      }
      if (region !== "__all__" && cardRegion !== region) {
        return false;
      }
      return true;
    });
    if (luoghiEmpty) {
      luoghiEmpty.hidden = shown > 0;
    }
  }

  function filterPg() {
    const query = normalize(pgSearch && pgSearch.value);
    const cards = pgGrid ? pgGrid.querySelectorAll(".prompt-small-card") : [];
    const shown = applyCardVisibility(cards, (card) => {
      const blob = card.dataset.search || "";
      return !query || blob.includes(query);
    });
    if (pgEmpty) {
      pgEmpty.hidden = shown > 0;
    }
  }

  function filterPng() {
    const query = normalize(pngSearch && pngSearch.value);
    const region = pngRegion ? pngRegion.value : "__all__";
    const blocks = pngRegions
      ? pngRegions.querySelectorAll(".prompt-png-region-block")
      : [];
    let totalShown = 0;

    for (const block of blocks) {
      const blockRegion = block.dataset.regione || "";
      if (region !== "__all__" && blockRegion !== region) {
        block.hidden = true;
        continue;
      }
      block.hidden = false;
      const cards = block.querySelectorAll(".prompt-small-card");
      const shown = applyCardVisibility(cards, (card) => {
        const blob = card.dataset.search || "";
        return !query || blob.includes(query);
      });
      totalShown += shown;
      block.hidden = shown === 0;
    }

    if (pngEmpty) {
      pngEmpty.hidden = totalShown > 0;
    }
  }

  function selectedLuogo() {
    if (!luoghiGrid || !catalog) {
      return null;
    }
    const checked = luoghiGrid.querySelector('input[name="prompt-luogo"]:checked');
    if (!checked) {
      return null;
    }
    return (catalog.luoghi || []).find((item) => item.id === checked.value) || null;
  }

  function selectedCharacters() {
    if (!catalog) {
      return [];
    }
    const ids = new Set();
    for (const input of root.querySelectorAll(
      'input[name="prompt-pg"]:checked, input[name="prompt-png"]:checked'
    )) {
      ids.add(input.value);
    }
    const all = [...(catalog.personaggi || []), ...(catalog.png || [])];
    return all.filter((item) => ids.has(item.id));
  }

  function composePrompt(sceneText, luogo, characters) {
    const lines = ["Image prompt:", ""];

    const scene = sceneText.trim();
    if (scene) {
      lines.push(`Scene: ${scene}`, "");
    }

    if (luogo && luogo.visualRef && !isEmptyRefValue(luogo.visualRef.imagePrompt)) {
      lines.push(`Setting: ${luogo.visualRef.imagePrompt.trim()}`, "");
    }

    const charsWithPrompt = characters.filter(
      (c) => c.visualRef && c.visualRef.imagePrompt && !isEmptyRefValue(c.visualRef.imagePrompt)
    );

    if (charsWithPrompt.length) {
      lines.push("Characters present:");
      for (const c of charsWithPrompt) {
        lines.push(`- ${c.label}: ${c.visualRef.imagePrompt.trim()}`);
      }
      lines.push("");
    }

    lines.push(
      "Overall look: cinematically realistic; preserve height and proportion comparisons between non-medium races when multiple figures appear.",
      "",
      "Constraints to preserve:",
      ""
    );

    const constraintBullets = bulletLines([
      luogo && luogo.visualRef ? luogo.visualRef.constraints : "",
      ...characters.map((c) => (c.visualRef ? c.visualRef.constraints : "")),
    ]);
    if (constraintBullets.length) {
      lines.push(...constraintBullets, "");
    } else {
      lines.push("_None._", "");
    }

    lines.push("Details to avoid:", "");

    const avoidBullets = bulletLines([
      luogo && luogo.visualRef ? luogo.visualRef.avoids : "",
      ...characters.map((c) => (c.visualRef ? c.visualRef.avoids : "")),
      "no cartoon",
      "no plastic CGI",
      "no generic fantasy illustration",
      "no videogame HUD look",
    ]);
    if (avoidBullets.length) {
      lines.push(...avoidBullets);
    } else {
      lines.push("_None._");
    }

    return lines.join("\n").trim() + "\n";
  }

  function onGenera() {
    if (!catalog) {
      setStatus("Dati non ancora caricati.", true);
      return;
    }
    const luogo = selectedLuogo();
    const characters = selectedCharacters();
    const sceneText = scenaInput ? scenaInput.value : "";

    if (!sceneText.trim() && !luogo && !characters.length) {
      setStatus("Aggiungi una scena, un luogo o almeno un personaggio.", true);
      if (outputPanel) {
        outputPanel.hidden = true;
      }
      if (outputEl) {
        outputEl.textContent = "";
      }
      return;
    }

    const prompt = composePrompt(sceneText, luogo, characters);
    if (outputEl) {
      outputEl.textContent = prompt;
    }
    if (outputPanel) {
      outputPanel.hidden = false;
    }
    setStatus("");
  }

  async function onCopiaTutto() {
    if (!outputEl || (outputPanel && outputPanel.hidden)) {
      return;
    }
    const text = outputEl.textContent || "";
    try {
      await navigator.clipboard.writeText(text);
      setStatus("Prompt copiato negli appunti.");
    } catch (_err) {
      setStatus("Impossibile copiare: seleziona il testo manualmente.", true);
    }
  }

  function initUI(data) {
    catalog = data;
    fillRegionSelect(luoghiRegion, data.luoghi || []);
    fillRegionSelect(pngRegion, data.png || []);
    renderLuoghiGrid();
    renderPgGrid();
    renderPngRegions();
    setStatus("");
  }

  async function loadCatalog() {
    setStatus("Caricamento…");
    try {
      const response = await fetch("/assets/prompt-data.json", { cache: "no-cache" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      initUI(data);
    } catch (err) {
      setStatus(
        "Impossibile caricare i dati per il generatore prompt. Rigenera il sito pubblico.",
        true
      );
      console.error("prompt-page:", err);
    }
  }

  if (generaBtn) {
    generaBtn.addEventListener("click", onGenera);
  }
  if (copiaTuttoBtn) {
    copiaTuttoBtn.addEventListener("click", onCopiaTutto);
  }
  if (luoghiSearch) {
    luoghiSearch.addEventListener("input", filterLuoghi);
  }
  if (luoghiRegion) {
    luoghiRegion.addEventListener("change", filterLuoghi);
  }
  if (pgSearch) {
    pgSearch.addEventListener("input", filterPg);
  }
  if (pngSearch) {
    pngSearch.addEventListener("input", filterPng);
  }
  if (pngRegion) {
    pngRegion.addEventListener("change", filterPng);
  }

  loadCatalog();
})();
