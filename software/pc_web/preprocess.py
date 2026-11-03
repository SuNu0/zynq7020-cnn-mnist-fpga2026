"""White ink, black background, 20-pixel bounding box and center of mass."""
import base64
import io
import numpy as np
from PIL import Image,ImageOps

def normalize_digit(image):
    if image.width < 2 or image.height < 2 or max(image.size)>2048:
        raise ValueError('图片尺寸不合适')
    # Canvas CSS is not encoded in its PNG. Composite alpha on real black.
    if 'A' in image.getbands():
        rgba=image.convert('RGBA')
        background=Image.new('RGBA',image.size,(0,0,0,255))
        background.alpha_composite(rgba)
        image=background.convert('L')
    else:
        image=image.convert('L')
    arr=np.asarray(image)
    border=np.concatenate((arr[0],arr[-1],arr[:,0],arr[:,-1]))
    if np.median(border)>127:
        image=ImageOps.invert(image)
    arr=np.asarray(image).astype(np.float32)
    arr=np.maximum(arr-float(np.percentile(arr,5)),0)
    if arr.max()<24:
        raise ValueError('请先写一个数字')
    arr=np.clip(arr*(255/arr.max()),0,255).astype(np.uint8)
    ys,xs=np.nonzero(arr>max(20,int(arr.max()*0.12)))
    if len(xs)<8:
        raise ValueError('笔迹太少，请写完整数字')
    crop=Image.fromarray(arr).crop((int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1))
    scale=20/max(crop.size)
    crop=crop.resize((max(1,round(crop.width*scale)),max(1,round(crop.height*scale))),Image.Resampling.LANCZOS)
    out=Image.new('L',(28,28))
    out.paste(crop,((28-crop.width)//2,(28-crop.height)//2))
    a=np.asarray(out,dtype=np.float64)
    yy,xx=np.indices(a.shape)
    dx=round(13.5-float((a*xx).sum()/a.sum()))
    dy=round(13.5-float((a*yy).sum()/a.sum()))
    centered=Image.new('L',(28,28))
    centered.paste(out,(dx,dy))
    return centered

def png_data_url(image):
    f=io.BytesIO(); image.save(f,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(f.getvalue()).decode('ascii')
