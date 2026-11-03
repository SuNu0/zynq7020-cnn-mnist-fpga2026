"""Recalculate all 75 saved vectors using current V3 integer reference."""
from pathlib import Path
import importlib.util,sys,tempfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'model'));sys.path.insert(0,str(ROOT/'skill'))
from common import integer_logits
from compare_mem import compare

def main():
    vectors=ROOT/'tb/vectors'
    images=np.array([int(v,16) for v in (vectors/'images.mem').read_text().split()],np.uint8).reshape(-1,28,28)
    assert len(images)==75
    scores,features=integer_logits(images,return_features=True)
    outputs=[('features1',features[0],16,False),('features2',features[1],16,False),('scores',scores,48,True),('predictions',scores.argmax(1),8,False)]
    with tempfile.TemporaryDirectory(prefix='cnn_reference_') as t:
        for name,values,bits,signed in outputs:
            actual=Path(t)/(name+'.mem');actual.write_text('\n'.join(f'{int(v)&((1<<bits)-1):x}' for v in values.flatten()),encoding='ascii')
            ok,msg=compare(vectors/(name+'.mem'),actual,bits,signed);print(name,msg,flush=True);assert ok,msg
    print('V3_REFERENCE_VECTOR_PASS cases=75 pooled_values=105600 scores=750')

if __name__=='__main__':main()
