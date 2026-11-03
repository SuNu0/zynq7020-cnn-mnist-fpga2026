import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'model'))
from train_v3 import extra
from common import dataset

def sheet(x,y,label,stem,writers=None,source_ids=None):
    dest=ROOT/'training_preview';out=dest/stem;out.mkdir(parents=True,exist_ok=True)
    for old in out.glob('*.png'):old.unlink()
    rng=np.random.default_rng(20261025);selected=[]
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15);title=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28)
    canvas=Image.new('RGB',(1120,1230),'#eff3f8');d=ImageDraw.Draw(canvas)
    d.text((25,16),label,font=title,fill='#16243a');d.text((25,62),'各行依次为数字 0—9，每类 10 张；真实 28×28 训练图片，按像素放大。',font=font,fill='#52647a')
    for digit in range(10):
        pool=rng.permutation(np.flatnonzero(y==digit));indices=[];seen=set()
        for index in pool:
            if writers is not None and int(writers[index]) in seen:continue
            indices.append(index)
            if writers is not None:seen.add(int(writers[index]))
            if len(indices)==10:break
        for col,index in enumerate(indices):
            im=Image.fromarray(x[index]);im.save(out/f'{digit}_{index:06d}.png');left=25+109*col;top=100+111*digit
            canvas.paste(im.resize((84,84),Image.Resampling.NEAREST).convert('RGB'),(left,top));d.text((left,top+85),f'{digit} #{index:05d}',font=font,fill='#34475d')
            selected.append(dict(digit=digit,training_index=int(index),source_index=int(source_ids[index]) if source_ids is not None else int(index),writer_id=int(writers[index]) if writers is not None else None))
    canvas.save(dest/(stem+'.png'))
    (dest/(stem+'_indices.json')).write_text(json.dumps(selected,indent=2),encoding='utf-8')

def main():
    x,y=dataset(True);sheet(x[:55000],y[:55000],'V3 保留的 MNIST 训练样本','original_mnist')
    x,y=extra('train');idx=np.load(ROOT/'data/v3_splits.npz')['extra_train'];meta=np.load(ROOT/'data/qmnist/source_metadata.npy',mmap_mode='r')
    sheet(x,y,'V3 新增的 NIST 真实训练样本','added_nist',meta[idx,2],idx)
    (ROOT/'training_preview/说明.txt').write_text('原有训练图片 55000 张，新增真实图片 277455 张，总计 332455 张。\n两张总览及对应 PNG 文件夹每类随机抽取 10 张真实训练图片；新增 NIST 每类选取不同书写者。\n固定随机种子 20261025，来源索引见同目录 *_indices.json。\n完整数据、来源和划分见 data/qmnist、data/v3_splits.npz 与 reports/dataset_v3.json。\n',encoding='utf-8')
    print('V3_TRAINING_PREVIEW_PASS')

if __name__=='__main__':main()
