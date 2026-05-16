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

  const heroEl = document.getElementById("prompt-hero");
  const heroStartBtn = document.getElementById("prompt-hero-start");
  const wizardNav = document.getElementById("prompt-wizard-nav");
  const wizardActions = document.getElementById("prompt-wizard-actions");
  const prevBtn = document.getElementById("prompt-prev");
  const nextBtn = document.getElementById("prompt-next");
  const skipLuogoBtn = document.getElementById("prompt-skip-luogo");
  const stepLuogo = document.getElementById("prompt-step-luogo");
  const stepPersonaggi = document.getElementById("prompt-step-personaggi");
  const stepScena = document.getElementById("prompt-step-scena");
  const luogoSummary = document.getElementById("prompt-luogo-summary");
  const charsSummary = document.getElementById("prompt-chars-summary");
  const scenaRecap = document.getElementById("prompt-scena-recap");
  const alertNoChars = document.getElementById("prompt-alert-no-chars");
  const alertUnmatched = document.getElementById("prompt-alert-unmatched");
  const alertUnmatchedList = document.getElementById("prompt-alert-unmatched-list");
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
  const scenaNameBar = document.getElementById("prompt-scena-name-bar");
  const scenaNameButtons = document.getElementById("prompt-scena-name-buttons");
  const generaBtn = document.getElementById("prompt-genera");
  const copiaTuttoBtn = document.getElementById("prompt-copia-tutto");
  const outputPanel = document.getElementById("prompt-output-panel");
  const outputEl = document.getElementById("prompt-output");
  const stepIndicators = root.querySelectorAll("[data-step-indicator]");

  let catalog = null;
  let currentStep = 0;
  let luogoSkipped = false;

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

  function hideAlert(el) {
    if (el) {
      el.hidden = true;
    }
  }

  function showAlert(el) {
    if (el) {
      el.hidden = false;
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
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

  function labeledBullets(entries, field) {
    const lines = [];
    for (const entry of entries) {
      const ref = entry.item.visualRef;
      if (!ref || isEmptyRefValue(ref[field])) {
        continue;
      }
      const chunks = ref[field]
        .split(/\n+/)
        .map((line) => line.replace(/^[-*]\s*/, "").trim())
        .filter(Boolean);
      for (const chunk of chunks) {
        const line = `- ${entry.label}: ${chunk}`;
        const key = line.toLowerCase();
        if (!lines.some((existing) => existing.toLowerCase() === key)) {
          lines.push(line);
        }
      }
    }
    return lines;
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

  function escapeRegExp(text) {
    return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function escapeHtml(text) {
    return (text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function allCharacters() {
    if (!catalog) {
      return [];
    }
    return [...(catalog.personaggi || []), ...(catalog.png || [])];
  }

  function nameMentionedInText(name, text) {
    const label = (name || "").trim();
    if (!label || label.length < 2 || !text) {
      return false;
    }
    try {
      return new RegExp(escapeRegExp(label), "i").test(text);
    } catch (_err) {
      return text.toLowerCase().includes(label.toLowerCase());
    }
  }

  function findMentionedUnselected(sceneText, selectedIds) {
    const mentioned = [];
    const sorted = [...allCharacters()].sort(
      (a, b) => (b.label || "").length - (a.label || "").length
    );
    for (const item of sorted) {
      if (selectedIds.has(item.id)) {
        continue;
      }
      if (nameMentionedInText(item.label, sceneText)) {
        mentioned.push(item);
      }
    }
    return mentioned;
  }

  function mergeCharacters(selected, inferred) {
    const byId = new Map();
    for (const item of [...selected, ...inferred]) {
      byId.set(item.id, item);
    }
    return [...byId.values()];
  }

  function thumbMarkup(item) {
    if (item.thumbPath) {
      return `<img class="prompt-small-card-thumb" src="${item.thumbPath}" alt="" loading="lazy">`;
    }
    return '<span class="prompt-small-card-thumb prompt-small-card-thumb--placeholder" aria-hidden="true"></span>';
  }

  function syncInputGroupCards(inputName) {
    for (const peer of root.querySelectorAll(`input[name="${inputName}"]`)) {
      const card = peer.closest(".prompt-small-card");
      if (card) {
        card.classList.toggle("prompt-small-card--selected", peer.checked);
      }
      peer.dataset.wasChecked = peer.checked ? "true" : "false";
    }
  }

  function createSmallCard(item, options) {
    const { inputType, inputName, portrait } = options;
    const label = document.createElement("label");
    label.className = "prompt-small-card";
    if (portrait) {
      label.classList.add("prompt-small-card--portrait");
    }
    label.dataset.search = item.search || "";
    label.dataset.itemId = item.id;
    label.dataset.itemLabel = item.label || "";
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
      if (inputType === "radio") {
        syncInputGroupCards(inputName);
      } else {
        label.classList.toggle("prompt-small-card--selected", input.checked);
      }
      if (currentStep === 2) {
        updateCharsSummary();
        hideAlert(alertNoChars);
      }
      if (currentStep === 1) {
        updateLuogoSummary();
        luogoSkipped = false;
      }
    }

    input.addEventListener("change", syncSelected);
    if (inputType === "radio") {
      input.addEventListener("click", () => {
        if (input.dataset.wasChecked === "true") {
          input.checked = false;
        }
        requestAnimationFrame(() => syncInputGroupCards(inputName));
      });
    }

    syncSelected();
    return label;
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
    pgGrid.classList.add("prompt-small-card-grid--portrait");
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
      grid.className = "prompt-small-card-grid prompt-small-card-grid--portrait";
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
    if (!luoghiGrid || !catalog || luogoSkipped) {
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
    return allCharacters().filter((item) => ids.has(item.id));
  }

  function clearLuogoSelection() {
    luogoSkipped = true;
    for (const input of root.querySelectorAll('input[name="prompt-luogo"]')) {
      input.checked = false;
    }
    syncInputGroupCards("prompt-luogo");
    updateLuogoSummary();
  }

  function updateLuogoSummary() {
    if (!luogoSummary) {
      return;
    }
    const luogo = selectedLuogo();
    if (luogoSkipped || !luogo) {
      luogoSummary.hidden = false;
      luogoSummary.textContent = luogoSkipped
        ? "Luogo: nessuno (passaggio saltato)"
        : "";
      luogoSummary.hidden = !luogoSkipped;
      return;
    }
    luogoSummary.hidden = false;
    luogoSummary.textContent = `Luogo selezionato: ${luogo.label}`;
  }

  function updateCharsSummary() {
    if (!charsSummary) {
      return;
    }
    const chars = selectedCharacters();
    if (!chars.length) {
      charsSummary.hidden = true;
      charsSummary.textContent = "";
      return;
    }
    charsSummary.hidden = false;
    charsSummary.textContent = `Personaggi (${chars.length}): ${chars.map((c) => c.label).join(", ")}`;
  }

  function insertNameAtCursor(name) {
    if (!scenaInput || !name) {
      return;
    }
    const start = scenaInput.selectionStart ?? scenaInput.value.length;
    const end = scenaInput.selectionEnd ?? start;
    const value = scenaInput.value;
    const before = value.slice(0, start);
    const after = value.slice(end);
    const needsSpaceBefore = before.length > 0 && !/\s$/.test(before);
    const needsSpaceAfter = after.length > 0 && !/^\s|[,.;:!?]/.test(after);
    const insert =
      (needsSpaceBefore ? " " : "") + name + (needsSpaceAfter ? " " : "");
    scenaInput.value = before + insert + after;
    const pos = start + insert.length;
    scenaInput.setSelectionRange(pos, pos);
    scenaInput.focus();
    scenaInput.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function updateScenaNameBar() {
    if (!scenaNameBar || !scenaNameButtons) {
      return;
    }
    const chars = sortByLabel(selectedCharacters());
    scenaNameButtons.innerHTML = "";
    if (!chars.length) {
      scenaNameBar.hidden = true;
      return;
    }
    scenaNameBar.hidden = false;
    for (const item of chars) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "prompt-scena-name-btn";
      btn.textContent = item.label;
      btn.title = `Inserisci «${item.label}» al cursore`;
      btn.addEventListener("click", () => insertNameAtCursor(item.label));
      scenaNameButtons.appendChild(btn);
    }
  }

  function updateScenaRecap() {
    if (!scenaRecap) {
      return;
    }
    const parts = [];
    const luogo = selectedLuogo();
    if (luogo) {
      parts.push(`Luogo: ${luogo.label}`);
    } else if (luogoSkipped) {
      parts.push("Luogo: nessuno");
    }
    const chars = selectedCharacters();
    if (chars.length) {
      parts.push(`Personaggi: ${chars.map((c) => c.label).join(", ")}`);
    }
    scenaRecap.textContent = parts.length
      ? parts.join(" · ")
      : "Completa la descrizione della scena in inglese.";
  }

  const INTIMATE_SCENE_PATTERNS = [
    /\b(?:tea|drawing|dining|living|bed|ball|smoking)\s+room\b/i,
    /\b(?:interior|indoors|inside)\b/i,
    /\b(?:parlor|parlour|salon|chamber|alcove|nook)\b/i,
    /\b(?:kitchen|bedroom|corridor|hallway|passage|foyer|vestibule)\b/i,
    /\b(?:office|study|library|cellar|attic|basement|storeroom)\b/i,
    /\b(?:tavern|inn|saloon)\s+(?:interior|inside|room)\b/i,
    /\b(?:cabin|barn|stable|shed)\s+(?:interior|inside)\b/i,
    /\b(?:booth|pew|counter|bar\s+interior)\b/i,
    /\bat\s+the\s+table\b/i,
    /\baround\s+the\s+table\b/i,
    /\bclose[- ]?up\b/i,
    /\bsmall\s+room\b/i,
    /\bconfined\s+space\b/i,
  ];

  const WIDE_SCENE_PATTERNS = [
    /\bcityscape\b/i,
    /\bpanorama\b/i,
    /\baerial\b/i,
    /\bbird['']?s[- ]?eye\b/i,
    /\bestablishing\s+shot\b/i,
    /\bskyline\b/i,
    /\bentire\s+city\b/i,
    /\bwhole\s+(?:city|town)\b/i,
    /\bwide\s+(?:shot|view|angle|establishing)\b/i,
    /\boverlooking\s+the\s+(?:city|town|harbor|harbour|river|plains)\b/i,
    /\bfrom\s+above\b/i,
    /\b(?:riverfront|waterfront|harbor|harbour)\s+at\s+(?:dusk|dawn|sunset|sunrise)\b/i,
  ];

  function classifySceneFraming(sceneText) {
    const text = (sceneText || "").trim();
    if (!text) {
      return "neutral";
    }
    let intimate = false;
    let wide = false;
    for (const pattern of INTIMATE_SCENE_PATTERNS) {
      if (pattern.test(text)) {
        intimate = true;
        break;
      }
    }
    for (const pattern of WIDE_SCENE_PATTERNS) {
      if (pattern.test(text)) {
        wide = true;
        break;
      }
    }
    if (intimate && !wide) {
      return "intimate";
    }
    if (wide && !intimate) {
      return "wide";
    }
    if (intimate && wide) {
      return "neutral";
    }
    return "neutral";
  }

  function locationScaleOf(luogo) {
    const scale = luogo && luogo.locationScale;
    if (scale === "compact" || scale === "settlement" || scale === "city") {
      return scale;
    }
    return "settlement";
  }

  function settingWeightPrefix(sceneFraming, locationScale) {
    if (sceneFraming === "intimate") {
      if (locationScale === "compact") {
        return "binding reference — match this small location's architecture, materials, and mood; Scene defines the moment, poses, and room details: ";
      }
      return "evocative reference only — mood, era, materials, and palette; do NOT recreate city-wide layout or wide establishing view; Scene defines the actual room and framing: ";
    }
    if (sceneFraming === "wide") {
      if (locationScale === "compact") {
        return "binding reference — this small location defines the environment; fuse with Scene into one view: ";
      }
      return "primary environment — merge with Scene into one continuous wide view: ";
    }
    if (locationScale === "compact") {
      return "binding reference — this small location defines the environment; Scene adds action and figures: ";
    }
    return "context reference — setting supplies place and atmosphere; Scene has priority for action and figures: ";
  }

  function compositionLines(sceneFraming, isLongPrompt) {
    const base = [
      "Composition: ONE single continuous photograph, one camera setup, one moment in time; all figures and environment share the same lighting and depth of field.",
      "Do NOT render split screen, comic panels, diptych, triptych, storyboard strip, collage, or multiple unrelated shots.",
    ];
    if (isLongPrompt) {
      base.push(
        "Integrate Scene, Setting, and every character below into this ONE frame — not separate chapters or panels to illustrate in sequence."
      );
    }
    if (sceneFraming === "intimate") {
      base.push(
        "Keep a single interior or contained framing; do not pull back to a city-wide or landscape establishing shot unless Scene explicitly asks for it."
      );
    }
    return base;
  }

  function estimatePromptLength(scene, luogo, characters) {
    let len = scene.length;
    if (luogo && luogo.visualRef && luogo.visualRef.imagePrompt) {
      len += luogo.visualRef.imagePrompt.length;
    }
    for (const c of characters) {
      if (c.visualRef && c.visualRef.imagePrompt) {
        len += c.visualRef.imagePrompt.length;
      }
    }
    return len;
  }

  function isLongPrompt(scene, luogo, characters) {
    const charsWithPrompt = characters.filter(
      (c) => c.visualRef && c.visualRef.imagePrompt && !isEmptyRefValue(c.visualRef.imagePrompt)
    );
    return estimatePromptLength(scene, luogo, characters) > 900 || charsWithPrompt.length >= 2;
  }

  function updateUnmatchedAlert(sceneText, selected) {
    if (!alertUnmatched || !alertUnmatchedList) {
      return;
    }
    const selectedIds = new Set(selected.map((c) => c.id));
    const inferred = findMentionedUnselected(sceneText, selectedIds);
    if (!inferred.length) {
      hideAlert(alertUnmatched);
      alertUnmatchedList.textContent = "";
      return;
    }
    alertUnmatchedList.textContent = ` ${inferred.map((c) => c.label).join(", ")}.`;
    showAlert(alertUnmatched);
  }

  function composePrompt(sceneText, luogo, characters) {
    const lines = ["Image prompt:", ""];

    const scene = sceneText.trim();
    const sceneFraming = classifySceneFraming(scene);
    const locationScale = locationScaleOf(luogo);
    const longPrompt = isLongPrompt(scene, luogo, characters);

    if (scene) {
      lines.push(`Scene: ${scene}`, "");
    }

    lines.push(...compositionLines(sceneFraming, longPrompt), "");

    if (luogo && luogo.visualRef && !isEmptyRefValue(luogo.visualRef.imagePrompt)) {
      const weight = settingWeightPrefix(sceneFraming, locationScale);
      const namePart = luogo.label ? `Setting (${luogo.label})` : "Setting";
      lines.push(`${namePart} — ${weight}${luogo.visualRef.imagePrompt.trim()}`, "");
    }

    const charsWithPrompt = characters.filter(
      (c) => c.visualRef && c.visualRef.imagePrompt && !isEmptyRefValue(c.visualRef.imagePrompt)
    );

    if (charsWithPrompt.length) {
      const charsHeader = longPrompt
        ? "Characters present (same frame):"
        : "Characters present:";
      lines.push(charsHeader);
      for (const c of charsWithPrompt) {
        lines.push(`- ${c.label}: ${c.visualRef.imagePrompt.trim()}`);
      }
      lines.push("");
    }

    lines.push(
      "Overall look: cinematically realistic; character labels use proper names only as section headers; do not repeat names inside visual descriptions; preserve height and proportion comparisons between non-medium races when multiple figures appear.",
      "",
      "Constraints to preserve:",
      ""
    );

    const constraintEntries = [];
    if (luogo && luogo.visualRef && !isEmptyRefValue(luogo.visualRef.constraints)) {
      constraintEntries.push({ label: luogo.label, item: luogo });
    }
    for (const c of characters) {
      if (c.visualRef && !isEmptyRefValue(c.visualRef.constraints)) {
        constraintEntries.push({ label: c.label, item: c });
      }
    }
    const constraintBullets = labeledBullets(constraintEntries, "constraints");
    if (constraintBullets.length) {
      lines.push(...constraintBullets, "");
    } else {
      lines.push("_None._", "");
    }

    lines.push("Details to avoid:", "");

    const avoidEntries = [];
    if (luogo && luogo.visualRef && !isEmptyRefValue(luogo.visualRef.avoids)) {
      avoidEntries.push({ label: luogo.label, item: luogo });
    }
    for (const c of characters) {
      if (c.visualRef && !isEmptyRefValue(c.visualRef.avoids)) {
        avoidEntries.push({ label: c.label, item: c });
      }
    }
    const avoidBullets = labeledBullets(avoidEntries, "avoids");
    const globalAvoids = [
      "no cartoon",
      "no plastic CGI",
      "no generic fantasy illustration",
      "no videogame HUD look",
      "no split screen",
      "no multi-panel layout",
      "no storyboard",
      "no comic strip",
    ];
    for (const item of globalAvoids) {
      if (!avoidBullets.some((line) => line.toLowerCase().includes(item))) {
        avoidBullets.push(`- ${item}`);
      }
    }
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
    hideAlert(alertNoChars);
    const luogo = selectedLuogo();
    const selected = selectedCharacters();
    const sceneText = scenaInput ? scenaInput.value : "";

    if (!selected.length) {
      showAlert(alertNoChars);
      return;
    }

    const selectedIds = new Set(selected.map((c) => c.id));
    const inferred = findMentionedUnselected(sceneText, selectedIds);
    const characters = mergeCharacters(selected, inferred);
    updateUnmatchedAlert(sceneText, selected);

    if (!sceneText.trim() && !luogo && !characters.length) {
      setStatus("Aggiungi una descrizione di scena.", true);
      if (outputPanel) {
        outputPanel.hidden = true;
      }
      return;
    }

    const prompt = composePrompt(sceneText, luogo, characters);
    if (outputEl) {
      outputEl.textContent = prompt;
    }
    if (outputPanel) {
      outputPanel.hidden = false;
      outputPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
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

  function showWizardChrome() {
    if (wizardNav) {
      wizardNav.hidden = false;
    }
    if (wizardActions) {
      wizardActions.hidden = false;
    }
  }

  function hideWizardChrome() {
    if (wizardNav) {
      wizardNav.hidden = true;
    }
    if (wizardActions) {
      wizardActions.hidden = true;
    }
    for (const panel of [stepLuogo, stepPersonaggi, stepScena]) {
      if (panel) {
        panel.hidden = true;
      }
    }
    if (outputPanel) {
      outputPanel.hidden = true;
    }
  }

  function setStep(step) {
    currentStep = step;
    const panels = [stepLuogo, stepPersonaggi, stepScena];
    for (const panel of panels) {
      if (panel) {
        panel.hidden = true;
      }
    }
    const active = panels[step - 1];
    if (active) {
      active.hidden = false;
    }

    for (const indicator of stepIndicators) {
      const n = Number(indicator.getAttribute("data-step-indicator"));
      const isActive = n === step;
      indicator.classList.toggle("prompt-wizard-breadcrumb-item--active", isActive);
      indicator.classList.toggle("prompt-wizard-breadcrumb-item--done", n < step);
      if (isActive) {
        indicator.setAttribute("aria-current", "step");
      } else {
        indicator.removeAttribute("aria-current");
      }
    }

    if (prevBtn) {
      prevBtn.hidden = step <= 1;
    }
    if (skipLuogoBtn) {
      skipLuogoBtn.hidden = step !== 1;
    }
    if (nextBtn) {
      nextBtn.hidden = step >= 3;
    }
    if (generaBtn) {
      generaBtn.hidden = step !== 3;
    }

    hideAlert(alertNoChars);
    if (step !== 3) {
      hideAlert(alertUnmatched);
    }

    if (step === 2) {
      updateCharsSummary();
    }
    if (step === 3) {
      updateScenaRecap();
      updateScenaNameBar();
      const sceneText = scenaInput ? scenaInput.value : "";
      updateUnmatchedAlert(sceneText, selectedCharacters());
    }

    root.dataset.promptStep = String(step);
  }

  function onNext() {
    if (currentStep === 1) {
      if (!selectedLuogo() && !luogoSkipped) {
        setStatus("Seleziona un luogo oppure usa «Salta luogo».", true);
        return;
      }
      setStatus("");
      updateLuogoSummary();
    }

    if (currentStep === 2) {
      if (!selectedCharacters().length) {
        showAlert(alertNoChars);
        return;
      }
      hideAlert(alertNoChars);
      updateCharsSummary();
    }

    if (currentStep < 3) {
      setStep(currentStep + 1);
    }
  }

  function onPrev() {
    if (currentStep > 1) {
      setStep(currentStep - 1);
    }
  }

  function onSkipLuogo() {
    clearLuogoSelection();
    setStatus("");
    setStep(2);
  }

  function startWizard() {
    if (heroEl) {
      heroEl.hidden = true;
    }
    showWizardChrome();
    setStep(1);
  }

  function initHero() {
    try {
      localStorage.removeItem("campagna-prompt-hero-seen");
    } catch (_err) {
      /* ignore */
    }
    currentStep = 0;
    hideWizardChrome();
    hideAlert(alertNoChars);
    hideAlert(alertUnmatched);
    setStatus("");
    if (heroEl) {
      heroEl.hidden = false;
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
    initHero();
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

  if (heroStartBtn) {
    heroStartBtn.addEventListener("click", startWizard);
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", onNext);
  }
  if (prevBtn) {
    prevBtn.addEventListener("click", onPrev);
  }
  if (skipLuogoBtn) {
    skipLuogoBtn.addEventListener("click", onSkipLuogo);
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
  if (scenaInput) {
    scenaInput.addEventListener("input", () => {
      if (currentStep === 3) {
        updateUnmatchedAlert(scenaInput.value, selectedCharacters());
      }
    });
  }

  loadCatalog();
})();
