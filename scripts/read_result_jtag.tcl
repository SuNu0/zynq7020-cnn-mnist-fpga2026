connect
targets -set -nocase -filter {name =~ "ARM Cortex-A9 MPCore #0"}
stop
set pc [rrd pc]
set result [mrd -value 0x0010CB40]
puts [format "CPU_PC=%s" $pc]
puts [format "CNN_RESULT_WORD=0x%08X" $result]
if {($result & 0xFF) == 3} {
    puts "CNN_PHYSICAL_DMA_TEST_PASSED"
} else {
    puts "CNN_PHYSICAL_DMA_TEST_FAILED"
}
disconnect
