"""Verify relative_path,sha256 CSV manifests; fail closed on missing/unsafe paths."""
import argparse,csv,hashlib
from pathlib import Path

def verify(manifest,root):
    root=Path(root).resolve();errors=[];count=0
    with Path(manifest).open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            count+=1;name=row['relative_path'];p=(root/name).resolve()
            if not p.is_relative_to(root):errors.append(f'UNSAFE_PATH {name}');continue
            if not p.is_file():errors.append(f'MISSING {name}');continue
            h=hashlib.sha256()
            with p.open('rb') as item:
                while chunk:=item.read(1024*1024):h.update(chunk)
            if h.hexdigest()!=row['sha256'].lower():errors.append(f'HASH_MISMATCH {name}')
    if count==0:errors.append('EMPTY_MANIFEST')
    return count,errors

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('manifest');parser.add_argument('--root',default='.')
    args=parser.parse_args();count,errors=verify(args.manifest,args.root)
    print('\n'.join(errors) if errors else f'MANIFEST_PASS files={count}')
    raise SystemExit(1 if errors else 0)
