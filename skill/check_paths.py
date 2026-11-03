"""Check the English-only filename policy; .git is not submission content."""
import argparse,os,re
from pathlib import Path

def check(root):
    root=Path(root);bad=[]
    for folder,dirs,files in os.walk(root):
        dirs[:]=[d for d in dirs if d not in {'.git','.venv','__pycache__','vivado','build'}]
        for name in dirs+files:
            if name not in {'README.md','LICENSE'} and not re.fullmatch(r'[a-z0-9_.-]+',name):bad.append(str((Path(folder)/name).relative_to(root)))
    return bad

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',nargs='?',default='.');a=p.parse_args();bad=check(a.root);print('\n'.join(bad) if bad else 'ENGLISH_PATHS_PASS');raise SystemExit(bool(bad))
