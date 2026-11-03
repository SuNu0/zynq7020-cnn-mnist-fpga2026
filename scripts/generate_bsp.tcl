# Generate the BSP from the current XSA, with no Eclipse application project.
set root [file normalize "[file dirname [info script]]/.."]
if {$argc!=1} {error "USAGE:generate_bsp.tcl <new-workspace>"}
set workspace [file normalize [lindex $argv 0]]
if {![string match "$root/build/*" $workspace]} {error "WORKSPACE_OUTSIDE_V3_BUILD:$workspace"}
setws $workspace
platform create -name cnn_v3_platform -hw "$root/output/cnn_mnist_haoyue.xsa" -proc ps7_cortexa9_0 -os standalone
platform generate
file copy -force "$workspace/cnn_v3_platform/hw/ps7_init.tcl" "$root/output/ps7_init.tcl"
puts V3_BSP_GENERATION_PASS
