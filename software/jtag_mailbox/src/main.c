#include "xaxidma.h"
#include "xil_cache.h"
#include "xil_io.h"
#include "xil_printf.h"
#include "xparameters.h"

#define DMA_DEVICE_ID XPAR_AXIDMA_0_DEVICE_ID
#define IMAGE_BYTES 784U

#define MAILBOX_BASE       0x08000000U
#define MAILBOX_MAGIC      (MAILBOX_BASE + 0x00U)
#define MAILBOX_VERSION    (MAILBOX_BASE + 0x04U)
#define MAILBOX_COMMAND    (MAILBOX_BASE + 0x08U)
#define MAILBOX_STATUS     (MAILBOX_BASE + 0x0CU)
#define MAILBOX_SEQUENCE   (MAILBOX_BASE + 0x10U)
#define MAILBOX_COMPLETED  (MAILBOX_BASE + 0x14U)
#define MAILBOX_RESULT     (MAILBOX_BASE + 0x18U)
#define MAILBOX_ERROR      (MAILBOX_BASE + 0x1CU)
#define MAILBOX_INPUT      (MAILBOX_BASE + 0x100U)
#define MAILBOX_DMA_OUTPUT (MAILBOX_BASE + 0x440U)

#define MAGIC_JTAG 0x4A544147U
#define PROTOCOL_VERSION 3U
#define COMMAND_INFER 1U
#define STATUS_READY 0U
#define STATUS_BUSY 1U
#define STATUS_DONE 2U
#define STATUS_ERROR_FLAG 0x80000000U

#define ERR_DMA_RX_START 3U
#define ERR_DMA_TX_START 4U
#define ERR_DMA_TX_TIMEOUT 5U
#define ERR_DMA_RX_TIMEOUT 6U
#define ERR_DMA_INIT 7U

#define DMA_TIMEOUT 20000000U

static XAxiDma dma;

static void publish_error(u32 sequence, u32 code)
{
    Xil_Out32(MAILBOX_ERROR, code);
    Xil_Out32(MAILBOX_COMPLETED, sequence);
    Xil_Out32(MAILBOX_STATUS, STATUS_ERROR_FLAG | code);
}

static void reset_dma(void)
{
    u32 timeout = DMA_TIMEOUT;
    XAxiDma_Reset(&dma);
    while (timeout != 0U && !XAxiDma_ResetIsDone(&dma)) --timeout;
}

static int run_inference(void)
{
    int status;
    u32 timeout;

    Xil_Out8(MAILBOX_DMA_OUTPUT, 0xFFU);
    status = XAxiDma_SimpleTransfer(&dma, (UINTPTR)MAILBOX_DMA_OUTPUT, 1U,
                                    XAXIDMA_DEVICE_TO_DMA);
    if (status != XST_SUCCESS) {
        reset_dma();
        return ERR_DMA_RX_START;
    }

    status = XAxiDma_SimpleTransfer(&dma, (UINTPTR)MAILBOX_INPUT, IMAGE_BYTES,
                                    XAXIDMA_DMA_TO_DEVICE);
    if (status != XST_SUCCESS) {
        reset_dma();
        return ERR_DMA_TX_START;
    }

    timeout = DMA_TIMEOUT;
    while (XAxiDma_Busy(&dma, XAXIDMA_DMA_TO_DEVICE) && timeout != 0U) --timeout;
    if (XAxiDma_Busy(&dma, XAXIDMA_DMA_TO_DEVICE)) {
        reset_dma();
        return ERR_DMA_TX_TIMEOUT;
    }

    timeout = DMA_TIMEOUT;
    while (XAxiDma_Busy(&dma, XAXIDMA_DEVICE_TO_DMA) && timeout != 0U) --timeout;
    if (XAxiDma_Busy(&dma, XAXIDMA_DEVICE_TO_DMA)) {
        reset_dma();
        return ERR_DMA_RX_TIMEOUT;
    }

    return XST_SUCCESS;
}

int main(void)
{
    XAxiDma_Config *cfg;
    u32 sequence;
    int status;

    Xil_ICacheEnable();
    Xil_DCacheDisable();

    cfg = XAxiDma_LookupConfig(DMA_DEVICE_ID);
    if (cfg == NULL) {
        Xil_Out32(MAILBOX_MAGIC, MAGIC_JTAG);
        Xil_Out32(MAILBOX_VERSION, PROTOCOL_VERSION);
        publish_error(0U, ERR_DMA_INIT);
        for (;;) {}
    }

    status = XAxiDma_CfgInitialize(&dma, cfg);
    if (status != XST_SUCCESS || XAxiDma_HasSg(&dma)) {
        Xil_Out32(MAILBOX_MAGIC, MAGIC_JTAG);
        Xil_Out32(MAILBOX_VERSION, PROTOCOL_VERSION);
        publish_error(0U, ERR_DMA_INIT);
        for (;;) {}
    }

    Xil_Out32(MAILBOX_COMMAND, 0U);
    Xil_Out32(MAILBOX_STATUS, STATUS_READY);
    Xil_Out32(MAILBOX_COMPLETED, 0U);
    Xil_Out32(MAILBOX_RESULT, 0xFFFFFFFFU);
    Xil_Out32(MAILBOX_ERROR, 0U);
    Xil_Out32(MAILBOX_VERSION, PROTOCOL_VERSION);
    Xil_Out32(MAILBOX_MAGIC, MAGIC_JTAG);
    xil_printf("CNN JTAG mailbox service ready\r\n");

    for (;;) {
        if (Xil_In32(MAILBOX_COMMAND) != COMMAND_INFER) continue;

        sequence = Xil_In32(MAILBOX_SEQUENCE);
        Xil_Out32(MAILBOX_COMMAND, 0U);
        Xil_Out32(MAILBOX_ERROR, 0U);
        Xil_Out32(MAILBOX_STATUS, STATUS_BUSY);

        status = run_inference();
        if (status != XST_SUCCESS) {
            publish_error(sequence, (u32)status);
            continue;
        }

        Xil_Out32(MAILBOX_RESULT, (u32)(Xil_In8(MAILBOX_DMA_OUTPUT) & 0x0FU));
        Xil_Out32(MAILBOX_COMPLETED, sequence);
        Xil_Out32(MAILBOX_STATUS, STATUS_DONE);
    }
}
