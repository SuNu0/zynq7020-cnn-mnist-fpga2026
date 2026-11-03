import argparse
from pathlib import Path

from board_driver import HaoyueCnn
from jtag_board_driver import JtagMailboxCnn


def load_hex_pixels(path: Path) -> bytes:
    pixels = bytes(int(token, 16) for token in path.read_text().split())
    if len(pixels) != 784:
        raise ValueError(f"Expected 784 bytes in {path}, found {len(pixels)}")
    return pixels


def main() -> None:
    default_vector = Path(__file__).resolve().parents[2] / "rtl" / "testvector" / "3_0.txt"
    parser = argparse.ArgumentParser(description="Send one raw 28x28 MNIST vector to the board")
    parser.add_argument("--transport", choices=("jtag", "uart"), default="jtag")
    parser.add_argument("--port", help="USB-UART port, for example COM5")
    parser.add_argument("--vector", type=Path, default=default_vector)
    args = parser.parse_args()

    board = JtagMailboxCnn() if args.transport == "jtag" else HaoyueCnn(port=args.port)
    try:
        prediction = board.predict(load_hex_pixels(args.vector))
    finally:
        board.close()
    print(f"BOARD_PREDICTION={prediction}")
    if args.vector.resolve() == default_vector.resolve() and prediction != 3:
        raise SystemExit("Expected prediction 3 for the supplied test vector")
    print(f"{args.transport.upper()}_INFERENCE_TEST_PASSED")


if __name__ == "__main__":
    main()
