// Right-click any selected text → check with Scam Shield.
const API = "http://127.0.0.1:8001";
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({ id: "scamshield", title: "Check with Scam Shield", contexts: ["selection"] });
});
chrome.contextMenus.onClicked.addListener(async (info) => {
  if (info.menuItemId !== "scamshield" || !info.selectionText) return;
  try {
    const r = await fetch(`${API}/check`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: info.selectionText }),
    });
    const j = await r.json();
    chrome.notifications?.create({
      type: "basic", title: `Scam Shield: ${j.verdict} ${(j.score * 100).toFixed(0)}%`,
      message: (j.explanation || "").slice(0, 120), iconUrl: "icon.png",
    });
  } catch { /* backend offline */ }
});
