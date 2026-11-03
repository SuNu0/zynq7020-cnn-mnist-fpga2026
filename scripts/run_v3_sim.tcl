set root [file normalize "[file dirname [info script]]/.."]
set dir "$root/build/sim_v3"
create_project sim_v3 $dir -part xc7z020clg400-2 -force
set_property target_simulator XSim [current_project]
add_files -norecurse "$root/rtl/axis_cnn_mnist_v3.v"
add_files -norecurse [glob "$root/rtl/v3_*.mem"]
add_files -fileset sim_1 -norecurse "$root/tb/tb_v3.sv"
add_files -fileset sim_1 -norecurse [glob "$root/tb/vectors/*.mem"]
set_property top tb_v3 [get_filesets sim_1]
set_property xsim.simulate.runtime 0ns [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
run 950ms
close_sim
set log "$dir/sim_v3.sim/sim_1/behav/xsim/simulate.log"
set fd [open $log];set body [read $fd];close $fd
file copy -force $log "$root/reports/v3_simulation.log"
if {[string first V3_RTL_PASS $body]<0 || [regexp -nocase {Fatal:|Error:} $body]} {error V3_SIMULATION_FAILED}
puts V3_RTL_PASS
