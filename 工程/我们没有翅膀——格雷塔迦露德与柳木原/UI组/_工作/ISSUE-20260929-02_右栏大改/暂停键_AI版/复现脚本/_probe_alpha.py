# -*- coding: utf-8 -*-
r"""E5 探针：/images/edits 下「真 alpha」到底哪个组合能拿到（mode 实测）。
只跑 4 次，串行，结果写 _probe_alpha.json。"""
import base64, json, os, time, urllib.request, urllib.error, uuid
from PIL import Image

sys_dir = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(sys_dir), "候选", "_probe")
os.makedirs(OUT, exist_ok=True)
REF = os.path.join(os.path.dirname(sys_dir), "候选", "_ref", "ref_4x.png")
CFG = r"E:\ZCode Workspace\.zcode\v2\provider_config.json"
BASE = "https://api.lyaiapp.com/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

def key():
    d = json.load(open(CFG, encoding="utf-8"))
    for r in d["config"]["providerConfigRules"]["providerRules"]:
        if r["providerId"] == "new-provider-2":
            return r["config"]["access"]["apiKey"]

PROMPT = (
 "Transparent background with a real alpha channel - the PNG must have genuine transparency, "
 "alpha = 0 on every pixel outside the icon's soft glow.\n"
 "Change only the symbol in the middle of this round button: replace the play triangle with a "
 "pause symbol made of two vertical rounded bars. Keep the disc, ring and outer glow unchanged."
)

def body(fields, png):
    b = uuid.uuid4().hex
    out = bytearray()
    for k, v in fields:
        out += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (b, k, v)).encode()
    out += ("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"ref.png\"\r\n"
            "Content-Type: image/png\r\n\r\n" % b).encode()
    out += open(png, "rb").read() + b"\r\n"
    out += ("--%s--\r\n" % b).encode()
    return b, bytes(out)

def call(name, model, extra):
    f = [("model", model), ("prompt", PROMPT), ("n", "1"), ("size", "1024x1024"),
         ("response_format", "b64_json")] + extra
    b, data = body(f, REF)
    req = urllib.request.Request(BASE + "/images/edits", data=data, method="POST",
        headers={"Authorization": "Bearer " + key(),
                 "Content-Type": "multipart/form-data; boundary=" + b,
                 "Accept": "application/json", "User-Agent": UA})
    t0 = time.time()
    rec = dict(name=name, model=model, extra=extra)
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            js = json.loads(r.read().decode())
        raw = base64.b64decode(js["data"][0]["b64_json"])
        p = os.path.join(OUT, "probe_%s.png" % name)
        open(p, "wb").write(raw)
        im = Image.open(p)
        rec.update(http=200, sec=round(time.time()-t0, 1), mode=im.mode, size=list(im.size),
                   file=os.path.basename(p),
                   alpha=("有" if "A" in im.mode else "无"))
    except urllib.error.HTTPError as e:
        rec.update(http=e.code, sec=round(time.time()-t0, 1), err=e.read().decode("utf-8", "replace")[:300])
    except Exception as e:
        rec.update(http=-1, sec=round(time.time()-t0, 1), err=repr(e)[:300])
    print(json.dumps(rec, ensure_ascii=False))
    return rec

res = []
res.append(call("bgparam", "gpt-image-2.5-1k",
                [("background", "transparent")]))
res.append(call("bgparam_fmt", "gpt-image-2.5-1k",
                [("background", "transparent"), ("output_format", "png")]))
res.append(call("gptimage2", "gpt-image-2",
                [("background", "transparent")]))
res.append(call("gemini", "gemini-2.5-flash-image",
                [("background", "transparent")]))
json.dump(res, open(os.path.join(OUT, "_probe_alpha.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("done ->", OUT)
