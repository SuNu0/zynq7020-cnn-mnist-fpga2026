# JTAG mailbox transport

V3 uses a low-rate JTAG mailbox with the retrained PL CNN in
`rtl/axis_cnn_mnist_v3.v`. Use the root README and double-click launchers.

```text
Browser -> Flask/Pillow -> 784 bytes -> Python subprocess -> XSCT/JTAG
        -> PS DDR mailbox -> Cortex-A9 -> AXI DMA -> PL CNN
        <- prediction <---- PS DDR mailbox <--------------+
```

## DDR contract

All fields are little-endian 32-bit words except the image and DMA output.

| Address | Name | Owner | Meaning |
| --- | --- | --- | --- |
| `0x08000000` | magic | PS | `0x4A544147` (`JTAG`) when service is ready |
| `0x08000004` | version | PS | V3 firmware version `3`; host rejects V1/V2 |
| `0x08000008` | command | Host/PS | Host writes `1`; PS clears it after accepting |
| `0x0800000C` | status | PS | `0` ready, `1` busy, `2` done, high bit set on error |
| `0x08000010` | sequence | Host | Request sequence number |
| `0x08000014` | completed | PS | Sequence number whose result is complete |
| `0x08000018` | result | PS | Predicted digit in bits `[3:0]` |
| `0x0800001C` | error | PS | DMA error code |
| `0x08000100` | image | Host | 784 grayscale bytes, row-major |
| `0x08000440` | DMA output | PS/DMA | One-byte raw CNN response |

The Cortex-A9 data cache is disabled in this debug service so JTAG writes and
DMA accesses observe the same DDR contents without a separate cache protocol.

## Build and run

From the repository root:

```powershell
.\.venv\Scripts\python scripts\build_firmware.py
& 'D:\Xilinx\2025.2\Vitis\bin\xsct.bat' scripts\program_jtag_mailbox.tcl
cd software\pc_web
..\..\.venv\Scripts\python send_testvector.py --transport jtag
```

The program command must print `CNN_JTAG_MAILBOX_PROGRAMMED`. The supplied
digit-3 vector must then print `BOARD_PREDICTION=3` and
`JTAG_INFERENCE_TEST_PASSED`.

For the web application:

```powershell
$env:HAOYUE_TRANSPORT = 'jtag'
..\..\.venv\Scripts\python app.py
```

Open <http://127.0.0.1:5003>. Keep the JTAG cable connected and do not run
Vivado Hardware Manager or another XSCT process against the same cable while a
request is in progress.

## Error codes

| Code | Meaning |
| --- | --- |
| `3` | S2MM receive transfer did not start |
| `4` | MM2S image transfer did not start |
| `5` | MM2S transfer timed out |
| `6` | S2MM transfer timed out |
| `7` | AXI DMA initialization failed |

## Validation boundary

The firmware compiles successfully with Vitis 2025.2, the host driver and
Flask path have mock tests, and the ELF memory map does not overlap the mailbox.
Physical validation still requires a JTAG scan that exposes the Zynq APU and a
successful transaction. V3 retains the verified frame input handshaking and output backpressure handling;
the numerical and protocol checks are in `reports/v3_simulation.log`.
