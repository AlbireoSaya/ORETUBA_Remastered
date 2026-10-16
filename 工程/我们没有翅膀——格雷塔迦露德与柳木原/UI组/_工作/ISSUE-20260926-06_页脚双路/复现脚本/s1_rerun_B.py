# -*- coding: utf-8 -*-
r"""s1 · B 路重跑（缺陷件 otv_bklog / otv_gm_bg1 各再跑 2 次 = run3 / run4）

背景（ISSUE-20260926-06 · 页脚落地轮）：
  `_复核_20260926\页脚双路\*_B_生图.png` 采用 pC_deliver.py 的 PICK=run2。实测两件有**图标位置漂移**：
    · otv_bklog  第 1 项图标右移 ≈21px（文字随之右移）
    · otv_gm_bg1 第 2 项「決定」整体左移 ≈47px（图标几乎贴上前一项文字）
  本脚本用**与 pB.py 完全相同的流程与 prompt**（绿叶 /v1/images/edits，模型 gpt-image-2.5-sunburst，
  白底→1024 输入窗口 (880,64)-(1904,1088)，回裁 (880,940)-(1904,1088)）各再跑 2 次，
  产物落 `_证据\B_footer_rerun\`、原始回包落 `_证据\B_raw_rerun\`（**不覆盖既有 B_footer/B_raw 证据**）。
  选优判据见 `复现脚本\s2_icon_disp.py`（图标中心位移量）。

用法：python s1_rerun_B.py            # 两件 × 2 次，并发 2
      python s1_rerun_B.py bklog      # 只重跑 otv_bklog
"""
import base64, json, os, sys, time, urllib.request, urllib.error, uuid, threading, queue
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
RAW = os.path.join(WORK, "_证据", "B_raw_rerun"); os.makedirs(RAW, exist_ok=True)
FB = os.path.join(WORK, "_证据", "B_footer_rerun"); os.makedirs(FB, exist_ok=True)
CFG = r"E:\ZCode Workspace\.zcode\v2\provider_config.json"
API = "https://api.lyaiapp.com/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
MODEL = "gpt-image-2.5-sunburst"

WX0, WY0, WX1, WY1 = 880, 64, 1904, 1088     # 1024x1024 输入窗口
FX0, FY0 = 880, 940                          # 页脚裁片原点（窗口内 1:1）
FW, FH = 1024, 148

# 与 pB.py 逐字一致的 prompt 组块与译名映射（只做这两件）
MAPS = {
    "otv_bklog.png": (["音声の再生", "戻る"], ["语音播放", "返回"]),
    "otv_gm_bg1.png": (["一部の画像表示スクロール", "決定", "戻る"],
                       ["部分图片可滚动查看", "确定", "返回"]),
}
_HEAD = ("This is the BOTTOM FOOTER STRIP of a PlayStation-Vita visual-novel system screen, "
         "sitting on a flat frosted white background with faint blue snowflakes. The footer is a row "
         "of {n} round PlayStation-style button icons; immediately to the right of each icon there is "
         "a Japanese button label rendered in a rounded blue-outline font (near-white letters with a "
         "strong blue edge and a soft blue glow around them).")
_TASK = ("TASK: replace ONLY the Japanese letters with the Simplified Chinese given below. There are "
         "exactly {n} labels, counted left to right. Keep each label in its own place, next to its own "
         "icon.")
_RULES = ("HARD REQUIREMENTS:\n"
          "- Keep every round icon exactly as it is: same shape, same size, same position, same blue "
          "colour, same inner symbol. Do NOT redraw, move, resize, restyle or translate the icons.\n"
          "- Keep the frosted white background and the snowflakes pixel-identical. Add no new "
          "snowflake, no decoration, and no text anywhere else in the image.\n"
          "- Match the label style exactly: same letter height as the Japanese letters it replaces, "
          "near-white fill with a strong blue outline and a soft blue glow, same vertical position.\n"
          "- Each Chinese label replaces the Japanese label at the SAME position, centred on the "
          "Japanese label it replaces and starting right after its icon.\n"
          "- Do not add, remove, move or restyle anything else.")


def make_prompt(n, pairs_text):
    return "\n".join([_HEAD.format(n=n), _TASK.format(n=n), pairs_text, _RULES])


def key():
    d = json.load(open(CFG, encoding="utf-8"))
    for r in d["config"]["providerConfigRules"]["providerRules"]:
        if r["providerId"] == "new-provider-2":
            return r["config"]["access"]["apiKey"]
    raise SystemExit("no key")


def build_input(name):
    p = os.path.join(RAW, "in_" + name)
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    flat = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im).convert("RGB")
    flat.crop((WX0, WY0, WX1, WY1)).save(p)
    return p


def edits(png, prompt, size="auto", timeout=900):
    b = uuid.uuid4().hex
    parts = []

    def f(n, v):
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                      % (b, n, v)).encode("utf-8"))

    f("model", MODEL); f("prompt", prompt)
    f("response_format", "b64_json"); f("n", "1"); f("size", size)
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"in.png\"\r\n"
                  "Content-Type: image/png\r\n\r\n" % b).encode("utf-8"))
    parts.append(open(png, "rb").read())
    parts.append(("\r\n--%s--\r\n" % b).encode("utf-8"))
    req = urllib.request.Request(API + "/images/edits", data=b"".join(parts), method="POST",
        headers={"Authorization": "Bearer " + key(),
                 "Content-Type": "multipart/form-data; boundary=" + b,
                 "Accept": "application/json", "User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return ("ok", json.loads(r.read().decode("utf-8")), time.time() - t0)
    except urllib.error.HTTPError as e:
        return ("http%d" % e.code, e.read().decode("utf-8", "replace")[:400], time.time() - t0)
    except Exception as e:
        return ("err", repr(e)[:300], time.time() - t0)


def one(name, run, size="auto", tries=4):
    jp, cn = MAPS[name]
    pairs = ("Japanese label -> Simplified Chinese replacement:\n"
             + "\n".join("  %d. %s  ->  %s" % (i + 1, a, b) for i, (a, b) in enumerate(zip(jp, cn))))
    prompt = make_prompt(len(jp), pairs)
    inp = build_input(name)
    tag = "%s_run%d" % (name.replace(".png", ""), run)
    st = resp = None
    for attempt in range(tries):
        st, resp, dt = edits(inp, prompt, size=size)
        print("[%s] run%d attempt%d %s  %.1fs  size=%s" % (name, run, attempt + 1, st, dt, size),
              flush=True)
        if st == "ok":
            break
        # 上游临时故障（503 upstream_temporary）与网络抖动属**请求级**失败 ⇒ 退避重试
        if st in ("err",) or (st.startswith("http") and st[4:] in ("429", "500", "502", "503", "504")):
            time.sleep(20 + 10 * attempt)
            continue
        print("   ", str(resp)[:300], flush=True)
        return None
    if st != "ok":
        print("   ", str(resp)[:300], flush=True)
        return None
    raw = base64.b64decode(resp["data"][0]["b64_json"])
    p = os.path.join(RAW, tag + ".png")
    open(p, "wb").write(raw)
    print("   raw out", Image.open(p).size, "->", p, flush=True)
    return p


def to_footer(p, out_name):
    im = Image.open(p).convert("RGB")
    sx = im.width / 1024.0
    sy = im.height / 1024.0
    box = (int((FX0 - WX0) * sx), int((FY0 - WY0) * sy),
           int((FX0 - WX0 + FW) * sx), int((FY0 - WY0 + FH) * sy))
    crop = im.crop(box)
    if crop.size != (FW, FH):
        crop = crop.resize((FW, FH), Image.LANCZOS)
    q = os.path.join(FB, out_name)
    crop.save(q)
    return q


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    jobs = []
    for n, short in (("otv_bklog.png", "bklog"), ("otv_gm_bg1.png", "gm_bg1")):
        if only and only != short:
            continue
        for k in (3, 4):
            jobs.append((n, k))
    q = queue.Queue()
    for j in jobs:
        q.put(j)
    lock = threading.Lock()
    errs = []

    def worker():
        while True:
            try:
                n, k = q.get_nowait()
            except queue.Empty:
                return
            try:
                p = one(n, k)
                if p:
                    to_footer(p, "%s_B_run%d.png" % (n.replace(".png", ""), k))
                else:
                    with lock:
                        errs.append((n, k, "fail"))
            except Exception as e:
                with lock:
                    errs.append((n, k, repr(e)[:150]))

    ths = [threading.Thread(target=worker) for _ in range(2)]
    t0 = time.time()
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    print("done %.0fs  jobs=%d  errs=%s" % (time.time() - t0, len(jobs), errs), flush=True)
