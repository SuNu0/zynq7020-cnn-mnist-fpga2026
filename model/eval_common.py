import csv, json, sys, hashlib
import numpy as np
from PIL import Image, ImageDraw
from common import ROOT, dataset, integer_logits
sys.path.insert(0, str(ROOT / 'software' / 'pc_web'))
from preprocess import normalize_digit

def write_mem(path, a, bits):
    path.write_text('\n'.join((f'{int(v) & (1 << bits) - 1:0{bits // 4}x}' for v in np.asarray(a).flatten())) + '\n', encoding='ascii')

def measure(pred, y):
    cm = np.zeros((10, 10), int)
    np.add.at(cm, (y, pred), 1)
    return dict(correct=int((pred == y).sum()), total=len(y), accuracy=float((pred == y).mean()), per_digit=[dict(digit=d, correct=int(cm[d, d]), total=int(cm[d].sum())) for d in range(10)], confusion_matrix=cm.tolist())

def canvases(x):
    rng = np.random.default_rng(1926)
    old = []
    new = []
    previews = []
    for k, a in enumerate(x):
        ys, xs = np.nonzero(a > 24)
        crop = Image.fromarray(a).crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
        extent = int(rng.integers(70, 226))
        s = extent / max(crop.size)
        crop = crop.resize((max(1, round(crop.width * s)), max(1, round(crop.height * s))), Image.Resampling.BICUBIC)
        canvas = Image.new('RGBA', (280, 280), (0, 0, 0, 0))
        ox = int(rng.integers(4, 277 - crop.width))
        oy = int(rng.integers(4, 277 - crop.height))
        canvas.paste(crop, (ox, oy))
        old.append(np.asarray(canvas.convert('L').resize((28, 28))))
        processed = normalize_digit(canvas)
        new.append(np.asarray(processed))
        if k < 30:
            previews.append((canvas.convert('RGB'), processed))
    sheet = Image.new('RGB', (900, 30 * 80), (238, 242, 246))
    draw = ImageDraw.Draw(sheet)
    for k, (a, b) in enumerate(previews):
        sheet.paste(a.resize((76, 76)), (0, k * 80))
        sheet.paste(b.resize((76, 76)), (90, k * 80))
        draw.text((190, k * 80 + 30), f'Test index {k}: raw canvas -> FPGA input', fill='black')
    sheet.save(ROOT / 'reports' / 'preprocessing_examples.png')
    return (np.stack(old), np.stack(new))
