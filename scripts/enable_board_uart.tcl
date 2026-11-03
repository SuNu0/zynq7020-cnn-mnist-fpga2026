set script_dir [file dirname [file normalize [info script]]]
set root [file normalize "$script_dir/.."]
set project "$root/vivado/cnn_mnist_haoyue/cnn_mnist_haoyue.xpr"

open_project $project
open_bd_design [get_files system.bd]
set ps [get_bd_cells processing_system7_0]
set_property -dict [list \
    CONFIG.PCW_UART0_PERIPHERAL_ENABLE {1} \
    CONFIG.PCW_UART0_UART0_IO {MIO 14 .. 15}] $ps
validate_bd_design
save_bd_design
generate_target all [get_files system.bd]

set uart_enable [get_property CONFIG.PCW_UART0_PERIPHERAL_ENABLE $ps]
set uart_io [get_property CONFIG.PCW_UART0_UART0_IO $ps]
puts "READBACK:UART0_ENABLE=$uart_enable"
puts "READBACK:UART0_IO=$uart_io"
if {$uart_enable ne "1" || $uart_io ne "MIO 14 .. 15"} {
    error "UART0_READBACK_FAILED"
}
puts "HAOYUE_UART0_CONFIGURATION_PASSED"
close_project
