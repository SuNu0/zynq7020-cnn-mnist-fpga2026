set script_dir [file dirname [file normalize [info script]]]
set root [file normalize "$script_dir/.."]
set project_dir [file normalize "$root/vivado/cnn_mnist_haoyue"]
file mkdir [file dirname $project_dir]

proc ip_vlnv {name} {
    set defs [get_ipdefs -all -filter "NAME == $name"]
    if {[llength $defs] == 0} { error "IP_NOT_FOUND:$name" }
    return [get_property VLNV [lindex $defs 0]]
}

create_project cnn_mnist_haoyue $project_dir -part xc7z020clg400-2 -force
set_property target_language Verilog [current_project]
add_files -norecurse "$root/rtl/axis_cnn_mnist_v3.v"
add_files -norecurse [glob "$root/rtl/*.mem"]
update_compile_order -fileset sources_1

create_bd_design system

set ps [create_bd_cell -type ip -vlnv [ip_vlnv processing_system7] processing_system7_0]
set_property -dict [list \
    CONFIG.PCW_EN_DDR {1} \
    CONFIG.PCW_UIPARAM_DDR_ENABLE {1} \
    CONFIG.PCW_UIPARAM_DDR_PARTNO {MT41K256M16 RE-125} \
    CONFIG.PCW_UIPARAM_DDR_BUS_WIDTH {32 Bit} \
    CONFIG.PCW_CRYSTAL_PERIPHERAL_FREQMHZ {33.333333} \
    CONFIG.PCW_UART0_PERIPHERAL_ENABLE {1} \
    CONFIG.PCW_UART0_UART0_IO {MIO 14 .. 15} \
    CONFIG.PCW_USE_M_AXI_GP0 {1} \
    CONFIG.PCW_USE_S_AXI_HP0 {1} \
    CONFIG.PCW_EN_CLK0_PORT {1} \
    CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {90.0} \
    CONFIG.PCW_EN_RST0_PORT {1}] $ps

make_bd_intf_pins_external [get_bd_intf_pins $ps/DDR]
set_property name DDR [get_bd_intf_ports DDR_0]
make_bd_intf_pins_external [get_bd_intf_pins $ps/FIXED_IO]
set_property name FIXED_IO [get_bd_intf_ports FIXED_IO_0]

set dma [create_bd_cell -type ip -vlnv [ip_vlnv axi_dma] axi_dma_0]
set_property -dict [list \
    CONFIG.c_include_sg {0} \
    CONFIG.c_include_mm2s {1} \
    CONFIG.c_include_s2mm {1} \
    CONFIG.c_m_axis_mm2s_tdata_width {8} \
    CONFIG.c_s_axis_s2mm_tdata_width {8} \
    CONFIG.c_sg_length_width {14}] $dma

set rst [create_bd_cell -type ip -vlnv [ip_vlnv proc_sys_reset] rst_ps7_0_100M]
set gp_ic [create_bd_cell -type ip -vlnv [ip_vlnv axi_interconnect] ps7_gp0_axi_periph]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] $gp_ic
set hp_ic [create_bd_cell -type ip -vlnv [ip_vlnv axi_interconnect] dma_hp0_interconnect]
set_property -dict [list CONFIG.NUM_SI {2} CONFIG.NUM_MI {1}] $hp_ic

set cnn [create_bd_cell -type module -reference axis_cnn_mnist axis_cnn_mnist_0]

connect_bd_intf_net [get_bd_intf_pins $ps/M_AXI_GP0] [get_bd_intf_pins $gp_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins $gp_ic/M00_AXI] [get_bd_intf_pins $dma/S_AXI_LITE]
connect_bd_intf_net [get_bd_intf_pins $dma/M_AXI_MM2S] [get_bd_intf_pins $hp_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins $dma/M_AXI_S2MM] [get_bd_intf_pins $hp_ic/S01_AXI]
connect_bd_intf_net [get_bd_intf_pins $hp_ic/M00_AXI] [get_bd_intf_pins $ps/S_AXI_HP0]
connect_bd_intf_net [get_bd_intf_pins $dma/M_AXIS_MM2S] [get_bd_intf_pins $cnn/s_axis]
connect_bd_intf_net [get_bd_intf_pins $cnn/m_axis] [get_bd_intf_pins $dma/S_AXIS_S2MM]

set clk_pin [get_bd_pins $ps/FCLK_CLK0]
connect_bd_net $clk_pin \
    [get_bd_pins $ps/M_AXI_GP0_ACLK] [get_bd_pins $ps/S_AXI_HP0_ACLK] \
    [get_bd_pins $gp_ic/ACLK] [get_bd_pins $gp_ic/S00_ACLK] [get_bd_pins $gp_ic/M00_ACLK] \
    [get_bd_pins $hp_ic/ACLK] [get_bd_pins $hp_ic/S00_ACLK] [get_bd_pins $hp_ic/S01_ACLK] [get_bd_pins $hp_ic/M00_ACLK] \
    [get_bd_pins $dma/s_axi_lite_aclk] [get_bd_pins $dma/m_axi_mm2s_aclk] [get_bd_pins $dma/m_axi_s2mm_aclk] \
    [get_bd_pins $cnn/aclk] [get_bd_pins $rst/slowest_sync_clk]
connect_bd_net [get_bd_pins $ps/FCLK_RESET0_N] [get_bd_pins $rst/ext_reset_in]
connect_bd_net [get_bd_pins $rst/peripheral_aresetn] \
    [get_bd_pins $dma/axi_resetn] [get_bd_pins $cnn/aresetn] \
    [get_bd_pins $gp_ic/ARESETN] [get_bd_pins $gp_ic/S00_ARESETN] [get_bd_pins $gp_ic/M00_ARESETN] \
    [get_bd_pins $hp_ic/ARESETN] [get_bd_pins $hp_ic/S00_ARESETN] [get_bd_pins $hp_ic/S01_ARESETN] [get_bd_pins $hp_ic/M00_ARESETN]

assign_bd_address
validate_bd_design
save_bd_design

set required [dict create \
    PCW_EN_DDR 1 \
    PCW_UIPARAM_DDR_ENABLE 1 \
    PCW_UIPARAM_DDR_BUS_WIDTH {32 Bit} \
    PCW_UART0_PERIPHERAL_ENABLE 1 \
    PCW_UART0_UART0_IO {MIO 14 .. 15} \
    PCW_USE_M_AXI_GP0 1 \
    PCW_USE_S_AXI_HP0 1]
dict for {key expected} $required {
    set actual [get_property CONFIG.$key $ps]
    puts "READBACK:$key=$actual"
    if {$actual ne $expected} { error "PS7_READBACK_FAIL:$key expected=$expected actual=$actual" }
}
puts "READBACK:DDR_PART=[get_property CONFIG.PCW_UIPARAM_DDR_PARTNO $ps]"
puts "READBACK:FCLK0_MHZ=[get_property CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ $ps]"
puts "READBACK:DMA_SG=[get_property CONFIG.c_include_sg $dma]"
puts "IP_CONFIGURATION_COVERAGE:FULL"

generate_target all [get_files "$project_dir/cnn_mnist_haoyue.srcs/sources_1/bd/system/system.bd"]
set wrapper [make_wrapper -files [get_files "$project_dir/cnn_mnist_haoyue.srcs/sources_1/bd/system/system.bd"] -top]
add_files -norecurse $wrapper
set_property top system_wrapper [get_filesets sources_1]
update_compile_order -fileset sources_1
puts "HAOYUE_CNN_PROJECT_CREATED:$project_dir"
