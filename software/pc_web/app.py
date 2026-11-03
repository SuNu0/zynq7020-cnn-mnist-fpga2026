import atexit
import base64
import io
import os
import re
import threading
import hashlib
import time

from flask import Flask, jsonify, render_template, request
from PIL import Image

from board_driver import HaoyueCnn
from jtag_board_driver import JtagMailboxCnn
from preprocess import normalize_digit, png_data_url

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
board_lock = threading.Lock()
board = None


def get_board():
    global board
    if board is None:
        transport = os.environ.get("HAOYUE_TRANSPORT", "jtag").lower()
        if transport == "jtag":
            board = JtagMailboxCnn()
        elif transport == "uart":
            board = HaoyueCnn(port=os.environ.get("HAOYUE_COM_PORT"))
        else:
            raise ValueError(f"Unsupported HAOYUE_TRANSPORT: {transport}")
        atexit.register(board.close)
    return board


@app.get("/")
def index():
    return render_template("index_v3.html")


def prepare_request():
    payload = request.get_json(force=True)
    if not isinstance(payload, dict) or not isinstance(payload.get('base64str'), str):
        raise ValueError('请提供画布图片')
    encoded = payload['base64str']
    match = re.fullmatch(r'data:image/(?:png|jpeg);base64,([A-Za-z0-9+/=]+)', encoded)
    if match is None:
        raise ValueError('图片编码无效')
    image = Image.open(io.BytesIO(base64.b64decode(match.group(1), validate=True)))
    image.load()
    return normalize_digit(image)

@app.post('/prepare')
def preview():
    try:
        image = prepare_request()
        return jsonify(preview=png_data_url(image))
    except Exception as exc:
        return jsonify(error=str(exc)), 400

@app.post('/')
def predict():
    try:
        image = prepare_request()
        pixels = image.tobytes()
        started = time.monotonic()
        with board_lock:
            prediction = get_board().predict(pixels)
        return jsonify(prediction=str(prediction), preview=png_data_url(image),
                       input_sha256=hashlib.sha256(pixels).hexdigest(),
                       elapsed_s=round(time.monotonic()-started, 2),
                       backend='Zynq-7020 PL CNN V3')
    except (ValueError, KeyError, TypeError) as exc:
        return jsonify(error=str(exc)), 400
    except Exception as exc:
        app.logger.warning('Board inference failed: %s', exc)
        detail = str(exc)
        if 'V3_FIRMWARE_REQUIRED' in detail:
            message = '开发板仍在运行旧版本，请双击 02_program_v3_board.cmd 下载 V3。'
        elif isinstance(exc, FileNotFoundError):
            message = '未找到 Xilinx 下载工具，请检查工具安装路径。'
        else:
            message = '开发板连接未就绪。请上电、接好 JTAG，并双击 02_program_v3_board.cmd 下载 V3。'
        return jsonify(error=message), 503


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get('HAOYUE_WEB_PORT', '5003')), threaded=True)
