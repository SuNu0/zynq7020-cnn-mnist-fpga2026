"""Strict reusable hexadecimal dump comparison with explicit word width."""
import argparse
from pathlib import Path

def load(path,bits,signed=False):
    if bits<=0:raise ValueError('bits must be positive')
    values=[]
    for token in Path(path).read_text().split():
        value=int(token,16)
        if value<0 or value>=1<<bits:raise ValueError(f'out-of-range {token} for {bits} bits')
        if signed and value>=1<<(bits-1):value-=1<<bits
        values.append(value)
    return values

def compare(a,b,bits,signed=False):
    ref=load(a,bits,signed);got=load(b,bits,signed)
    if len(ref)!=len(got):return False,f'LENGTH_MISMATCH reference={len(ref)} actual={len(got)}'
    for i,(x,y) in enumerate(zip(ref,got)):
        if x!=y:return False,f'VALUE_MISMATCH index={i} reference={x} actual={y}'
    if not ref:return False,'EMPTY_INPUT'
    return True,f'MEM_COMPARE_PASS values={len(ref)} bits={bits} signed={signed}'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('reference');p.add_argument('actual');p.add_argument('--bits',type=int,required=True);p.add_argument('--signed',action='store_true');a=p.parse_args()
    try:ok,msg=compare(a.reference,a.actual,a.bits,a.signed)
    except (ValueError,OSError) as e:ok,msg=False,str(e)
    print(msg);raise SystemExit(0 if ok else 1)
