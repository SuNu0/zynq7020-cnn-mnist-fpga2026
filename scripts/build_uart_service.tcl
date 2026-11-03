set script_dir [file dirname [file normalize [info script]]]
set root [file normalize "$script_dir/.."]
set workspace [file normalize "$root/vitis_uart_workspace"]
set xsa [file normalize "$root/output/cnn_mnist_haoyue.xsa"]

if {![file exists $xsa]} { error "XSA_NOT_FOUND:$xsa" }
if {[file exists $workspace]} {
    if {[file dirname $workspace] ne $root || [file tail $workspace] ne "vitis_uart_workspace"} {
        error "UNSAFE_GENERATED_WORKSPACE_PATH:$workspace"
    }
    file delete -force $workspace
}
setws $workspace
platform create -name cnn_mnist_uart_platform -hw $xsa \
    -proc ps7_cortexa9_0 -os standalone
platform generate
app create -name cnn_mnist_uart_service -platform cnn_mnist_uart_platform \
    -domain standalone_domain -template {Empty Application}
importsources -name cnn_mnist_uart_service -path "$root/software/uart_service/src"
app build -name cnn_mnist_uart_service

set elf "$workspace/cnn_mnist_uart_service/Debug/cnn_mnist_uart_service.elf"
if {![file exists $elf]} { error "UART_SERVICE_ELF_NOT_FOUND:$elf" }
file copy -force $elf "$root/output/cnn_mnist_uart_service.elf"
puts "CNN_UART_SERVICE_BUILD_PASSED"
