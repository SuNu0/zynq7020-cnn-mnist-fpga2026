"""Dataset and integer reference; inference here is for validation only."""
from pathlib import Path
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
ROOT = Path(__file__).resolve().parents[1]

def dataset(train=False):
    prefix = 'train' if train else 't10k'
    x = np.frombuffer((ROOT / 'data' / f'{prefix}-images-idx3-ubyte').read_bytes(), np.uint8, offset=16).reshape(-1, 28, 28).copy()
    y = np.frombuffer((ROOT / 'data' / f'{prefix}-labels-idx1-ubyte').read_bytes(), np.uint8, offset=8).copy()
    assert len(x) == len(y) == (60000 if train else 10000)
    return (x, y)

def conv(x, w):
    patches = sliding_window_view(x, (5, 5), axis=(-2, -1))
    return np.einsum('bcyxij,ocij->boyx', patches, w, optimize=True)

def pool(x):
    b, c, h, w = x.shape
    return x.reshape(b, c, h // 2, 2, w // 2, 2).max(axis=(3, 5)).clip(0)

def integer_logits(x, weights=None, return_features=False):
    weights = weights if weights is not None else np.load(ROOT / 'model' / 'weights_int.npz')
    a = x[:, None].astype(np.int64)
    features = []
    for layer in ('conv1', 'conv2'):
        a = pool(np.clip(conv(a, weights[layer + '_w']) + weights[layer + '_b'][None, :, None, None] + 2048 >> 12, 0, 65535))
        features.append(a)
    scores = a.reshape(len(a), -1) @ weights['fc_w'].T + weights['fc_b']
    return (scores, features) if return_features else scores
