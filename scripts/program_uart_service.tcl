set script_dir [file dirname [file normalize [info script]]]
set root [file normalize "$script_dir/.."]
set bit "$root/output/cnn_mnist_haoyue.bit"
set elf "$root/output/cnn_mnist_uart_service.elf"
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
puts "CNN_UART_SERVICE_PROGRAMMED"
disconnect
