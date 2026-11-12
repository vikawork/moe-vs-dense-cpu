"""Declared HTTPS model download; verifies bytes before publishing a cache entry."""
import hashlib
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

files = json.loads(sys.argv[1])
for item in files:
    url = item["url"]
    if urllib.parse.urlsplit(url).scheme != "https":
        raise RuntimeError("HTTPS required")
    path = pathlib.Path("/work") / item["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        h = hashlib.sha256()
        with path.open("rb") as src:
            for block in iter(lambda: src.read(8 * 1024 * 1024), b""):
                h.update(block)
        if h.hexdigest() != item["sha256"] or path.stat().st_size != item["size"]:
            raise RuntimeError(f"cached model hash mismatch: {path}")
        print(f"verified cached {item['path']}", flush=True)
        continue
    part = path.with_suffix(path.suffix + ".partial")
    h = hashlib.sha256()
    size = 0
    print(f"download {url}", flush=True)
    with urllib.request.urlopen(url, timeout=120) as response, part.open("wb") as dst:
        if urllib.parse.urlsplit(response.url).scheme != "https":
            raise RuntimeError("non-HTTPS redirect refused")
        for block in iter(lambda: response.read(8 * 1024 * 1024), b""):
            h.update(block)
            size += len(block)
            dst.write(block)
    if h.hexdigest() != item["sha256"] or size != item["size"]:
        raise RuntimeError(f"download hash/size mismatch: {item['path']}")
    os.rename(part, path)
    print(json.dumps(dict(path=item["path"], bytes=size, sha256=h.hexdigest())), flush=True)
