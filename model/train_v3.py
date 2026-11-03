"""Train on 332455 real glyphs. Test images are never used for selection."""
import argparse,json,time,random
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from common import ROOT,dataset

class CNN(nn.Module):
    def __init__(self):
        super().__init__();self.conv1=nn.Conv2d(1,8,5);self.conv2=nn.Conv2d(8,16,5);self.fc=nn.Linear(256,10)
    def forward(self,x):
        x=F.max_pool2d(F.relu(self.conv1(x)),2);x=F.max_pool2d(F.relu(self.conv2(x)),2)
        return self.fc(x.flatten(1))

def extra(split):
    if not (ROOT/'data/qmnist/xnist-images-idx3-ubyte').is_file():
        import subprocess,sys
        subprocess.run([sys.executable,str(ROOT/'scripts/prepare_v3_data.py')],check=True)
    meta=np.load(ROOT/'data/qmnist/source_metadata.npy',mmap_mode='r')
    raw=np.memmap(ROOT/'data/qmnist/xnist-images-idx3-ubyte',dtype=np.uint8,mode='r',offset=16,shape=(len(meta),28,28))
    idx=np.load(ROOT/'data/v3_splits.npz')['extra_'+split]
    return np.array(raw[idx]),np.array(meta[idx,0],dtype=np.int64)

def augment(x):
    n=len(x);angle=(torch.rand(n)*2-1)*.18;scale=.90+torch.rand(n)*.20;shear=(torch.rand(n)*2-1)*.12
    theta=torch.zeros(n,2,3);theta[:,0,0]=angle.cos()*scale;theta[:,0,1]=-angle.sin()+shear;theta[:,1,0]=angle.sin();theta[:,1,1]=angle.cos()*scale;theta[:,:,2]=(torch.rand(n,2)*2-1)*.11
    return F.grid_sample(x,F.affine_grid(theta,x.shape,align_corners=False),align_corners=False)

def export(m):
    q={}
    for layer in ('conv1','conv2','fc'):
        w=np.rint(m.state_dict()[layer+'.weight'].numpy()*4096).astype(np.int64)
        b=np.rint(m.state_dict()[layer+'.bias'].numpy()*255*4096).astype(np.int64)
        assert np.abs(w).max()<32768 and np.abs(b).max()<2**31
        q[layer+'_w']=w;q[layer+'_b']=b
        for suffix,values,bits in [('weight',w,16),('bias',b,32)]:
            (ROOT/'rtl'/f'v3_{layer}_{suffix}.mem').write_text('\n'.join(f'{int(v)&((1<<bits)-1):0{bits//4}x}' for v in values.flatten())+'\n',encoding='ascii')
    np.savez(ROOT/'model/weights_int.npz',**q)

@torch.no_grad()
def correct(model,x,y):
    return int(sum((model(b[:,None].float()/255).argmax(1)==t).sum() for b,t in zip(x.split(512),y.split(512))))

def main():
    p=argparse.ArgumentParser();p.add_argument('--epochs',type=int,default=36);args=p.parse_args()
    torch.set_num_threads(8);torch.manual_seed(20261025);np.random.seed(20261025);random.seed(20261025)
    mx,my=dataset(True);ex,ey=extra('train');vx,vy=extra('val')
    xt=torch.from_numpy(np.concatenate((mx[:55000],ex)));yt=torch.from_numpy(np.concatenate((my[:55000].astype(np.int64),ey)))
    xm=torch.from_numpy(mx[55000:].copy());ym=torch.from_numpy(my[55000:].astype(np.int64))
    xv=torch.from_numpy(vx);yv=torch.from_numpy(vy)
    m=CNN();m.load_state_dict(torch.load(ROOT/'baseline_v2/model/cnn_v2.pt',weights_only=True))
    optimizer=torch.optim.AdamW(m.parameters(),lr=.0008,weight_decay=.0001)
    scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,args.epochs,eta_min=.000025)
    m.eval();base_m=correct(m,xm,ym);base_e=correct(m,xv,yv)
    best=-1;history=[];start=time.time()
    for epoch in range(args.epochs):
        m.train()
        # Original MNIST is replayed once per epoch to keep its handwriting
        # domain represented. Unique image count is reported separately.
        order=torch.cat((torch.arange(len(xt)),torch.arange(55000)))
        order=order[torch.randperm(len(order))];loss_sum=0
        for idx in order.split(256):
            xb=augment(xt[idx,None].float()/255)
            optimizer.zero_grad();loss=F.cross_entropy(m(xb),yt[idx]);loss.backward();optimizer.step();loss_sum+=loss.item()*len(idx)
        scheduler.step();m.eval();cm=correct(m,xm,ym);ce=correct(m,xv,yv)
        score=.6*cm/len(ym)+.4*ce/len(yv)
        row=dict(epoch=epoch+1,train_loss=loss_sum/len(order),mnist_val_correct=cm,mnist_val_total=len(ym),nist_val_correct=ce,nist_val_total=len(yv),selection_score=score,elapsed_s=round(time.time()-start,2))
        history.append(row);print(json.dumps(row),flush=True)
        if cm>=base_m and score>best:
            best=score;torch.save(m.state_dict(),ROOT/'model/cnn_v3.pt');best_row=row
    assert best>=0,'No checkpoint met MNIST validation non-regression gate'
    m.load_state_dict(torch.load(ROOT/'model/cnn_v3.pt',weights_only=True));export(m)
    report=dict(seed=20261025,architecture='1->8 conv5 / pool2 / 8->16 conv5 / pool2 / FC256->10',parameters=sum(p.numel() for p in m.parameters()),unique_training_count=len(xt),mnist_replay_per_epoch=55000,training_draws_per_epoch=len(xt)+55000,epochs=args.epochs,warm_start='preserved V2 checkpoint',validation=dict(mnist=len(ym),nist=len(yv)),baseline_validation=dict(mnist_correct=base_m,nist_correct=base_e),test_used_for_selection=False,selection_rule='max .6*MNIST_val_acc+.4*NIST_val_acc subject to MNIST_val_correct >= V2',best_epoch=best_row,history=history,torch_version=torch.__version__)
    (ROOT/'reports/training_v3.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('V3_TRAIN_EXPORT_PASS',flush=True)

if __name__=='__main__':main()
