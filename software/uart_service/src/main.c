#include "xaxidma.h"
#include "xil_cache.h"
#include "xparameters.h"
#include "xstatus.h"
#include "xuartps.h"

#define IMAGE_BYTES 784U
#define DMA_TIMEOUT 10000000U
#define UART_BAUD 115200U

static XAxiDma dma;
static XUartPs uart;
static unsigned char tx_buffer[IMAGE_BYTES] __attribute__((aligned(64)));
static unsigned char rx_buffer[64] __attribute__((aligned(64)));

static unsigned short crc16_ccitt(const unsigned char *data, unsigned length)
{
    unsigned short crc = 0xFFFFU;
    unsigned i;
    while (length-- != 0U) {
        crc ^= (unsigned short)(*data++) << 8;
        for (i = 0; i < 8U; ++i)
            crc = (crc & 0x8000U) ? (unsigned short)((crc << 1) ^ 0x1021U)
                                  : (unsigned short)(crc << 1);
    }
    return crc;
}

static unsigned char uart_get(void)
{
    return XUartPs_RecvByte(XPAR_XUARTPS_0_BASEADDR);
}

static void uart_put(unsigned char value)
{
    XUartPs_SendByte(XPAR_XUARTPS_0_BASEADDR, value);
}

static void send_response(unsigned char status, unsigned char prediction)
{
    unsigned char body[2];
    unsigned short crc;
    body[0] = status;
    body[1] = prediction;
    crc = crc16_ccitt(body, 2U);
    uart_put('R'); uart_put('S'); uart_put('L'); uart_put('T');
    uart_put(status);
    uart_put(prediction);
    uart_put((unsigned char)(crc & 0xFFU));
    uart_put((unsigned char)(crc >> 8));
}

static int receive_request(void)
{
    static const unsigned char magic[4] = {'M', 'N', 'S', 'T'};
    unsigned matched = 0U;
    unsigned length;
    unsigned i;
    unsigned short received_crc;
    unsigned short calculated_crc;

    while (matched < 4U) {
        unsigned char value = uart_get();
        matched = (value == magic[matched]) ? matched + 1U
                                            : ((value == magic[0]) ? 1U : 0U);
    }
    length = (unsigned)uart_get();
    length |= (unsigned)uart_get() << 8;
    if (length != IMAGE_BYTES) {
        send_response(1U, 0xFFU);
        return XST_FAILURE;
    }
    for (i = 0U; i < IMAGE_BYTES; ++i) tx_buffer[i] = uart_get();
    received_crc = (unsigned short)uart_get();
    received_crc |= (unsigned short)((unsigned short)uart_get() << 8);
    calculated_crc = crc16_ccitt(tx_buffer, IMAGE_BYTES);
    if (received_crc != calculated_crc) {
        send_response(2U, 0xFFU);
        return XST_FAILURE;
    }
    return XST_SUCCESS;
}

static int run_inference(unsigned char *prediction)
{
    unsigned timeout;
    int status;

    rx_buffer[0] = 0xFFU;
    Xil_DCacheFlushRange((UINTPTR)tx_buffer, IMAGE_BYTES);
    Xil_DCacheFlushRange((UINTPTR)rx_buffer, sizeof(rx_buffer));

    status = XAxiDma_SimpleTransfer(&dma, (UINTPTR)rx_buffer, 1U,
                                    XAXIDMA_DEVICE_TO_DMA);
    if (status != XST_SUCCESS) return 3;
    status = XAxiDma_SimpleTransfer(&dma, (UINTPTR)tx_buffer, IMAGE_BYTES,
                                    XAXIDMA_DMA_TO_DEVICE);
    if (status != XST_SUCCESS) return 4;

    timeout = DMA_TIMEOUT;
    while (XAxiDma_Busy(&dma, XAXIDMA_DMA_TO_DEVICE) && --timeout != 0U) {}
    if (timeout == 0U) return 5;
    timeout = DMA_TIMEOUT;
    while (XAxiDma_Busy(&dma, XAXIDMA_DEVICE_TO_DMA) && --timeout != 0U) {}
    if (timeout == 0U) return 6;

    Xil_DCacheInvalidateRange((UINTPTR)rx_buffer, sizeof(rx_buffer));
    *prediction = rx_buffer[0] & 0x0FU;
    return 0;
}

int main(void)
{
    XAxiDma_Config *dma_cfg;
    XUartPs_Config *uart_cfg;

    Xil_ICacheEnable();
    Xil_DCacheEnable();
    uart_cfg = XUartPs_LookupConfig(XPAR_XUARTPS_0_DEVICE_ID);
    if (uart_cfg == NULL ||
        XUartPs_CfgInitialize(&uart, uart_cfg, uart_cfg->BaseAddress) != XST_SUCCESS)
        return XST_FAILURE;
    XUartPs_SetBaudRate(&uart, UART_BAUD);

    dma_cfg = XAxiDma_LookupConfig(XPAR_AXIDMA_0_DEVICE_ID);
    if (dma_cfg == NULL || XAxiDma_CfgInitialize(&dma, dma_cfg) != XST_SUCCESS ||
        XAxiDma_HasSg(&dma))
        return XST_FAILURE;

    for (;;) {
        unsigned char prediction = 0xFFU;
        int status;
        if (receive_request() != XST_SUCCESS) continue;
        status = run_inference(&prediction);
        send_response((unsigned char)status, prediction);
    }
}
