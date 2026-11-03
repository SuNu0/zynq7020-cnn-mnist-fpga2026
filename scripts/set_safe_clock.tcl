set script_dir [file dirname [file normalize [info script]]]
set root [file normalize "$script_dir/.."]
open_project "$root/vivado/cnn_mnist_haoyue/cnn_mnist_haoyue.xpr"
open_bd_design "$root/vivado/cnn_mnist_haoyue/cnn_mnist_haoyue.srcs/sources_1/bd/system/system.bd"
set ps [get_bd_cells processing_system7_0]
set_property -dict [list CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {90.0}] $ps
validate_bd_design
save_bd_design
generate_target all [get_files system.bd] -force
set actual [get_property CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ $ps]
puts "READBACK:FCLK0_MHZ=$actual"
if {$actual ne {90.0}} { error "FCLK_READBACK_FAIL:$actual" }
puts "SAFE_CLOCK_APPLIED"
