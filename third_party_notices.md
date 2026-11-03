# Third-party notices and publication scope

The root MIT license applies to the original code and documentation contributed to this V3 publication. It does not replace the licenses of third-party datasets, vendor-generated initialization code, vendor tools, or libraries.

- QMNIST software and reconstruction metadata: Facebook and contributors, BSD license retained at `data/qmnist/LICENSE`. Source: https://github.com/facebookresearch/qmnist. Citation: Chhavi Yadav and Leon Bottou, Cold Case The Lost MNIST Digits, NeurIPS 2019.
- MNIST/NIST digit data retain their original dataset terms. Dataset names and their original sources are retained in the data documentation; they are not relicensed as new MIT-authored images.
- AMD/Xilinx Vivado, Vitis, BSP libraries and generated PS initialization files retain applicable vendor terms and original notices. Tool installers and BSP library sources are not included. Reproduction requires the user's own licensed tool installation.
- Python, PyTorch, NumPy, Flask, Pillow and other dependencies are installed separately under their respective licenses.
- The local project developed from an earlier KV260/PYNQ-oriented CNN example. Legacy V1 RTL headers name Bo Young Kang (2021, all rights reserved), and no redistribution license was supplied for those files. The unused V1 RTL, its old wrapper/testbench and legacy hardware bitstreams are excluded from this public V3 repository and its release archives. The actual V3 core is self-contained in `rtl/axis_cnn_mnist_v3.v`; the Vivado build now explicitly selects that core. This publication does not claim authorship or MIT relicensing of the excluded V1 code.
- V2 numeric checkpoints are retained only as the actual warm-start and accuracy comparison baseline. The public source contains the V3 training and quantization procedure, V3 core and host/firmware implementation.
