set script_dir [file dirname [file normalize [info script]]]
set root [file normalize "$script_dir/.."]
set workspace [file normalize "$root/vitis_jtag_mailbox_workspace"]
set xsa [file normalize "$root/output/cnn_mnist_haoyue.xsa"]

if {![file exists $xsa]} { error "XSA_NOT_FOUND:$xsa" }
if {[file exists $workspace]} {
    if {[file dirname $workspace] ne $root || [file tail $workspace] ne "vitis_jtag_mailbox_workspace"} {
        error "UNSAFE_GENERATED_WORKSPACE_PATH:$workspace"
    }
    # This directory is generated and ignored by Git; recreate it so source
    # changes cannot be hidden by stale imported Vitis files.
    file delete -force $workspace
}
setws $workspace
platform create -name cnn_mnist_jtag_platform -hw $xsa \
    -proc ps7_cortexa9_0 -os standalone
platform generate
set ps_init "$workspace/cnn_mnist_jtag_platform/hw/ps7_init.tcl"
if {![file exists $ps_init]} { error "PS_INIT_NOT_FOUND:$ps_init" }
file copy -force $ps_init "$root/output/ps7_init.tcl"
app create -name cnn_mnist_jtag_mailbox -platform cnn_mnist_jtag_platform \
    -domain standalone_domain -template {Empty Application}
importsources -name cnn_mnist_jtag_mailbox -path "$root/software/jtag_mailbox/src"
app build -name cnn_mnist_jtag_mailbox

set elf "$workspace/cnn_mnist_jtag_mailbox/Debug/cnn_mnist_jtag_mailbox.elf"
if {![file exists $elf]} { error "JTAG_MAILBOX_ELF_NOT_FOUND:$elf" }
file copy -force $elf "$root/output/cnn_mnist_jtag_mailbox.elf"
puts "CNN_JTAG_MAILBOX_BUILD_PASSED"
