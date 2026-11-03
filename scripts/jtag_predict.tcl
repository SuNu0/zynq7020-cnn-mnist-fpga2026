if {$argc != 1} {
    error "USAGE:xsct scripts/jtag_predict.tcl <784-byte-input.bin>"
}

set image [file normalize [lindex $argv 0]]
if {![file exists $image]} { error "INPUT_FILE_NOT_FOUND:$image" }
if {[file size $image] != 784} {
    error "INPUT_SIZE_MISMATCH:expected=784 actual=[file size $image]"
}

set mailbox_magic 0x08000000
set mailbox_command 0x08000008
set mailbox_status 0x0800000C
set mailbox_sequence 0x08000010
set mailbox_completed 0x08000014
set mailbox_result 0x08000018
set mailbox_error 0x0800001C
set mailbox_input 0x08000100
set expected_magic 0x4A544147
set status_done 2
set error_flag 0x80000000

connect
try {
    targets -set -nocase -filter {name =~ "ARM Cortex-A9 MPCore #0"}
    catch {stop}

    set magic [mrd -value $mailbox_magic]
    if {$magic != $expected_magic} {
        error [format "JTAG_MAILBOX_NOT_RUNNING:magic=0x%08X" $magic]
    }
    if {[mrd -value 0x08000004] != 3} {
        error "V3_FIRMWARE_REQUIRED: reload V3 BIT and ELF using program_jtag_mailbox.tcl"
    }

    set sequence [expr {([mrd -value $mailbox_completed] + 1) & 0xFFFFFFFF}]
    dow -data $image $mailbox_input
    mwr $mailbox_sequence $sequence
    mwr $mailbox_status 0
    mwr $mailbox_command 1
    con

    set finished 0
    for {set poll 0} {$poll < 200} {incr poll} {
        after 25
        stop
        set status [mrd -value $mailbox_status]
        if {$status == $status_done && [mrd -value $mailbox_completed] == $sequence} {
            set finished 1
            break
        }
        if {($status & $error_flag) != 0} {
            set code [mrd -value $mailbox_error]
            error [format "JTAG_MAILBOX_INFERENCE_FAILED:status=0x%08X code=%u" $status $code]
        }
        con
    }

    if {!$finished} { error "JTAG_MAILBOX_TIMEOUT" }
    set prediction [expr {[mrd -value $mailbox_result] & 0x0F}]
    puts [format "JTAG_PREDICTION=%u" $prediction]
    puts "JTAG_INFERENCE_TEST_PASSED"
} finally {
    catch {con}
    catch {disconnect}
}
