import os,sys,threading,webbrowser,importlib,subprocess
from pathlib import Path
web_root=Path(__file__).resolve().parents[1]/'software'/'pc_web'
missing=[]
for name in ('flask','PIL.Image','numpy','serial'):
    try:
        importlib.import_module(name)
    except ModuleNotFoundError:
        missing.append(name)
if missing:
    print('Installing missing web dependencies: '+', '.join(missing),flush=True)
    subprocess.run([sys.executable,'-m','pip','install','-r',str(web_root/'requirements.txt')],check=True)
sys.path.insert(0,str(web_root))
from app import app
port=int(os.environ.get('HAOYUE_WEB_PORT','5003'))
threading.Timer(1.5,lambda:webbrowser.open(f'http://127.0.0.1:{port}')).start()
app.run(host='127.0.0.1',port=port,threaded=True)
