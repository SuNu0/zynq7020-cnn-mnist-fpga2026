// V3: 1->8->16 CNN, signed Q12 weights, 48-bit accumulation.
// The frame is accepted on TVALID && TREADY; output is held until accepted.
module axis_cnn_mnist (
    input wire aclk, input wire aresetn,
    output wire s_axis_tready,
    input wire [7:0] s_axis_tdata, input wire s_axis_tvalid,
    input wire m_axis_tready,
    output wire [7:0] m_axis_tdata,
    output wire m_axis_tvalid, output wire m_axis_tlast
);
    localparam LOAD=0, C_INIT=1, C_READ=2, C_MUL=3, C_ADD=4,
               C_DONE=5, F_INIT=6, F_READ=7, F_MUL=8, F_ADD=9,
               F_DONE=10, RESULT=11;
    reg [3:0] state;
    reg [9:0] load_index;
    reg layer;
    reg [4:0] oc;
    reg [3:0] ic,px,py;
    reg [2:0] kx,ky;
    reg [1:0] window;
    reg [10:0] out_index;
    reg [7:0] fc_index;
    reg [3:0] best_digit;
    reg signed [47:0] accumulator,pool_best,best_score;
    reg [3:0] result_digit;
    (* ram_style="block" *) reg [7:0] image_mem [0:783];
    (* ram_style="block" *) reg [15:0] feature1 [0:1151];
    (* ram_style="block" *) reg [15:0] feature2 [0:255];
    (* rom_style="block" *) reg signed [15:0] c1_weight [0:199];
    (* rom_style="block" *) reg signed [15:0] c2_weight [0:3199];
    (* rom_style="block" *) reg signed [15:0] fc_weight [0:2559];
    reg signed [31:0] c1_bias [0:7];
    reg signed [31:0] c2_bias [0:15];
    reg signed [31:0] fc_bias [0:9];
    reg signed [16:0] operand_a;
    reg signed [15:0] operand_b;
    (* use_dsp="yes" *) reg signed [32:0] product;
    initial begin
        $readmemh("v3_conv1_weight.mem",c1_weight);
        $readmemh("v3_conv2_weight.mem",c2_weight);
        $readmemh("v3_fc_weight.mem",fc_weight);
        $readmemh("v3_conv1_bias.mem",c1_bias);
        $readmemh("v3_conv2_bias.mem",c2_bias);
        $readmemh("v3_fc_bias.mem",fc_bias);
    end
    wire [10:0] image_address=(py*2+window[1]+ky)*28+px*2+window[0]+kx;
    wire [10:0] c2_address=ic*144+(py*2+window[1]+ky)*12+px*2+window[0]+kx;
    wire [7:0] c1_waddress=oc*25+ky*5+kx;
    wire [11:0] c2_waddress=oc*200+ic*25+ky*5+kx;
    wire [11:0] fc_waddress=oc*256+fc_index;
    wire signed [47:0] selected_max=(accumulator>pool_best)?accumulator:pool_best;
    wire signed [47:0] rounded=(selected_max+48'sd2048)>>>12;
    wire [15:0] pooled=(rounded<=0)?16'd0:((rounded>65535)?16'hffff:rounded[15:0]);
    assign s_axis_tready=aresetn && state==LOAD;
    assign m_axis_tvalid=aresetn && state==RESULT;
    assign m_axis_tlast=m_axis_tvalid;
    assign m_axis_tdata={4'b0,result_digit};
    // A single pipelined DSP multiplier. ADD uses the preceding product.
    always @(posedge aclk) product <= operand_a*operand_b;
    always @(posedge aclk) begin
        if(!aresetn) begin
            state<=LOAD;load_index<=0;layer<=0;oc<=0;ic<=0;
            px<=0;py<=0;kx<=0;ky<=0;window<=0;out_index<=0;fc_index<=0;
            accumulator<=0;pool_best<=0;best_score<=0;best_digit<=0;
            result_digit<=0;operand_a<=0;operand_b<=0;
        end else case(state)
            LOAD: if(s_axis_tvalid && s_axis_tready) begin
                image_mem[load_index]<=s_axis_tdata;
                if(load_index==783) begin
                    load_index<=0;layer<=0;oc<=0;ic<=0;px<=0;py<=0;
                    kx<=0;ky<=0;window<=0;out_index<=0;pool_best<=0;
                    state<=C_INIT;
                end else load_index<=load_index+1'b1;
            end
            C_INIT: begin
                accumulator<=layer?{{16{c2_bias[oc][31]}},c2_bias[oc]}:
                                   {{16{c1_bias[oc][31]}},c1_bias[oc]};
                ic<=0;kx<=0;ky<=0;state<=C_READ;
            end
            C_READ: begin
                if(layer) begin
                    operand_a<=$signed({1'b0,feature1[c2_address]});
                    operand_b<=c2_weight[c2_waddress];
                end else begin
                    operand_a<=$signed({9'b0,image_mem[image_address]});
                    operand_b<=c1_weight[c1_waddress];
                end
                state<=C_MUL;
            end
            C_MUL: state<=C_ADD;
            C_ADD: begin
                accumulator<=accumulator+{{15{product[32]}},product};
                if(kx==4) begin
                    kx<=0;
                    if(ky==4) begin
                        ky<=0;
                        if(!layer || ic==7) state<=C_DONE;
                        else begin ic<=ic+1'b1;state<=C_READ;end
                    end else begin ky<=ky+1'b1;state<=C_READ;end
                end else begin kx<=kx+1'b1;state<=C_READ;end
            end
            C_DONE: begin
                if(window!=3) begin
                    pool_best<=selected_max;window<=window+1'b1;state<=C_INIT;
                end else begin
                    if(layer) feature2[out_index]<=pooled;
                    else feature1[out_index]<=pooled;
                    window<=0;pool_best<=0;out_index<=out_index+1'b1;
                    state<=C_INIT;
                    if(px==(layer?3:11)) begin
                        px<=0;
                        if(py==(layer?3:11)) begin
                            py<=0;
                            if(oc==(layer?15:7)) begin
                                oc<=0;out_index<=0;
                                if(layer) begin
                                    fc_index<=0;best_digit<=0;
                                    best_score<=48'sh800000000000;state<=F_INIT;
                                end else layer<=1;
                            end else oc<=oc+1'b1;
                        end else py<=py+1'b1;
                    end else px<=px+1'b1;
                end
            end
            F_INIT: begin
                accumulator<={{16{fc_bias[oc][31]}},fc_bias[oc]};
                fc_index<=0;state<=F_READ;
            end
            F_READ: begin
                operand_a<=$signed({1'b0,feature2[fc_index]});
                operand_b<=fc_weight[fc_waddress];state<=F_MUL;
            end
            F_MUL: state<=F_ADD;
            F_ADD: begin
                accumulator<=accumulator+{{15{product[32]}},product};
                if(fc_index==255) state<=F_DONE;
                else begin fc_index<=fc_index+1'b1;state<=F_READ;end
            end
            F_DONE: begin
                if(accumulator>best_score) begin
                    best_score<=accumulator;best_digit<=oc[3:0];
                end
                if(oc==9) begin
                    result_digit<=(accumulator>best_score)?oc[3:0]:best_digit;
                    state<=RESULT;
                end else begin oc<=oc+1'b1;state<=F_INIT;end
            end
            RESULT: if(m_axis_tready) state<=LOAD;
            default: state<=LOAD;
        endcase
    end
endmodule
