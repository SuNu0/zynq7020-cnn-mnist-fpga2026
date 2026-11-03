set script_dir [file dirname [file normalize [info script]]]
set root [file normalize "$script_dir/.."]
set bit "$root/output/cnn_mnist_haoyue.bit"
set elf "$root/output/cnn_mnist_jtag_mailbox.elf"
set ps_init "$root/output/ps7_init.tcl"
set mailbox_magic 0x08000000
set expected_magic 0x4A544147

foreach required [list $bit $elf $ps_init] {
    if {![file exists $required]} { error "REQUIRED_FILE_MISSING:$required" }
}

connect
try {
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
    after 200
    stop
    set magic [mrd -value $mailbox_magic]
    if {$magic != $expected_magic} {
        error [format "JTAG_MAILBOX_BOOT_FAILED:magic=0x%08X" $magic]
    }
    if {[mrd -value 0x08000004] != 3} {error "V3_MAILBOX_VERSION_CHECK_FAILED"}
    puts "CNN_JTAG_MAILBOX_PROGRAMMED"
} finally {
    catch {con}
    catch {disconnect}
}
