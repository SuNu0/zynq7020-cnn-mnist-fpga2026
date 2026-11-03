#include "xaxidma.h"
#include "xil_cache.h"
#include "xil_printf.h"
#include "xparameters.h"
#include "test_image_3.h"

#define DMA_DEVICE_ID XPAR_AXIDMA_0_DEVICE_ID
#define IMAGE_BYTES 784U

static XAxiDma dma;
static unsigned char tx_buffer[IMAGE_BYTES] __attribute__((aligned(64)));
static unsigned char rx_buffer[64] __attribute__((aligned(64)));

int main(void)
{
    XAxiDma_Config *cfg;
    int status;
    unsigned i;

    Xil_ICacheEnable();
    Xil_DCacheEnable();
    xil_printf("CNN MNIST Haoyue Zynq-7020 DMA test\r\n");
    cfg = XAxiDma_LookupConfig(DMA_DEVICE_ID);
    if (cfg == NULL) { xil_printf("FAIL: DMA config\r\n"); return XST_FAILURE; }
    status = XAxiDma_CfgInitialize(&dma, cfg);
    if (status != XST_SUCCESS || XAxiDma_HasSg(&dma)) {
        xil_printf("FAIL: DMA init or SG enabled\r\n"); return XST_FAILURE;
    }
    for (i = 0; i < IMAGE_BYTES; ++i) tx_buffer[i] = test_image_3[i];
    rx_buffer[0] = 0xFF;
    Xil_DCacheFlushRange((UINTPTR)tx_buffer, IMAGE_BYTES);
    Xil_DCacheFlushRange((UINTPTR)rx_buffer, sizeof(rx_buffer));

    status = XAxiDma_SimpleTransfer(&dma, (UINTPTR)rx_buffer, 1,
                                    XAXIDMA_DEVICE_TO_DMA);
    if (status != XST_SUCCESS) { xil_printf("FAIL: S2MM start\r\n"); return XST_FAILURE; }
    status = XAxiDma_SimpleTransfer(&dma, (UINTPTR)tx_buffer, IMAGE_BYTES,
                                    XAXIDMA_DMA_TO_DEVICE);
    if (status != XST_SUCCESS) { xil_printf("FAIL: MM2S start\r\n"); return XST_FAILURE; }
    while (XAxiDma_Busy(&dma, XAXIDMA_DMA_TO_DEVICE)) {}
    while (XAxiDma_Busy(&dma, XAXIDMA_DEVICE_TO_DMA)) {}
    Xil_DCacheInvalidateRange((UINTPTR)rx_buffer, sizeof(rx_buffer));
    xil_printf("Prediction: %d\r\n", rx_buffer[0] & 0x0F);
    if ((rx_buffer[0] & 0x0F) == 3U) xil_printf("CNN_DMA_TEST_PASSED\r\n");
    else xil_printf("CNN_DMA_TEST_FAILED\r\n");
    Xil_DCacheDisable();
    Xil_ICacheDisable();
    return 0;
}
