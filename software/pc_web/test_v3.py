import base64,io
import numpy as np
import pytest
from PIL import Image,ImageDraw
import app as web
from preprocess import normalize_digit,png_data_url

def digit(offset=(0,0),alpha=False):
    a=Image.new('RGBA' if alpha else 'RGB',(280,280),(0,0,0,0) if alpha else (0,0,0))
    d=ImageDraw.Draw(a);x,y=offset
    d.line([(x+50,y+30),(x+110,y+30),(x+60,y+150)],fill='white',width=18)
    return a

def test_offset_alpha_polarity():
    a=np.asarray(normalize_digit(digit()))
    b=np.asarray(normalize_digit(digit((80,50),True)))
    assert np.array_equal(a,b)
    inv=Image.eval(digit().convert('L'),lambda v:255-v)
    assert np.array_equal(a,np.asarray(normalize_digit(inv)))
    yy,xx=np.indices(a.shape);assert abs((xx*a).sum()/a.sum()-13.5)<.6
    assert abs((yy*a).sum()/a.sum()-13.5)<.6
    assert np.count_nonzero(a)>30

def test_blank_rejected():
    for c in ['black','white']:
        with pytest.raises(ValueError):normalize_digit(Image.new('RGB',(280,280),c))

def test_preview_and_board_exact_input(monkeypatch):
    calls=[]
    class Board:
        def predict(self,pixels):calls.append(pixels);return 7
    monkeypatch.setattr(web,'get_board',lambda:Board())
    client=web.app.test_client();body={'base64str':png_data_url(digit())}
    a=client.post('/prepare',json=body);assert a.status_code==200 and calls==[]
    b=client.post('/',json=body);assert b.status_code==200
    assert b.json['prediction']=='7' and len(calls)==1
    assert calls[0]==normalize_digit(digit()).tobytes()
    assert a.json['preview']==b.json['preview']
    assert b.json['backend']=='Zynq-7020 PL CNN V3'

def test_no_board_and_bad_input(monkeypatch):
    def fail():raise RuntimeError('JTAG disconnected')
    monkeypatch.setattr(web,'get_board',fail)
    c=web.app.test_client()
    assert c.get('/').status_code==200
    r=c.post('/',json={'base64str':png_data_url(digit())})
    assert r.status_code==503 and 'prediction' not in r.json
    assert c.post('/',json={'base64str':'bad'}).status_code==400
    assert c.post('/',json={'base64str':png_data_url(Image.new('RGB',(280,280)))}).status_code==400
    assert c.post('/',json=[]).status_code==400
