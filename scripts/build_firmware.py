"""Vitis BSP + ARM GCC; bypass the deprecated Eclipse app-create step."""
import hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]
XSA=ROOT/'output/cnn_mnist_haoyue.xsa'
tool=Path(os.environ.get('XILINX_ARM_GCC_DIR','D:/Xilinx/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin'))
gcc=tool/'arm-none-eabi-gcc.exe';size=tool/'arm-none-eabi-size.exe'
xsct=os.environ.get('XILINX_XSCT','D:/Xilinx/2025.2/Vitis/bin/xsct.bat')

def run(cmd,log):
    log.write('COMMAND '+json.dumps(list(map(str,cmd)))+'\n');log.flush()
    r=subprocess.run(list(map(str,cmd)),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
    log.write(r.stdout);log.flush();print(r.stdout,end='',flush=True)
    if r.returncode:raise RuntimeError(f'Compiler command failed: {r.returncode}')

def find_bsp():
    candidates=[(ROOT/'vitis_jtag_mailbox_workspace','cnn_mnist_jtag_platform')]
    candidates.extend((p,'cnn_v3_platform') for p in (ROOT/'build').glob('bsp_*'))
    for workspace,name in candidates:
        export=workspace/name/'export'/name
        hw=export/'hw/cnn_mnist_haoyue.xsa'
        sw=export/'sw'/name/'standalone_domain'
        if hw.is_file() and hw.read_bytes()==XSA.read_bytes() and (sw/'bsplib/lib/libxil.a').is_file():
            return workspace,name,sw
    workspace=ROOT/'build'/('bsp_'+hashlib.sha256(XSA.read_bytes()).hexdigest()[:12]+'_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    with (ROOT/'reports/bsp_build.log').open('w',encoding='utf-8') as log:
        run([xsct,ROOT/'scripts/generate_bsp.tcl',workspace],log)
    sw=workspace/'cnn_v3_platform/export/cnn_v3_platform/sw/cnn_v3_platform/standalone_domain'
    assert (sw/'bsplib/lib/libxil.a').is_file()
    return workspace,'cnn_v3_platform',sw

def elf_check(p):
    b=p.read_bytes();assert b[:6]==b'\x7fELF\x01\x01'
    entry,phoff=struct.unpack_from('<II',b,24)
    phentsize,phnum=struct.unpack_from('<HH',b,42)
    ranges=[]
    for i in range(phnum):
        typ,offset,vaddr,paddr,filesz,memsz,flags,align=struct.unpack_from('<IIIIIIII',b,phoff+i*phentsize)
        if typ==1:
            assert 0x100000<=vaddr and vaddr+memsz<0x08000000,'ELF overlaps mailbox'
            ranges.append(dict(start=hex(vaddr),end=hex(vaddr+memsz),bytes=memsz))
    assert ranges and 0x100000<=entry<0x08000000
    return dict(entry=hex(entry),load_segments=ranges)

def main():
    assert XSA.is_file() and gcc.is_file()
    work=ROOT/'build/firmware';work.mkdir(parents=True,exist_ok=True)
    workspace,name,bsp=find_bsp()
    ps=workspace/name/'hw/ps7_init.tcl'
    if ps.is_file():shutil.copy2(ps,ROOT/'output/ps7_init.tcl')
    manifest=dict(method='Vitis 2025.2 generated BSP + ARM GCC, without Eclipse app create',bsp_xsa_sha256=hashlib.sha256(XSA.read_bytes()).hexdigest(),bsp_libxil_sha256=hashlib.sha256((bsp/'bsplib/lib/libxil.a').read_bytes()).hexdigest(),applications={})
    for profile,filename,marker in [('jtag_mailbox','cnn_mnist_jtag_mailbox','CNN_JTAG_MAILBOX_BUILD_PASSED'),('uart_service','cnn_mnist_uart_service','CNN_UART_SERVICE_BUILD_PASSED')]:
        log_path=ROOT/'reports'/('jtag_firmware_build.log' if profile=='jtag_mailbox' else 'uart_firmware_build.log')
        elf=ROOT/'output'/(filename+'.elf');obj=work/(filename+'.o')
        with log_path.open('w',encoding='utf-8') as log:
            flags=['-mcpu=cortex-a9','-mfpu=vfpv3','-mfloat-abi=hard']
            run([gcc,'-Wall','-O2','-g3','-c','-fmessage-length=0',*flags,'-I',bsp/'bspinclude/include','-o',obj,ROOT/'software'/profile/'src/main.c'],log)
            run([gcc,*flags,'-Wl,-build-id=none','-specs='+str(ROOT/'software/linker/xilinx.spec'),'-T',ROOT/'software/linker/lscript.ld','-L',bsp/'bsplib/lib','-o',elf,obj,'-Wl,--start-group,-lxil,-lgcc,-lc,--end-group'],log)
            run([size,elf],log)
            manifest['applications'][filename]=elf_check(elf)
            log.write(marker+'\n');print(marker,flush=True)
    (ROOT/'reports/firmware_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('V3_FIRMWARE_BUILD_PASS',flush=True)

if __name__=='__main__':main()
