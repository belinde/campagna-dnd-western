(function () {
  const root = document.querySelector("[data-prompt-tool]");
  if (!root) {
    return;
  }

  const statusEl = document.getElementById("prompt-status");
  const luogoSelect = document.getElementById("prompt-luogo");
  const pgList = document.getElementById("prompt-pg-list");
  const pngList = document.getElementById("prompt-png-list");
  const scenaInput = document.getElementById("prompt-scena");
  const generaBtn = document.getElementById("prompt-genera");
  const copiaBtn = document.getElementById("prompt-copia");
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

  function selectedEntries(selectEl, listEl, items) {
    if (!items || !items.length) {
      return [];
    }
    if (selectEl && selectEl.value) {
      const found = items.find((item) => item.id === selectEl.value);
      return found ? [found] : [];
    }
    if (!listEl) {
      return [];
    }
    const checked = listEl.querySelectorAll('input[type="checkbox"]:checked');
    const ids = Array.from(checked).map((el) => el.value);
    return items.filter((item) => ids.includes(item.id));
  }

  function renderCheckboxList(container, items) {
    if (!container) {
      return;
    }
    container.innerHTML = "";
    if (!items.length) {
      const empty = document.createElement("p");
      empty.className = "prompt-tool-empty";
      empty.textContent = "Nessun personaggio disponibile.";
      container.appendChild(empty);
      return;
    }
    for (const item of items) {
      const label = document.createElement("label");
      label.className = "prompt-tool-checkbox";
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = item.id;
      const text = document.createElement("span");
      text.className = "prompt-tool-checkbox-text";
      text.textContent = item.subtitle
        ? `${item.label} (${item.subtitle})`
        : item.label;
      label.appendChild(input);
      label.appendChild(text);
      container.appendChild(label);
    }
  }

  function renderLuogoSelect(items) {
    if (!luogoSelect) {
      return;
    }
    luogoSelect.innerHTML = "";
    const none = document.createElement("option");
    none.value = "";
    none.textContent = "Nessun luogo";
    luogoSelect.appendChild(none);
    for (const item of items) {
      const opt = document.createElement("option");
      opt.value = item.id;
      opt.textContent = item.subtitle ? `${item.label} (${item.subtitle})` : item.label;
      luogoSelect.appendChild(opt);
    }
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

    const charPrompts = characters
      .map((c) => c.visualRef && c.visualRef.imagePrompt)
      .filter((p) => p && !isEmptyRefValue(p));

    if (charPrompts.length) {
      lines.push("Characters present:");
      for (const prompt of charPrompts) {
        lines.push(`- ${prompt.trim()}`);
      }
      lines.push("");
    }

    lines.push(
      "Overall look: cinematically realistic; no proper names in prompt body; preserve height and proportion comparisons between non-medium races when multiple figures appear.",
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
    const luogo =
      luogoSelect && luogoSelect.value
        ? (catalog.luoghi || []).find((item) => item.id === luogoSelect.value)
        : null;
    const pgSelected = selectedEntries(null, pgList, catalog.personaggi || []);
    const pngSelected = selectedEntries(null, pngList, catalog.png || []);
    const characters = [...pgSelected, ...pngSelected];
    const sceneText = scenaInput ? scenaInput.value : "";

    if (!sceneText.trim() && !luogo && !characters.length) {
      setStatus("Aggiungi una scena, un luogo o almeno un personaggio.", true);
      if (outputEl) {
        outputEl.hidden = true;
        outputEl.textContent = "";
      }
      if (copiaBtn) {
        copiaBtn.disabled = true;
      }
      return;
    }

    const prompt = composePrompt(sceneText, luogo, characters);
    if (outputEl) {
      outputEl.hidden = false;
      outputEl.textContent = prompt;
    }
    if (copiaBtn) {
      copiaBtn.disabled = false;
    }
    setStatus("");
  }

  async function onCopia() {
    if (!outputEl || outputEl.hidden) {
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

  function sortByLabel(items) {
    return [...items].sort((a, b) =>
      (a.label || "").localeCompare(b.label || "", "it", { sensitivity: "base" })
    );
  }

  function initUI(data) {
    catalog = data;
    renderLuogoSelect(sortByLabel(data.luoghi || []));
    renderCheckboxList(pgList, sortByLabel(data.personaggi || []));
    renderCheckboxList(pngList, sortByLabel(data.png || []));
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
        "Impossibile caricare i dati per il compositore prompt. Rigenera il sito pubblico.",
        true
      );
      console.error("prompt-page:", err);
    }
  }

  if (generaBtn) {
    generaBtn.addEventListener("click", onGenera);
  }
  if (copiaBtn) {
    copiaBtn.addEventListener("click", onCopia);
  }

  loadCatalog();
})();
