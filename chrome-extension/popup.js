const API = "http://127.0.0.1:8001";
document.getElementById("go").onclick = async () => {
  const message = document.getElementById("m").value;
  const out = document.getElementById("out");
  out.textContent = "Checking…";
  try {
    const r = await fetch(`${API}/check`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const j = await r.json();
    const color = j.verdict === "Scam" ? "#dc2626" : j.verdict === "Suspicious" ? "#d97706" : "#059669";
    out.innerHTML = `<span class="badge" style="background:${color}">${j.verdict} ${(j.score * 100).toFixed(0)}%</span>\n${j.category}\n${j.explanation}`;
  } catch (e) {
    out.textContent = "Backend offline. Start: uvicorn main:app --reload";
  }
};
