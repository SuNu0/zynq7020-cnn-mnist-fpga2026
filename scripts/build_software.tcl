set script_dir [file dirname [file normalize [info script]]]
set root [file normalize "$script_dir/.."]
set workspace [file normalize "$root/vitis_workspace"]
set xsa [file normalize "$root/output/cnn_mnist_haoyue.xsa"]

if {![file exists $xsa]} { error "XSA_NOT_FOUND:$xsa" }
setws $workspace
platform create -name cnn_mnist_platform -hw $xsa \
    -proc ps7_cortexa9_0 -os standalone
platform generate

set ps_init "$workspace/cnn_mnist_platform/hw/ps7_init.tcl"
if {![file exists $ps_init]} { error "PS_INIT_NOT_FOUND:$ps_init" }
file copy -force $ps_init "$root/output/ps7_init.tcl"

app create -name cnn_mnist_dma_app -platform cnn_mnist_platform \
    -domain standalone_domain -template {Empty Application}
importsources -name cnn_mnist_dma_app -path "$root/software/baremetal/src"
app build -name cnn_mnist_dma_app

set elf "$workspace/cnn_mnist_dma_app/Debug/cnn_mnist_dma_app.elf"
if {![file exists $elf]} { error "ELF_NOT_FOUND:$elf" }
file copy -force $elf "$root/output/cnn_mnist_dma_app.elf"
puts "CNN_SOFTWARE_BUILD_PASSED"
puts "ELF_FILE:$root/output/cnn_mnist_dma_app.elf"
