#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_thai_frequency_ui.py

批次更新 Thai Frequency HTML：
1. 🔊 播放時變成 ⏸，加上 .speaking class；播放結束/錯誤恢復 🔊
2. Favorites tab 改成「輕量字卡 + 展開更多」
3. 自動處理 thai-frequency-rank*-notes-audio.html
4. 不需要 bs4，只用 Python 標準庫

用法：
  # 先預覽
  python3 patch_thai_frequency_ui.py --dry-run

  # 套用目前資料夾內所有 thai-frequency-rank*-notes-audio.html
  python3 patch_thai_frequency_ui.py

  # 指定資料夾
  python3 patch_thai_frequency_ui.py --dir "/Users/你的路徑/thai frequency"

  # 不備份
  python3 patch_thai_frequency_ui.py --no-backup
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


CSS_MARKER_START = "/* === THAI FREQUENCY UI PATCH: START === */"
CSS_MARKER_END = "/* === THAI FREQUENCY UI PATCH: END === */"
JS_MARKER_START = "<!-- === THAI FREQUENCY UI PATCH JS: START === -->"
JS_MARKER_END = "<!-- === THAI FREQUENCY UI PATCH JS: END === -->"


PATCH_CSS = f"""
{CSS_MARKER_START}

/* 播放中狀態：一般喇叭可以微微 pulse */
.speak.speaking,
.tts.speaking {{
  background: #fff1df !important;
  border-color: rgba(245,158,11,.68) !important;
  color: #9a3412 !important;
  animation: tfSpeakPulse .65s ease-in-out infinite alternate;
}}

@keyframes tfSpeakPulse {{
  from {{ transform: scale(1); }}
  to {{ transform: scale(1.12); }}
}}

/* 避免 collocation pill 播放時彈跳，只變色 */
.colloc-chip.speaking,
.pill.speaking {{
  background: rgba(255,247,237,.92) !important;
  border-color: rgba(245,158,11,.42) !important;
  color: var(--text, #263238) !important;
  transform: none !important;
  animation: none !important;
}}

/* Favorites：輕量字卡版 */
.tf-favs-wrap {{
  display: grid;
  gap: 14px;
}}

.tf-favs-toolbar {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin: 10px 0 14px;
}}

.tf-favs-count {{
  font-size: 13px;
  color: var(--muted, #6b7280);
  border: .5px solid var(--line, rgba(120,130,140,.25));
  border-radius: 999px;
  padding: 5px 10px;
  background: rgba(255,255,255,.6);
}}

.tf-favs-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(285px, 1fr));
  gap: 12px;
}}

.tf-fav-card {{
  position: relative;
  background: var(--card, rgba(255,255,255,.72));
  border: .5px solid var(--line, rgba(120,130,140,.25));
  border-radius: 22px;
  padding: 16px;
  box-shadow: 0 8px 22px rgba(15,23,42,.06);
}}

.tf-fav-rank {{
  position: absolute;
  right: 14px;
  top: 12px;
  font-size: 12px;
  color: var(--muted, #6b7280);
  background: rgba(255,255,255,.72);
  border: .5px solid var(--line, rgba(120,130,140,.25));
  border-radius: 999px;
  padding: 2px 8px;
}}

.tf-fav-head {{
  display: grid;
  grid-template-columns: 36px 1fr;
  gap: 10px;
  align-items: start;
  padding-right: 46px;
}}

.tf-fav-word {{
  font-family: "Noto Sans Thai", "Tahoma", sans-serif;
  font-size: 31px;
  line-height: 1.12;
  font-weight: 800;
  color: var(--text, #263238);
}}

.tf-fav-rom {{
  color: #6b7280;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  font-size: 13px;
  margin-top: 2px;
}}

.tf-fav-meaning {{
  font-size: 14px;
  margin-top: 6px;
  color: var(--text, #263238);
}}

.tf-fav-example {{
  margin-top: 12px;
  padding: 10px;
  border: .5px dashed rgba(120,130,140,.28);
  border-radius: 14px;
  background: rgba(255,255,255,.62);
  display: grid;
  grid-template-columns: 30px 1fr;
  gap: 8px;
}}

.tf-fav-example .thai {{
  font-family: "Noto Sans Thai", "Tahoma", sans-serif;
  font-size: 15px;
  font-weight: 500;
}}

.tf-fav-actions {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}}

.tf-fav-action {{
  border: .5px solid var(--line, rgba(120,130,140,.25));
  border-radius: 999px;
  background: rgba(255,255,255,.72);
  padding: 6px 10px;
  cursor: pointer;
  font-size: 12px;
  color: var(--text, #263238);
}}

.tf-fav-action.remove {{
  background: rgba(254,242,242,.78);
  border-color: rgba(231,111,81,.32);
  color: #b91c1c;
}}

.tf-fav-details {{
  margin-top: 12px;
  border: .5px solid var(--line, rgba(120,130,140,.25));
  border-radius: 16px;
  background: rgba(255,255,255,.56);
  padding: 10px 12px;
}}

.tf-fav-details summary {{
  cursor: pointer;
  font-weight: 800;
  color: #9a3412;
}}

.tf-fav-section {{
  margin-top: 10px;
  padding-top: 10px;
  border-top: .5px dashed rgba(120,130,140,.25);
}}

.tf-fav-section-title {{
  font-size: 12px;
  font-weight: 900;
  color: var(--muted, #6b7280);
  text-transform: uppercase;
  letter-spacing: .04em;
  margin-bottom: 6px;
}}

.tf-empty-favs {{
  text-align: center;
  padding: 48px 18px;
  border: .5px dashed rgba(2,132,199,.28);
  border-radius: 18px;
  background: rgba(239,246,255,.62);
  color: var(--muted, #6b7280);
}}

.tf-fav-highlight {{
  animation: tfFavHighlight 1.6s ease forwards;
}}

@keyframes tfFavHighlight {{
  0%   {{ outline: 3px solid #f59e0b; outline-offset: 4px; }}
  80%  {{ outline: 3px solid #f59e0b; outline-offset: 4px; }}
  100% {{ outline: 0 solid transparent; outline-offset: 0; }}
}}

@media (max-width: 640px) {{
  .tf-fav-word {{ font-size: 27px; }}
  .tf-fav-card {{ padding: 14px; }}
}}

{CSS_MARKER_END}
""".strip()


PATCH_JS = f"""
{JS_MARKER_START}
<script>
(function() {{
  "use strict";

  const FILE_KEY = location.pathname.split("/").pop() || "thai_vocab";
  const STORE_KEY = "fav__" + FILE_KEY;

  let activeBtn = null;
  let activeUtterance = null;
  let voices = [];

  function loadVoices() {{
    if (!("speechSynthesis" in window)) return;
    voices = window.speechSynthesis.getVoices ? window.speechSynthesis.getVoices() : [];
  }}

  if ("speechSynthesis" in window) {{
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }}

  function thaiVoice() {{
    return voices.find(v => /th-TH/i.test(v.lang))
        || voices.find(v => /^th/i.test(v.lang))
        || voices.find(v => /Kanya|Thai/i.test(v.name))
        || null;
  }}

  function resetSpeakButton(btn) {{
    if (!btn) return;
    btn.classList.remove("speaking");
    if (btn.dataset && btn.dataset.originalText) {{
      btn.textContent = btn.dataset.originalText;
    }} else if (btn.matches(".speak, .tts")) {{
      btn.textContent = "🔊";
    }}
  }}

  function resetAllAudioUI() {{
    document.querySelectorAll(".speak.speaking, .tts.speaking, .colloc-chip.speaking, .pill.speaking")
      .forEach(el => {{
        el.classList.remove("speaking");
        if (el.matches(".speak, .tts")) resetSpeakButton(el);
      }});
  }}

  function getThaiFromAudioTarget(target) {{
    const btn = target.closest(".speak, .tts");
    if (btn) return {{ btn, text: btn.dataset.thai || btn.getAttribute("data-thai") || "" }};

    const chip = target.closest(".colloc-chip[data-thai], .pill[data-thai]");
    if (chip) {{
      let innerBtn = chip.querySelector(".speak, .tts");
      return {{
        btn: innerBtn || chip,
        chip,
        text: chip.dataset.thai || chip.getAttribute("data-thai") || ""
      }};
    }}
    return null;
  }}

  function speakThai(text, btn, chip) {{
    if (!text || !("speechSynthesis" in window)) return;

    if (activeBtn === btn && window.speechSynthesis.speaking) {{
      window.speechSynthesis.cancel();
      resetAllAudioUI();
      activeBtn = null;
      activeUtterance = null;
      return;
    }}

    window.speechSynthesis.cancel();
    resetAllAudioUI();

    if (btn && btn.matches(".speak, .tts")) {{
      if (!btn.dataset.originalText) btn.dataset.originalText = btn.textContent.trim() || "🔊";
      btn.textContent = "⏸";
      btn.classList.add("speaking");
    }}
    if (chip) chip.classList.add("speaking");

    const u = new SpeechSynthesisUtterance(text);
    u.lang = "th-TH";
    u.rate = 0.86;
    u.pitch = 1.0;

    const voice = thaiVoice();
    if (voice) u.voice = voice;

    activeBtn = btn;
    activeUtterance = u;

    u.onend = function() {{
      resetAllAudioUI();
      activeBtn = null;
      activeUtterance = null;
    }};

    u.onerror = function() {{
      resetAllAudioUI();
      activeBtn = null;
      activeUtterance = null;
    }};

    window.speechSynthesis.speak(u);
  }}

  function favArray() {{
    try {{
      return JSON.parse(localStorage.getItem(STORE_KEY) || "[]").map(String);
    }} catch (e) {{
      return [];
    }}
  }}

  function favSet() {{
    return new Set(favArray());
  }}

  function saveFavs(set) {{
    localStorage.setItem(STORE_KEY, JSON.stringify(Array.from(set)));
  }}

  function getCardRank(card) {{
    return String(card?.dataset?.rank || card?.getAttribute("data-rank") || "");
  }}

  function ensureFavButtons() {{
    document.querySelectorAll(".word-card").forEach(card => {{
      if (card.querySelector(":scope > .fav-btn")) return;
      const rank = getCardRank(card);
      if (!rank) return;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "fav-btn";
      btn.setAttribute("aria-label", "favorite");
      btn.textContent = "☆";
      card.appendChild(btn);
    }});
  }}

  function updateFavUI() {{
    const favs = favSet();
    document.querySelectorAll(".word-card").forEach(card => {{
      const rank = getCardRank(card);
      const btn = card.querySelector(":scope > .fav-btn");
      if (!btn) return;
      const on = favs.has(rank);
      btn.classList.toggle("faved", on);
      btn.textContent = on ? "★" : "☆";
    }});

    const count = favs.size;
    const favCount = document.getElementById("favCount");
    if (favCount) favCount.textContent = "已收藏 " + count + " 字";

    const favTab = document.querySelector('.tab[data-tab="favs"], .tab[data-tab="favorites"]');
    if (favTab) favTab.textContent = "我的收藏 " + (count ? "(" + count + ")" : "");

    const showFav = document.getElementById("showFav");
    if (showFav) showFav.textContent = "只看收藏 ★" + (count ? " (" + count + ")" : "");
  }}

  function cleanText(text) {{
    return (text || "").replace(/\\s+/g, " ").trim();
  }}

  function firstDirectText(el) {{
    if (!el) return "";
    const clone = el.cloneNode(true);
    clone.querySelectorAll("button, .speak, .tts").forEach(x => x.remove());
    return cleanText(clone.textContent);
  }}

  function parseMeaning(card) {{
    const meaningEl = card.querySelector(".meaning");
    const raw = cleanText(meaningEl?.textContent || "");
    if (!raw) return {{ zh: "", en: "" }};

    const parts = raw.split("｜");
    if (parts.length >= 2) {{
      return {{
        zh: cleanText(parts[0]),
        en: cleanText(parts.slice(1).join("｜"))
      }};
    }}
    return {{ zh: raw, en: "" }};
  }}

  function extractExample(ex) {{
    if (!ex) return null;
    const thai = firstDirectText(ex.querySelector(".thai"));
    const rom = cleanText(ex.querySelector(".rom")?.textContent || "");
    const en = cleanText(ex.querySelector(".en, .eng")?.textContent || "");
    const zh = cleanText(ex.querySelector(".zh")?.textContent || "");
    const btn = ex.querySelector(".speak[data-thai], .tts[data-thai]");
    const audio = btn?.dataset?.thai || thai;
    return {{ thai, rom, en, zh, audio }};
  }}

  function cardData(card) {{
    const rank = getCardRank(card);
    const word = cleanText(card.dataset.word || card.querySelector(".word")?.textContent || card.querySelector(".thai.word")?.textContent || "");
    const romFull = cleanText(card.querySelector(".word-head .rom, .rom")?.textContent || "");
    const rom = cleanText(romFull.replace(/IPA:.*/i, ""));
    const meaning = parseMeaning(card);
    const usage = cleanText(card.querySelector(".usage")?.textContent || "");
    const examples = Array.from(card.querySelectorAll(".ex")).map(extractExample).filter(Boolean);
    const collocs = Array.from(card.querySelectorAll(".colloc-chip")).map(chip => {{
      const thai = firstDirectText(chip.querySelector(".thai")) || cleanText(chip.dataset.thai || "");
      const en = cleanText(chip.querySelector(".en-colloc, .eng, .en")?.textContent || "");
      const audio = chip.dataset.thai || chip.querySelector(".speak[data-thai], .tts[data-thai]")?.dataset?.thai || thai;
      return {{ thai, en, audio }};
    }}).filter(x => x.thai);

    return {{ rank, word, rom, meaning, usage, examples, collocs }};
  }}

  function escapeHtml(s) {{
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }}

  function makeSpeakButton(text, className) {{
    return '<button class="' + className + '" type="button" data-thai="' + escapeHtml(text) + '">🔊</button>';
  }}

  function favCardHTML(data) {{
    const firstEx = data.examples[0];
    const examplesMore = data.examples.slice(1);
    const meaningLine = [data.meaning.zh, data.meaning.en].filter(Boolean).join(" ｜ ");

    const collocHTML = data.collocs.length ? data.collocs.map(c => `
      <button class="colloc-chip" type="button" data-thai="${{escapeHtml(c.audio || c.thai)}}">
        <span class="thai">${{escapeHtml(c.thai)}}</span>
        ${{c.en ? `<span class="en-colloc">${{escapeHtml(c.en)}}</span>` : ""}}
      </button>
    `).join("") : '<div class="en">No collocations found.</div>';

    const moreExamplesHTML = examplesMore.length ? examplesMore.map(ex => `
      <div class="tf-fav-example">
        ${{makeSpeakButton(ex.audio || ex.thai, "speak mini")}}
        <div>
          <div class="thai">${{escapeHtml(ex.thai)}}</div>
          <div class="rom">${{escapeHtml(ex.rom)}}</div>
          <div class="en">${{escapeHtml(ex.en)}}</div>
          <div class="zh">${{escapeHtml(ex.zh)}}</div>
        </div>
      </div>
    `).join("") : '<div class="en">No more examples.</div>';

    return `
      <article class="tf-fav-card" data-rank="${{escapeHtml(data.rank)}}">
        <div class="tf-fav-rank">#${{escapeHtml(data.rank)}}</div>
        <div class="tf-fav-head">
          ${{makeSpeakButton(data.word, "speak")}}
          <div>
            <div class="tf-fav-word">${{escapeHtml(data.word)}}</div>
            <div class="tf-fav-rom">${{escapeHtml(data.rom)}}</div>
            <div class="tf-fav-meaning">${{escapeHtml(meaningLine)}}</div>
          </div>
        </div>

        ${{firstEx ? `
          <div class="tf-fav-example">
            ${{makeSpeakButton(firstEx.audio || firstEx.thai, "speak mini")}}
            <div>
              <div class="thai">${{escapeHtml(firstEx.thai)}}</div>
              <div class="rom">${{escapeHtml(firstEx.rom)}}</div>
              <div class="en">${{escapeHtml(firstEx.en)}}</div>
              <div class="zh">${{escapeHtml(firstEx.zh)}}</div>
            </div>
          </div>
        ` : ""}}

        <details class="tf-fav-details">
          <summary>展開更多：Usage / Collocations / Examples</summary>

          <div class="tf-fav-section">
            <div class="tf-fav-section-title">Usage</div>
            <div>${{escapeHtml(data.usage || "No usage note found.")}}</div>
          </div>

          <div class="tf-fav-section">
            <div class="tf-fav-section-title">Collocations</div>
            <div>${{collocHTML}}</div>
          </div>

          <div class="tf-fav-section">
            <div class="tf-fav-section-title">More Examples</div>
            ${{moreExamplesHTML}}
          </div>
        </details>

        <div class="tf-fav-actions">
          <button type="button" class="tf-fav-action remove" data-remove-rank="${{escapeHtml(data.rank)}}">移除收藏</button>
          <button type="button" class="tf-fav-action" data-jump-rank="${{escapeHtml(data.rank)}}">看完整卡片</button>
        </div>
      </article>
    `;
  }}

  function ensureFavPanel() {{
    let favPanel = document.getElementById("favs") || document.getElementById("favorites");
    let favTab = document.querySelector('.tab[data-tab="favs"], .tab[data-tab="favorites"]');

    const tabs = document.querySelector(".tabs");
    const lastPanel = Array.from(document.querySelectorAll(".panel")).pop();

    if (!favTab && tabs) {{
      favTab = document.createElement("button");
      favTab.className = "tab";
      favTab.dataset.tab = "favs";
      favTab.type = "button";
      favTab.textContent = "我的收藏";
      tabs.appendChild(favTab);
    }}

    if (!favPanel) {{
      favPanel = document.createElement("section");
      favPanel.id = "favs";
      favPanel.className = "panel";
      favPanel.innerHTML = `
        <h2>Favorites｜我的收藏</h2>
        <div class="tf-favs-wrap" id="tfFavsRoot"></div>
      `;
      if (lastPanel) {{
        lastPanel.insertAdjacentElement("afterend", favPanel);
      }} else {{
        document.body.appendChild(favPanel);
      }}
    }} else if (!favPanel.querySelector("#tfFavsRoot")) {{
      favPanel.innerHTML = `
        <h2>Favorites｜我的收藏</h2>
        <div class="tf-favs-wrap" id="tfFavsRoot"></div>
      `;
    }}

    return favPanel;
  }}

  function renderFavs() {{
    ensureFavPanel();
    const root = document.getElementById("tfFavsRoot");
    if (!root) return;

    const favs = favArray();
    const cards = favs.map(rank => document.querySelector(`.word-card[data-rank="${{CSS.escape(String(rank))}}"]`)).filter(Boolean);

    if (!cards.length) {{
      root.innerHTML = `
        <div class="tf-empty-favs">
          <h3>還沒有收藏字卡</h3>
          <p>到 Vocabulary Cards 點星星，就會出現在這裡。</p>
        </div>
      `;
      updateFavUI();
      return;
    }}

    root.innerHTML = `
      <div class="tf-favs-toolbar">
        <div>
          <h2 style="margin:0;">Favorites｜輕量複習字卡</h2>
          <div class="subtitle">預設只放重點；忘記時再展開 Usage / Collocations / Examples。</div>
        </div>
        <div class="tf-favs-count">已收藏 ${{cards.length}} 字</div>
      </div>
      <div class="tf-favs-grid">
        ${{cards.map(card => favCardHTML(cardData(card))).join("")}}
      </div>
    `;
    updateFavUI();
  }}

  function activateTab(tabName) {{
    const targetName = tabName === "favorites" ? "favs" : tabName;
    document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", (t.dataset.tab === targetName || (targetName === "favs" && t.dataset.tab === "favorites"))));
    document.querySelectorAll(".panel").forEach(p => p.classList.toggle("active", p.id === targetName || (targetName === "favs" && p.id === "favorites")));
    if (targetName === "favs") renderFavs();
  }}

  function toggleFavorite(card) {{
    const rank = getCardRank(card);
    if (!rank) return;
    const favs = favSet();
    if (favs.has(rank)) favs.delete(rank);
    else favs.add(rank);
    saveFavs(favs);
    updateFavUI();
    renderFavs();
  }}

  function removeFavorite(rank) {{
    const favs = favSet();
    favs.delete(String(rank));
    saveFavs(favs);
    updateFavUI();
    renderFavs();
  }}

  function jumpToCard(rank) {{
    activateTab("cards");
    const card = document.querySelector(`.word-card[data-rank="${{CSS.escape(String(rank))}}"]`);
    if (!card) return;
    card.scrollIntoView({{ behavior: "smooth", block: "center" }});
    card.classList.remove("tf-fav-highlight");
    void card.offsetWidth;
    card.classList.add("tf-fav-highlight");
  }}

  function initPatch() {{
    ensureFavButtons();
    ensureFavPanel();
    updateFavUI();

    window.addEventListener("click", function(e) {{
      const audioTarget = getThaiFromAudioTarget(e.target);
      if (audioTarget) {{
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        speakThai(audioTarget.text, audioTarget.btn, audioTarget.chip);
        return;
      }}

      const favBtn = e.target.closest(".fav-btn");
      if (favBtn) {{
        const card = favBtn.closest(".word-card");
        if (card) {{
          e.preventDefault();
          e.stopPropagation();
          e.stopImmediatePropagation();
          toggleFavorite(card);
        }}
        return;
      }}

      const removeBtn = e.target.closest("[data-remove-rank]");
      if (removeBtn) {{
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        removeFavorite(removeBtn.dataset.removeRank);
        return;
      }}

      const jumpBtn = e.target.closest("[data-jump-rank]");
      if (jumpBtn) {{
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        jumpToCard(jumpBtn.dataset.jumpRank);
        return;
      }}

      const tab = e.target.closest(".tab[data-tab]");
      if (tab && (tab.dataset.tab === "favs" || tab.dataset.tab === "favorites")) {{
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        activateTab("favs");
      }}
    }}, true);

    renderFavs();
  }}

  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", initPatch);
  }} else {{
    initPatch();
  }}
}})();
</script>
{JS_MARKER_END}
""".strip()


def remove_existing_patch(html: str) -> str:
    css_pattern = re.compile(
        re.escape(CSS_MARKER_START) + r".*?" + re.escape(CSS_MARKER_END),
        re.DOTALL,
    )
    js_pattern = re.compile(
        re.escape(JS_MARKER_START) + r".*?" + re.escape(JS_MARKER_END),
        re.DOTALL,
    )
    html = css_pattern.sub("", html)
    html = js_pattern.sub("", html)
    return html


def inject_patch(html: str) -> str:
    html = remove_existing_patch(html)

    if "</style>" not in html:
        raise ValueError("找不到 </style>，無法注入 CSS。")
    html = html.replace("</style>", "\n" + PATCH_CSS + "\n</style>", 1)

    if "</body>" not in html:
        raise ValueError("找不到 </body>，無法注入 JS。")
    html = html.replace("</body>", "\n" + PATCH_JS + "\n</body>", 1)

    return html


def patch_file(path: Path, dry_run: bool = False, backup: bool = True) -> str:
    original = path.read_text(encoding="utf-8")
    patched = inject_patch(original)

    if patched == original:
        return "OK no change"

    if dry_run:
        return "WOULD PATCH"

    if backup:
        backup_path = path.with_suffix(path.suffix + ".bak")
        if not backup_path.exists():
            backup_path.write_text(original, encoding="utf-8")

    path.write_text(patched, encoding="utf-8")
    return "PATCHED"


def find_files(base_dir: Path) -> list[Path]:
    return sorted(base_dir.glob("thai-frequency-rank*-notes-audio.html"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="HTML 檔案所在資料夾")
    parser.add_argument("--dry-run", action="store_true", help="只預覽，不修改")
    parser.add_argument("--no-backup", action="store_true", help="不要產生 .bak 備份")
    args = parser.parse_args()

    base_dir = Path(args.dir).expanduser().resolve()
    files = find_files(base_dir)

    if not files:
      print(f"找不到檔案：{base_dir}/thai-frequency-rank*-notes-audio.html")
      return

    for file in files:
        try:
            status = patch_file(file, dry_run=args.dry_run, backup=not args.no_backup)
            print(f"{status:12} {file.name}")
        except Exception as e:
            print(f"ERROR       {file.name}: {e}")

    if args.dry_run:
        print("\nDry run 完成：尚未修改檔案。確認沒問題後執行：python3 patch_thai_frequency_ui.py")
    else:
        print("\n完成。若有備份，會在原檔旁產生 .html.bak。")


if __name__ == "__main__":
    main()
