import os
import re
import subprocess
import tempfile
from pathlib import Path

IMAGE_BYTES = 784


class JtagMailboxCnn:
    def __init__(self, xsct: str | None = None, timeout: float = 90.0):
        self.root = Path(__file__).resolve().parents[2]
        self.xsct = Path(
            xsct
            or os.environ.get("XILINX_XSCT", "D:/Xilinx/2025.2/Vitis/bin/xsct.bat")
        )
        self.script = self.root / "scripts" / "jtag_predict.tcl"
        self.timeout = timeout
        if not self.xsct.is_file():
            raise FileNotFoundError(f"XSCT not found: {self.xsct}")

    def close(self) -> None:
        pass

    def predict(self, pixels: bytes) -> int:
        if len(pixels) != IMAGE_BYTES:
            raise ValueError(f"Expected {IMAGE_BYTES} pixels, received {len(pixels)}")

        payload_path = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix="cnn-mnist-", suffix=".jtag-input.bin", delete=False
            ) as payload:
                payload.write(pixels)
                payload_path = Path(payload.name)

            completed = subprocess.run(
                [str(self.xsct), str(self.script), str(payload_path)],
                cwd=self.root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                check=False,
            )
            output = f"{completed.stdout}\n{completed.stderr}"
            if completed.returncode != 0:
                tail = "\n".join(output.strip().splitlines()[-12:])
                raise RuntimeError(f"XSCT JTAG inference failed:\n{tail}")

            match = re.search(r"JTAG_PREDICTION=(\d+)", output)
            if match is None:
                raise RuntimeError("XSCT completed without a JTAG_PREDICTION marker")
            prediction = int(match.group(1))
            if not 0 <= prediction <= 9:
                raise RuntimeError(f"Invalid prediction returned over JTAG: {prediction}")
            return prediction
        finally:
            if payload_path is not None:
                payload_path.unlink(missing_ok=True)
