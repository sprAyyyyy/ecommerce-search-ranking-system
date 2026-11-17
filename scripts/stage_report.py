"""Copy the original, user-reviewed PDF into docs without modifying its content."""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--apply', action='store_true')
    a = p.parse_args()
    source = a.source.expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != '.pdf':
        p.error('Please provide an existing original PDF file')
    if source.stat().st_size > 25*1024*1024:
        p.error('Report is over the GitHub web upload size limit (25 MB)')
    if source.open('rb').read(5) != b'%PDF-':
        p.error('File does not appear to be a PDF')
    target = ROOT/'docs'/'final_technical_report.pdf'
    print(f"{'COPY' if a.apply else 'PLAN'} {source} -> {target}")
    if target.exists():
        p.error('Target already exists: please review before replacing it')
    if a.apply:
        shutil.copyfile(source, target)
        print('Original PDF copied unchanged. Review its text and images before committing.')
    else:
        print('Dry run only; use --apply to copy the reviewed file.')

if __name__ == '__main__':
    main()
