set script_dir [file dirname [file normalize [info script]]]
set root [file normalize "$script_dir/.."]
set project "$root/vivado/cnn_mnist_haoyue/cnn_mnist_haoyue.xpr"
set output "$root/output"
file mkdir $output

if {![file exists $project]} {
    source "$script_dir/create_project.tcl"
} else {
    open_project $project
}

reset_run synth_1
# Serialize synthesis: Vivado 2025.2 intermittently fails while loading Tcl apps
# when several block-design OOC runs start at the same time on this machine.
launch_runs synth_1 -jobs 1
wait_on_run synth_1
if {[get_property STATUS [get_runs synth_1]] ne {synth_design Complete!}} {
    error "SYNTHESIS_FAILED:[get_property STATUS [get_runs synth_1]]"
}

launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
if {[get_property STATUS [get_runs impl_1]] ne {write_bitstream Complete!}} {
    error "IMPLEMENTATION_FAILED:[get_property STATUS [get_runs impl_1]]"
}

open_run impl_1
report_utilization -file "$output/utilization.rpt"
report_timing_summary -file "$output/timing_summary.rpt"
report_drc -file "$output/drc.rpt"
write_hw_platform -fixed -include_bit -force -file "$output/cnn_mnist_haoyue.xsa"
set bit_file "[get_property DIRECTORY [get_runs impl_1]]/system_wrapper.bit"
if {![file exists $bit_file]} { error "BITSTREAM_NOT_FOUND:$bit_file" }
file copy -force $bit_file "$output/cnn_mnist_haoyue.bit"
puts "CNN_HARDWARE_BUILD_PASSED"
