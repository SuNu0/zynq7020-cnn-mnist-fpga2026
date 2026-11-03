# V3 网页运行方法（JTAG 或 UART）

优先使用项目根目录的 `02_program_v3_board.cmd` 和 `01_start_v3_web.cmd`。
V3 的模型、预处理、准确率与验证说明见根目录 `README.md`。以下是底层连接说明；
Python 环境统一使用根目录 `.venv`，网页地址为 `http://127.0.0.1:5003`。

本目录中的程序让 Windows 电脑代替板端 Linux：网页负责采集手写数字，
Python 驱动把 784 个灰度像素通过 USB-UART 发给 Zynq PS 裸机程序，PS 再通过
AXI DMA 把数据送入 PL 中的 CNN。

`feature/jtag-mailbox` 分支默认不需要 USB-UART。Python 会调用 XSCT，经现有
JTAG 下载器把 784 字节写入 DDR 邮箱，再从邮箱读取识别结果。UART 仍作为可选
回退路径保留。

数据路径如下：

```text
浏览器画布 -> Flask/Pillow -> 28x28 灰度字节 -> USB-UART
             -> Zynq PS 裸机程序 -> AXI DMA -> PL CNN -> 预测数字
             <- USB-UART <- Zynq PS <------ AXI DMA <------+
```

## 1. 连接

- JTAG 用于下载 BIT、ELF，以及默认的图像/结果传输。
- 开发板的 USB-UART 口用于收发推理数据；它与 JTAG 是两条不同用途的连接。
- 串口参数固定为 `115200, 8N1`。

使用 JTAG 邮箱时只连接 JTAG 即可，USB-UART 可以不接。

## 2. 默认 JTAG 邮箱方式

先下载并启动邮箱服务：

```powershell
& 'D:\Xilinx\2025.2\Vitis\bin\xsct.bat' scripts\program_jtag_mailbox.tcl
```

测试项目自带的数字 3：

```powershell
cd software\pc_web
..\..\.venv\Scripts\python send_testvector.py --transport jtag
```

正确结果应包含 `BOARD_PREDICTION=3` 和 `JTAG_INFERENCE_TEST_PASSED`。启动网页：

```powershell
$env:HAOYUE_TRANSPORT = 'jtag'
..\..\.venv\Scripts\python app.py
```

浏览器打开 <http://127.0.0.1:5003>。每次识别会启动一次短暂的 XSCT 进程，适合
交互演示，不以高速吞吐为目标。

## 3. UART 回退方式

在项目根目录打开 PowerShell：

```powershell
& 'D:\Xilinx\2025.2\Vitis\bin\xsct.bat' scripts\program_uart_service.tcl
```

此命令依次初始化 PS、下载 `output/cnn_mnist_haoyue.bit`，再运行
`output/cnn_mnist_uart_service.elf`。每次开发板断电后都需要重新下载；若希望上电
自动运行，后续可再制作 BOOT.BIN 写入 SD 卡或 QSPI，这仍然不需要 Linux 镜像。

## 4. 启动 Windows 网页驱动

首次运行：

```powershell
cd software\pc_web
py -m venv ..\..\.venv
..\..\.venv\Scripts\python -m pip install -r requirements.txt
..\..\.venv\Scripts\python -m serial.tools.list_ports -v
```

如果自动识别失败，把实际端口填入环境变量：

```powershell
$env:HAOYUE_COM_PORT = 'COM5'
$env:HAOYUE_TRANSPORT = 'uart'
..\..\.venv\Scripts\python app.py
```

然后浏览器打开 <http://127.0.0.1:5003>，手写数字并提交。

若先跳过网页和 PNG，直接把项目自带的 784 字节数字 3 测试向量发给开发板：

```powershell
..\..\.venv\Scripts\python send_testvector.py --port COM5
```

正确结果应包含 `BOARD_PREDICTION=3` 和 `UART_INFERENCE_TEST_PASSED`。

## 串口协议

请求包：`MNST` + `uint16_le(784)` + `784字节像素` + `uint16_le(CRC16)`。
像素顺序为从左到右、从上到下；黑色是 0，白色是 255。CRC 使用
CRC-16/CCITT-FALSE（初值 `0xFFFF`，多项式 `0x1021`）。

响应包：`RSLT` + `status` + `prediction` + `uint16_le(CRC16)`。
`status=0` 表示成功；1/2 分别表示长度或 CRC 错误，3/4 表示 DMA 接收或发送
启动失败，5/6 表示 DMA 发送或接收超时。
