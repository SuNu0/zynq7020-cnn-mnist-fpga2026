import struct
import time

import serial
from serial.tools import list_ports

REQUEST_MAGIC = b"MNST"
RESPONSE_MAGIC = b"RSLT"
IMAGE_BYTES = 784


def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def find_board_port() -> str:
    ports = list(list_ports.comports())
    for port in ports:
        text = f"{port.description} {port.manufacturer or ''} {port.hwid}".lower()
        if "ch340" in text or "wch" in text or "1a86" in text:
            return port.device
    if len(ports) == 1:
        return ports[0].device
    visible = ", ".join(f"{p.device} ({p.description})" for p in ports) or "none"
    raise RuntimeError(f"Cannot identify the Haoyue USB-UART port; visible ports: {visible}")


class HaoyueCnn:
    def __init__(self, port: str | None = None, baudrate: int = 115200):
        self.port = port or find_board_port()
        self.serial = serial.Serial(self.port, baudrate=baudrate, timeout=2.0)
        time.sleep(0.1)
        self.serial.reset_input_buffer()

    def close(self) -> None:
        self.serial.close()

    def _read_exact(self, size: int) -> bytes:
        data = self.serial.read(size)
        if len(data) != size:
            raise TimeoutError(f"Board response timeout: expected {size} bytes, received {len(data)}")
        return data

    def predict(self, pixels: bytes) -> int:
        if len(pixels) != IMAGE_BYTES:
            raise ValueError(f"Expected {IMAGE_BYTES} pixels, received {len(pixels)}")
        packet = REQUEST_MAGIC + struct.pack("<H", len(pixels)) + pixels
        packet += struct.pack("<H", crc16_ccitt(pixels))
        self.serial.reset_input_buffer()
        self.serial.write(packet)
        self.serial.flush()

        magic = self._read_exact(4)
        if magic != RESPONSE_MAGIC:
            raise RuntimeError(f"Invalid board response magic: {magic!r}")
        body = self._read_exact(2)
        received_crc = struct.unpack("<H", self._read_exact(2))[0]
        if received_crc != crc16_ccitt(body):
            raise RuntimeError("Board response CRC check failed")
        status, prediction = body
        if status != 0:
            raise RuntimeError(f"Board inference failed with status {status}")
        return prediction
