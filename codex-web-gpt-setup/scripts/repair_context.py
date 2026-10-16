import json
import re
import sys
import tomllib
from pathlib import Path


def tune_context(text):
    original = tomllib.loads(text)
    settings = {"model_context_window": 90000, "model_auto_compact_token_limit": 60000}
    boundary = re.search(r"(?m)^\s*\[", text)
    index = boundary.start() if boundary else len(text)
    top, remainder = text[:index], text[index:]
    for key, value in settings.items():
        pattern = rf"(?m)^{key}\s*=.*$"
        if re.search(pattern, top):
            top = re.sub(pattern, f"{key} = {value}", top)
        else:
            top = top.rstrip() + f"\n{key} = {value}\n\n"
    result = top + remainder
    parsed = tomllib.loads(result)
    expected = {**original, **settings}
    if parsed != expected:
        raise ValueError("Context repair changed unrelated configuration")
    return result


if __name__ == "__main__":
    request = json.load(sys.stdin)
    path = Path(request["path"])
    before = path.read_text(encoding="utf-8-sig")
    after = tune_context(before)
    if before != after:
        backup = Path(request["backup"])
        backup.write_bytes(path.read_bytes())
        path.write_text(after, encoding="utf-8")
    print(json.dumps({"changed": before != after, "contextWindow": 90000, "compactAt": 60000}))
