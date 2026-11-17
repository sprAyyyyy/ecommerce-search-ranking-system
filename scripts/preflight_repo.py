"""Conservative repository preflight for potentially sensitive/unreviewed files."""
import json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
MAX_BYTES=20*1024*1024
EXCLUDE={'.git','.venv','venv','__pycache__','.ipynb_checkpoints'}
BAD_EXT={'.parquet','.pkl','.pickle','.joblib','.pt','.pth','.ckpt','.safetensors','.onnx','.h5','.zip','.7z'}
SECRET_PATTERNS=[
 ('private_key',re.compile(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----')),
 ('aws_access_key',re.compile(r'AKIA[0-9A-Z]{16}')),
 ('github_token',re.compile(r'gh[pousr]_[A-Za-z0-9_]{30,}')),
 ('openai_key',re.compile(r'sk-[A-Za-z0-9_-]{20,}')),
 ('credential_assignment',re.compile(r'(?i)(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*=\s*[\"\'](?!YOUR|PLACEHOLDER)[^\"\']{12,}[\"\']')),
]
problems=[]
for p in root.rglob('*'):
    if not p.is_file() or any(part in EXCLUDE for part in p.relative_to(root).parts): continue
    rel=p.relative_to(root)
    if p.stat().st_size>MAX_BYTES: problems.append(f'LARGE {rel} ({p.stat().st_size} bytes)')
    if p.suffix.lower() in BAD_EXT: problems.append(f'REVIEW BINARY/ARCHIVE {rel}')
    if any(x.lower() in {'data','datasets','checkpoints','models'} for x in rel.parts): problems.append(f'REVIEW DATA/MODELS {rel}')
    if p.name.startswith('.env') and p.name!='.env.example': problems.append(f'ENV FILE {rel}')
    if p.suffix.lower() in {'.py','.md','.txt','.json','.ipynb','.yml','.yaml','.csv','.toml'}:
        try: content=p.read_text(encoding='utf-8')
        except UnicodeDecodeError: problems.append(f'NON UTF-8 {rel}'); continue
        for name,regex in SECRET_PATTERNS:
            # This detector is intentionally conservative and can produce false positives.
            if regex.search(content): problems.append(f'POSSIBLE {name} {rel}')
        if p.suffix.lower()=='.ipynb':
            try:
                nb=json.loads(content)
                outputs=sum(bool(c.get('outputs')) for c in nb.get('cells',[]))
                if outputs: problems.append(f'NOTEBOOK SAVED OUTPUTS {rel} ({outputs} cells)')
            except (ValueError,TypeError): problems.append(f'INVALID NOTEBOOK {rel}')
print('Repository preflight:')
if problems:
    for item in problems:print('  REVIEW:',item)
    sys.exit(1)
print('  PASS: no automatically detected problems.')
print('  Manual review remains required for licensing, proprietary code, PII, and dataset permissions.')
