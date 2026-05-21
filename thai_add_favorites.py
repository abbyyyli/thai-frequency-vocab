#!/usr/bin/env python3
"""
thai_add_favorites.py
─────────────────────────────────────────────────────────────────────────────
批量為 thai-frequency-rank*-notes-audio.html 加入「收藏不熟單字」功能。

使用方式：
  python thai_add_favorites.py              # 處理當前目錄的所有符合檔案
  python thai_add_favorites.py --dir /path  # 指定目錄
  python thai_add_favorites.py --dry-run    # 預覽，不實際寫入
"""

import re, sys, glob, os, argparse

# ─── CSS ──────────────────────────────────────────────────────────────────────
FAV_CSS = """
    /* ── 收藏功能 (auto-injected) ──────────────────────────────────────────── */
    .fav-btn {
      position: absolute; right: 14px; bottom: 13px;
      width: 30px; height: 30px;
      border: .5px solid transparent;
      background: rgba(255,255,255,.7);
      border-radius: 50%; cursor: pointer;
      font-size: 17px; line-height: 1; padding: 0;
      display: flex; align-items: center; justify-content: center;
      transition: transform .15s, border-color .15s; color: #d1d5db;
    }
    .fav-btn:hover { transform: scale(1.18); border-color: rgba(245,158,11,.4); }
    .fav-btn.faved { color: #f59e0b; border-color: rgba(245,158,11,.45); background: rgba(255,247,237,.85); }
    .word-card.fav-hidden { display: none !important; }
    #showFav { white-space: nowrap; }
    #showFav.active { background: #fff7ed; border-color: rgba(245,158,11,.55); color: #9a3412; font-weight: 700; }
    #favCount {
      font-size: 13px; color: var(--muted, #6b7280);
      border: .5px solid var(--line, rgba(120,130,140,.25));
      border-radius: 999px; padding: 5px 10px;
      background: rgba(255,255,255,.58); white-space: nowrap;
    }
    /* 收藏 tab 面板 */
    .fav-mini-card {
      background: var(--card); border: .5px solid var(--line);
      border-radius: 18px; padding: 14px 40px 14px 16px;
      cursor: pointer; position: relative;
      transition: box-shadow .15s, transform .1s;
    }
    .fav-mini-card:hover { box-shadow: 0 6px 20px rgba(15,23,42,.1); transform: translateY(-1px); }
    .fav-mini-card .fmc-rank { font-size: 11px; color: var(--muted); }
    .fav-mini-card .fmc-word { font-size: 26px; font-weight: 700; line-height: 1.2; margin: 2px 0;
      font-family: "Noto Sans Thai", "Tahoma", sans-serif; }
    .fav-mini-card .fmc-rom  { font-size: 12px; color: #6b7280; font-family: ui-monospace, monospace; }
    .fav-mini-card .fmc-zh   { font-size: 13px; margin-top: 8px; font-weight: 500; }
    .fav-mini-card .fmc-remove {
      position: absolute; top: 10px; right: 12px;
      background: none; border: none; cursor: pointer;
      font-size: 18px; color: #f59e0b; padding: 0; line-height: 1;
      transition: transform .15s;
    }
    .fav-mini-card .fmc-remove:hover { transform: scale(1.25); }
    #favs-empty { text-align: center; padding: 60px 20px; color: var(--muted, #6b7280); }
    #favs-empty p { margin: 6px 0; }
    .fav-jump-hint {
      font-size: 12px; color: var(--muted, #6b7280);
      text-align: right; margin-top: 6px;
    }
    @keyframes fav-highlight {
      0%   { outline: 3px solid #f59e0b; outline-offset: 4px; }
      80%  { outline: 3px solid #f59e0b; outline-offset: 4px; }
      100% { outline: 0px solid transparent; outline-offset: 0; }
    }
    .fav-highlight { animation: fav-highlight 1.6s ease forwards; }
"""

# ─── 控制列按鈕 HTML（注入到 playVisible 按鈕之後）─────────────────────────────
FAV_CONTROLS_INLINE = (
    '<button class="btn" id="showFav">只看收藏 ★</button>'
    '<span id="favCount">已收藏 0 字</span>'
)

# ─── JavaScript（注入到 </body> 之前）─────────────────────────────────────────
FAV_JS = r"""
  <!-- ── 收藏功能 (auto-injected) ─────────────────────────────────────────── -->
  <script>
  (function () {
    'use strict';

    var FILE_KEY  = location.pathname.split('/').pop() || 'thai_vocab';
    var STORE_KEY = 'fav__' + FILE_KEY;
    var favs      = new Set(JSON.parse(localStorage.getItem(STORE_KEY) || '[]'));
    var filterOn  = false;

    function save() {
      localStorage.setItem(STORE_KEY, JSON.stringify(Array.from(favs)));
    }

    function updateCount() {
      var el = document.getElementById('favCount');
      if (el) el.textContent = '已收藏 ' + favs.size + ' 字';
      var badge = document.getElementById('favTabBadge');
      if (badge) badge.textContent = favs.size ? String(favs.size) : '';
    }

    function applyFilter() {
      document.querySelectorAll('.word-card').forEach(function (card) {
        card.classList.toggle('fav-hidden', filterOn && !favs.has(card.dataset.rank));
      });
    }

    /* ── 星號按鈕 ─────────────────────────────────────────────────────────── */
    function makeFavBtn(card) {
      var rank   = card.dataset.rank;
      var isFaved = favs.has(rank);
      var btn    = document.createElement('button');
      btn.className    = 'fav-btn' + (isFaved ? ' faved' : '');
      btn.dataset.rank = rank;
      btn.setAttribute('aria-label', isFaved ? '取消收藏' : '加入收藏');
      btn.title        = '標記為不熟悉的字';
      btn.textContent  = isFaved ? '★' : '☆';

      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        if (favs.has(rank)) {
          favs.delete(rank);
          btn.textContent = '☆';
          btn.classList.remove('faved');
          btn.setAttribute('aria-label', '加入收藏');
        } else {
          favs.add(rank);
          btn.textContent = '★';
          btn.classList.add('faved');
          btn.setAttribute('aria-label', '取消收藏');
        }
        save();
        updateCount();
        if (filterOn) applyFilter();
        if (document.getElementById('favs') &&
            document.getElementById('favs').classList.contains('active')) {
          renderFavCards();
        }
      });
      return btn;
    }

    function injectButtons() {
      document.querySelectorAll('.word-card').forEach(function (card) {
        if (card.querySelector('.fav-btn')) return;
        card.appendChild(makeFavBtn(card));
      });
    }

    /* ── 收藏 Tab 面板 ────────────────────────────────────────────────────── */
    function getCardData(rank) {
      var card = document.querySelector('.word-card[data-rank="' + rank + '"]');
      if (!card) return null;
      var romEl     = card.querySelector('.rom');
      var meaningEl = card.querySelector('.meaning b');
      var enEl      = card.querySelector('.meaning span');
      return {
        rank:    rank,
        word:    card.dataset.word || '',
        rom:     romEl     ? romEl.firstChild.textContent.trim() : '',
        meaning: meaningEl ? meaningEl.textContent.trim() : '',
        en:      enEl      ? enEl.textContent.trim() : '',
      };
    }

    function jumpToCard(rank) {
      var cardsTab = document.querySelector('.tab[data-tab="cards"]');
      if (cardsTab) cardsTab.click();
      setTimeout(function () {
        var target = document.querySelector('.word-card[data-rank="' + rank + '"]');
        if (!target) return;
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        target.classList.remove('fav-highlight');
        void target.offsetWidth; /* reflow to restart animation */
        target.classList.add('fav-highlight');
        target.addEventListener('animationend', function () {
          target.classList.remove('fav-highlight');
        }, { once: true });
      }, 150);
    }

    function renderFavCards() {
      var panel = document.getElementById('favs');
      if (!panel) return;
      var ranks = Array.from(favs).sort(function (a, b) {
        return parseInt(a, 10) - parseInt(b, 10);
      });

      if (!ranks.length) {
        panel.innerHTML =
          '<div id="favs-empty">' +
          '<p style="font-size:44px;margin:0">☆</p>' +
          '<p style="font-size:16px;font-weight:500">還沒有收藏的字</p>' +
          '<p style="font-size:13px">在單字卡右下角點 ☆ 來標記不熟悉的字</p>' +
          '</div>';
        return;
      }

      panel.innerHTML =
        '<h2 style="font-size:22px;margin:0 0 4px">我的收藏</h2>' +
        '<p style="color:var(--muted,#6b7280);font-size:13px;margin:0 0 16px">' +
        '點擊字卡跳至完整內容 ▸ 收藏狀態自動儲存於瀏覽器</p>' +
        '<div class="grid" id="favGrid"></div>';

      var grid = panel.querySelector('#favGrid');

      ranks.forEach(function (rank) {
        var d = getCardData(rank);
        if (!d) return;

        var mc = document.createElement('div');
        mc.className = 'fav-mini-card';
        mc.setAttribute('role', 'button');
        mc.setAttribute('tabindex', '0');
        mc.innerHTML =
          '<div class="fmc-rank">#' + d.rank + '</div>' +
          '<div class="fmc-word">' + d.word + '</div>' +
          '<div class="fmc-rom">' + d.rom + '</div>' +
          '<div class="fmc-zh">' + d.meaning +
            ' <span style="color:var(--muted,#6b7280);font-weight:400">' + d.en + '</span>' +
          '</div>' +
          '<div class="fav-jump-hint">點擊看完整卡片 →</div>' +
          '<button class="fmc-remove" aria-label="取消收藏" title="取消收藏">★</button>';

        mc.querySelector('.fmc-remove').addEventListener('click', function (e) {
          e.stopPropagation();
          favs.delete(rank);
          save();
          updateCount();
          var starBtn = document.querySelector('.fav-btn[data-rank="' + rank + '"]');
          if (starBtn) {
            starBtn.textContent = '☆';
            starBtn.classList.remove('faved');
            starBtn.setAttribute('aria-label', '加入收藏');
          }
          if (filterOn) applyFilter();
          renderFavCards();
        });

        mc.addEventListener('click', function () { jumpToCard(rank); });
        mc.addEventListener('keydown', function (e) {
          if (e.key === 'Enter' || e.key === ' ') jumpToCard(rank);
        });
        grid.appendChild(mc);
      });
    }

    /* ── 建立「我的收藏」頁籤 ────────────────────────────────────────────── */
    function setupFavTab() {
      /* 1. panel section */
      var favsPanel     = document.createElement('section');
      favsPanel.id      = 'favs';
      favsPanel.className = 'panel';
      var wrap = document.querySelector('.wrap');
      if (wrap) wrap.appendChild(favsPanel);

      /* 2. tab button */
      var tabsNav = document.querySelector('.tabs');
      if (!tabsNav) return;

      var favTab       = document.createElement('button');
      favTab.className = 'tab';
      favTab.dataset.tab = 'favs';
      favTab.innerHTML =
        '我的收藏' +
        ' <span id="favTabBadge" style="' +
          'display:inline-block;background:#f59e0b;color:#fff;' +
          'border-radius:999px;padding:0 6px;font-size:11px;font-weight:700;' +
          'margin-left:4px;min-width:16px;text-align:center;line-height:18px;' +
          'vertical-align:middle' +
        '"></span>';
      tabsNav.appendChild(favTab);

      /* 3. 收藏 tab 點擊 */
      favTab.addEventListener('click', function () {
        document.querySelectorAll('.tab[data-tab]').forEach(function (t) {
          t.classList.remove('active');
        });
        document.querySelectorAll('.panel').forEach(function (p) {
          p.classList.remove('active');
        });
        favTab.classList.add('active');
        favsPanel.classList.add('active');
        renderFavCards();
      });

      /* 4. 現有 tab 點擊時隱藏 favs panel（舊 NodeList 不含新 panel，需手動修補） */
      document.querySelectorAll('.tab[data-tab]').forEach(function (btn) {
        if (btn === favTab) return;
        btn.addEventListener('click', function () {
          favsPanel.classList.remove('active');
          favTab.classList.remove('active');
        });
      });
    }

    /* ── 「只看收藏」filter 按鈕 ─────────────────────────────────────────── */
    function bindShowFav() {
      var btn = document.getElementById('showFav');
      if (!btn || btn._favBound) return;
      btn._favBound = true;
      btn.addEventListener('click', function () {
        filterOn = !filterOn;
        btn.classList.toggle('active', filterOn);
        btn.textContent = filterOn ? '顯示全部' : '只看收藏 ★';
        applyFilter();
      });
    }

    /* ── 初始化 ──────────────────────────────────────────────────────────── */
    function init() {
      injectButtons();
      bindShowFav();
      setupFavTab();
      updateCount();

      var grid = document.getElementById('wordGrid');
      if (grid) {
        new MutationObserver(function () {
          injectButtons();
          updateCount();
        }).observe(grid, { childList: true, subtree: false });
      }
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  })();
  </script>
"""

# ─── 注入邏輯 ─────────────────────────────────────────────────────────────────
def inject(html: str) -> tuple[str, bool]:
    if 'fav-btn' in html:
        return html, False  # 已注入，跳過

    original = html

    # ① CSS → 插入第一個 </style> 之前
    html = html.replace('</style>', FAV_CSS + '</style>', 1)

    # ② 控制列按鈕 → 插在 id="playVisible" 的 </button> 之後
    html, _ = re.subn(
        r'(<button[^>]+id=["\']playVisible["\'][^>]*>.*?</button>)',
        r'\1' + FAV_CONTROLS_INLINE,
        html, count=1, flags=re.DOTALL,
    )

    # ③ JavaScript → 插在 </body> 之前
    html = html.replace('</body>', FAV_JS + '</body>', 1)

    return html, (html != original)


# ─── 主程式 ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='批量為泰文詞頻 HTML 加入收藏功能')
    parser.add_argument('--dir', default='.', help='HTML 所在目錄（預設：當前目錄）')
    parser.add_argument('--dry-run', action='store_true', help='預覽，不實際寫入')
    args = parser.parse_args()

    pattern = os.path.join(args.dir, 'thai-frequency-rank*-notes-audio.html')
    files   = sorted(glob.glob(pattern))

    if not files:
        print(f'❌  找不到符合的檔案：{pattern}')
        sys.exit(1)

    mode = '（dry-run）' if args.dry_run else ''
    print(f'找到 {len(files)} 個檔案 {mode}\n')

    ok = skip = err = 0

    for path in files:
        fname = os.path.basename(path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                original = f.read()

            new_html, changed = inject(original)

            if not changed:
                print(f'  ⏭  {fname}  （已注入，跳過）')
                skip += 1
                continue

            if args.dry_run:
                print(f'  🔍 {fname}  → 將會注入（未寫入）')
                ok += 1
                continue

            # 備份原始檔（只在第一次執行時建立）
            bak = path + '.bak'
            if not os.path.exists(bak):
                with open(bak, 'w', encoding='utf-8') as f:
                    f.write(original)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_html)

            print(f'  ✅  {fname}')
            ok += 1

        except Exception as e:
            print(f'  ❌  {fname}  錯誤：{e}')
            err += 1

    print(f'\n完成：修改 {ok} ｜ 跳過 {skip} ｜ 錯誤 {err}')
    if ok and not args.dry_run:
        print('原始檔備份為 *.html.bak（僅第一次建立）')


if __name__ == '__main__':
    main()
