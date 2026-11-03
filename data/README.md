# Dataset payload

The Git repository includes this index, small RTL reference vectors in `tb/vectors`, deployed weights, and model checkpoints. Full training/evaluation data are supplied in the fixed release asset:

https://github.com/SuNu0/zynq7020-cnn-mnist-fpga2026/releases/download/v3-submission-20261103/datasets.zip

From the project root run `python scripts/fetch_data.py`, or download that ZIP manually and extract it at the root, preserving its `data/` prefix. Then run `python skill/verify_manifest.py data/dataset_manifest.csv --root .`.

The payload contains original MNIST IDX files, compressed xNIST, source metadata, and the fixed V3 split indices. `scripts/prepare_v3_data.py` can recover the large uncompressed xNIST image file from its checksum-verified XZ before training/evaluation. Do not count augmentation or repeated epochs as additional unique training images.
