figma.showUI(__html__, { width: 440, height: 360 });

function applyBindingsToTextNodes(rootNodes, data) {
  const textNodes = [];

  function collect(node) {
    if (node.type === "TEXT") textNodes.push(node);
    if ("children" in node) {
      for (const child of node.children) collect(child);
    }
  }

  for (const root of rootNodes) collect(root);

  const tokenRegex = /\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}/g;
  let changed = 0;
  let scanned = 0;
  const missingKeys = new Set();

  for (const node of textNodes) {
    scanned += 1;
    const original = node.characters;
    let hasToken = false;
    const keysToLoad = new Set();
    let m;

    tokenRegex.lastIndex = 0;
    while ((m = tokenRegex.exec(original)) !== null) {
      hasToken = true;
      keysToLoad.add(m[1]);
    }
    if (!hasToken) continue;

    try {
      awaitLoadFonts(node);
      let next = original;
      tokenRegex.lastIndex = 0;
      next = next.replace(tokenRegex, (_, key) => {
        if (Object.prototype.hasOwnProperty.call(data, key)) {
          const val = data[key];
          return val == null ? "" : String(val);
        }
        missingKeys.add(key);
        return "";
      });
      if (next !== original) {
        node.characters = next;
        changed += 1;
      }
    } catch (e) {
      // keep processing other nodes
    }
  }

  return {
    scanned,
    changed,
    missingKeys: Array.from(missingKeys).sort(),
  };
}

async function awaitLoadFonts(textNode) {
  const segs = textNode.getStyledTextSegments(["fontName"]);
  const seen = new Set();
  for (const seg of segs) {
    const f = seg.fontName;
    if (!f || typeof f === "symbol") continue;
    const key = `${f.family}__${f.style}`;
    if (seen.has(key)) continue;
    seen.add(key);
    await figma.loadFontAsync(f);
  }
}

function pickRoots(scope) {
  if (scope === "selection" && figma.currentPage.selection.length > 0) {
    return figma.currentPage.selection;
  }
  return [figma.currentPage];
}

figma.ui.onmessage = async (msg) => {
  if (msg.type === "apply-json") {
    const scope = msg.scope === "selection" ? "selection" : "page";
    let data = msg.data;

    if (!data || typeof data !== "object") {
      figma.ui.postMessage({
        type: "result",
        ok: false,
        message: "JSON пустой или некорректный",
      });
      return;
    }

    const roots = pickRoots(scope);
    const result = await applyBindingsToTextNodes(roots, data);

    figma.ui.postMessage({
      type: "result",
      ok: true,
      ...result,
      scope,
    });
    return;
  }

  if (msg.type === "close") {
    figma.closePlugin("Готово");
  }
};
