"""Real additional NIST digits with source-ID and writer exclusion."""
import gzip,hashlib,json,lzma,struct,urllib.request,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/qmnist'
BASE='https://raw.githubusercontent.com/facebookresearch/qmnist/master/'
FILES={
 'xnist-images-idx3-ubyte.xz':'7f124b3b8ab81486c9d8c2749c17f834',
 'xnist-labels-idx2-int.xz':'5ed0e788978e45d4a8bd4b7caec3d79d',
 'qmnist-train-labels-idx2-int.gz':'0058f8dd561b90ffdd0f734c6a30e5e4',
 'qmnist-test-labels-idx2-int.gz':'5b5b05890a5e13444e108efe57b788aa'}

def fetch(name,md5=None):
    p=RAW/name
    if not p.is_file():
        for attempt in range(4):
            try:
                with urllib.request.urlopen(BASE+name,timeout=60) as r, p.with_suffix(p.suffix+'.part').open('wb') as f:
                    while chunk:=r.read(1024*1024):f.write(chunk)
                p.with_suffix(p.suffix+'.part').replace(p);break
            except Exception:
                if attempt==3:raise
                time.sleep(2)
    if md5:assert hashlib.md5(p.read_bytes()).hexdigest()==md5,name
    print('DOWNLOAD_VERIFIED',name,p.stat().st_size,flush=True)
    return p

def labels(name):
    p=RAW/name
    data=(lzma.decompress if p.suffix=='.xz' else gzip.decompress)(p.read_bytes())
    magic,n,cols=struct.unpack('>III',data[:12]);assert magic==3074 and cols==8
    return np.frombuffer(data,dtype='>i4',offset=12).reshape(n,cols).astype(np.int64)

def main():
    RAW.mkdir(parents=True,exist_ok=True)
    for n,h in FILES.items():fetch(n,h)
    for n in ['README.md','LICENSE']:fetch(n)
    meta=labels('xnist-labels-idx2-int.xz');mtrain=labels('qmnist-train-labels-idx2-int.gz');mtest=labels('qmnist-test-labels-idx2-int.gz')[:10000]
    ytrain=np.frombuffer((ROOT/'data/train-labels-idx1-ubyte').read_bytes(),np.uint8,offset=8)
    ytest=np.frombuffer((ROOT/'data/t10k-labels-idx1-ubyte').read_bytes(),np.uint8,offset=8)
    assert np.array_equal(mtrain[:,0],ytrain) and np.array_equal(mtest[:,0],ytest),'MNIST/source mapping mismatch'
    assert len(meta)==402953
    raw=RAW/'xnist-images-idx3-ubyte'
    if not raw.is_file():
        with lzma.open(RAW/'xnist-images-idx3-ubyte.xz','rb') as a, raw.open('wb') as b:
            while chunk:=a.read(1024*1024):b.write(chunk)
    header=raw.read_bytes()[:16]
    assert struct.unpack('>IIII',header)==(2051,len(meta),28,28)
    np.save(RAW/'source_metadata.npy',meta)
    # QMNIST source column 5 identifies the same original glyph despite
    # small reconstruction pixel differences. Also exclude duplicate flags.
    forbidden=np.unique(np.concatenate((mtrain[:,5],mtest[:,5])))
    test_writers=np.unique(mtest[:,2])
    eligible=(~np.isin(meta[:,5],forbidden)) & (meta[:,6]==0) & (~np.isin(meta[:,2],test_writers))
    authors=np.unique(meta[eligible,2]);rng=np.random.default_rng(20261025);rng.shuffle(authors)
    # Extra validation/test writers are also distinct from original training writers.
    independent=authors[~np.isin(authors,np.unique(mtrain[:,2]))]
    rng.shuffle(independent)
    nv=max(20,len(independent)//20);nt=nv
    val_authors=independent[:nv];test_authors=independent[nv:nv+nt]
    val_idx=np.flatnonzero(eligible & np.isin(meta[:,2],val_authors))
    test_idx=np.flatnonzero(eligible & np.isin(meta[:,2],test_authors))
    train_idx=np.flatnonzero(eligible & ~np.isin(meta[:,2],np.concatenate((val_authors,test_authors))))
    assert len(train_idx)>55000 and len(val_idx)>1000 and len(test_idx)>1000
    assert not np.intersect1d(meta[train_idx,5],forbidden).size
    assert not np.intersect1d(meta[train_idx,2],np.concatenate((val_authors,test_authors,test_writers))).size
    np.savez(ROOT/'data/v3_splits.npz',extra_train=train_idx,extra_val=val_idx,extra_test=test_idx)
    # Content duplicates, including any held-out MNIST pixels, are removed.
    x=np.memmap(raw,dtype=np.uint8,mode='r',offset=16,shape=(len(meta),28,28))
    mx=np.frombuffer((ROOT/'data/train-images-idx3-ubyte').read_bytes(),np.uint8,offset=16).reshape(-1,28,28)
    tx=np.frombuffer((ROOT/'data/t10k-images-idx3-ubyte').read_bytes(),np.uint8,offset=16).reshape(-1,28,28)
    digest=lambda a:hashlib.blake2b(a.tobytes(),digest_size=16).digest()
    forbidden_pixels={digest(a) for block in [mx[55000:],tx,x[val_idx],x[test_idx]] for a in block}
    seen=set(forbidden_pixels);seen.update(digest(a) for a in mx[:55000]);kept=[]
    for i in train_idx:
        h=digest(x[i])
        if h not in seen:kept.append(int(i));seen.add(h)
    removed=len(train_idx)-len(kept);train_idx=np.array(kept,dtype=np.int64)
    np.savez(ROOT/'data/v3_splits.npz',extra_train=train_idx,extra_val=val_idx,extra_test=test_idx)
    report=dict(source='facebookresearch/qmnist xNIST representation of NIST SD19',source_url='https://github.com/facebookresearch/qmnist',seed=20261025,raw_xnist=402953,mnist_train=55000,mnist_validation=5000,mnist_test=10000,extra_train=len(train_idx),extra_validation=len(val_idx),extra_test=len(test_idx),total_training=55000+len(train_idx),training_increase_factor=(55000+len(train_idx))/55000,mnist_source_ids_excluded=len(forbidden),mnist_test_writers_excluded=len(test_writers),extra_train_writers=len(np.unique(meta[train_idx,2])),extra_validation_writers=len(val_authors),extra_test_writers=len(test_authors),source_id_overlap_with_original_mnist=0,added_train_writer_overlap_with_mnist_test=0,added_train_writer_overlap_with_extra_validation_test=0,removed_pixel_duplicates=removed,added_train_per_digit=np.bincount(meta[train_idx,0],minlength=10).tolist(),files={n:dict(url=BASE+n,md5=h,sha256=hashlib.sha256((RAW/n).read_bytes()).hexdigest()) for n,h in FILES.items()},notes=['Unique source images, not augmentation count.','NIST split is a new custom split, not the standard QMNIST test benchmark.','Original MNIST validation split may share writers with its original training split; additional test/val writers are excluded from all training sources.'])
    (ROOT/'reports/dataset_v3.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('V3_DATA_PREPARATION_PASS',json.dumps(report),flush=True)

if __name__=='__main__':main()
