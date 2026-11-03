`timescale 1ns/1ps
module tb_v3;
    reg clk=0,rstn=0;
    always #5 clk=~clk;
    reg [7:0] din=0;
    reg vin=0,rout=0;
    wire rin,vout,last;
    wire [7:0] dout;
    axis_cnn_mnist dut(clk,rstn,rin,din,vin,rout,dout,vout,last);
    localparam N=75;
    reg [7:0] images[0:N*784-1],expected[0:N-1];
    reg [15:0] f1[0:N*1152-1],f2[0:N*256-1];
    reg [47:0] scores[0:N*10-1];
    integer test_id=0,i,cycles=0,total_features=0,total_scores=0;
    reg [7:0] held;
    // Independent software oracle checks every pooled activation and raw logit.
    always @(posedge clk) if(rstn) begin
        cycles<=cycles+1;
        if(dut.state==5 && dut.window==3) begin
            if(!dut.layer && dut.pooled !== f1[test_id*1152+dut.out_index])
                $fatal(1,"C1_MISMATCH test=%0d address=%0d got=%0d expected=%0d",test_id,dut.out_index,dut.pooled,f1[test_id*1152+dut.out_index]);
            if(dut.layer && dut.pooled !== f2[test_id*256+dut.out_index])
                $fatal(1,"C2_MISMATCH test=%0d address=%0d got=%0d expected=%0d",test_id,dut.out_index,dut.pooled,f2[test_id*256+dut.out_index]);
            total_features<=total_features+1;
        end
        if(dut.state==10) begin
            if(dut.accumulator !== scores[test_id*10+dut.oc])
                $fatal(1,"FC_MISMATCH test=%0d digit=%0d got=%0d expected=%0d",test_id,dut.oc,dut.accumulator,$signed(scores[test_id*10+dut.oc]));
            total_scores<=total_scores+1;
        end
        if(dut.state!=0 && rin) $fatal(1,"READY_WHILE_BUSY");
    end
    task send_pixel(input [7:0] value);
        begin
            @(negedge clk);vin=1;din=value;
            @(posedge clk);while(!rin) @(posedge clk);
        end
    endtask
    initial begin
        $readmemh("images.mem",images);$readmemh("predictions.mem",expected);
        $readmemh("features1.mem",f1);$readmemh("features2.mem",f2);$readmemh("scores.mem",scores);
        repeat(8) @(negedge clk);rstn=1;
        // Reset discards an incomplete frame, then accepts a fresh 784 bytes.
        for(i=0;i<73;i=i+1) send_pixel(8'hff);
        @(negedge clk);vin=0;rstn=0;
        repeat(3) @(negedge clk);rstn=1;
        for(test_id=0;test_id<N;test_id=test_id+1) begin
            for(i=0;i<784;i=i+1) begin
                if(test_id%2==1 && i%7==0) begin
                    @(negedge clk);vin=0;din=8'hc7;
                    repeat((i%3)+1) @(negedge clk);
                end
                send_pixel(images[test_id*784+i]);
            end
            @(negedge clk);vin=0;
            // Present an offered next pixel while busy; it must not be accepted.
            if(test_id==0) begin
                vin=1;din=8'hf1;repeat(17) @(negedge clk);vin=0;
            end
            wait(vout);@(negedge clk);
            if(dout !== expected[test_id] || !last) $fatal(1,"DECISION_MISMATCH test=%0d got=%0d expected=%0d",test_id,dout,expected[test_id]);
            held=dout;
            repeat(13+test_id%11) begin
                @(negedge clk);
                if(!vout || !last || dout!==held || rin) $fatal(1,"BACKPRESSURE_FAILURE");
            end
            rout=1;@(negedge clk);rout=0;
            if(vout || !rin) $fatal(1,"DUPLICATE_OUTPUT_OR_NOT_READY");
            $display("V3_CASE_PASS id=%0d digit=%0d cycles=%0d",test_id,held,cycles);
        end
        $display("V3_RTL_PASS cases=%0d pooled_values=%0d scores=%0d",N,total_features,total_scores);
        $finish;
    end
    initial begin #900000000; $fatal(1,"V3_WATCHDOG_TIMEOUT");end
endmodule
