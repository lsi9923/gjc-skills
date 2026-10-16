"""Edit only top-level model fields, validate TOML, and repair exported link stubs."""
import json
import pathlib
import re
import sys
import tomllib


def model_toml(text, model):
    data = tomllib.loads(text.lstrip('\ufeff'))
    fields = {'model': model, 'model_reasoning_effort': 'high'}
    lines = text.lstrip('\ufeff').splitlines(keepends=True)
    newline = '\r\n' if '\r\n' in text else '\n'
    multiline = None
    in_table = False
    found = set()
    output = []
    for line in lines:
        if multiline is None and re.match(r'^\s*\[', line):
            in_table = True
        if multiline is None and not in_table:
            match = re.match(r'^(\s*)(model|model_reasoning_effort)\s*=\s*("(?:[^"\\]|\\.)*"|\'(?:[^\']*)\')(.*?)(\r?\n)?$', line)
            if match:
                key = match[2]
                output.append(f'{match[1]}{key} = {json.dumps(fields[key])}{match[4]}{match[5] or ""}')
                found.add(key)
                continue
        # Scan TOML strings/comments so embedded Markdown tables are not TOML tables.
        i = 0
        while i < len(line):
            if multiline:
                if line.startswith(multiline, i) and (multiline == "'''" or i == 0 or line[i-1] != '\\'):
                    i += 3
                    multiline = None
                else:
                    i += 1
            elif line[i] == '#':
                break
            elif line.startswith('"""', i) or line.startswith("'''", i):
                multiline = line[i:i+3]
                i += 3
            elif line[i] in "\"'":
                quote = line[i]
                i += 1
                while i < len(line):
                    if quote == '"' and line[i] == '\\':
                        i += 2
                    elif line[i] == quote:
                        i += 1
                        break
                    else:
                        i += 1
            else:
                i += 1
        output.append(line)
    prefix = ''.join(f'{key} = {json.dumps(value)}{newline}' for key, value in fields.items() if key not in found)
    result = prefix + ''.join(output)
    after = tomllib.loads(result)
    expected = dict(data, **fields)
    if after != expected:
        raise ValueError('TOML edit changed unrelated fields')
    return result


def load_role(path, shared_skills, codex_skills):
    text = path.read_bytes().decode('utf-8-sig')
    try:
        tomllib.loads(text)
        return text, False
    except tomllib.TOMLDecodeError:
        stub = text.strip()
        match = re.fullmatch(r'(?:\.\./)+skills/([a-z0-9-]+)/agents/codex\.toml', stub)
        if not match:
            raise
        # The old exported symlink points two directories too high on Windows.
        for root in (shared_skills, codex_skills):
            candidate = root / match[1] / 'agents' / 'codex.toml'
            if candidate.is_file():
                source = candidate.read_bytes().decode('utf-8-sig')
                tomllib.loads(source)
                return source, True
        raise ValueError(f'Missing source for role {path.name}')


def plan(codex_home, shared_skills, model):
    entries = []
    config = codex_home / 'config.toml'
    if not config.is_file():
        raise ValueError('Codex config.toml is missing; run setup first')
    entries.append((config, model_toml(config.read_bytes().decode('utf-8-sig'), model), False))
    for path in sorted((codex_home / 'agents').glob('*.toml')):
        source, repaired = load_role(path, shared_skills, codex_home / 'skills')
        entries.append((path, model_toml(source, model), repaired))
    return entries


def main():
    request = json.loads(sys.stdin.read())
    codex_home = pathlib.Path(request['codexHome'])
    if request.get('action') == 'audit':
        files = [codex_home / 'config.toml', *sorted((codex_home / 'agents').glob('*.toml'))]
        for path in files:
            data = tomllib.loads(path.read_bytes().decode('utf-8-sig'))
            if data.get('model') != request['model'] or data.get('model_reasoning_effort') != 'high':
                raise ValueError('A role does not use the requested model/effort')
        print(json.dumps({'validatedRoles': len(files)-1, 'allGPT6High': True}))
        return
    entries = plan(codex_home, pathlib.Path(request['sharedSkills']), request['model'])
    backup = pathlib.Path(request['backup'])
    manifest = []
    changed = 0
    repaired = 0
    for path, text, repair in entries:
        current = path.read_bytes().decode('utf-8-sig')
        repaired += int(repair)
        if text == current:
            continue
        relative = path.relative_to(codex_home)
        target = backup / 'codex' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        manifest.append({'target': str(path), 'backup': str(target)})
        (backup / 'codex-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        # Preserve UTF-8, comments, prompts, tables, and newline style.
        with path.open('w', encoding='utf-8', newline='') as stream:
            stream.write(text)
        changed += 1
    (backup / 'codex-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'configuredRoles': len(entries)-1, 'changedFiles': changed, 'repairedLinkStubs': repaired}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Do not expose TOML values or credential-bearing source lines.
        print(json.dumps({'error': type(exc).__name__, 'message': 'Agent configuration could not be validated; no unvalidated TOML is written.'}))
        sys.exit(1)
