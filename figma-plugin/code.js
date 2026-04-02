figma.showUI(__html__, { width: 460, height: 620 });

function collectTextNodes(rootNodes) {
  const textNodes = [];

  function walk(node) {
    if (node.type === "TEXT") textNodes.push(node);
    if ("children" in node) {
      for (const child of node.children) walk(child);
    }
  }

  for (const root of rootNodes) walk(root);
  return textNodes;
}

async function ensureFontsLoaded(textNode) {
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

function normalizePayload(raw) {
  if (Array.isArray(raw)) {
    return raw[0] && typeof raw[0] === "object" ? raw[0] : null;
  }
  return raw && typeof raw === "object" ? raw : null;
}

function listTokensFromTextNodes(textNodes) {
  const tokenRegex = /\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}/g;
  const tokens = new Set();
  for (const node of textNodes) {
    const text = node.characters || "";
    tokenRegex.lastIndex = 0;
    let m;
    while ((m = tokenRegex.exec(text)) !== null) {
      tokens.add(m[1]);
    }
  }
  return Array.from(tokens).sort();
}

async function applyBindingsToTextNodes(textNodes, data) {
  const tokenRegex = /\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}/g;
  let changed = 0;
  let scanned = 0;
  const missingKeys = new Set();

  for (const node of textNodes) {
    scanned += 1;
    const original = node.characters || "";
    tokenRegex.lastIndex = 0;
    if (!tokenRegex.test(original)) continue;

    try {
      await ensureFontsLoaded(node);
      tokenRegex.lastIndex = 0;
      const next = original.replace(tokenRegex, (_, key) => {
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
    } catch (_) {
      // continue processing other nodes
    }
  }

  return {
    scanned,
    changed,
    missingKeys: Array.from(missingKeys).sort(),
  };
}

figma.ui.onmessage = async (msg) => {
  if (msg.type === "scan-placeholders") {
    const scope = msg.scope === "selection" ? "selection" : "page";
    const roots = pickRoots(scope);
    const textNodes = collectTextNodes(roots);
    const tokens = listTokensFromTextNodes(textNodes);
    figma.ui.postMessage({
      type: "scan-result",
      scope,
      tokens,
      textNodes: textNodes.length,
    });
    return;
  }

  if (msg.type === "apply-data") {
    const scope = msg.scope === "selection" ? "selection" : "page";
    const payload = normalizePayload(msg.payload);

    if (!payload) {
      figma.ui.postMessage({
        type: "apply-error",
        message: "Данные пустые или некорректные",
      });
      return;
    }

    const roots = pickRoots(scope);
    const textNodes = collectTextNodes(roots);
    const result = await applyBindingsToTextNodes(textNodes, payload);
    figma.ui.postMessage({
      type: "apply-result",
      ...result,
      scope,
    });
    return;
  }

  if (msg.type === "close") {
    figma.closePlugin("Готово");
  }
};
