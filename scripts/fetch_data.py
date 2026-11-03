"""Download the pinned, checksum-verified dataset Release asset."""
from pathlib import Path
import argparse,hashlib,shutil,stat,tempfile,urllib.request,zipfile
ROOT=Path(__file__).resolve().parents[1]
URL='https://github.com/SuNu0/zynq7020-cnn-mnist-fpga2026/releases/download/v3-submission-20261103/datasets.zip'
SHA256='efe4b37a96869a245bd8c8eb9fcb457832cd8277fe533f15d78d41347b753bd7'
def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,help='Use a manually downloaded datasets.zip');args=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='cnn_dataset_') as work:
        archive=args.archive or Path(work)/'datasets.zip'
        if not args.archive:
            print('Downloading',URL,flush=True)
            with urllib.request.urlopen(URL,timeout=120) as source,archive.open('wb') as dest:shutil.copyfileobj(source,dest)
        digest=hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest!=SHA256:raise RuntimeError('DATASET_SHA256_MISMATCH')
        with zipfile.ZipFile(archive) as z:
            for item in z.infolist():
                rel=Path(item.filename);target=(ROOT/rel).resolve()
                if not target.is_relative_to((ROOT/'data').resolve()) or not rel.parts or rel.parts[0]!='data':raise RuntimeError('UNSAFE_ARCHIVE_PATH')
                if stat.S_ISLNK(item.external_attr>>16):raise RuntimeError('SYMLINK_NOT_ALLOWED')
            z.extractall(ROOT)
    print('DATASET_FETCH_PASS')
if __name__=='__main__':main()
