"""
fix_mobile_audio.py
修正行動裝置（iOS/Android）無法播放音訊。

策略：在 </script> 前注入 capture-phase 攔截器。
- 在 iOS/Android 上，於 capture 階段攔截 .speak 的點擊
- stopImmediatePropagation() 阻止原本的 async handler 執行
- 同步呼叫 speechSynthesis.speak()，iOS Safari 不會封鎖

執行：python3 fix_mobile_audio.py
"""

import glob, os

INJECT = """
// ── Mobile audio fix: iOS/Android capture-phase intercept ──────────────
(function(){
  if(!/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) return;
  document.addEventListener('click', function(e){
    var btn = e.target && e.target.closest && e.target.closest('.speak');
    if(!btn) return;
    e.stopImmediatePropagation();
    window.speechSynthesis && window.speechSynthesis.cancel();
    var text = btn.getAttribute('data-thai') || btn.textContent.trim();
    if(!text) return;
    var u = new SpeechSynthesisUtterance(text);
    u.lang='th-TH'; u.rate=0.82; u.pitch=1.0;
    window.speechSynthesis && window.speechSynthesis.speak(u);
  }, true); // capture phase — runs before all bubble-phase handlers
})();
// ── End mobile audio fix ────────────────────────────────────────────────
"""

MARKER = "Mobile audio fix: iOS/Android capture-phase intercept"

def patch_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        original = f.read()

    if MARKER in original:
        return "⏭️  已是最新版，略過"

    # 找最後一個 </script>
    idx = original.rfind("</script>")
    if idx == -1:
        return "⚠️  找不到 </script>，略過"

    patched = original[:idx] + INJECT + original[idx:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(patched)
    return "✅ 已注入 mobile fix"


def main():
    pattern = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "thai-frequency-rank*-notes-audio.html")
    files = sorted(glob.glob(pattern))

    if not files:
        print("找不到任何 thai-frequency-rank*-notes-audio.html")
        print("請確認此腳本和 HTML 在同一資料夾。")
        return

    print(f"找到 {len(files)} 個檔案\n")
    for path in files:
        status = patch_file(path)
        print(f"  {os.path.basename(path)}\n    {status}\n")
    print("完成！")

if __name__ == "__main__":
    main()
