param([ValidateSet('web','program','build','sim','evaluate','board','setup')][string]$Action='web')
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath=Join-Path $projectRoot '.venv\Scripts\python.exe'
$xsctPath=if($env:XILINX_XSCT){$env:XILINX_XSCT}else{'D:\Xilinx\2025.2\Vitis\bin\xsct.bat'}
$vivadoPath=if($env:XILINX_VIVADO_BIN){$env:XILINX_VIVADO_BIN}else{'D:\Xilinx\2025.2\Vivado\bin\vivado.bat'}
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
New-Item -ItemType Directory -Path (Join-Path $projectRoot 'reports') -Force | Out-Null
function Run-Checked([string]$executable,[string[]]$arguments,[string]$label) {
    if(!(Test-Path -LiteralPath $executable)){throw "Tool not found: $executable"}
    $logPath=Join-Path $projectRoot "reports\${stamp}_${label}.txt"
    & $pythonPath -X utf8 (Join-Path $PSScriptRoot 'run_logged.py') $logPath $executable @arguments
    if($LASTEXITCODE -ne 0){throw "Failed: $label. See $logPath"}
    $markers=@{program='CNN_JTAG_MAILBOX_PROGRAMMED';hardware='CNN_HARDWARE_BUILD_PASSED';hardware_resume='CNN_HARDWARE_BUILD_PASSED';firmware_bundle='V3_FIRMWARE_BUILD_PASS';simulation='V3_RTL_PASS';accuracy='V3_ACCURACY_EVALUATION_PASS';board_accuracy='V3_PHYSICAL_BOARD_PASS'}
    if($markers.ContainsKey($label) -and !([IO.File]::ReadAllText($logPath).Contains($markers[$label]))) {throw "Expected PASS marker missing: $label. See $logPath"}
}
if($Action -eq 'setup') {
    if(!(Test-Path -LiteralPath $pythonPath)) { & python -m venv (Join-Path $projectRoot '.venv');if($LASTEXITCODE -ne 0){throw 'Python environment creation failed'} }
    Run-Checked $pythonPath @('-m','pip','install','-r','software\pc_web\requirements.txt') 'setup'
} elseif($Action -eq 'web') {
    if(!(Test-Path -LiteralPath $pythonPath)){throw 'Run scripts/run_v3.ps1 -Action setup first'}
    if(!$env:HAOYUE_TRANSPORT){$env:HAOYUE_TRANSPORT='jtag'}
    if(!$env:HAOYUE_WEB_PORT){$env:HAOYUE_WEB_PORT='5003'}
    Run-Checked $pythonPath @('scripts\start_web.py') 'web'
} elseif($Action -eq 'program') {
    Run-Checked $xsctPath @('scripts\program_jtag_mailbox.tcl') 'program'
} elseif($Action -eq 'build') {
    try {
        Run-Checked $vivadoPath @('-mode','batch','-source','scripts\build_hardware.tcl','-log',"reports\${stamp}_hardware.log",'-journal',"reports\${stamp}_hardware.jou") 'hardware'
    } catch {
        Write-Host 'Retrying incomplete hardware runs; completed IP checkpoints are preserved.'
        Run-Checked $vivadoPath @('-mode','batch','-source','scripts\resume_hardware.tcl','-log',"reports\${stamp}_hardware_resume.log",'-journal',"reports\${stamp}_hardware_resume.jou") 'hardware_resume'
    }
    Run-Checked $pythonPath @('scripts\build_firmware.py') 'firmware_bundle'
} elseif($Action -eq 'sim') {
    Run-Checked $vivadoPath @('-mode','batch','-source','scripts\run_v3_sim.tcl','-log',"reports\${stamp}_sim.log",'-journal',"reports\${stamp}_sim.jou") 'simulation'
} elseif($Action -eq 'evaluate') {
    Run-Checked $pythonPath @('model\evaluate.py') 'accuracy'
} elseif($Action -eq 'board') {
    Run-Checked $xsctPath @('scripts\verify_board.tcl') 'board_accuracy'
}
