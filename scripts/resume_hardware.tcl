# Recover interrupted/tool-startup OOC runs without discarding completed IPs.
set root [file normalize "[file dirname [info script]]/.."]
open_project "$root/vivado/cnn_mnist_haoyue/cnn_mnist_haoyue.xpr"
foreach run [get_runs -quiet *_synth_1] {
    set status [get_property STATUS $run]
    puts "OOC_STATUS:$run=$status"
    if {$status eq "synth_design Complete!"} {continue}
    reset_run $run
    launch_runs $run -jobs 1
    wait_on_run $run
    if {[get_property STATUS $run] ne "synth_design Complete!"} {error "OOC_RECOVERY_FAILED:$run"}
}
reset_run synth_1
launch_runs synth_1 -jobs 1
wait_on_run synth_1
if {[get_property STATUS [get_runs synth_1]] ne "synth_design Complete!"} {error SYNTHESIS_FAILED}
launch_runs impl_1 -to_step write_bitstream -jobs 1
wait_on_run impl_1
if {[get_property STATUS [get_runs impl_1]] ne "write_bitstream Complete!"} {error IMPLEMENTATION_FAILED}
open_run impl_1
set output "$root/output"
report_utilization -file "$output/utilization.rpt"
report_timing_summary -file "$output/timing_summary.rpt"
report_drc -file "$output/drc.rpt"
write_hw_platform -fixed -include_bit -force -file "$output/cnn_mnist_haoyue.xsa"
file copy -force "[get_property DIRECTORY [get_runs impl_1]]/system_wrapper.bit" "$output/cnn_mnist_haoyue.bit"
puts CNN_HARDWARE_BUILD_PASSED
