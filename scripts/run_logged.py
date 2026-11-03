"""Stream tool messages into one UTF-8 log without PowerShell stderr errors."""
import os,subprocess,sys
from pathlib import Path
log_path,command,*arguments=sys.argv[1:]
env=os.environ.copy();env['PYTHONUTF8']='1'
process=None
with Path(log_path).open('w',encoding='utf-8') as log:
    try:
        process=subprocess.Popen([command,*arguments],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',env=env)
        for line in process.stdout:
            log.write(line);log.flush();print(line,end='',flush=True)
        sys.exit(process.wait())
    except KeyboardInterrupt:
        if process is not None and process.poll() is None:process.terminate()
        sys.exit(130)
