connect
puts "JTAG_TARGET_SNAPSHOT_BEGIN"
puts [targets -target-properties]
puts "JTAG_TARGET_SNAPSHOT_END"
disconnect
