# Compare forty labeled samples to the integer reference over one connection.
set root [file normalize "[file dirname [info script]]/.."]
set f [open "$root/tb/vectors/board_images.bin" rb];set images [read $f];close $f
set f [open "$root/tb/vectors/board_predictions.bin" rb];binary scan [read $f] cu* expected;close $f
set f [open "$root/tb/vectors/board_labels.bin" rb];binary scan [read $f] cu* labels;close $f
set log [open "$root/reports/physical_board_test.txt" w]
set correct 0
connect
try {
    targets -set -nocase -filter {name =~ "ARM Cortex-A9 MPCore #0"}
    stop
    if {[mrd -value 0x08000000]!=0x4A544147 || [mrd -value 0x08000004]!=3} {error "LOAD_V3_BIT_AND_ELF_FIRST"}
    for {set i 0} {$i<40} {incr i} {
        set payload "$root/reports/board_test_input.bin"
        set f [open $payload wb];puts -nonewline $f [string range $images [expr {$i*784}] [expr {$i*784+783}]];close $f
        set seq [expr {([mrd -value 0x08000014]+1)&0xffffffff}]
        dow -data $payload 0x08000100
        mwr 0x08000010 $seq;mwr 0x0800000C 0;mwr 0x08000008 1;con
        set done 0
        for {set poll 0} {$poll<200} {incr poll} {
            after 25;stop
            set status [mrd -value 0x0800000C]
            if {($status&0x80000000)!=0} {error "BOARD_DMA_ERROR:[mrd -value 0x0800001C]"}
            if {$status==2 && [mrd -value 0x08000014]==$seq} {set done 1;break}
            con
        }
        if {!$done} {error "BOARD_TIMEOUT:$i"}
        set got [mrd -value 0x08000018]
        if {$got!=[lindex $expected $i]} {error "BOARD_REFERENCE_MISMATCH:$i got=$got expected=[lindex $expected $i]"}
        if {$got==[lindex $labels $i]} {incr correct}
        set line "BOARD_CASE_PASS index=$i label=[lindex $labels $i] prediction=$got"
        puts $line;puts $log $line
    }
    set line "V3_PHYSICAL_BOARD_PASS agreement=40/40 label_correct=$correct/40"
    puts $line;puts $log $line
} on error {msg opts} {
    puts $log "PHYSICAL_TEST_FAILED:$msg"
    return -options $opts $msg
} finally {
    close $log
    catch {con};catch {disconnect}
}
