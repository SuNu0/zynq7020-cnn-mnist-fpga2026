# Program PL, initialize the Zynq PS, download the DMA test application, and run.
# Usage: D:/Xilinx/2025.2/Vitis/bin/xsct.bat scripts/program_jtag.tcl
set script_dir [file dirname [file normalize [info script]]]
set root [file normalize "$script_dir/.."]
set bit "$root/output/cnn_mnist_haoyue.bit"
set elf "$root/output/cnn_mnist_dma_app.elf"
set ps_init "$root/output/ps7_init.tcl"

foreach required [list $bit $elf $ps_init] {
    if {![file exists $required]} { error "REQUIRED_FILE_MISSING:$required" }
}

connect
targets -set -nocase -filter {name =~ "APU"}
rst -system
after 1000
targets -set -nocase -filter {name =~ "ARM Cortex-A9 MPCore #0"}
fpga -file $bit
source $ps_init
ps7_init
ps7_post_config
dow $elf
con
puts "CNN_JTAG_PROGRAM_AND_RUN_PASSED"
disconnect
