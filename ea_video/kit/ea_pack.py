#!/usr/bin/env python3
"""Goi bo cong cu video EA thanh kit_bundle.b64.txt (tar.gz base64): script, font, brand, docs, vi du.
Model giong / may nghe khong nam trong goi (tu tai tu GitHub releases khi can).
  python3 kit/ea_pack.py            # -> ./kit_bundle.b64.txt (dung o thu muc chua kit/)
"""
import base64, io, os, tarfile, time
KIT = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(KIT)
files = []
for d, _, fs in os.walk(KIT):
    if "models" in d.split(os.sep) or "__pycache__" in d:
        continue
    for f in fs:
        if f.endswith((".py", ".ttf", ".json", ".md", ".txt")) and f != "kit_bundle.b64.txt":
            files.append(os.path.relpath(os.path.join(d, f), ROOT))
files.sort()
stamp = time.strftime("%Y-%m-%d %H:%M")
with open(os.path.join(KIT, "GOI.txt"), "w", encoding="utf-8") as g:
    g.write(f"EA video kit - goi luc {stamp} - {len(files)} file\n" + "\n".join(files) + "\n")
if "kit/GOI.txt" not in files:
    files.append("kit/GOI.txt")
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as t:
    for f in files:
        t.add(os.path.join(ROOT, f), arcname=f)
out = os.path.join(os.getcwd(), "kit_bundle.b64.txt")
open(out, "w").write(base64.b64encode(buf.getvalue()).decode())
print(f"[goi] {out}  {len(files)} file, {os.path.getsize(out) / 1e6:.2f}MB")
