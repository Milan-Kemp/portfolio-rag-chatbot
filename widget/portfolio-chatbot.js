/*
 * Portfolio RAG chatbot widget — vanilla JS, no dependencies.
 *
 * Embed on your site with one line:
 *
 *   <script src="portfolio-chatbot.js"
 *           data-api="https://your-api-host.example.com"></script>
 *
 * data-api  = base URL of the FastAPI service (no trailing slash).
 * data-title (optional) = header text, default "Vraag het mijn portfolio".
 *
 * The script injects its own styles and a floating button in the bottom
 * right. Everything is scoped under the .prc- class prefix.
 */
(function () {
  "use strict";

  var self = document.currentScript;
  var API = (self && self.dataset.api ? self.dataset.api : "").replace(/\/$/, "");
  var TITLE = (self && self.dataset.title) || "Vraag het mijn portfolio";

  if (!API) {
    console.error("[portfolio-chatbot] missing data-api attribute on script tag");
    return;
  }

  /* ---------- styles ---------- */
  var css = `
  .prc-btn{position:fixed;right:20px;bottom:20px;z-index:2147483000;
    width:56px;height:56px;border-radius:50%;border:none;cursor:pointer;
    background:#111;color:#fff;font-size:22px;line-height:56px;text-align:center;
    box-shadow:0 4px 16px rgba(0,0,0,.22);transition:transform .15s ease}
  .prc-btn:hover{transform:scale(1.05)}
  .prc-panel{position:fixed;right:20px;bottom:88px;z-index:2147483000;
    width:360px;max-width:calc(100vw - 40px);height:520px;max-height:calc(100vh - 120px);
    display:none;flex-direction:column;background:#fff;color:#1a1a1a;
    border:1px solid #e6e6e6;border-radius:14px;overflow:hidden;
    box-shadow:0 12px 40px rgba(0,0,0,.18);
    font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
  .prc-panel.prc-open{display:flex}
  .prc-head{padding:14px 16px;border-bottom:1px solid #eee;font-weight:600;
    display:flex;justify-content:space-between;align-items:center}
  .prc-close{background:none;border:none;font-size:20px;cursor:pointer;color:#888;line-height:1}
  .prc-log{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px}
  .prc-msg{max-width:85%;padding:10px 12px;border-radius:12px;white-space:pre-wrap;word-wrap:break-word}
  .prc-user{align-self:flex-end;background:#111;color:#fff;border-bottom-right-radius:3px}
  .prc-bot{align-self:flex-start;background:#f3f3f3;color:#1a1a1a;border-bottom-left-radius:3px}
  .prc-sources{align-self:flex-start;max-width:85%;font-size:12px;color:#666;margin-top:-6px}
  .prc-sources span{display:inline-block;background:#ececec;border-radius:6px;
    padding:2px 7px;margin:2px 4px 2px 0}
  .prc-hint{color:#999;font-size:12.5px;align-self:center;text-align:center}
  .prc-dots{align-self:flex-start;background:#f3f3f3;border-radius:12px;padding:12px 14px}
  .prc-dots i{display:inline-block;width:6px;height:6px;margin:0 2px;border-radius:50%;
    background:#aaa;animation:prc-b 1.2s infinite ease-in-out both}
  .prc-dots i:nth-child(2){animation-delay:.16s}
  .prc-dots i:nth-child(3){animation-delay:.32s}
  @keyframes prc-b{0%,80%,100%{transform:scale(.6);opacity:.4}40%{transform:scale(1);opacity:1}}
  .prc-form{display:flex;gap:8px;padding:12px;border-top:1px solid #eee}
  .prc-input{flex:1;border:1px solid #ddd;border-radius:9px;padding:9px 11px;font:inherit;outline:none}
  .prc-input:focus{border-color:#111}
  .prc-send{border:none;background:#111;color:#fff;border-radius:9px;padding:0 15px;cursor:pointer;font:inherit}
  .prc-send:disabled{opacity:.45;cursor:not-allowed}
  @media (prefers-color-scheme:dark){
    .prc-panel{background:#1c1c1e;color:#f2f2f2;border-color:#333}
    .prc-head{border-color:#333}
    .prc-bot{background:#2c2c2e;color:#f2f2f2}
    .prc-sources span{background:#333;color:#bbb}
    .prc-form{border-color:#333}
    .prc-input{background:#2c2c2e;border-color:#444;color:#f2f2f2}
    .prc-dots{background:#2c2c2e}
  }`;
  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  /* ---------- DOM ---------- */
  var btn = el("button", "prc-btn", { title: TITLE });
  btn.textContent = "💬";

  var panel = el("div", "prc-panel");
  panel.innerHTML =
    '<div class="prc-head"><span></span><button class="prc-close" aria-label="Sluiten">×</button></div>' +
    '<div class="prc-log"></div>' +
    '<form class="prc-form">' +
    '<input class="prc-input" type="text" placeholder="Stel een vraag over een project…" ' +
    'maxlength="500" autocomplete="off">' +
    '<button class="prc-send" type="submit">Stuur</button>' +
    "</form>";
  panel.querySelector(".prc-head span").textContent = TITLE;

  document.body.appendChild(btn);
  document.body.appendChild(panel);

  var log = panel.querySelector(".prc-log");
  var form = panel.querySelector(".prc-form");
  var input = panel.querySelector(".prc-input");
  var sendBtn = panel.querySelector(".prc-send");

  addHint(
    "Antwoorden komen uitsluitend uit Milans eigen projectteksten, met bronvermelding."
  );

  /* ---------- behaviour ---------- */
  btn.addEventListener("click", function () {
    panel.classList.toggle("prc-open");
    if (panel.classList.contains("prc-open")) input.focus();
  });
  panel.querySelector(".prc-close").addEventListener("click", function () {
    panel.classList.remove("prc-open");
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var q = input.value.trim();
    if (!q || sendBtn.disabled) return;
    input.value = "";
    addMsg(q, "prc-user");
    ask(q);
  });

  function ask(question) {
    setBusy(true);
    var dots = el("div", "prc-dots");
    dots.innerHTML = "<i></i><i></i><i></i>";
    log.appendChild(dots);
    scroll();

    fetch(API + "/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question }),
    })
      .then(function (r) {
        return r.json().then(function (data) {
          if (!r.ok) {
            var e = new Error(data.detail || "HTTP " + r.status);
            e.rateLimited = r.status === 429;
            throw e;
          }
          return data;
        });
      })
      .then(function (data) {
        dots.remove();
        addMsg(data.answer || "(geen antwoord)", "prc-bot");
        if (data.sources && data.sources.length) addSources(data.sources);
      })
      .catch(function (err) {
        dots.remove();
        addMsg(
          err.rateLimited
            ? err.message
            : "Er ging iets mis bij het ophalen van een antwoord. Probeer het later opnieuw.",
          "prc-bot"
        );
      })
      .finally(function () {
        setBusy(false);
        input.focus();
      });
  }

  function setBusy(b) {
    sendBtn.disabled = b;
    input.disabled = b;
  }

  /* ---------- helpers ---------- */
  function addMsg(text, cls) {
    var m = el("div", "prc-msg " + cls);
    m.textContent = text;
    log.appendChild(m);
    scroll();
  }
  function addSources(list) {
    var s = el("div", "prc-sources");
    s.appendChild(document.createTextNode("Bron: "));
    list.forEach(function (src) {
      var tag = document.createElement("span");
      tag.textContent = src;
      s.appendChild(tag);
    });
    log.appendChild(s);
    scroll();
  }
  function addHint(text) {
    var h = el("div", "prc-hint");
    h.textContent = text;
    log.appendChild(h);
  }
  function el(tag, cls, attrs) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (attrs) for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }
  function scroll() {
    log.scrollTop = log.scrollHeight;
  }
})();
