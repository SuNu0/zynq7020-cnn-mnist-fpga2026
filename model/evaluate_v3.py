import json,sys,csv,hashlib
import numpy as np
import torch
from PIL import Image
from common import ROOT,dataset,integer_logits
from train_v3 import CNN,extra
from eval_common import measure,canvases,write_mem
sys.path.insert(0,str(ROOT/'software/pc_web'))
from preprocess import normalize_digit

def predict(x,w):
    return np.concatenate([integer_logits(b,w).argmax(1) for b in np.array_split(x,max(1,(len(x)+63)//64))])

def vectors(x,y,ex,ey):
    folder=ROOT/'tb/vectors';folder.mkdir(exist_ok=True)
    indices=np.concatenate([np.flatnonzero(y==d)[:4] for d in range(10)])
    ei=np.concatenate([np.flatnonzero(ey==d)[:2] for d in range(10)])
    normalized=np.stack([np.asarray(normalize_digit(Image.fromarray(x[np.flatnonzero(y==d)[5]]))) for d in range(10)])
    rng=np.random.default_rng(723)
    stress=np.stack([np.zeros((28,28),np.uint8),np.full((28,28),255,np.uint8),np.indices((28,28)).sum(0).astype(np.uint8)%2*255,rng.integers(0,256,(28,28),dtype=np.uint8)])
    old=np.array([int(t,16) for t in (ROOT/'rtl/testvector/3_0.txt').read_text().split()],np.uint8).reshape(28,28)
    xx=np.concatenate((x[indices],ex[ei],normalized,stress,old[None]));assert len(xx)==75
    scores,f=integer_logits(xx,return_features=True)
    for name,a,bits in [('images',xx,8),('predictions',scores.argmax(1),8),('features1',f[0],16),('features2',f[1],16),('scores',scores,48)]:write_mem(folder/(name+'.mem'),a,bits)
    (folder/'board_images.bin').write_bytes(xx[:40].tobytes());(folder/'board_predictions.bin').write_bytes(scores[:40].argmax(1).astype(np.uint8).tobytes());(folder/'board_labels.bin').write_bytes(y[indices].tobytes())
    (folder/'manifest.json').write_text(json.dumps(dict(count=75,mnist_test_indices=indices.tolist(),new_nist_test_positions=ei.tolist(),normalized_cases=10,stress_cases=5,pooled_values=75*1408,scores=750),indent=2),encoding='utf-8')
    print('V3_VECTORS_READY cases=75',flush=True)

def main():
    torch.set_num_threads(8)
    x,y=dataset(False);ex,ey=extra('test');vectors(x,y,ex,ey)
    w2=np.load(ROOT/'baseline_v2/model/weights_int.npz');w3=np.load(ROOT/'model/weights_int.npz')
    result={};preds={}
    for source,xx,yy in [('mnist',x,y),('nist_new_writers',ex,ey)]:
        for version,w in [('v2',w2),('v3',w3)]:
            key=version+'_'+source;p=predict(xx,w);preds[key]=p;result[key]=measure(p,yy)
            print(key,result[key]['accuracy'],flush=True)
    m=CNN();m.load_state_dict(torch.load(ROOT/'model/cnn_v3.pt',weights_only=True));m.eval()
    with torch.no_grad():
        fp=torch.cat([m(torch.from_numpy(b[:,None].astype(np.float32)/255)).argmax(1) for b in np.array_split(x,40)]).numpy()
    result['v3_float_mnist']=measure(fp,y);result['v3_float_integer_mnist_disagreements']=int((fp!=preds['v3_mnist']).sum())
    raw,norm=canvases(x[:2000])
    for version,w in [('v2',w2),('v3',w3)]:
        for stage,a in [('raw',raw),('normalized',norm)]:
            key=version+'_canvas_'+stage;result[key]=measure(predict(a,w),y[:2000]);print(key,result[key]['accuracy'],flush=True)
    norm_all=np.stack([np.asarray(normalize_digit(Image.fromarray(a))) for a in x])
    for version,w in [('v2',w2),('v3',w3)]:
        key=version+'_mnist_normalized';result[key]=measure(predict(norm_all,w),y);print(key,result[key]['accuracy'],flush=True)
    result['evidence']=dict(checkpoint_selection='Validation only; no test scores used',accuracy_backend='Python integer reference; RTL checked separately',extra_test='Custom NIST holdout: source IDs and writers absent from training, not standard QMNIST benchmark',canvas='Deterministic synthetic MNIST canvas placement/scale test; not real user handwriting',training_count=json.loads((ROOT/'reports/dataset_v3.json').read_text())['total_training'])
    (ROOT/'reports/accuracy_v3.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    with (ROOT/'reports/mnist_v2_v3_predictions.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['index','label','v2_integer','v3_integer','v3_float']);writer.writerows(zip(range(len(y)),y,preds['v2_mnist'],preds['v3_mnist'],fp))
    with (ROOT/'reports/nist_v2_v3_predictions.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['holdout_position','label','v2_integer','v3_integer']);writer.writerows(zip(range(len(ey)),ey,preds['v2_nist_new_writers'],preds['v3_nist_new_writers']))
    print('V3_ACCURACY_EVALUATION_PASS',flush=True)

if __name__=='__main__':main()
