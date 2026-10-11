#!/usr/bin/env python3
"""
HDL Tutor 5 — single-file edition. Learn Verilog, VHDL & SystemVerilog.

    pip install PySide6
    python hdl_tutor.py

Optional: iverilog/vvp (incl. SystemVerilog via -g2012), ghdl, yosys,
nextpnr-ice40 — all auto-detected.  Built-in simulator needs nothing.
"""
import bisect, datetime, heapq, html, json, math, os, random, re, shutil
import subprocess, sys, tempfile

from PySide6.QtCore import QRect, QRectF, QSize, Qt, QTimer, QSettings, QCompleter
from PySide6.QtGui import (QAction, QColor, QFont, QFontDatabase, QPainter,
    QPainterPath, QPen, QKeySequence, QTextCharFormat, QTextCursor,
    QTextFormat, QSyntaxHighlighter, QStringListModel, QListWidgetItem,
    QToolTip)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox,
    QComboBox, QDialog, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QInputDialog, QLabel, QLineEdit, QListWidget, QMainWindow,
    QMenu, QMessageBox, QPlainTextEdit, QPushButton, QRadioButton,
    QScrollArea, QSlider, QSpinBox, QSplitter, QStackedWidget, QStyle,
    QTabWidget, QTableWidget, QTableWidgetItem, QTextBrowser, QTextEdit,
    QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    QSizePolicy)

APP_NAME = "HDL Tutor"
PROGRESS_PATH = os.path.join(os.path.expanduser("~"), ".hdl_tutor_progress.json")
MAX_TT_INPUTS = 5
SESSION_DIR = tempfile.mkdtemp(prefix="hdl_tutor_")
ROM_DIRS = [SESSION_DIR, os.getcwd()]

# ══════════════════════════════ THEMES ══════════════════════════════
DARK = dict(window="#14171e", panel="#1b1f29", input="#10131a", text="#dde3ee",
    sub="#8a93a6", border="#2a3040", accent="#4f8cff", sel="#31445f",
    editor_bg="#10131a", editor_text="#dde3ee", editor_cur="#e0af68",
    editor_num="#454f63", console_bg="#0d1017", console_text="#c9d4e3",
    ok="#7ee787", warn="#ffa657", err="#ff7b72",
    lesson_bg="#1b1f29", lesson_text="#d5dbe7", lesson_code="#6ec1ff",
    lesson_head="#9ecbff", lesson_pre="#141824",
    wave_bg="#12151c", wave_alt="#1a1f2b", wave_text="#c8d0e0",
    wave_grid="#566078", wave_sig="#7ee787", wave_bus="#4fc3f7",
    sch_bg="#12151c", sch_text="#d5dbe7", sch_wire="#5a6b8c", sch_port="#e0af68")
LIGHT = dict(window="#f2f4f8", panel="#ffffff", input="#ffffff", text="#1d2330",
    sub="#5a6274", border="#c9cfd9", accent="#2563eb", sel="#cfe0ff",
    editor_bg="#ffffff", editor_text="#1d2330", editor_cur="#b3670a",
    editor_num="#9aa1ad", console_bg="#1e2430", console_text="#d6dce8",
    ok="#1c7c2e", warn="#b25f00", err="#c62828",
    lesson_bg="#ffffff", lesson_text="#242a38", lesson_code="#0b6e99",
    lesson_head="#24356b", lesson_pre="#f0f2f7",
    wave_bg="#ffffff", wave_alt="#f0f3f9", wave_text="#2a3242",
    wave_grid="#8b93a5", wave_sig="#1c7c2e", wave_bus="#1565c0",
    sch_bg="#ffffff", sch_text="#242a38", sch_wire="#5c6b8a", sch_port="#a05a00")

def th(k, d="#888888"):
    app = QApplication.instance()
    t = app.property("theme") if app else DARK
    return (t or DARK).get(k, d)

def build_qss(t):
    return f"""
    QMainWindow, QDialog {{ background:{t['window']}; }}
    QWidget {{ background:{t['window']}; color:{t['text']}; font-size:10pt; }}
    QLabel {{ background:transparent; }}
    QGroupBox {{ border:1px solid {t['border']}; border-radius:6px;
                 margin-top:12px; background:{t['panel']}; }}
    QGroupBox::title {{ color:{t['sub']}; left:8px; }}
    QTreeWidget, QTableWidget, QListWidget {{
        background:{t['panel']}; border:1px solid {t['border']}; }}
    QHeaderView::section {{ background:{t['panel']}; color:{t['sub']}; border:0;
        border-right:1px solid {t['border']};
        border-bottom:1px solid {t['border']}; padding:4px; }}
    QTabWidget::pane {{ border:1px solid {t['border']}; background:{t['panel']}; }}
    QTabBar::tab {{ background:{t['window']}; color:{t['sub']};
        padding:5px 12px; border:1px solid {t['border']}; border-bottom:0; }}
    QTabBar::tab:selected {{ color:{t['text']};
        border-top:2px solid {t['accent']}; background:{t['panel']}; }}
    QPushButton {{ background:{t['panel']}; color:{t['text']};
        border:1px solid {t['border']}; padding:5px 12px; border-radius:4px; }}
    QPushButton:hover {{ border-color:{t['accent']}; }}
    QPushButton:checked {{ background:{t['accent']}; color:#fff; }}
    QPushButton:disabled {{ color:{t['sub']}; }}
    QLineEdit, QSpinBox, QComboBox {{ background:{t['input']}; color:{t['text']};
        border:1px solid {t['border']}; border-radius:4px; padding:3px 6px; }}
    QSlider::groove:horizontal {{ height:5px; background:{t['border']}; }}
    QSlider::handle:horizontal {{ background:{t['accent']}; width:14px;
        margin:-6px 0; border-radius:7px; }}
    QToolBar {{ background:{t['panel']}; border:0; spacing:4px; padding:3px; }}
    QStatusBar {{ background:{t['panel']}; border-top:1px solid {t['border']}; }}
    QMenu {{ background:{t['panel']}; border:1px solid {t['border']}; }}
    QMenu::item:selected {{ background:{t['accent']}; color:#fff; }}
    QScrollBar:vertical {{ background:{t['window']}; width:11px; }}
    QScrollBar::handle:vertical {{ background:{t['border']};
        border-radius:5px; min-height:30px; }}
    QScrollBar:horizontal {{ background:{t['window']}; height:11px; }}
    QScrollBar::handle:horizontal {{ background:{t['border']};
        border-radius:5px; min-width:30px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width:0; height:0; }}
    QToolTip {{ background:{t['panel']}; color:{t['text']};
        border:1px solid {t['border']}; }}
    QSplitter::handle {{ background:{t['border']}; width:2px; height:2px; }}"""

# ══════════════════════════ EXAMPLE CODE ══════════════════════════
EX_AND_GATE = """\
module and_gate(
    input  a, b,
    output y
);
    assign y = a & b;   // continuous assignment: y is ALWAYS a&b (a wire)
endmodule
"""
EX_COMBINED_TB = """\
// Design + testbench. Press Run (built-in simulator OR Icarus).
module and_gate(input a, b, output y);
    assign y = a & b;
endmodule

module tb;
    reg a, b;  wire y;
    and_gate uut (.a(a), .b(b), .y(y));
    initial begin
        a=0; b=0; #1 $display("a=%b b=%b -> y=%b", a, b, y);
        a=0; b=1; #1 $display("a=%b b=%b -> y=%b", a, b, y);
        a=1; b=0; #1 $display("a=%b b=%b -> y=%b", a, b, y);
        a=1; b=1; #1 $display("a=%b b=%b -> y=%b", a, b, y);
        $finish;
    end
endmodule
"""
ST_INV = """\
// EXERCISE: make this an inverter (y = NOT a). Press Check when done.
module inverter(
    input  a,
    output y
);
    assign y = 1'b0;   // TODO
endmodule
"""
EX_TYPES = """\
// Vectors, bit-selects, parameters.
module vec_demo #(parameter WIDTH = 4)(
    input  [WIDTH-1:0] sw,
    output [WIDTH-1:0] led,
    output             parity
);
    assign led    = ~sw;     // bitwise NOT of the whole bus
    assign parity = ^sw;     // reduction XOR
    // Literals: 4'b1010  8'hFF  16'd1000
endmodule
"""
EX_OPS = """\
// Majority-of-three. Truth Table verifies all 8 rows.
module majority3(input a, b, c, output y);
    assign y = (a & b) | (a & c) | (b & c);
    // & | ^ ~  reductions &bus  {a,b} concat  s?x:y mux
endmodule
"""
ST_NOR = """\
// EXERCISE: build a NOR gate. Keep ports a, b, y.
module nor_gate(input a, b, output y);
    assign y = 1'b0;   // TODO
endmodule
"""
EX_STRUCT = """\
// Structural: full adder from two half adders + OR gate.
module half_adder(input a, b, output s, c);
    assign s = a ^ b;  assign c = a & b;
endmodule

module full_adder(input a, b, cin, output sum, cout);
    wire s1, c1, c2;
    half_adder HA1 (.a(a), .b(b), .s(s1), .c(c1));
    half_adder HA2 (.a(s1), .b(cin), .s(sum), .c(c2));
    or OR1 (cout, c1, c2);      // gate primitive: first port = output
endmodule
"""
ST_FA = """\
// EXERCISE: full adder.  sum = a^b^cin ; cout = majority(a,b,cin)
module full_adder(input a, b, cin, output sum, cout);
    assign sum = 1'b0;   // TODO
    assign cout = 1'b0;  // TODO
endmodule
"""
EX_NANDXOR = """\
// XOR from four NANDs -- "NAND is universal".
module xor_nand(input a, b, output y);
    wire n1, n2, n3;
    nand N1 (n1, a, b);
    nand N2 (n2, a, n1);
    nand N3 (n3, b, n1);
    nand N4 (y, n2, n3);
endmodule
"""
ST_NANDXOR = """\
// EXERCISE: XOR from ONLY nand primitives (four of them):
// n1=nand(a,b); n2=nand(a,n1); n3=nand(b,n1); y=nand(n2,n3)
module xor_nand(input a, b, output y);
    wire n1, n2, n3;
    assign y = 1'b0;   // TODO
endmodule
"""
EX_MUX = """\
module mux2to1(input a, b, sel, output y);
    assign y = sel ? b : a;      // also: (~sel & a) | (sel & b)
endmodule
"""
ST_MUX = """\
// EXERCISE: 2-to-1 mux. Ports in this order: a, b, sel, y.
module mux2to1(input a, b, sel, output y);
    assign y = 1'b0;   // TODO: y = b when sel=1 else a
endmodule
"""
EX_DEC_CASE = """\
// Behavioral decoder (built-in Truth Table understands always @(*)+case).
module dec2to4(input [1:0] sel, output reg [3:0] y);
    always @(*) case (sel)
        2'd0: y = 4'b0001;
        2'd1: y = 4'b0010;
        2'd2: y = 4'b0100;
        default: y = 4'b1000;
    endcase
endmodule
"""
EX_DEC_ASSIGN = """\
module dec2to4(input a, b, output y0, y1, y2, y3);
    assign y0 = ~a & ~b;  assign y1 = ~a & b;
    assign y2 =  a & ~b;  assign y3 =  a & b;
endmodule
"""
ST_DEC = """\
// EXERCISE: 2-to-4 decoder (one-hot). Ports: a, b, y0..y3.
module dec2to4(input a, b, output y0, y1, y2, y3);
    assign y0 = 1'b0;  // TODO
    assign y1 = 1'b0;  // TODO
    assign y2 = 1'b0;  // TODO
    assign y3 = 1'b0;  // TODO
endmodule
"""
EX_SEG = """\
// BCD -> seven segment (a..g active high). K-map each segment!
module seg7(input d3, d2, d1, d0,
            output seg_a, seg_b, seg_c, seg_d, seg_e, seg_f, seg_g);
    reg [6:0] seg;
    always @(*) case ({d3, d2, d1, d0})
        4'b0000: seg = 7'b1111110;  4'b0001: seg = 7'b0110000;
        4'b0010: seg = 7'b1101101;  4'b0011: seg = 7'b1111001;
        4'b0100: seg = 7'b0110011;  4'b0101: seg = 7'b1011011;
        4'b0110: seg = 7'b1011111;  4'b0111: seg = 7'b1110000;
        4'b1000: seg = 7'b1111111;  4'b1001: seg = 7'b1111011;
        default: seg = 7'b0000000;
    endcase
    assign {seg_a, seg_b, seg_c, seg_d, seg_e, seg_f, seg_g} = seg;
endmodule
"""
ST_SEG = """\
// EXERCISE: seven-segment decoder, dataflow. Patterns (a b c d e f g):
// 0:1111110 1:0110000 2:1101101 3:1111001 4:0110011 5:1011011
// 6:1011111 7:1110000 8:1111111 9:1111011  A-F: blank
module seg7(input d3, d2, d1, d0,
            output seg_a, seg_b, seg_c, seg_d, seg_e, seg_f, seg_g);
    assign seg_a = 1'b0;  // TODO
    assign seg_b = 1'b0;  assign seg_c = 1'b0;  assign seg_d = 1'b0;
    assign seg_e = 1'b0;  assign seg_f = 1'b0;  assign seg_g = 1'b0;
endmodule
"""
EX_COMP = """\
// Equality is XNOR; magnitude compares MSB first.
module comp2(input a1, a0, b1, b0, output gt);
    wire e1;  assign e1 = ~(a1 ^ b1);
    assign gt = (a1 & ~b1) | (e1 & a0 & ~b0);
endmodule
"""
ST_COMP = """\
// EXERCISE: 2-bit greater-than. Ports: a1 a0 b1 b0 -> gt.
module comp2(input a1, a0, b1, b0, output gt);
    assign gt = 1'b0;   // TODO
endmodule
"""
EX_ENC = """\
// 4-to-2 priority encoder (r3 highest): index of highest set bit.
module prio_enc(input r3, r2, r1, r0, output v, y1, y0);
    assign v  = r3 | r2 | r1 | r0;
    assign y1 = r3 | r2;
    assign y0 = r3 | (r2 & ~r1);
endmodule
"""
ST_ENC = """\
// EXERCISE: 4-to-2 priority encoder (r3 highest priority).
module prio_enc(input r3, r2, r1, r0, output v, y1, y0);
    assign v = 1'b0;  assign y1 = 1'b0;  assign y0 = 1'b0;   // TODO
endmodule
"""
EX_ADDER4 = """\
// 4-bit ripple-carry adder.
module adder4(input [3:0] a, b, input cin, output [3:0] sum, output cout);
    wire [4:0] c;  assign c[0] = cin;
    full_adder FA0 (.a(a[0]), .b(b[0]), .cin(c[0]), .sum(sum[0]), .cout(c[1]));
    full_adder FA1 (.a(a[1]), .b(b[1]), .cin(c[1]), .sum(sum[1]), .cout(c[2]));
    full_adder FA2 (.a(a[2]), .b(b[2]), .cin(c[2]), .sum(sum[2]), .cout(c[3]));
    full_adder FA3 (.a(a[3]), .b(b[3]), .cin(c[3]), .sum(sum[3]), .cout(c[4]));
    assign cout = c[4];
endmodule
module full_adder(input a, b, cin, output sum, cout);
    assign sum = a ^ b ^ cin;  assign cout = (a&b) | (cin&(a^b));
endmodule
"""
EX_GLITCH = """\
// HAZARDS: every assign has an inertial #delay. Run -> the glitch engine
// schedules each net update; the Waveform shows cout briefly DROPPING
// when b falls (the p&cin path wakes up late). Wave starts at x: nothing
// computed at t=0 yet (why resets matter).
module fa(input a, b, cin, output sum, cout);
    wire p, g;
    assign #1 p   = a ^ b;
    assign #1 g   = a & b;
    assign #1 sum = p ^ cin;
    assign #2 cout = g | (p & cin);
endmodule
module tb;
    reg a = 1, b = 1, cin = 1;
    wire sum, cout;
    fa uut (.a(a), .b(b), .cin(cin), .sum(sum), .cout(cout));
    initial begin
        #30 b = 0;      // cout must STAY 1 ... but glitches first!
        #40 $display("cout=%b", cout);
        $finish;
    end
endmodule
"""
EX_MUX_ALWAYS = """\
module mux2to1(input a, b, sel, output reg y);
    always @(*) if (sel) y = b; else y = a;   // blocking = in comb logic
endmodule
"""
EX_DFF = """\
// The D flip-flop. Run it: q shows 'x' until the first clock edge
// writes it -- that is why resets matter.
module dff(input clk, d, output reg q);
    always @(posedge clk) q <= d;   // non-blocking <= in clocked blocks
endmodule
"""
EX_DFF_TB = """\
`timescale 1ns/1ps
module tb;
    reg clk = 0, d = 0;  wire q;
    dff uut (.clk(clk), .d(d), .q(q));
    always #5 clk = ~clk;
    initial begin
        #2 d=1; #10 d=0; #10 d=1; #10 d=0; #10 $finish;
    end
endmodule
"""
EX_COUNTER = """\
module counter #(parameter WIDTH = 4)(
    input clk, rst, output reg [WIDTH-1:0] count);
    always @(posedge clk) begin
        if (rst) count <= {WIDTH{1'b0}};
        else     count <= count + 1'b1;    // wraps 15 -> 0
    end
endmodule
"""
EX_COUNTER_TB = """\
`timescale 1ns/1ps
module tb;
    reg clk = 0, rst = 1;  wire [3:0] count;
    counter #(.WIDTH(4)) uut (.clk(clk), .rst(rst), .count(count));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;  #100;
        $display("count = %0d", count);
        $finish;
    end
endmodule
"""
EX_SHIFT = """\
module shiftreg(input clk, d, output reg [3:0] q);
    always @(posedge clk) q <= {q[2:0], d};   // shift left, d in at LSB
endmodule
"""
EX_SHIFT_TB = """\
`timescale 1ns/1ps
module tb;
    reg clk = 0, d = 0;  wire [3:0] q;
    shiftreg uut (.clk(clk), .d(d), .q(q));
    always #5 clk = ~clk;
    initial begin
        #2 d=1; #10 d=0; #10 d=1; #10 d=1; #10 d=0;
        #10 $display("q = %b", q);
        $finish;
    end
endmodule
"""
EX_VHDL_AND = """\
library ieee;
use ieee.std_logic_1164.all;
entity and_gate is
    port (a, b : in std_logic; y : out std_logic);
end entity;
architecture rtl of and_gate is
begin
    y <= a and b;    -- concurrent assignment
end architecture;
"""
EX_VHDL_DFF = """\
library ieee;
use ieee.std_logic_1164.all;
entity dff is
    port (clk, d : in std_logic; q : out std_logic);
end entity;
architecture rtl of dff is
begin
    process (clk) begin
        if rising_edge(clk) then q <= d; end if;
    end process;
end architecture;
"""
EX_FSM_V = """\
// 3-state Moore FSM. Every Run prints [coverage]: which case branches
// (states) your stimulus visited.
module fsm(input clk, rst, go, output reg done);
    localparam IDLE = 2'd0, RUN = 2'd1, DONE = 2'd2;
    reg [1:0] state, next;
    always @(posedge clk or posedge rst)
        if (rst) state <= IDLE; else state <= next;
    always @(*) begin
        next = state;  done = 1'b0;
        case (state)
            IDLE: if (go) next = RUN;
            RUN : next = DONE;
            DONE: begin done = 1'b1; next = IDLE; end
            default: next = IDLE;
        endcase
    end
endmodule
"""
EX_FSM_V_TB = """\
`timescale 1ns/1ps
module tb;
    reg clk = 0, rst = 1, go = 0;  wire done;
    fsm uut (.clk(clk), .rst(rst), .go(go), .done(done));
    always #5 clk = ~clk;
    initial begin
        #7 rst = 0;  #10 go = 1;  #10 go = 0;  #60;
        $display("done");
        $finish;
    end
endmodule
"""
EX_FSM_COV_TB = """\
`timescale 1ns/1ps
-- EXERCISE: pulse `go` so the run covers IDLE, RUN and DONE (3 of 4
-- case branches). Coverage is printed after Run and auto-grades this.
module tb;
    reg clk = 0, rst = 1, go = 0;  wire done;
    fsm uut (.clk(clk), .rst(rst), .go(go), .done(done));
    always #5 clk = ~clk;
    initial begin
        #7 rst = 0;
        // TODO: drive go so the FSM walks to RUN and DONE...
        #100 $finish;
    end
endmodule
"""
EX_FSM_VHDL = """\
library ieee;
use ieee.std_logic_1164.all;
entity fsm is
    port (clk, rst, go : in std_logic; done : out std_logic);
end entity;
architecture rtl of fsm is
    type state_t is (IDLE, RUN, DONE);
    signal state, next_state : state_t;
begin
    process (clk, rst) begin
        if rst = '1' then state <= IDLE;
        elsif rising_edge(clk) then state <= next_state;
        end if;
    end process;
    process (state, go) begin
        next_state <= state;  done <= '0';
        case state is
            when IDLE => if go = '1' then next_state <= RUN; end if;
            when RUN  => next_state <= DONE;
            when DONE => done <= '1'; next_state <= IDLE;
        end case;
    end process;
end architecture;
"""
EX_TB_MAJ = """\
// SELF-CHECKING testbench: count errors, print verdict.
module majority3(input a, b, c, output y);
    assign y = (a & b) | (a & c) | (b & c);
endmodule
module tb;
    reg a = 0, b = 0, c = 0;  wire y;  integer errors = 0;
    majority3 uut (.a(a), .b(b), .c(c), .y(y));
    initial begin
        a=0; b=0; c=0; #1; if (y !== 1'b0) errors = errors + 1;
        a=0; b=0; c=1; #1; if (y !== 1'b0) errors = errors + 1;
        a=0; b=1; c=0; #1; if (y !== 1'b0) errors = errors + 1;
        a=0; b=1; c=1; #1; if (y !== 1'b1) errors = errors + 1;
        a=1; b=0; c=0; #1; if (y !== 1'b0) errors = errors + 1;
        a=1; b=0; c=1; #1; if (y !== 1'b1) errors = errors + 1;
        a=1; b=1; c=0; #1; if (y !== 1'b1) errors = errors + 1;
        a=1; b=1; c=1; #1; if (y !== 1'b1) errors = errors + 1;
        $display("errors = %0d", errors);
        if (errors == 0) $display("ALL PASS");
        $finish;
    end
endmodule
"""
ST_TB_MUX = """\
// EXERCISE: finish this testbench. Console must show exactly:
//   a=0 b=0 sel=0 -> y=0
//   a=0 b=1 sel=0 -> y=0
//   a=1 b=0 sel=0 -> y=0
//   a=1 b=1 sel=1 -> y=1
// Pattern: drive, wait a delta (#1), then $display. Press Run!
module mux2to1(input a, b, sel, output y);
    assign y = sel ? b : a;
endmodule
module tb;
    reg a = 0, b = 0, sel = 0;  wire y;
    mux2to1 uut (.a(a), .b(b), .sel(sel), .y(y));
    initial begin
        // TODO: four stimulus+display pairs
        $finish;
    end
endmodule
"""
EX_WAVE_TOGGLE = """\
// Write TB stimulus so q transitions 0->1->0->1. The app compares the
// SEQUENCE of value changes on q (robust to your exact delays).
module toggler(input clk, rst, output reg q);
    always @(posedge clk or posedge rst)
        if (rst) q <= 1'b0; else q <= ~q;
endmodule
"""
ST_WAVE_TOGGLE = """\
`timescale 1ns/1ps
module tb;
    reg clk = 0, rst = 1;  wire q;
    toggler uut (.clk(clk), .rst(rst), .q(q));
    always #5 clk = ~clk;
    initial begin
        // TODO: reset one cycle, release, let exactly 3 rising edges pass,
        // then $finish.
        $finish;
    end
endmodule
"""
EX_SV_LOGIC = """\
// SystemVerilog: `logic` replaces wire/reg (needs Icarus -g2012, added
// automatically). 4-state: 0, 1, x, z.
module sv_logic(input logic a, b, output logic y);
    logic tmp;
    always_comb tmp = a & b;    // intent-checked combinational
    assign y = tmp | a;
endmodule
"""
EX_SV_FF = """\
// always_ff may ONLY describe flops; always_comb ONLY combinational --
// tools error on violations, so the classic = / <= bug dies at compile.
module sv_ff(input logic clk, rst, d, output logic q);
    always_ff @(posedge clk or posedge rst)
        if (rst) q <= '0; else q <= d;
endmodule
"""
EX_SV_ENUM = """\
typedef enum logic [1:0] {IDLE, RUN, DONE} state_t;
module fsm_sv(input logic clk, rst, go, output logic done);
    state_t state, next;
    always_ff @(posedge clk or posedge rst)
        if (rst) state <= IDLE; else state <= next;
    always_comb begin
        next = state;  done = 1'b0;
        unique case (state)       // tool proves full/parallel branching
            IDLE: if (go) next = RUN;
            RUN : next = DONE;
            DONE: begin done = 1'b1; next = IDLE; end
        endcase
    end
endmodule
"""
EX_RAM = """\
// Inferred RAM (arrays + for). Memory tab shows `mem` after Run.
module ram #(parameter AW = 4, DW = 8)(
    input clk, we, input [AW-1:0] addr, input [DW-1:0] din,
    output [DW-1:0] dout);
    reg [DW-1:0] mem [0:(1<<AW)-1];
    integer i;
    initial for (i = 0; i < (1<<AW); i = i + 1) mem[i] = i * 3;
    always @(posedge clk) if (we) mem[addr] <= din;   // sync write = RAM
    assign dout = mem[addr];                          // async read
endmodule
module tb;
    reg clk = 0, we = 0;  reg [3:0] addr = 0;  reg [7:0] din = 0;
    wire [7:0] dout;
    ram uut (.clk(clk), .we(we), .addr(addr), .din(din), .dout(dout));
    always #5 clk = ~clk;
    initial begin
        #12 we = 1; addr = 5; din = 8'hAB;
        #10 we = 0; #1 $display("q=%h", dout);
        #10 addr = 2; #1 $display("q2=%h", dout);   // 2*3=6
        $finish;
    end
endmodule
"""
EX_FIFO = """\
// Synchronous FIFO: circular buffer + pointers + count.
module sync_fifo #(parameter DEPTH = 8, DW = 8)(
    input clk, rst, wr, rd, input [DW-1:0] din,
    output [DW-1:0] dout, output full, empty);
    reg [DW-1:0] mem [0:DEPTH-1];
    reg [3:0] wp, rp, count;
    assign full = (count == DEPTH);  assign empty = (count == 0);
    assign dout = mem[rp];
    always @(posedge clk) begin
        if (rst) begin wp <= 0; rp <= 0; count <= 0; end
        else begin
            if (wr && !full) begin
                mem[wp] <= din;
                wp <= (wp == DEPTH-1) ? 4'd0 : wp + 1'b1;
            end
            if (rd && !empty)
                rp <= (rp == DEPTH-1) ? 4'd0 : rp + 1'b1;
            case ({wr && !full, rd && !empty})
                2'b10: count <= count + 1'b1;
                2'b01: count <= count - 1'b1;
                default: ;
            endcase
        end
    end
endmodule
module tb;
    reg clk = 0, rst = 1, wr = 0, rd = 0;  reg [7:0] din = 0;
    wire [7:0] dout;  wire full, empty;
    sync_fifo uut (.clk(clk), .rst(rst), .wr(wr), .rd(rd), .din(din),
                   .dout(dout), .full(full), .empty(empty));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;
        #10 wr = 1; din = 8'h11;
        #10 din = 8'h22;  #10 din = 8'h33; wr = 0;
        #10 rd = 1; #10 $display("d=%h", dout);
        #10 $display("d=%h", dout);  #10 $display("empty=%b", empty);
        $finish;
    end
endmodule
"""
EX_CDC = """\
// CDC: two-flop synchronizer. First flop may go metastable; second
// gives it a cycle. Run: two unrelated clocks, no tools needed.
module cdc(input clk_a, clk_b, d_a, output reg q_sync);
    reg meta, q_b1;
    always @(posedge clk_b) begin
        meta <= d_a;  q_b1 <= meta;  q_sync <= q_b1;
    end
endmodule
module tb;
    reg clk_a = 0, clk_b = 0, d_a = 0;  wire q_sync;
    cdc uut (.clk_a(clk_a), .clk_b(clk_b), .d_a(d_a), .q_sync(q_sync));
    always #4 clk_a = ~clk_a;   // 8 ns
    always #5 clk_b = ~clk_b;   // 10 ns
    initial begin
        #10 d_a = 1;  #20 d_a = 0;  #20 d_a = 1;
        #22 $display("s=%b", q_sync);   // still 0: crossing takes ~3 edges
        #10 $display("s=%b", q_sync);   // now 1
        #30 $display("s=%b", q_sync);   #10 $display("s=%b", q_sync);
        $finish;
    end
endmodule
"""
BUG1 = """\
// BUG HUNT: this "swap" doesn't swap. Console must show a=2 b=1 then
// a=1 b=2. Classic clocked-block mistake -- find it, fix it, Run.
module swap(input clk, rst, input [7:0] ain, bin,
            output reg [7:0] a, b);
    always @(posedge clk) begin
        if (rst) begin a <= ain; b <= bin; end
        else begin
            a = b;    // <-- something is wrong here...
            b = a;
        end
    end
endmodule
module tb;
    reg clk = 0, rst = 1;  reg [7:0] ain = 8'd1, bin = 8'd2;
    wire [7:0] a, b;
    swap uut (.clk(clk), .rst(rst), .ain(ain), .bin(bin), .a(a), .b(b));
    always #5 clk = ~clk;
    initial begin
        #8 rst = 0;  #12 $display("a=%0d b=%0d", a, b);
        #10 $display("a=%0d b=%0d", a, b);
        $finish;
    end
endmodule
"""
BUG2 = """\
// BUG HUNT: y must be 1 ONLY when sel==0 (table "10") but Check fails
// on row 1 -- a latch sneaked into the case.
module latchy(input sel, output reg y);
    always @(*) case (sel)
        1'd0: y = 1'b1;
        // ...missing something?
    endcase
endmodule
"""
BUG3 = """\
// BUG HUNT: reset never works (c must be 0 then 3). Two always blocks
// drive the same reg -- a simulation race.
module race(input clk, rst, output reg [7:0] cnt);
    always @(posedge clk) if (rst) cnt <= 8'd0;
    always @(posedge clk) cnt <= cnt + 8'd1;
endmodule
module tb;
    reg clk = 0, rst = 1;  wire [7:0] cnt;
    race uut (.clk(clk), .rst(rst), .cnt(cnt));
    always #5 clk = ~clk;
    initial begin
        #8  $display("c=%0d", cnt);   // rst still high
        #2  rst = 0;
        #30 $display("c=%0d", cnt);   // 3 clocks later
        $finish;
    end
endmodule
"""
BUG4 = """\
// BUG HUNT: intended y = (a & b) | c -- one truth-table row is wrong.
module precedence(input a, b, c, output y);
    assign y = a & b ^ c;    // precedence surprise!
endmodule
"""
EX_ALU = """\
// 4-bit ALU. The lesson's Python golden model checks EVERY input
// combination against this hardware (press Check).
module alu4(input [3:0] a, b, input [1:0] op, output reg [3:0] y);
    always @(*) case (op)
        2'd0: y = a + b;   2'd1: y = a - b;
        2'd2: y = a & b;   default: y = a | b;
    endcase
endmodule
"""
EX_GRAY = """\
// Registered binary->Gray. Golden model pulses clk once per vector
// (cycles=1) and compares q.
module gray_reg(input clk, input [3:0] d, output reg [3:0] q);
    always @(posedge clk) q <= d ^ (d >> 1);
endmodule
module tb;
    reg clk = 0;  reg [3:0] d = 4'h8;  wire [3:0] q;
    gray_reg uut (.clk(clk), .d(d), .q(q));
    always #5 clk = ~clk;
    initial begin #32 $display("q=%h", q); $finish; end
endmodule
"""
EX_ARB = """\
// Arbiter + IMMEDIATE ASSERTIONS. grant only when its request is high
// AND busy low. Run the starter: assertions catch the seeded bug in the
// console. Fix the DUT until Check reports 0 failures.
module arb(input req0, req1, busy, output reg g0, g1);
    always @(*) begin
        g0 = req0 & busy;               // BUG: should be req0 & ~busy
        g1 = req1 & ~busy & ~req0;
    end
endmodule
module tb;
    reg req0 = 0, req1 = 0, busy = 0;  wire g0, g1;
    arb uut (.req0(req0), .req1(req1), .busy(busy), .g0(g0), .g1(g1));
    integer k;
    initial begin
        for (k = 0; k < 40; k = k + 1) begin
            req0 = $prob(50); req1 = $prob(50); busy = $prob(30);
            #1;
            assert (!(g0 && busy)) else $error("g0 granted while busy");
            #1;
        end
        $finish;
    end
endmodule
"""
EX_HANDSHAKE = """\
// Valid/ready handshake. PROPERTY: whenever valid rises, ready must
// assert within 50 ns (5 clocks). The starter's ready is far too slow.
module handshake(input clk, valid, output reg ready);
    reg [3:0] n;
    always @(posedge clk) begin
        if (valid && n == 0) n <= 10;          // latency -- try <= 4
        else if (n > 0) begin
            n <= n - 1;  ready <= (n == 1);
        end else ready <= 0;
    end
endmodule
module tb;
    reg clk = 0, valid = 0;  wire ready;
    handshake uut (.clk(clk), .valid(valid), .ready(ready));
    always #5 clk = ~clk;
    integer k;
    initial begin
        #12;
        for (k = 0; k < 4; k = k + 1) begin
            valid = 1; #10; valid = 0; #40;
        end
        $finish;
    end
endmodule
"""
EX_FIFO_PLAN = """\
// FIFO + TEST PLAN. Design is finished; YOUR job is verification:
// write the four stimulus scenarios (fill->full, drain->empty,
// same-cycle rd+wr, write-while-full) until the checklist is green.
module sync_fifo #(parameter DEPTH = 4)(
    input clk, rst, wr, rd, input [7:0] din,
    output reg [7:0] dout, output full, empty);
    reg [7:0] mem [0:DEPTH-1];
    reg [1:0] wp, rp, count;
    assign full = (count == DEPTH);  assign empty = (count == 0);
    always @(posedge clk) begin
        if (rst) begin wp <= 0; rp <= 0; count <= 0; end
        else begin
            if (wr && !full)  begin mem[wp] <= din; wp <= wp + 1; end
            if (rd && !empty) begin dout <= mem[rp]; rp <= rp + 1; end
            case ({wr && !full, rd && !empty})
                2'b10: count <= count + 1;
                2'b01: count <= count - 1;
                default: ;
            endcase
        end
    end
endmodule
module tb;
    reg clk = 0, rst = 1, wr = 0, rd = 0;  reg [7:0] din = 8'h11;
    wire [7:0] dout;  wire full, empty;
    sync_fifo uut (.clk(clk), .rst(rst), .wr(wr), .rd(rd), .din(din),
                   .dout(dout), .full(full), .empty(empty));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;
        // scenario 1: fill until full
        // scenario 2: drain back to empty
        // scenario 3: read and write in the same cycle
        // scenario 4: attempt a write while full
        #200 $finish;
    end
endmodule
"""
EX_PIPELINE = """\
// 4-stage laundry pipeline. A "prewash" item (bit 3 of rom word) stalls
// the front end STALL_CYCLES cycles -- bubbles visible in Pipeline tab.
module laundry #(parameter STALL_CYCLES = 2)(
    input clk, rst, output stall, output reg [4:0] stages);
    reg [3:0] rom [0:3];
    integer i;
    initial begin
        rom[0] = 4'b0_01;  rom[1] = 4'b1_10;   // needs prewash
        rom[2] = 4'b0_11;  rom[3] = 4'b0_01;
    end
    reg [1:0] pc;  reg [3:0] s0, s1, s2, s3;  reg [1:0] hcnt;
    wire need = rom[pc][3];
    wire load_en = (hcnt == 0);
    assign stall = (need && load_en) || (hcnt != 0);
    always @(posedge clk) begin
        if (rst) begin
            pc <= 0; s0 <= 0; s1 <= 0; s2 <= 0; s3 <= 0; hcnt <= 0;
        end else begin
            s3 <= s2; s2 <= s1; s1 <= s0;
            if (hcnt != 0) begin s0 <= 0; hcnt <= hcnt - 1'b1; end
            else if (need) begin s0 <= 0; hcnt <= STALL_CYCLES[1:0]; end
            else begin
                s0 <= rom[pc];
                pc <= (pc == 2'd3) ? 2'd0 : pc + 1'b1;
            end
        end
    end
    always @(*) stages = {s3 != 0, s2 != 0, s1 != 0, s0 != 0,
                          (s0 != 0) || (need && load_en)};
endmodule
module tb;
    reg clk = 0, rst = 1;  wire stall;  wire [4:0] stages;
    laundry uut (.clk(clk), .rst(rst), .stall(stall), .stages(stages));
    always #5 clk = ~clk;
    integer k, ns = 0;
    initial begin
        #12 rst = 0;
        for (k = 0; k < 35; k = k + 1) begin
            #10;  if (stall) ns = ns + 1;
        end
        $display("stalls=%0d", ns);
        $finish;
    end
endmodule
"""
EX_LFSR = """\
// 8-bit maximal LFSR: taps 8,6,5,4. Wrong taps -> period=0.
module lfsr8(input clk, rst, output reg [7:0] q);
    wire fb;  assign fb = q[7] ^ q[5] ^ q[4] ^ q[3];
    always @(posedge clk) begin
        if (rst) q <= 8'b0000_0001;
        else     q <= {q[6:0], fb};
    end
endmodule
module tb;
    reg clk = 0, rst = 1;  wire [7:0] q;
    lfsr8 uut (.clk(clk), .rst(rst), .q(q));
    always #5 clk = ~clk;
    integer i;  reg ok;
    initial begin
        #12 rst = 0;
        for (i = 0; i < 255; i = i + 1) #10;
        ok = (q == 8'b0000_0001);  #10;
        $display("period=%0d", ok ? 1 : 0);
        $finish;
    end
endmodule
"""
EX_CRC = """\
// Serial CRC-8, poly 0x07. Feeding message+CRC through a second
// instance must leave its register at ZERO -- self-checking!
module crc8(input clk, rst, d, output reg [7:0] crc);
    wire fb;  assign fb = d ^ crc[7];
    always @(posedge clk)
        if (rst) crc <= 8'h00;
        else     crc <= {crc[6:0], 1'b0} ^ (fb ? 8'h07 : 8'h00);
endmodule
module tb;
    reg clk = 0, rst = 1, d1 = 0, d2 = 0;  wire [7:0] c1, c2;
    crc8 u1 (.clk(clk), .rst(rst), .d(d1), .crc(c1));
    crc8 u2 (.clk(clk), .rst(rst), .d(d2), .crc(c2));
    always #5 clk = ~clk;
    integer i;
    initial begin
        #12 rst = 0;
        for (i = 7; i >= 0; i = i - 1) begin d1 = (8'h31 >> i) & 1; #10; end
        d1 = 0;
        for (i = 7; i >= 0; i = i - 1) begin d2 = (8'h31 >> i) & 1; #10; end
        for (i = 7; i >= 0; i = i - 1) begin d2 = (c1 >> i) & 1; #10; end
        d2 = 0;
        $display("crc=%h", c1);
        $display("ok=%0d", (c2 == 0) ? 1 : 0);
        $finish;
    end
endmodule
"""
EX_MUL = """\
// Bit-serial 4x4 multiply: shift-and-add over 4 cycles. 13*11 = 143.
module serialmul(input clk, rst, input [3:0] a, b, output reg [7:0] p);
    reg [7:0] mc;  reg [2:0] count;
    always @(posedge clk) begin
        if (rst) begin p <= 0; mc <= {4'b0, a}; count <= 0; end
        else if (count != 3'd4) begin
            if (b[count]) p <= p + mc;    // <-- the money line
            mc <= mc << 1;  count <= count + 1'b1;
        end
    end
endmodule
module tb;
    reg clk = 0, rst = 1;  reg [3:0] a = 4'd13, b = 4'd11;
    wire [7:0] p;
    serialmul uut (.clk(clk), .rst(rst), .a(a), .b(b), .p(p));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;  #60;
        $display("p=%0d", p);
        $finish;
    end
endmodule
"""
EX_AFIFO = """\
// Dual-clock FIFO with Gray-coded pointers (Cummings style). Two
// unrelated clocks; bytes cross in order; empty=1 after the drain.
module async_fifo #(parameter AW = 2, DW = 8)(
    input wr_clk, rd_clk, wrst, rrst, wr, rd, input [DW-1:0] wdata,
    output reg [DW-1:0] rdata, output wfull, rempty);
    reg [DW-1:0] mem [0:(1<<AW)-1];
    reg [AW:0] wbin, rbin, wptr, rptr, wq1, wq2, rq1, rq2;
    wire [AW:0] wgraynext, rgraynext, wbinnext, rbinnext;
    assign wbinnext  = wbin + (wr && !wfull);
    assign rbinnext  = rbin + (rd && !rempty);
    assign wgraynext = wbinnext ^ (wbinnext >> 1);
    assign rgraynext = rbinnext ^ (rbinnext >> 1);
    assign wfull  = (wgraynext == {~rq2[AW:AW-1], rq2[AW-2:0]});
    assign rempty = (rgraynext == wq2);
    always @(posedge wr_clk) begin
        if (wrst) begin wbin <= 0; wptr <= 0; wq1 <= 0; wq2 <= 0; end
        else begin
            wbin <= wbinnext; wptr <= wgraynext;
            wq1 <= rptr; wq2 <= wq1;
            if (wr && !wfull) mem[wbin[AW-1:0]] <= wdata;
        end
    end
    always @(posedge rd_clk) begin
        if (rrst) begin
            rbin <= 0; rptr <= 0; rq1 <= 0; rq2 <= 0; rdata <= 0;
        end else begin
            rbin <= rbinnext; rptr <= rgraynext;
            rq1 <= wptr; rq2 <= rq1;
            if (rd && !rempty) rdata <= mem[rbin[AW-1:0]];
        end
    end
endmodule
module tb;
    reg wr_clk = 0, rd_clk = 0, wrst = 1, rrst = 1, wr = 0, rd = 0;
    reg [7:0] wdata = 0;  wire [7:0] rdata;  wire wfull, rempty;
    async_fifo uut (.wr_clk(wr_clk), .rd_clk(rd_clk), .wrst(wrst),
        .rrst(rrst), .wr(wr), .rd(rd), .wdata(wdata), .rdata(rdata),
        .wfull(wfull), .rempty(rempty));
    always #4 wr_clk = ~wr_clk;   // 8 ns
    always #5 rd_clk = ~rd_clk;   // 10 ns
    initial begin
        #10 wrst = 0;  #10 rrst = 0;
        wr = 1; wdata = 8'h11;
        #10 wdata = 8'h22;  #10 wdata = 8'h33;  #10 wr = 0;
        #40 rd = 1;
        #20 $display("d=%h", rdata);  #20 $display("d=%h", rdata);
        #20 $display("d=%h", rdata);  rd = 0;
        #20 $display("empty=%b", rempty);
        $finish;
    end
endmodule
"""

# ---- capstone solutions ---------------------------------------------------
UART_S1 = """\
// UART TX stage 1: frame-tick counter (one clock = one bit).
module uart_tx(input clk, rst, output reg [3:0] tick);
    always @(posedge clk) begin
        if (rst) tick <= 0;
        else if (tick == 4'd9) tick <= 0;
        else tick <= tick + 1'b1;
    end
endmodule
module tb;
    reg clk = 0, rst = 1;  wire [3:0] tick;
    uart_tx uut (.clk(clk), .rst(rst), .tick(tick));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;  #35 $display("tick=%0d", tick);
        #10 $display("tick=%0d", tick);  #10 $display("tick=%0d", tick);
        #40 $display("tick=%0d", tick);
        $finish;
    end
endmodule
"""
UART_S2 = """\
// UART TX stage 2: serialize constant 8'hA6 (LSB first, framed).
module uart_tx(input clk, rst, output reg tx);
    reg [3:0] n;  reg [7:0] sh;
    always @(posedge clk) begin
        if (rst) begin n <= 0; sh <= 8'hA6; tx <= 1'b1; end
        else case (n)
            4'd0: begin tx <= 1'b0; sh <= 8'hA6; n <= 1; end
            4'd9: begin tx <= 1'b1; n <= 0; end
            default: begin
                tx <= sh[0];  sh <= {1'b0, sh[7:1]};  n <= n + 1'b1;
            end
        endcase
    end
endmodule
module tb;
    reg clk = 0, rst = 1;  wire tx;
    uart_tx uut (.clk(clk), .rst(rst), .tx(tx));
    always #5 clk = ~clk;
    integer k;
    initial begin
        #12 rst = 0;
        for (k = 0; k < 11; k = k + 1) begin
            #10;  $display("tx=%b", tx);
        end
        $finish;
    end
endmodule
"""
UART_S3 = """\
// UART TX stage 3: send strobe + busy; TB acts as a software receiver.
module uart_tx(input clk, rst, send, input [7:0] din,
               output reg tx, output busy);
    reg [3:0] n;  reg [7:0] sh;  reg run;
    assign busy = run;
    always @(posedge clk) begin
        if (rst) begin n<=0; sh<=0; run<=0; tx<=1'b1; end
        else if (!run && send) begin
            sh <= din; n <= 0; run <= 1'b1; tx <= 1'b0;   // start bit
        end else if (run) begin
            if (n == 4'd9) begin tx <= 1'b1; run <= 1'b0; n <= 0; end
            else if (n == 4'd8) begin tx <= 1'b1; n <= 4'd9; end
            else begin
                tx <= sh[0];  sh <= {1'b0, sh[7:1]};  n <= n + 1'b1;
            end
        end
    end
endmodule
module tb;
    reg clk = 0, rst = 1, send = 0;  reg [7:0] din = 8'h3C;
    wire tx, busy;
    uart_tx uut (.clk(clk), .rst(rst), .send(send), .din(din),
                 .tx(tx), .busy(busy));
    always #5 clk = ~clk;
    integer k;  reg [7:0] rxb;
    initial begin
        #12 rst = 0;  #10 send = 1;  #10 send = 0;  #8;
        for (k = 0; k < 8; k = k + 1) begin
            rxb[k] = tx;  #10;
        end
        $display("rx=%h", rxb);
        $display("busy=%b", busy);
        #20 $display("idle=%b", tx);
        $finish;
    end
endmodule
"""
UART_S4 = """\
// UART RX stage 4: detect start, shift 8 bits LSB-first, pulse done.
module uart_rx(input clk, rst, rx, output reg [7:0] dout, output reg done);
    reg [3:0] n;  reg run;
    always @(posedge clk) begin
        if (rst) begin run<=0; n<=0; done<=0; dout<=0; end
        else begin
            done <= 1'b0;
            if (!run) begin
                if (rx == 1'b0) begin run <= 1'b1; n <= 0; dout <= 0; end
            end else begin
                dout <= {rx, dout[7:1]};      // LSB first
                if (n == 4'd7) begin done <= 1'b1; run <= 1'b0; end
                else n <= n + 1'b1;
            end
        end
    end
endmodule
module tb;
    reg clk = 0, rst = 1, rx = 1;  wire [7:0] dout;  wire done;
    uart_rx uut (.clk(clk), .rst(rst), .rx(rx), .dout(dout), .done(done));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;
        #10 rx=0;  #10 rx=0;  #10 rx=1;  #10 rx=1;  #10 rx=0;
        #10 rx=1;  #10 rx=0;  #10 rx=0;  #10 rx=1;  #10 rx=1;
        #1  $display("dout=%h done=%b", dout, done);
        $finish;
    end
endmodule
"""
TRAF_S1 = """\
// TRAFFIC stage 1: loadable down-counter (the phase timer).
module timer #(parameter W = 4)(input clk, rst, load,
    input [W-1:0] din, output reg [W-1:0] cnt);
    always @(posedge clk) begin
        if (rst) cnt <= 0;
        else if (load) cnt <= din;
        else if (cnt != 0) cnt <= cnt - 1'b1;
    end
endmodule
module tb;
    reg clk = 0, rst = 1, load = 0;  reg [3:0] din = 0;  wire [3:0] cnt;
    timer uut (.clk(clk), .rst(rst), .load(load), .din(din), .cnt(cnt));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;  #10 load = 1; din = 4'd3;  #10 load = 0;
        #28 $display("t1 cnt=%0d", cnt);  #20 $display("t2 cnt=%0d", cnt);
        $finish;
    end
endmodule
"""
TRAF_S2 = """\
// TRAFFIC stage 2: timed G->Y->R Moore machine.
module traffic(input clk, rst, output reg [1:0] main);
    localparam G = 2'd2, Y = 2'd1, R = 2'd0;
    reg [3:0] t;
    always @(posedge clk) begin
        if (rst) begin main <= G; t <= 0; end
        else begin
            t <= t + 1'b1;
            case (main)
                G: if (t == 4'd5) begin main <= Y; t <= 0; end
                Y: if (t == 4'd2) begin main <= R; t <= 0; end
                R: if (t == 4'd5) begin main <= G; t <= 0; end
                default: main <= G;
            endcase
        end
    end
endmodule
module tb;
    reg clk = 0, rst = 1;  wire [1:0] main;
    traffic uut (.clk(clk), .rst(rst), .main(main));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;
        #28 $display("main=%0d", main);  #40 $display("main=%0d", main);
        #40 $display("main=%0d", main);  #50 $display("main=%0d", main);
        $finish;
    end
endmodule
"""
TRAF_S3 = """\
// TRAFFIC stage 3: pedestrian button cuts green short; walk during red.
module traffic(input clk, rst, btn, output reg [1:0] main, output reg walk);
    localparam G = 2'd2, Y = 2'd1, R = 2'd0;
    reg [3:0] t;  reg ped_req;
    always @(posedge clk) begin
        if (rst) begin main<=G; t<=0; ped_req<=0; walk<=0; end
        else begin
            if (btn) ped_req <= 1'b1;
            t <= t + 1'b1;  walk <= 1'b0;
            case (main)
                G: if ((t >= 4'd2 && ped_req) || t == 4'd5) begin
                       main <= Y; t <= 0; ped_req <= 1'b0; end
                Y: if (t == 4'd2) begin main <= R; t <= 0; end
                R: begin
                       walk <= 1'b1;
                       if (t == 4'd5) begin main <= G; t <= 0; end
                   end
                default: main <= G;
            endcase
        end
    end
endmodule
module tb;
    reg clk = 0, rst = 1, btn = 0;  wire [1:0] main;  wire walk;
    traffic uut (.clk(clk), .rst(rst), .btn(btn), .main(main), .walk(walk));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;  #18 $display("m=%0d w=%b", main, walk);
        #10 btn = 1;  #8 btn = 0;
        #12 $display("m=%0d w=%b", main, walk);
        #20 $display("m=%0d w=%b", main, walk);
        #70 $display("m=%0d w=%b", main, walk);
        $finish;
    end
endmodule
"""
TRAF_S4 = """\
// TRAFFIC stage 4: parameterized phases + one-cycle all-red clearance.
module traffic #(parameter GREEN = 6, YELLOW = 3, RED = 6)(
    input clk, rst, btn, output reg [1:0] main, output reg walk);
    localparam G = 2'd2, Y = 2'd1, R = 2'd0;
    reg [3:0] t;  reg ped_req;
    always @(posedge clk) begin
        if (rst) begin main<=G; t<=0; ped_req<=0; walk<=0; end
        else begin
            if (btn) ped_req <= 1'b1;
            t <= t + 1'b1;  walk <= 1'b0;
            case (main)
                G: if ((t >= GREEN-3 && ped_req) || t == GREEN-1) begin
                       main <= Y; t <= 0; ped_req <= 1'b0; end
                Y: if (t == YELLOW-1) begin main <= R; t <= 0; end
                R: begin
                       walk <= (main == R) && (t != RED-1);  // clearance 1st
                       if (t == RED-1) begin main <= G; t <= 0; end
                   end
                default: main <= G;
            endcase
        end
    end
endmodule
module tb;
    reg clk = 0, rst = 1, btn = 0;  wire [1:0] main;  wire walk;
    traffic uut (.clk(clk), .rst(rst), .btn(btn), .main(main), .walk(walk));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;  #18 $display("m=%0d w=%b", main, walk);
        #10 btn = 1;  #8 btn = 0;
        #12 $display("m=%0d w=%b", main, walk);
        #20 $display("m=%0d w=%b", main, walk);
        #10 $display("m=%0d w=%b", main, walk);
        #60 $display("m=%0d w=%b", main, walk);
        $finish;
    end
endmodule
"""
SPI_S1 = """\
// SPI stage 1: clock-enable tick (clk/4).
module spi_tick(input clk, rst, output reg tick);
    reg [1:0] d;
    always @(posedge clk) begin
        if (rst) begin d <= 0; tick <= 0; end
        else begin
            tick <= (d == 2'd3);
            d <= (d == 2'd3) ? 2'd0 : d + 1'b1;
        end
    end
endmodule
module tb;
    reg clk = 0, rst = 1;  wire tick;
    spi_tick uut (.clk(clk), .rst(rst), .tick(tick));
    always #5 clk = ~clk;
    integer k;
    initial begin
        #12 rst = 0;
        for (k = 0; k < 16; k = k + 1) begin
            #10;  if (tick) $display("tick");
        end
        $finish;
    end
endmodule
"""
SPI_S2 = """\
// SPI stage 2: SCLK (clk/4) with CS framing, 8 pulses, CPOL=0.
module spi_master(input clk, rst, send, output reg sclk, csen);
    reg [1:0] div;  reg [3:0] n;  reg run;
    always @(posedge clk) begin
        if (rst) begin run<=0; n<=0; div<=0; sclk<=0; csen<=1; end
        else if (!run && send) begin run<=1; n<=0; div<=0; csen<=0; end
        else if (run) begin
            if (div == 2'd1) begin
                div <= 0;  sclk <= ~sclk;
                if (sclk) begin
                    if (n == 4'd7) begin run <= 0; csen <= 1; end
                    else n <= n + 1'b1;
                end
            end else div <= div + 1'b1;
        end
    end
endmodule
module tb;
    reg clk = 0, rst = 1, send = 0, prev = 0;
    wire sclk, csen;
    spi_master uut (.clk(clk), .rst(rst), .send(send), .sclk(sclk),
                    .csen(csen));
    always #5 clk = ~clk;
    integer k;
    initial begin
        #12 rst = 0;  #10 send = 1;  #10 send = 0;
        $display("cs=%b", csen);
        for (k = 0; k < 32; k = k + 1) begin
            #10;
            if (sclk && !prev) $display("rise");
            prev = sclk;
        end
        $display("cs=%b", csen);
        $finish;
    end
endmodule
"""
SPI_S3 = """\
// SPI stage 3: MOSI shifts MSB-first (mode 0: change on fall, sample on
// rise). TB loops the line back and rebuilds 0xB7.
module spi_master(input clk, rst, send, input [7:0] din,
                  output reg sclk, csen, mosi);
    reg [1:0] div;  reg [3:0] n;  reg [7:0] sh;  reg run;
    always @(posedge clk) begin
        if (rst) begin
            run<=0; n<=0; div<=0; sclk<=0; csen<=1; sh<=0; mosi<=0;
        end else if (!run && send) begin
            run<=1; n<=0; div<=0; csen<=0; sh<=din; mosi<=din[7];
        end else if (run) begin
            if (div == 2'd1) begin
                div <= 0;  sclk <= ~sclk;
                if (sclk) begin                    // falling edge
                    sh <= {sh[6:0], 1'b0};  mosi <= sh[6];
                    if (n == 4'd7) begin run <= 0; csen <= 1; end
                    else n <= n + 1'b1;
                end
            end else div <= div + 1'b1;
        end
    end
endmodule
module tb;
    reg clk = 0, rst = 1, send = 0, prev = 0;  reg [7:0] din = 8'hB7;
    wire sclk, csen, mosi;  wire miso;
    assign miso = mosi;                    // loopback
    spi_master uut (.clk(clk), .rst(rst), .send(send), .din(din),
                    .sclk(sclk), .csen(csen), .mosi(mosi));
    always #5 clk = ~clk;
    integer k;  reg [7:0] acc;
    initial begin
        #12 rst = 0;  #10 send = 1;  #10 send = 0;
        prev = 0; acc = 0;
        for (k = 0; k < 32; k = k + 1) begin
            #10;
            if (sclk && !prev) begin
                acc = {acc[6:0], miso};  $display("bit=%b", miso);
            end
            prev = sclk;
        end
        $display("recv=%h", acc);
        $finish;
    end
endmodule
"""
SPI_S4 = """\
// SPI stage 4: FULL DUPLEX -- sample MISO on rising edges into recv;
// done pulses at frame end. Two back-to-back transactions.
module spi_master(input clk, rst, send, input [7:0] din, input miso,
                  output reg sclk, csen, mosi,
                  output reg [7:0] recv, output reg done);
    reg [1:0] div;  reg [3:0] n;  reg [7:0] sh;  reg run;
    always @(posedge clk) begin
        if (rst) begin
            run<=0; n<=0; div<=0; sclk<=0; csen<=1;
            sh<=0; mosi<=0; recv<=0; done<=0;
        end else begin
            done <= 1'b0;
            if (!run && send) begin
                run<=1; n<=0; div<=0; csen<=0; sh<=din; mosi<=din[7]; recv<=0;
            end else if (run) begin
                if (div == 2'd1) begin
                    div <= 0;  sclk <= ~sclk;
                    if (!sclk) recv <= {recv[6:0], miso};  // rising: sample
                    else begin                             // falling: shift
                        sh <= {sh[6:0], 1'b0};  mosi <= sh[6];
                        if (n == 4'd7) begin run<=0; csen<=1; done<=1; end
                        else n <= n + 1'b1;
                    end
                end else div <= div + 1'b1;
            end
        end
    end
endmodule
module tb;
    reg clk = 0, rst = 1, send = 0;  reg [7:0] din = 8'hB7;
    wire sclk, csen, mosi, done;  wire [7:0] recv;
    spi_master uut (.clk(clk), .rst(rst), .send(send), .din(din),
        .miso(1'b0), .sclk(sclk), .csen(csen), .mosi(mosi),
        .recv(recv), .done(done));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;
        #10 send = 1; din = 8'hB7;  #10 send = 0;
        #320 $display("r=%h", recv);
        #8  send = 1; din = 8'h5A;  #10 send = 0;
        #330 $display("r=%h", recv);
        $finish;
    end
endmodule
"""
CPU_S1 = """\
// MINI-CPU stage 1: PC + ROM (fetch). instr = {op[2:0], arg[4:0]}.
module cpu(input clk, rst, output reg [4:0] pc,
           output [7:0] instr, output reg [7:0] acc);
    reg [7:0] rom_q;
    always @(*) case (pc)
        5'd0: rom_q = 8'b000_00101;   // LDI 5
        5'd1: rom_q = 8'b000_00011;   // LDI 3
        default: rom_q = 8'b001_00000; // HALT
    endcase
    assign instr = rom_q;
    always @(posedge clk) begin
        if (rst) pc <= 0;
        else if (instr[7:5] != 3'd1) pc <= pc + 1'b1;  // HALT freezes
    end
    always @(posedge clk) if (rst) acc <= 0;
endmodule
module tb;
    reg clk = 0, rst = 1;  wire [4:0] pc;  wire [7:0] instr, acc;
    cpu uut (.clk(clk), .rst(rst), .pc(pc), .instr(instr), .acc(acc));
    always #5 clk = ~clk;
    initial begin
        #1  $display("pc=%0d i=%h", pc, instr);
        #14 $display("pc=%0d i=%h", pc, instr);
        #10 $display("pc=%0d i=%h", pc, instr);
        #10 $display("pc=%0d i=%h", pc, instr);
        $finish;
    end
endmodule
"""
CPU_S2 = """\
// MINI-CPU stage 2: DECODE -- TB samples instr and prints op names.
module cpu(input clk, rst, output reg [4:0] pc,
           output [7:0] instr, output reg [7:0] acc);
    reg [7:0] rom_q;
    always @(*) case (pc)
        5'd0: rom_q = 8'b000_00101;
        5'd1: rom_q = 8'b000_00011;
        default: rom_q = 8'b001_00000;
    endcase
    assign instr = rom_q;
    always @(posedge clk) begin
        if (rst) pc <= 0;
        else if (instr[7:5] != 3'd1) pc <= pc + 1'b1;
    end
    always @(posedge clk) if (rst) acc <= 0;
endmodule
module tb;
    reg clk = 0, rst = 1;  wire [4:0] pc;  wire [7:0] instr, acc;
    cpu uut (.clk(clk), .rst(rst), .pc(pc), .instr(instr), .acc(acc));
    always #5 clk = ~clk;
    initial begin
        #1 begin
            if (instr[7:5] == 3'd0) $display("op=LDI");
            if (instr[7:5] == 3'd1) $display("op=HALT");
        end
        #15 begin
            if (instr[7:5] == 3'd0) $display("op=LDI");
            if (instr[7:5] == 3'd1) $display("op=HALT");
        end
        #10 begin
            if (instr[7:5] == 3'd0) $display("op=LDI");
            if (instr[7:5] == 3'd1) $display("op=HALT");
        end
        $finish;
    end
endmodule
"""
CPU_S3 = """\
// MINI-CPU stage 3: EXECUTE LDI -> accumulator.
module cpu(input clk, rst, output reg [4:0] pc,
           output [7:0] instr, output reg [7:0] acc);
    reg [7:0] rom_q;
    always @(*) case (pc)
        5'd0: rom_q = 8'b000_00101;
        5'd1: rom_q = 8'b000_00011;
        default: rom_q = 8'b001_00000;
    endcase
    assign instr = rom_q;
    always @(posedge clk) begin
        if (rst) pc <= 0;
        else if (instr[7:5] != 3'd1) pc <= pc + 1'b1;
    end
    always @(posedge clk) begin
        if (rst) acc <= 0;
        else if (instr[7:5] == 3'd0) acc <= {3'b000, instr[4:0]};
    end
endmodule
module tb;
    reg clk = 0, rst = 1;  wire [4:0] pc;  wire [7:0] instr, acc;
    cpu uut (.clk(clk), .rst(rst), .pc(pc), .instr(instr), .acc(acc));
    always #5 clk = ~clk;
    initial begin
        #1  $display("acc=%0d", acc);
        #14 $display("acc=%0d", acc);
        #10 $display("acc=%0d", acc);
        $finish;
    end
endmodule
"""
CPU_S4 = """\
// MINI-CPU stage 4: data RAM + STD/LDD/ADD + `peek` debug port.
// ops: 0 LDI 1 HALT 2 STD 3 LDD 4 ADD
module cpu(input clk, rst, input [2:0] peek, output reg [4:0] pc,
           output [7:0] instr, output reg [7:0] acc, output [7:0] peek_q);
    reg [7:0] rom_q;  reg [7:0] ram [0:7];
    always @(*) case (pc)
        5'd0: rom_q = 8'b000_00101;   // LDI 5
        5'd1: rom_q = 8'b010_00010;   // STD [2]
        5'd2: rom_q = 8'b000_00111;   // LDI 7
        5'd3: rom_q = 8'b100_00010;   // ADD [2]
        5'd4: rom_q = 8'b010_00011;   // STD [3]
        default: rom_q = 8'b001_00000;
    endcase
    assign instr = rom_q;  assign peek_q = ram[peek];
    always @(posedge clk) begin
        if (rst) pc <= 0;
        else if (instr[7:5] != 3'd1) pc <= pc + 1'b1;
    end
    always @(posedge clk) begin
        if (rst) acc <= 0;
        else case (instr[7:5])
            3'd0: acc <= {3'b000, instr[4:0]};
            3'd2: ram[instr[2:0]] <= acc;
            3'd3: acc <= ram[instr[2:0]];
            3'd4: acc <= acc + ram[instr[2:0]];
            default: ;
        endcase
    end
endmodule
module tb;
    reg clk = 0, rst = 1;  reg [2:0] peek = 3'd3;
    wire [4:0] pc;  wire [7:0] instr, acc, peek_q;
    cpu uut (.clk(clk), .rst(rst), .peek(peek), .pc(pc), .instr(instr),
             .acc(acc), .peek_q(peek_q));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;  #58 $display("acc=%0d", acc);
        #1  $display("peek=%h", peek_q);
        $finish;
    end
endmodule
"""
CPU_S5 = """\
// MINI-CPU stage 5: JUMPS + countdown program (3->2->1->0->HALT).
// ops: 0 LDI 1 HALT 2 STD 3 LDD 4 ADD 5 SUB-imm 6 JZ 7 JMP
module cpu(input clk, rst, input [2:0] peek, output reg [4:0] pc,
           output [7:0] instr, output reg [7:0] acc, output [7:0] peek_q);
    reg [7:0] rom_q;  reg [7:0] ram [0:7];
    always @(*) case (pc)
        5'd0: rom_q = 8'b000_00011;   // LDI 3
        5'd1: rom_q = 8'b010_00000;   // STD [0]
        5'd2: rom_q = 8'b011_00000;   // LDD [0]  <- loop top
        5'd3: rom_q = 8'b110_00111;   // JZ 7
        5'd4: rom_q = 8'b101_00001;   // SUB 1
        5'd5: rom_q = 8'b010_00000;   // STD [0]
        5'd6: rom_q = 8'b111_00010;   // JMP 2
        default: rom_q = 8'b001_00000;
    endcase
    assign instr = rom_q;  assign peek_q = ram[peek];
    always @(posedge clk) begin
        if (rst) pc <= 0;
        else case (instr[7:5])
            3'd1: pc <= pc;
            3'd6: pc <= (acc == 0) ? {2'b00, instr[2:0]} : pc + 1'b1;
            3'd7: pc <= {2'b00, instr[2:0]};
            default: pc <= pc + 1'b1;
        endcase
    end
    always @(posedge clk) begin
        if (rst) acc <= 0;
        else case (instr[7:5])
            3'd0: acc <= {3'b000, instr[4:0]};
            3'd2: ram[instr[2:0]] <= acc;
            3'd3: acc <= ram[instr[2:0]];
            3'd4: acc <= acc + ram[instr[2:0]];
            3'd5: acc <= acc - {3'b000, instr[4:0]};
            default: ;
        endcase
    end
endmodule
module tb;
    reg clk = 0, rst = 1;  reg [2:0] peek = 3'd0;
    wire [4:0] pc;  wire [7:0] instr, acc, peek_q;
    cpu uut (.clk(clk), .rst(rst), .peek(peek), .pc(pc), .instr(instr),
             .acc(acc), .peek_q(peek_q));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;
        #18  $display("s acc=%0d", acc);
        #70  $display("mid acc=%0d", acc);
        #110 $display("end acc=%0d pc=%0d", acc, pc);
        $finish;
    end
endmodule
"""
VGA_S1 = """\
// VGA (scaled 64x48) stage 1: sync counters, one clock/pixel.
module vga(input clk, rst, output reg [5:0] x, y,
           output hsync, vsync, video);
    assign hsync = ~(x == 6'd63);
    assign vsync = ~(y == 6'd47);
    assign video = (x < 6'd64) && (y < 6'd48);
    always @(posedge clk) begin
        if (rst) begin x <= 0; y <= 0; end
        else if (x == 6'd63) begin
            x <= 0;  y <= (y == 6'd47) ? 6'd0 : y + 1'b1;
        end else x <= x + 1'b1;
    end
endmodule
module tb;
    reg clk = 0, rst = 1;  wire [5:0] x, y;
    wire hsync, vsync, video;
    vga uut (.clk(clk), .rst(rst), .x(x), .y(y), .hsync(hsync),
             .vsync(vsync), .video(video));
    always #5 clk = ~clk;
    reg ph = 1'b1;  integer hf = 0;
    always @(posedge clk) begin
        if (ph && !hsync) hf = hf + 1;
        ph = hsync;
    end
    initial begin
        #12 rst = 0;  #30900;
        $display("h=%0d", hf);  $display("y=%0d", y);
        $finish;
    end
endmodule
"""
VGA_S2 = """\
// VGA stage 2: RGB test pattern. After Run the Framebuffer tab
// rebuilds the 64x48 image: red border, yellow checker, blue bg.
module vga(input clk, rst, output reg [5:0] x, y,
           output hsync, vsync, output r, g, b);
    wire border = (x == 0) || (y == 0) || (x == 6'd63) || (y == 6'd47);
    wire chk = x[3] ^ y[3];
    assign r = border | chk;  assign g = ~border & chk;  assign b = ~border & ~chk;
    assign hsync = ~(x == 6'd63);  assign vsync = ~(y == 6'd47);
    always @(posedge clk) begin
        if (rst) begin x <= 0; y <= 0; end
        else if (x == 6'd63) begin
            x <= 0;  y <= (y == 6'd47) ? 6'd0 : y + 1'b1;
        end else x <= x + 1'b1;
    end
endmodule
module tb;
    reg clk = 0, rst = 1;  wire [5:0] x, y;
    wire hsync, vsync, r, g, b;
    vga uut (.clk(clk), .rst(rst), .x(x), .y(y), .hsync(hsync),
             .vsync(vsync), .r(r), .g(g), .b(b));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;  #30900;
        $display("frame done");
        $finish;
    end
endmodule
"""
CPU2_CORE = """\
module cpu2(input clk, rst, output reg [3:0] pc, output reg [3:0] acc,
            output reg [3:0] outport, output reg halted);
    // CPU-II ISA: {op[7:4], arg[3:0]}
    // 0 LDI 1 HALT 2 STD 3 LDD 4 ADD 5 SUB 6 JZ 7 JMP
    // 8 JNZ 9 CALL 10 RET 11 OUT
    reg [7:0] rom [0:15];
    initial $readmemh("rom.hex", rom);
    reg [3:0] ram [0:15];  reg [3:0] sp;
    wire [3:0] op = rom[pc][7:4];
    wire [3:0] arg = rom[pc][3:0];
    always @(posedge clk) begin
        if (rst) begin
            pc <= 0; acc <= 0; outport <= 0; halted <= 0; sp <= 4'd15;
        end else if (!halted) begin
            case (op)
                4'd0: begin acc <= arg; pc <= pc + 1'b1; end
                4'd1: halted <= 1'b1;
                4'd2: begin ram[arg] <= acc; pc <= pc + 1'b1; end
                4'd3: begin acc <= ram[arg]; pc <= pc + 1'b1; end
                4'd4: begin acc <= acc + ram[arg]; pc <= pc + 1'b1; end
                4'd5: begin acc <= acc - arg; pc <= pc + 1'b1; end
                4'd6: pc <= (acc == 0) ? arg : pc + 1'b1;
                4'd7: pc <= arg;
                4'd8: pc <= (acc != 0) ? arg : pc + 1'b1;
                4'd9: begin ram[sp] <= pc + 1'b1; sp <= sp - 1'b1; pc <= arg; end
                4'd10: begin sp <= sp + 1'b1; pc <= ram[sp + 1'b1]; end
                4'd11: begin outport <= acc; pc <= pc + 1'b1; end
                default: pc <= pc + 1'b1;
            endcase
        end
    end
endmodule
"""
CPU2_S1 = CPU2_CORE + """\
module tb;
    reg clk = 0, rst = 1;
    wire [3:0] pc, acc, outport;  wire halted;
    cpu2 uut (.clk(clk), .rst(rst), .pc(pc), .acc(acc),
              .outport(outport), .halted(halted));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;  #200;
        $display("acc=%0d", acc);  $display("pc=%0d", pc);
        $finish;
    end
endmodule
"""
CPU2_S2 = CPU2_CORE + """\
module tb;
    reg clk = 0, rst = 1;
    wire [3:0] pc, acc, outport;  wire halted;
    cpu2 uut (.clk(clk), .rst(rst), .pc(pc), .acc(acc),
              .outport(outport), .halted(halted));
    always #5 clk = ~clk;
    initial begin
        #12 rst = 0;  #400;
        $display("out=%0d", outport);  $display("acc=%0d", acc);
        $finish;
    end
endmodule
"""
I2C_CORE = """\
// I2C master: START, phase-tick bit engine, ACK slot, STOP.
// Open-drain is modelled explicitly: the line ANDs both drivers.
module i2c_master(input clk, rst, start, input [7:0] din, input sda_i,
                  output reg scl, sda_o, output reg busy);
    localparam IDLE=3'd0, START=3'd1, DATA=3'd2, ACK=3'd3, STOP=3'd4;
    reg [2:0] st;  reg [1:0] ph;  reg [3:0] n;  reg [7:0] sh;
    always @(posedge clk) begin
        if (rst) begin
            st <= IDLE; ph <= 0; n <= 0;
            scl <= 1'b1; sda_o <= 1'b1; busy <= 1'b0; sh <= 0;
        end else case (st)
            IDLE: if (start && !busy)
                begin st <= START; ph <= 0; sh <= din; busy <= 1'b1; end
            START: case (ph)
                2'd0: begin sda_o <= 1'b0; ph <= 2'd1; end
                2'd1: begin scl <= 1'b0; ph <= 2'd2; end
                default: begin st <= DATA; ph <= 0; n <= 0; sda_o <= sh[7]; end
            endcase
            DATA: case (ph)
                2'd0: begin scl <= 1'b1; ph <= 2'd1; end
                2'd1: ph <= 2'd2;
                2'd2: begin scl <= 1'b0; ph <= 2'd3; end
                default: begin
                    ph <= 0;
                    if (n == 4'd7) begin st <= ACK; sda_o <= 1'b1; end
                    else begin n <= n + 1'b1; sda_o <= sh[6 - n]; end
                end
            endcase
            ACK: case (ph)
                2'd0: begin scl <= 1'b1; ph <= 2'd1; end
                2'd1: ph <= 2'd2;
                2'd2: begin scl <= 1'b0; ph <= 2'd3; end
                default: begin st <= STOP; ph <= 0; sda_o <= 1'b0; end
            endcase
            STOP: case (ph)
                2'd0: begin scl <= 1'b1; ph <= 2'd1; end
                2'd1: begin sda_o <= 1'b1; ph <= 2'd2; end
                default: begin st <= IDLE; busy <= 1'b0; end
            endcase
            default: st <= IDLE;
        endcase
    end
endmodule
"""
I2C_S1 = I2C_CORE + """\
module tb;
    reg clk = 0, rst = 1, start = 0;  reg [7:0] din = 8'hA5;
    wire scl, sda_m, busy;  reg sda_s = 1'b1;
    wire sda = sda_m & sda_s;          // open-drain wired-AND
    i2c_master uut (.clk(clk), .rst(rst), .start(start), .din(din),
                    .sda_i(sda), .scl(scl), .sda_o(sda_m), .busy(busy));
    // slave: samples on SCL rising, ACKs the 9th bit
    reg [3:0] bitn = 0;  reg [7:0] rx = 0;  reg pscl = 1'b1;
    always @(posedge clk) begin
        pscl <= scl;
        if (scl && !pscl) begin
            if (bitn < 8) begin rx <= {rx[6:0], sda}; bitn <= bitn + 1'b1; end
            else begin
                $display("byte=%h ack=%b", rx, ~sda);
                sda_s <= 1'b1;  bitn <= 0;
            end
        end
        if (!scl && pscl && bitn == 8) sda_s <= 1'b0;   // ACK pull-low
    end
    initial begin
        #12 rst = 0;  #10 start = 1;  #10 start = 0;  #200 $finish;
    end
endmodule
"""
I2C_S2 = I2C_CORE + """\
module tb;
    reg clk = 0, rst = 1, start = 0;  reg [7:0] din = 8'hA5;
    wire scl, sda_m, busy;  reg sda_s = 1'b1;
    wire sda = sda_m & sda_s;
    i2c_master uut (.clk(clk), .rst(rst), .start(start), .din(din),
                    .sda_i(sda), .scl(scl), .sda_o(sda_m), .busy(busy));
    reg [3:0] bitn = 0;  reg [7:0] rx = 0, mem0 = 0, mem1 = 0;
    reg pscl = 1'b1;  reg [1:0] mi = 0;  reg sent2 = 0;
    always @(posedge clk) begin
        pscl <= scl;
        if (scl && !pscl) begin
            if (bitn < 8) begin rx <= {rx[6:0], sda}; bitn <= bitn + 1'b1; end
            else begin
                $display("byte=%h", rx);
                if (mi == 0) mem0 <= rx; else mem1 <= rx;
                mi <= mi + 1'b1;  sda_s <= 1'b1;  bitn <= 0;
            end
        end
        if (!scl && pscl && bitn == 8) sda_s <= 1'b0;
    end
    integer k;
    initial begin
        #12 rst = 0;  #10 start = 1;  #10 start = 0;
        for (k = 0; k < 130; k = k + 1) begin
            #10;
            if (!busy && !sent2) begin
                din = 8'h3C;  start = 1;  sent2 = 1;
            end else if (sent2 && start) start = 0;
        end
        $display("m0=%h", mem0);  $display("m1=%h", mem1);
        $finish;
    end
endmodule
"""

# ══════════════════════════ CURRICULUM ══════════════════════════
def pre(code):
    return ("<pre style='margin:6px; background-color:%s;'>"
            % th("lesson_pre") + html.escape(code) + "</pre>")

def cd(s):
    return "<code>" + html.escape(s) + "</code>"

def _L(**kw):
    return kw

LESSONS = [
 dict(id="m1l1", module="1. Foundations", title="What is an HDL?", body=f"""
<h2>What is an HDL?</h2><p>HDL code does <b>not</b> run top-to-bottom — it
describes <b>concurrent components</b> reacting to inputs, like real wires
and gates. Styles: <b>dataflow</b> ({cd("assign")}), <b>behavioral</b>
({cd("always")}/{cd("process")}), <b>structural</b> (instances).</p>
{pre(EX_AND_GATE)}""", ex=EX_AND_GATE),
 dict(id="m1l2", module="1. Foundations", title="Simulation & tooling", body=f"""
<h2>Simulation &amp; Tooling</h2><p>This app ships a <b>built-in
simulator</b> — every Verilog lesson runs with zero setup. Icarus Verilog
(also SystemVerilog via -g2012), GHDL and Yosys are used automatically when
installed; "Run (built-in)" always uses the internal engine. A testbench
drives the DUT, prints with {cd("$display")}, stops with {cd("$finish")}.</p>
{pre(EX_COMBINED_TB)}<p><b>Press Run</b>, then try <b>Schematic</b>.</p>""",
 ex=EX_COMBINED_TB),
 dict(id="m2l1", module="2. Verilog Basics", title="Your first module", body=f"""
<h2>Your First Module</h2>{pre(EX_AND_GATE)}
<ul><li>{cd("assign")} = continuous assignment (a wire to a gate).</li>
<li>Instantiate: {cd("and_gate u0 (.a(x), .b(z), .y(w));")}</li></ul>
<p><b>Exercise:</b> build an inverter, press <b>Check</b>.</p>""",
 ex=EX_AND_GATE, starter=ST_INV,
 check=dict(module="inverter", inputs=["a"], outputs={"y": "10"})),
 dict(id="m2l2", module="2. Verilog Basics", title="wire, reg & vectors", body=f"""
<h2>Data Types</h2><ul><li>{cd("wire")} — net; {cd("reg")} — target of
procedural assignment (<i>not necessarily a flop!</i>)</li>
<li>Vectors {cd("[7:0] d")}, selects, concatenation, parameters</li></ul>
{pre(EX_TYPES)}""", ex=EX_TYPES),
 dict(id="m2l3", module="2. Verilog Basics", title="Operators", body=f"""
<h2>Operators</h2><p>{cd("& | ^ ~")}, reductions ({cd("&bus")}), equality,
concat, {cd("?:")}, arithmetic/shifts. &amp; binds tighter than ^ —
parenthesize!</p>{pre(EX_OPS)}<p><b>Exercise:</b> build a NOR gate.</p>""",
 ex=EX_OPS, starter=ST_NOR,
 check=dict(module="nor_gate", inputs=["a", "b"], outputs={"y": "1000"}),
 quiz=[_L(q="assign y = ~a; builds…", options=["a flip-flop", "an inverter",
        "a wire to ground", "a mux"], a=1, why="~ is bitwise NOT."),
       _L(q="4'b1010 =", options=["8", "10", "12", "5"], a=1, why="8+2."),
       _L(q="{c,s} with c=1,s=0 is…", options=["2'b01", "2'b10", "1'b1",
        "error"], a=1, why="Leftmost = MSB.")]),
 dict(id="m2l4", module="2. Verilog Basics", title="Structural modeling",
 body=f"""<h2>Structural Modeling</h2><p>Gate primitives
{cd("and or nand nor xor xnor not buf")} — first port is the output.</p>
{pre(EX_STRUCT)}<p>Press <b>Schematic</b> and <b>Truth Table</b>.
<b>Exercise:</b> write a full adder, press <b>Check</b>.</p>""",
 ex=EX_STRUCT, starter=ST_FA,
 check=dict(module="full_adder", inputs=["a", "b", "cin"],
            outputs={"sum": "01101001", "cout": "00010111"})),
 dict(id="m2l5", module="2. Verilog Basics", title="NAND logic", body=f"""
<h2>NAND Is Universal</h2>{pre(EX_NANDXOR)}
<p><b>Exercise:</b> build XOR from four NANDs.</p>""",
 ex=EX_NANDXOR, starter=ST_NANDXOR,
 check=dict(module="xor_nand", inputs=["a", "b"], outputs={"y": "0110"})),
 dict(id="m3l1", module="3. Combinational Logic", title="Multiplexers",
 body=f"""<h2>Multiplexers</h2>{pre(EX_MUX)}<p><b>Exercise:</b> write the
mux yourself.</p>""", ex=EX_MUX, starter=ST_MUX,
 check=dict(module="mux2to1", inputs=["a", "b", "sel"],
            outputs={"y": "00011011"})),
 dict(id="m3l2", module="3. Combinational Logic", title="Decoders", body=f"""
<h2>Decoders</h2><p>One-hot output — heart of address/instruction decoding.</p>
{pre(EX_DEC_CASE)}{pre(EX_DEC_ASSIGN)}<p><b>Exercise:</b> dataflow decoder.</p>""",
 ex=EX_DEC_ASSIGN, starter=ST_DEC,
 check=dict(module="dec2to4", inputs=["a", "b"],
            outputs={"y0": "10000000", "y1": "00100000",
                     "y2": "00001000", "y3": "00000010"})),
 dict(id="m3l3", module="3. Combinational Logic", title="Adders", body=f"""
<h2>Adders</h2><p>Full adders chained by carry = ripple-carry: simple but
the carry "ripples", limiting speed.</p>{pre(EX_ADDER4)}""", ex=EX_ADDER4),
 dict(id="m3l4", module="3. Combinational Logic", title="K-maps & minimization",
 body=f"""<h2>K-maps &amp; Quine-McCluskey</h2><p>Generate a truth table,
press <b>K-map / Minimize</b>: Gray-ordered map, implicant groups, minimal
SOP. Click a term to <b>see its gates in the Schematic tab</b>.</p>
{pre(EX_SEG)}<p><b>Exercise:</b> seven-segment decoder.</p>""", ex=EX_SEG,
 starter=ST_SEG,
 check=dict(module="seg7", inputs=["d3", "d2", "d1", "d0"],
   outputs={"seg_a": "1011011111000000", "seg_b": "1111100111000000",
            "seg_c": "1101111111000000", "seg_d": "1011011011000000",
            "seg_e": "1010001010000000", "seg_f": "1000111101000000",
            "seg_g": "0011111111000000"}),
 quiz=[_L(q="Adjacent K-map cells differ in…", options=["exactly one var",
        "two vars", "value", "nothing"], a=0, why="Gray-code ordering."),
       _L(q="8 ones in a 4-var map → term with…", options=["4 literals",
        "3 literals", "1 literal", "none"], a=2, why="8 = 2³."),
       _L(q="Quine-McCluskey finds…", options=["clocks", "minimal SOP",
        "schematics", "tokens"], a=1, why="")]),
 dict(id="m3l5", module="3. Combinational Logic", title="Comparators",
 body=f"""<h2>Comparators</h2>{pre(EX_COMP)}<p><b>Exercise:</b> 2-bit
greater-than (16 rows verified).</p>""", ex=EX_COMP, starter=ST_COMP,
 check=dict(module="comp2", inputs=["a1", "a0", "b1", "b0"],
            outputs={"gt": "0000100011001110"})),
 dict(id="m3l6", module="3. Combinational Logic", title="Priority encoders",
 body=f"""<h2>Priority Encoders</h2>{pre(EX_ENC)}<p><b>Exercise:</b>
implement it.</p>""", ex=EX_ENC, starter=ST_ENC,
 check=dict(module="prio_enc", inputs=["r3", "r2", "r1", "r0"],
            outputs={"v": "0000000011111111", "y1": "0000111100001111",
                     "y0": "0011001100110011"})),
 dict(id="m3l7", module="3. Combinational Logic", title="Gate delays & hazards",
 body=f"""<h2>Hazards</h2><p>Real gates have delays — here every assign has
an inertial {cd("#delay")}. Press <b>Run</b>: the glitch engine schedules
each net update and the waveform shows {cd("cout")} <b>glitch low</b> when
{cd("b")} falls even though steady state never changes. That transient is
why registered outputs exist. Waveform starts at <b>x</b>: nothing computed
at t=0. Try <b>Schematic → ▶ Replay</b> to animate it gate by gate.</p>
{pre(EX_GLITCH)}""", ex=EX_GLITCH),
 dict(id="m4l1", module="4. Sequential Verilog", title="always blocks", body=f"""
<h2>always Blocks</h2><table border="1" cellpadding="4"><tr>
<td>Combinational</td><td>{cd("@(*)")}</td><td>blocking {cd("=")}</td></tr>
<tr><td>Sequential</td><td>{cd("@(posedge clk)")}</td><td>non-blocking
{cd("&lt;=")}</td></tr></table><p>Mixing them = the #1 Verilog trap.</p>
{pre(EX_MUX_ALWAYS)}""", ex=EX_MUX_ALWAYS,
 quiz=[_L(q="Combinational sensitivity is…", options=["@(posedge clk)",
        "@(*)", "@(negedge rst)", "none"], a=1, why=""),
       _L(q="Clocked blocks use…", options=["y = x;", "y <= x;",
        "assign y = x;", "#5 y = x;"], a=1, why="All flops sample together."),
       _L(q="Signals assigned in always are…", options=["wire", "reg",
        "parameter", "tri0"], a=1, why="")]),
 dict(id="m4l2", module="4. Sequential Verilog", title="Flip-flops", body=f"""
<h2>Flip-Flops</h2>{pre(EX_DFF)}<p><b>Load both and Run</b> (built-in, no
tools): q shows <i>x</i> until the first clock writes it. Timing margins?
<b>View → Setup/Hold Lab</b>. Step through events with <b>Simulate → Step
debugger</b>.</p>""", ex=EX_DFF, ex_tb=EX_DFF_TB,
 quiz=[_L(q="A D flip-flop is…", options=["assign q = d;",
        "always @(*) q = d;", "always @(posedge clk) q <= d;",
        "always #5 q = d;"], a=2, why=""),
       _L(q="Async reset means…", options=["checked at clock edges only",
        "rst is in the sensitivity list", "sets q to 1", "needs a clock"],
        a=1, why=""),
       _L(q="Between edges a flop…", options=["follows d", "is high-Z",
        "holds", "toggles"], a=2, why="")]),
 dict(id="m4l3", module="4. Sequential Verilog", title="Counters", body=f"""
<h2>Counters</h2>{pre(EX_COUNTER)}{pre(EX_COUNTER_TB)}
<p>Predict the final count before Run — the app asks and compares.</p>""",
 ex=EX_COUNTER, ex_tb=EX_COUNTER_TB,
 predict=[dict(q="Final value of `count`? (decimal)", signal="count",
               fmt="d")]),
 dict(id="m4l4", module="4. Sequential Verilog", title="Shift registers",
 body=f"""<h2>Shift Registers</h2>{pre(EX_SHIFT)}{pre(EX_SHIFT_TB)}
<p>Trace the final {cd("q")} by hand, then Run (predict-then-run is on).</p>""",
 ex=EX_SHIFT, ex_tb=EX_SHIFT_TB,
 predict=[dict(q="Final value of `q`? (4-bit binary)", signal="q", fmt="b")]),
 dict(id="m5l1", module="5. VHDL Basics", title="Entities & architectures",
 body=f"""<h2>Entities &amp; Architectures</h2>{pre(EX_VHDL_AND)}
<p>{cd("std_logic")}, quoted literals, {cd("&lt;=")} for signals. Run with
GHDL installed.</p>""", ex=EX_VHDL_AND),
 dict(id="m5l2", module="5. VHDL Basics", title="Processes & flip-flops",
 body=f"""<h2>Processes &amp; Flip-Flops</h2>{pre(EX_VHDL_DFF)}
<p>Signals update at process end; variables instantly. Enumeration state
types make FSMs readable in waveforms.</p>""", ex=EX_VHDL_DFF),
 dict(id="m6l1", module="6. State Machines", title="FSM concepts", body="""
<h2>FSMs</h2><p><b>Moore</b>: outputs from state only (glitch-free).
<b>Mealy</b>: state + inputs. Template: clocked state register +
combinational next-state <code>case</code> + reset + <code>default</code>.</p>""",
 quiz=[_L(q="Moore outputs depend on…", options=["inputs", "state",
        "clock", "reset"], a=1, why=""),
       _L(q="Mealy outputs depend on…", options=["state and inputs",
        "state", "inputs", "nothing"], a=0, why=""),
       _L(q="default branch exists to…", options=["save power",
        "recover from illegal encodings", "satisfy syntax", "go faster"],
        a=1, why=""),
       _L(q="The state register is…", options=["combinational",
        "clocked with reset", "a mux", "assign-driven"], a=1, why="")]),
 dict(id="m6l2", module="6. State Machines", title="FSM in Verilog", body=f"""
<h2>FSM in Verilog</h2>{pre(EX_FSM_V)}<p>Run prints <b>[coverage]</b> per
case branch. Load both examples and Run — waveform included, no tools.</p>""",
 ex=EX_FSM_V, ex_tb=EX_FSM_V_TB),
 dict(id="m6l3", module="6. State Machines", title="FSM in VHDL", body=f"""
<h2>FSM in VHDL</h2>{pre(EX_FSM_VHDL)}<p>Compare with the Verilog version
line by line — concepts map 1:1. GHDL runs it.</p>""", ex=EX_FSM_VHDL),
 dict(id="m7l1", module="7. Testbenches", title="Writing testbenches", body=f"""
<h2>Writing Testbenches</h2><p>Pattern: <b>drive → wait a delta → check →
display</b>. Self-checking benches count errors.</p>{pre(EX_TB_MAJ)}
<p><b>Exercise:</b> complete the mux TB — exact console lines are
auto-verified in order.</p>""", ex=EX_TB_MAJ, starter=ST_TB_MUX,
 check_console=[r"a=0 b=0 sel=0 -> y=0", r"a=0 b=1 sel=0 -> y=0",
                r"a=1 b=0 sel=0 -> y=0", r"a=1 b=1 sel=1 -> y=1"]),
 dict(id="m7l2", module="7. Testbenches", title="Waveform goals", body=f"""
<h2>Waveform-Comparison Exercises</h2><p>Graded on the <b>sequence of
value changes</b> on {cd("q")}: must be 0→1→0→1.</p>{pre(EX_WAVE_TOGGLE)}""",
 ex=EX_WAVE_TOGGLE, starter=ST_WAVE_TOGGLE,
 check_wave=dict(signal="q", changes="0101")),
 dict(id="m7l3", module="7. Testbenches", title="Coverage-driven testing",
 body=f"""<h2>Coverage</h2><p>The simulator counts executed
<b>case branches</b> and prints [coverage] after every run. Starter covers
1/4; drive the FSM through <b>IDLE, RUN, DONE</b> (3 branches) to pass.</p>
{pre(EX_FSM_V)}{pre(EX_FSM_COV_TB)}""", ex=EX_FSM_V,
 starter=EX_FSM_V + "\n" + EX_FSM_COV_TB, require_coverage=3),
 dict(id="sv1", module="8. SystemVerilog", title="logic & new types", body=f"""
<h2><code>logic</code></h2><p>4-state, replaces wire+reg in most code.
Run with Icarus (auto -g2012); the built-in engine does not parse SV.</p>
{pre(EX_SV_LOGIC)}""", ex=EX_SV_LOGIC,
 quiz=[_L(q="SystemVerilog logic is…", options=["2-state",
        "4-state (0,1,x,z)", "only for clocks", "VHDL"], a=1, why=""),
       _L(q="Type replacing BOTH wire and reg:", options=["bit", "wire",
        "logic", "int"], a=2, why="")]),
 dict(id="sv2", module="8. SystemVerilog", title="always_ff / always_comb",
 body=f"""<h2>Intent-Typed Processes</h2>{pre(EX_SV_FF)}<p>always_ff = flops
only; always_comb = combinational only, no latches, full sensitivity —
checked by tools.</p>""", ex=EX_SV_FF,
 quiz=[_L(q="Blocking = inside always_ff is…", options=["required",
        "an intent violation tools flag", "faster", "fine"], a=1, why="")]),
 dict(id="sv3", module="8. SystemVerilog", title="enum FSMs & unique case",
 body=f"""<h2>Enumerated FSMs</h2>{pre(EX_SV_ENUM)}<p>{cd("unique case")}
asks the tool to prove full, parallel branching.</p>""", ex=EX_SV_ENUM,
 quiz=[_L(q="unique case asks the tool to…", options=["optimize area",
        "prove no missing/overlapping branches", "add a clock", "skip sim"],
        a=1, why="")]),
 dict(id="mem1", module="9. Memory & FIFO", title="Inferred RAM", body=f"""
<h2>Inferred RAM</h2><p>Clocked write into an array infers memory; read
style picks distributed RAM (async read) vs BRAM (sync read). <b>Run</b>
it — arrays and for-loops work on the built-in engine — and open the
<b>Memory tab</b> for a live hex dump.</p>{pre(EX_RAM)}""", ex=EX_RAM,
 quiz=[_L(q="Clocked write into an array infers…", options=["pure logic",
        "memory (flops or BRAM)", "a FIFO", "nothing"], a=1, why=""),
       _L(q="Sync write + async read maps to…", options=["BRAM",
        "distributed/LUT RAM", "registers only", "external"], a=1, why="")]),
 dict(id="mem2", module="9. Memory & FIFO", title="Register files",
 body="""<h2>Small Memories = Logic</h2><p>A few words → flops + muxes;
kilobits → BRAM. Keep one write clock (stay synchronous). Try the RAM
example with the step debugger watching the Memory tab.</p>""", ex=EX_RAM),
 dict(id="mem3", module="9. Memory & FIFO", title="Synchronous FIFO",
 body=f"""<h2>Sync FIFO</h2><p>Circular buffer + pointers + count. Watch
{cd("full")}/{cd("empty")} guards — unguarded writes/reads corrupt data.</p>
{pre(EX_FIFO)}""", ex=EX_FIFO,
 quiz=[_L(q="Writing while full…", options=["wraps safely",
        "silently corrupts — must be guarded", "raises count", "resets"],
        a=1, why=""),
       _L(q="FIFO count changes when…", options=["every clock",
        "exactly one of rd/wr succeeds", "reset asserts", "a pointer wraps"],
        a=1, why="")]),
 dict(id="mem4", module="9. Memory & FIFO", title="CDC & two-flop sync",
 body=f"""<h2>Clock Domain Crossing</h2><p>Never sample cross-domain
directly — metastability. Two back-to-back flops: first may go metastable,
second settles. Multi-bit buses need handshakes/async FIFOs, not syncs
(bits skew). See also <b>Classic Circuits → Async FIFO</b>.</p>
{pre(EX_CDC)}""", ex=EX_CDC,
 quiz=[_L(q="The first sync flop may…", options=["be skipped",
        "go metastable", "clock the source", "block data"], a=1,
        why="That's why the second exists."),
       _L(q="Multi-bit buses cross with…", options=["a two-flop sync alone",
        "handshakes or async FIFOs", "wider flops", "more clocks"], a=1,
        why="")]),
 dict(id="bh1", module="10. Bug Hunt", title="The swap that didn't", body=f"""
<h2>Bug Hunt: = vs &lt;=</h2><p>This swap doesn't swap. Load, Run, study
the console, fix — the console check passes automatically.</p>""",
 starter=BUG1, check_console=[r"a=2 b=1", r"a=1 b=2"],
 bughint="In clocked blocks use <=. Blocking = evaluates immediately, so "
         "both end up with the old b."),
 dict(id="bh2", module="10. Bug Hunt", title="The latch in the case",
 body="""<h2>Bug Hunt: incomplete case → latch</h2><p>Check reports a wrong
row. Generate the <b>Truth Table</b> and look carefully…</p>""",
 starter=BUG2, check=dict(module="latchy", inputs=["sel"],
                          outputs={"y": "10"}),
 bughint="A case without default keeps its OLD value (a latch). Add "
         "default: y = 1'b0;"),
 dict(id="bh3", module="10. Bug Hunt", title="The race on cnt", body=f"""
<h2>Bug Hunt: two writers</h2><p>Reset does nothing — two always blocks
drive one reg. Fix so the console shows c=0 then c=3.</p>""", starter=BUG3,
 check_console=[r"c=0", r"c=3"],
 bughint="One register, one writer: merge the blocks — if (rst) ... else "
         "cnt <= cnt + 1;"),
 dict(id="bh4", module="10. Bug Hunt", title="Precedence surprise",
 body="""<h2>Bug Hunt: operator precedence</h2><p>Intended
(a &amp; b) | c. One truth-table row betrays the bug.</p>""", starter=BUG4,
 check=dict(module="precedence", inputs=["a", "b", "c"],
            outputs={"y": "01010111"}),
 bughint="& binds tighter than ^: code computes (a&b)^c. Parenthesize."),
 dict(id="v1", module="11. Verification Lab", title="Golden models (Python)",
 body=f"""<h2>Reference Models &amp; Scoreboarding</h2><p>Industry
verification compares hardware against an independent <b>reference
model</b>. Here the model is a <b>Python function</b>: press <b>Check</b>
and the app drives every input combination through your design and calls
the model with the same inputs.</p>{pre(EX_ALU)}<p>Sequential designs: add
<code>cycles=1</code> (one clock per vector) — see the next lesson.</p>""",
 ex=EX_ALU,
 check_model=dict(module="alu4", inputs=["a", "b", "op"], outputs=["y"],
                  model=lambda a, b, op: [a + b, a - b, a & b, a | b][op])),
 dict(id="v2", module="11. Verification Lab", title="Sequential golden model",
 body=f"""<h2>Clocked Golden Models</h2><p>With <code>cycles=1</code> the
grader pulses the clock once per vector and compares after the edge.</p>
{pre(EX_GRAY)}<p>The model is pure Python — it never simulates Verilog,
which is what makes it an independent check.</p>""", ex=EX_GRAY,
 check_model=dict(module="gray_reg", inputs=["d"], outputs=["q"],
                  model=lambda d: (d ^ (d >> 1)) & 0xF, cycles=1)),
 dict(id="v3", module="11. Verification Lab", title="Immediate assertions",
 body=f"""<h2>Assertions</h2><p>{cd("assert (expr) else $error(…);")}
executes every step; violations are counted and reported. Assertions turn
"looks right" into "provably never wrong". Weighted-random helpers
{cd("$prob(p)")} and {cd("$urandom(lo,hi)")} (seeded = reproducible) make
stimulus dense.</p>{pre(EX_ARB)}<p><b>Exercise:</b> Run the starter (watch
the violation), fix the bug, press <b>Check</b> (needs 0 failures).</p>""",
 ex=EX_ARB, starter=EX_ARB, check_assert=dict(min_pass=78, max_fail=0)),
 dict(id="v4", module="11. Verification Lab", title="Properties (req→ack)",
 body=f"""<h2>Sequence Properties</h2><p>SVA thinking, tiny syntax — a
<b>response property</b>: whenever {cd("valid")} rises, {cd("ready")} must
assert within N ticks, checked over the recorded waveform. Invariants:
{cd("when")} → {cd("expr")} every sample.</p>{pre(EX_HANDSHAKE)}
<p><b>Exercise:</b> Run (fails: ready ~10 cycles late), tune latency ≤ 4 —
the property must also be <b>exercised</b> ≥ 4 times.</p>""", ex=EX_HANDSHAKE,
 check_props=[dict(after="valid", expr="ready", within=50, min_occ=4)]),
 dict(id="v5", module="11. Verification Lab", title="Test plans & cover bins",
 body=f"""<h2>Coverage-Driven Verification</h2><p>A <b>test plan</b> names
scenarios that must occur; each is a predicate over every recorded sample
(plus pairwise cross-coverage). Checklist prints after Run.</p>
{pre(EX_FIFO_PLAN)}<p><b>Exercise:</b> write the four scenarios until the
checklist is all green, then <b>Check</b>. Deciding <i>what to test</i> and
proving you tested it is the actual job.</p>""", ex=EX_FIFO_PLAN,
 starter=EX_FIFO_PLAN,
 check_plan=[dict(name="full", desc="reach full", expr="full"),
             dict(name="empty", desc="drain to empty", expr="empty"),
             dict(name="simul", desc="wr+rd same cycle",
                  expr="wr && rd && !empty"),
             dict(name="guard", desc="write attempted while full",
                  expr="wr && full")]),
 dict(id="pl1", module="12. Pipelining", title="Pipelining concepts", body="""
<h2>Pipelining</h2><p>Stages overlap: throughput approaches
<b>1 item/cycle</b> after k−1 fill cycles; per-item latency unchanged.
Hazards: <b>structural</b> (resource conflict), <b>data</b> (result in
flight → stall/forward), <b>control</b> (branch → flush).</p>""",
 quiz=[_L(q="Steady-state throughput of a k-stage pipeline:",
        options=["1/k per cycle", "1 per cycle", "k per cycle",
        "1 per k cycles"], a=1, why="One completes every cycle."),
       _L(q="Load-use hazard fixed by…", options=["more registers",
        "a stall or forwarding", "a wider clock", "dropping MEM"], a=1,
        why=""),
       _L(q="A branch flush squashes…", options=["nothing",
        "younger in-flight instructions", "the whole memory",
        "a pipeline register"], a=1, why="")]),
 dict(id="pl2", module="12. Pipelining", title="Pipeline lab (stalls)",
 body=f"""<h2>Pipeline Lab</h2><p>A 4-stage pipeline streams items in a
loop; "prewash" items stall the front end. The <b>Pipeline tab</b> renders
stage occupancy per cycle — stall columns tinted amber.</p>
{pre(EX_PIPELINE)}""", ex=EX_PIPELINE,
 pipeline=dict(clk="clk", stages="stages", stall="stall",
               names=["LOAD", "W1", "W2", "W3", "W4"])),
 dict(id="pl3", module="12. Pipelining", title="Exercise: fix the stall",
 body=f"""<h2>Parameterize the Stall</h2><p>The starter ships with
<code>STALL_CYCLES = 0</code>: only 7 stall samples. Set the parameter to
<b>2</b> and re-run: bubbles appear and the console reports
<code>stalls=15</code>. Press <b>Check</b>.</p>""",
 starter=EX_PIPELINE.replace("parameter STALL_CYCLES = 2",
                             "parameter STALL_CYCLES = 0  // TODO: 2"),
 pipeline=dict(clk="clk", stages="stages", stall="stall",
               names=["LOAD", "W1", "W2", "W3", "W4"]),
 check_console=[r"stalls=15"]),
 dict(id="cc1", module="13. Classic Circuits", title="LFSR", body=f"""
<h2>Linear-Feedback Shift Register</h2><p>XOR taps back into the shift
input; a maximal tap set cycles 2ⁿ−1 states (never zero). Used for
scramblers, PRBS, CRCs, adderless counters.</p>{pre(EX_LFSR)}
<p><b>Exercise:</b> TB shifts 255 times from seed 1 — maximal taps return
to the seed (<code>period=1</code>).</p>""", ex=EX_LFSR, starter=EX_LFSR,
 check_console=[r"period=1"]),
 dict(id="cc2", module="13. Classic Circuits", title="Serial CRC-8", body=f"""
<h2>CRC = division circuit</h2><p>Serial CRC-8 computes polynomial division
by x⁸+x²+x+1 (poly 0x07). The classic property: message+CRC fed back
through the same circuit leaves the register at <b>zero</b> — the TB uses
two instances to prove your sender, no golden numbers.</p>{pre(EX_CRC)}""",
 ex=EX_CRC, starter=EX_CRC, check_console=[r"ok=1"]),
 dict(id="cc3", module="13. Classic Circuits", title="Bit-serial multiplier",
 body=f"""<h2>Shift-and-Add Multiply</h2><p>Pencil-and-paper binary
multiplication in hardware: for each bit of b, add the shifted
multiplicand; shift every cycle. 4 cycles for 4×4.</p>{pre(EX_MUL)}
<p><b>Exercise:</b> 13 × 11 = <b>143</b>. Implement the accumulate line in
the starter, Run, Check.</p>""", ex=EX_MUL,
 starter=EX_MUL.replace("    if (b[count]) p <= p + mc;",
                        "    // TODO: accumulate when b[count]"),
 check_console=[r"p=143"]),
 dict(id="cc4", module="13. Classic Circuits", title="Async FIFO (Gray)",
 body=f"""<h2>Asynchronous FIFO</h2><p>Binary pointers sampled mid-transition
are metastability landmines. Fix: <b>Gray-coded</b> pointers (one bit
changes per crossing) synchronized by two flops in the destination domain;
full/empty become Gray decodings. Run it: two unrelated clocks, three bytes
cross <b>in order</b>.</p>{pre(EX_AFIFO)}""", ex=EX_AFIFO),
 dict(id="m8l1", module="14. Sandbox & Beyond", title="The toolbox", body=f"""
<h2>The Toolbox</h2><ul>
<li><b>Schematic</b> — live mode: input ports are <b>toggle switches</b>;
click and watch values ripple rank-by-rank. Critical path highlight, Yosys
gate view, FPGA stats, ▶ Replay of the last run's events.</li>
<li><b>Truth Table → K-map</b> — click a term → its gates highlighted.</li>
<li><b>Waveform</b> — wheel zoom, drag pan, click cursors A/B (Δt +
per-signal values), right-click → Signal manager.</li>
<li><b>Memory</b> — hex dump + CPU-II disassembler. <b>Framebuffer</b> /
<b>Pipeline</b> tabs render VGA/pipeline lessons.</li>
<li><b>Tools</b> — mini-assembler, exam mode, random exercise.
<b>Simulate</b> — step debugger, lint, TB generator, equivalence, VCD.</li>
</ul>""", ex=EX_OPS),
 dict(id="m8l2", module="14. Sandbox & Beyond", title="Where to go next",
 body="""<h2>Where to Go Next</h2><ul><li><b>HDLBits</b> — drills.</li>
<li><b>ASIC World</b>, <b>VHDLwhiz</b>, <b>fpga4fun</b>.</li>
<li><i>Digital Design and Computer Architecture</i> — Harris &amp; Harris.</li></ul>
<h3>Projects</h3><ol><li>Stopwatch · 2) UART+TX FIFO · 3) SPI peripheral ·
4) extend the CPU (flags, more ops, assembler macros).</li></ol>
<p>Open toolchain: <b>Yosys</b> + <b>nextpnr</b> + <b>GTKWave</b>. Good
luck — in hardware, <i>everything happens at once.</i></p>"""),
]

# ---- capstones -------------------------------------------------------------
CAPSTONES = [
 dict(id="cap_uart", title="UART Transceiver",
  blurb="Bit-serial transmitter and receiver; each clock = one bit period.",
  stage_titles=["Bit-tick counter", "Fixed-byte serializer",
                "TX with send/busy + software receiver", "UART receiver"],
  briefs=["<p>Build a mod-10 counter that later stages use to count frame "
          "bits. Goal: console shows tick cycling 4,5,6,…,0.</p>",
          "<p>Serialize <code>8'hA6</code> LSB-first with start/stop bits; "
          "the TB prints the exact 11-bit frame.</p>",
          "<p>Real TX interface: <code>send</code> latches "
          "<code>din</code>, <code>busy</code> frames the transfer. The TB "
          "recovers <code>3C</code> sampling bit centers.</p>",
          "<p>Detect the start bit, shift 8 bits LSB-first, pulse "
          "<code>done</code>. TB drives a line carrying <code>0x96</code>.</p>"],
  todos=["add the frame counter n: 0..9 with wrap",
         "replace the counter with sh + n and the case statement",
         "add send/busy handshake and the TB software receiver",
         "write the receiver module uart_rx"],
  solutions=[UART_S1, UART_S2, UART_S3, UART_S4],
  checks=[dict(check_console=[r"tick=4", r"tick=5", r"tick=6", r"tick=0"]),
          dict(check_console=[r"tx=0", r"tx=0", r"tx=1", r"tx=1", r"tx=0",
              r"tx=0", r"tx=1", r"tx=0", r"tx=1", r"tx=1", r"tx=0"]),
          dict(check_console=[r"rx=3c", r"busy=1", r"idle=1"]),
          dict(check_console=[r"dout=96", r"done=1"])]),
 dict(id="cap_traf", title="Traffic-Light Controller",
  blurb="Moore FSM with timed phases and a pedestrian button.",
  stage_titles=["Phase timer", "Timed G→Y→R machine", "Pedestrian request",
                "Parameters + clearance"],
  briefs=["<p>Build a loadable down-counter; the TB loads 3 and watches it "
          "drain to zero.</p>",
          "<p>3-state Moore FSM: green 6, yellow 3, red 6 cycles, repeat.</p>",
          "<p>Requirements creep: a button latches a request cutting green "
          "short after 3 cycles; <code>walk</code> high during red.</p>",
          "<p>Phase lengths become parameters plus a one-cycle all-red "
          "clearance before walk drops.</p>"],
  todos=["build the loadable down-counter",
         "add the 3-state FSM with timed case branches",
         "add btn/ped_req latch, early green exit and walk",
         "parameterize phases and add the clearance cycle"],
  solutions=[TRAF_S1, TRAF_S2, TRAF_S3, TRAF_S4],
  checks=[dict(check_console=[r"t1 cnt=0", r"t2 cnt=0"]),
          dict(check_console=[r"main=2", r"main=1", r"main=0", r"main=2"]),
          dict(check_console=[r"m=2 w=0", r"m=1 w=0", r"m=0 w=1", r"m=2 w=0"]),
          dict(check_console=[r"m=2 w=0", r"m=1 w=0", r"m=0 w=0", r"m=0 w=1",
              r"m=2 w=0"])]),
 dict(id="cap_spi", title="SPI Master",
  blurb="Mode 0 SPI: CS framing, divided SCLK, MSB-first MOSI, full duplex.",
  stage_titles=["Clock-enable tick", "SCLK + CS framing",
                "MOSI data + loopback check", "Full duplex with MISO"],
  briefs=["<p>SCLK runs at clk/4 — build the divide-by-4 tick first.</p>",
          "<p>Eight SCLK pulses framed by CS (idle high, low in frame); TB "
          "counts rising edges.</p>",
          "<p>Mode 0: MOSI changes on falling edges, sampled on rising. "
          "Loopback rebuilds 0xB7.</p>",
          "<p>Sample <code>miso</code> on every rising edge into "
          "<code>recv</code>, pulse done, run two transactions.</p>"],
  todos=["build the divide-by-4 tick",
         "add the run/n/div machine driving sclk + csen",
         "add sh/mosi shifting and the loopback TB",
         "add miso sampling into recv + done, and two transactions"],
  solutions=[SPI_S1, SPI_S2, SPI_S3, SPI_S4],
  checks=[dict(check_console=[r"tick", r"tick", r"tick", r"tick"]),
          dict(check_console=[r"cs=0"] + [r"rise"] * 8 + [r"cs=1"]),
          dict(check_console=[r"bit=1", r"bit=0", r"bit=1", r"bit=1",
              r"bit=0", r"bit=1", r"bit=1", r"bit=1", r"recv=b7"]),
          dict(check_console=[r"r=b7", r"r=5a"])]),
 dict(id="cap_cpu", title="Minimal CPU (fetch/decode/execute)",
  blurb="8-bit-instruction CPU: PC+ROM, decode, accumulator, data RAM, jumps.",
  stage_titles=["PC + fetch", "Decode", "Execute LDI",
                "Data RAM + arithmetic", "Jumps + a real program"],
  briefs=["<p>Instruction = {op[2:0], arg[4:0]}. Build the fetch loop: PC "
          "register + combinational ROM (case on pc). HALT freezes the PC.</p>",
          "<p>Decode = inspecting instr[7:5]; the TB prints op names.</p>",
          "<p>LDI loads a 5-bit immediate into the accumulator.</p>",
          "<p>Add a RAM array with STD/LDD/ADD and a peek debug port.</p>",
          "<p>Add JZ/JMP and assemble a countdown loop (3→2→1→0→HALT).</p>"],
  todos=["build PC + ROM and make HALT freeze the PC",
         "keep fetch, let the TB decode and print op names",
         "add the accumulator and LDI execution",
         "add ram[] with STD/LDD/ADD and the peek debug port",
         "add JZ/JMP and enter the countdown program"],
  solutions=[CPU_S1, CPU_S2, CPU_S3, CPU_S4, CPU_S5],
  checks=[dict(check_console=[r"pc=0", r"pc=1", r"pc=2", r"pc=2"]),
          dict(check_console=[r"op=LDI", r"op=LDI", r"op=HALT"]),
          dict(check_console=[r"acc=0", r"acc=5", r"acc=3"]),
          dict(check_console=[r"acc=12", r"peek=c"]),
          dict(check_console=[r"s acc=3", r"mid acc=2", r"end acc=0 pc=7"])]),
 dict(id="cap_vga", title="VGA Framebuffer",
  blurb="Scaled 64×48 raster: sync counters, then an RGB pattern you can SEE.",
  stage_titles=["Sync counters", "Test pattern + framebuffer"],
  briefs=["<p>One clock = one pixel. Wrap-around x (0..63), y (0..47), "
          "active-low sync, video window. TB counts hsync falls over one "
          "frame — must be <b>48</b>, y ends at 0.</p>",
          "<p>Add r/g/b: red border, yellow/blue checker (x[3]^y[3]). After "
          "Run the <b>Framebuffer tab</b> rebuilds the picture from the "
          "recorded waveform.</p>"],
  todos=["build x/y counters with sync pulses",
         "add the border + checker RGB pattern"],
  solutions=[VGA_S1, VGA_S2],
  checks=[dict(check_console=[r"h=48", r"y=0"]),
          dict(check_console=[r"frame done"],
               framebuffer=dict(x="x", y="y", r="r", g="g", b="b",
                                w=64, h=48))]),
 dict(id="cap_cpu2", title="CPU II: Assembler & Subroutines",
  blurb="Boot a CPU from an assembler-produced $readmemh ROM; stack + CALL/RET.",
  stage_titles=["Assembler + ROM boot", "Stack, CALL/RET, OUT"],
  briefs=["<p>ROM loads via <code>$readmemh(\"rom.hex\", rom)</code>. "
          "<b>Tools → Mini-assembler</b>: assemble LDI 3 / STD 0 / loop: "
          "LDD 0 / JZ done / SUB 1 / STD 0 / JMP loop / done: HALT, press "
          "<b>Write rom.hex</b>, then <b>Run</b>. Expect acc=0, pc=7.</p>",
          "<p>Add CALL (push pc+1 at ram[sp]), RET, OUT. Program: LDI 3 / "
          "STD 0 / LDI 4 / ADD 0 / CALL 12 / OUT / HALT; subroutine at 12: "
          "STD 1 / LDD 1 / ADD 1 / RET. Expect out=14, acc=14.</p>"],
  todos=["boot from rom.hex via the assembler workflow",
         "add sp/CALL/RET/OUT and the subroutine program"],
  solutions=[CPU2_S1, CPU2_S2],
  checks=[dict(check_console=[r"acc=0", r"pc=7"],
               files={"rom.hex": "03\n20\n30\n67\n51\n20\n72\n10\n"}),
          dict(check_console=[r"out=14", r"acc=14"],
               files={"rom.hex": "03\n20\n04\n40\n9c\nb0\n10\n00\n00\n00\n"
                                 "00\n00\n21\n31\n41\na0\n"})]),
 dict(id="cap_i2c", title="I2C Master",
  blurb="Open-drain two-wire bus: START/STOP, phase-tick bits, ACKs, bursts.",
  stage_titles=["START + one byte + ACK", "Burst writes + slave memory"],
  briefs=["<p>Phase machine per bit: setup → sample (SCL high) → hold → "
          "fall. START = SDA falling while SCL high. Open-drain modelled as "
          "<code>assign sda = sda_m &amp; sda_s;</code>. Slave must print "
          "<code>byte=a5 ack=1</code>.</p>",
          "<p>Two bytes back-to-back (A5, 3C): master waits !busy; slave "
          "stores and TB prints <code>m0=a5 m1=3c</code>.</p>"],
  todos=["build the START/byte/ACK/STOP phase FSM",
         "add back-to-back transactions and slave storage"],
  solutions=[I2C_S1, I2C_S2],
  checks=[dict(check_console=[r"byte=a5", r"ack=1"]),
          dict(check_console=[r"byte=a5", r"byte=3c", r"m0=a5", r"m1=3c"])]),
]

def build_cap_tasks():
    tasks = []
    for c in CAPSTONES:
        n = len(c["solutions"])
        for i in range(n):
            if i:
                starter = (c["solutions"][i - 1] +
                    "\n// ===== %s : STAGE %d/%d =====\n// TODO: %s\n"
                    % (c["title"], i + 1, n, c["todos"][i]))
            else:
                head, tbpart = c["solutions"][0].split("module tb", 1)
                starter = (head + "// ===== STAGE 1 =====\n// TODO: " +
                           c["todos"][0] +
                           "\n// (full TB included below -- study, then Run)\n"
                           "module tb" + tbpart)
            t = dict(id="%s%d" % (c["id"], i + 1),
                     module="Capstone · " + c["title"],
                     title=c["stage_titles"][i],
                     body=("<h2>%s — stage %d/%d</h2><p><i>%s</i></p>%s"
                           "<p><b>Load Starter</b> continues from the previous "
                           "stage. <b>Run</b> to test, <b>Check</b> to grade, "
                           "<b>Solution</b> if stuck.</p>"
                           % (html.escape(c["title"]), i + 1, n,
                              html.escape(c["blurb"]), c["briefs"][i])),
                     starter=starter, solution=c["solutions"][i], cap=bool(i))
            t.update(c["checks"][i])
            tasks.append(t)
    return tasks

TASKS = LESSONS + build_cap_tasks()

# ══════════════════════════ SIMULATOR CORE ══════════════════════════
class HDLSimError(Exception):
    pass

_TOKEN_RE = re.compile(r"""(?P<ws>\s+)|(?P<num>\d+'\s*[bBoOdDhH][0-9a-fA-FxXzZ_]+|\d+)|(?P<sys>\$[A-Za-z_]\w*)|(?P<str>"(?:[^"\\\n]|\\.)*")|(?P<id>[A-Za-z_]\w*)|(?P<op><=|>=|===|!==|==|!=|&&|\|\||<<|>>|[+\-*/%<>=!~&|^?:;,#()\[\]{}.@'])""", re.X)
_TS_RE = re.compile(r"`timescale\s+\d+\s*([munpf]?s)\s*/")
_DIRLINE_RE = re.compile(r"^\s*`.*$", re.M)
_NUM_RE = re.compile(r"(\d+)'\s*([bBoOdDhH])([0-9a-fA-FxXzZ_]+)$")

def preprocess(text):
    m = _TS_RE.search(text)
    unit = m.group(1) if m else "ns"
    text = _DIRLINE_RE.sub(" ", text)
    return re.sub(r"`\w+", " ", text), unit

def tokenize(text):
    toks, i, line = [], 0, 1
    while i < len(text):
        if text[i] == "\n":
            line += 1; i += 1; continue
        m = _TOKEN_RE.match(text, i)
        if not m:
            raise HDLSimError(f"line {line}: unexpected character {text[i]!r}")
        if m.lastgroup != "ws":
            toks.append((m.lastgroup, m.group(0), line))
        i = m.end()
    return toks

def num_literal(s):
    m = _NUM_RE.fullmatch(s.strip())
    if m:
        w = min(int(m.group(1)), 64)
        base = {"b": 2, "o": 8, "d": 10, "h": 16}[m.group(2).lower()]
        digs = "".join("0" if c in "xXzZ" else c
                       for c in m.group(3).replace("_", ""))
        return int(digs, base), w
    return int(s), 32

VERILOG_PRIMS = {"and", "nand", "or", "nor", "xor", "xnor", "not", "buf"}
_DECL_KW = {"input", "output", "inout", "wire", "reg", "tri", "integer",
            "parameter", "localparam", "assign", "always", "initial",
            "module", "endmodule", "begin", "end", "if", "else", "case",
            "casex", "casez", "endcase", "default", "function", "task",
            "for", "assert"}

class Port:
    __slots__ = ("name", "dir", "width")
    def __init__(self, n, d, w=1):
        self.name, self.dir, self.width = n, d, w

class Module:
    def __init__(self, name):
        self.name = name; self.params = []; self.ports = []; self.nets = {}
        self.assigns = []; self.procs = []; self.threads = []; self.insts = []

class Parser:
    def __init__(self, toks):
        self.t, self.i = toks, 0
    def peek(self, k=0):
        j = self.i + k
        return self.t[j] if j < len(self.t) else (None, None, 0)
    def next(self):
        tk = self.peek(); self.i += 1; return tk
    def at(self, v): return self.peek()[1] == v
    def accept(self, v):
        if self.at(v): self.next(); return True
        return False
    def expect(self, v):
        k, val, ln = self.next()
        if val != v:
            raise HDLSimError(f"line {ln}: expected '{v}', found '{val}'")
    def err(self, m): raise HDLSimError(f"line {self.peek()[2]}: {m}")
    # expressions
    def parse_expr(self): return self.p_or()
    def p_or(self):
        l = self.p_and()
        while self.at("||"): self.next(); l = ("|", l, self.p_and())
        return l
    def p_and(self):
        l = self.p_bor()
        while self.at("&&"): self.next(); l = ("&", l, self.p_bor())
        return l
    def p_bor(self):
        l = self.p_bxor()
        while self.peek()[1] == "|": self.next(); l = ("|", l, self.p_bxor())
        return l
    def p_bxor(self):
        l = self.p_band()
        while self.peek()[1] in ("^", "~^", "^~"):
            op = self.next()[1]; l = ("^" if op == "^" else "~^", l, self.p_band())
        return l
    def p_band(self):
        l = self.p_eq()
        while self.peek()[1] == "&": self.next(); l = ("&", l, self.p_eq())
        return l
    def p_eq(self):
        l = self.p_rel()
        while self.peek()[1] in ("==", "!=", "===", "!=="):
            op = self.next()[1]
            l = ("ne" if op in ("!=", "!==") else "eq", l, self.p_rel())
        return l
    def p_rel(self):
        l = self.p_shift()
        while self.peek()[1] in ("<", "<=", ">", ">="):
            op = self.next()[1]
            l = ({"<": "lt", "<=": "le", ">": "gt", ">=": "ge"}[op],
                 l, self.p_shift())
        return l
    def p_shift(self):
        l = self.p_add()
        while self.peek()[1] in ("<<", ">>"):
            op = self.next()[1]; l = (op, l, self.p_add())
        return l
    def p_add(self):
        l = self.p_mul()
        while self.peek()[1] in ("+", "-"):
            op = self.next()[1]; l = (op, l, self.p_mul())
        return l
    def p_mul(self):
        l = self.p_unary()
        while self.peek()[1] in ("*", "/", "%"):
            op = self.next()[1]; l = (op, l, self.p_unary())
        return l
    def p_unary(self):
        v = self.peek()[1]
        if v in ("!", "~", "-", "+", "&", "|", "^"):
            self.next(); o = self.p_unary()
            if v == "+": return o
            if v in ("!", "~", "-"): return ({"!": "lnot", "~": "not",
                                              "-": "neg"}[v], o)
            return ("red", v, o)
        return self.p_postfix()
    def p_postfix(self):
        a = self.p_primary()
        while self.at("["):
            self.next(); e1 = self.parse_expr()
            if self.accept(":"):
                e2 = self.parse_expr(); self.expect("]")
                a = ("part", a, e1, e2)
            else:
                self.expect("]"); a = ("bit", a, e1)
        return a
    def p_primary(self):
        k, v, ln = self.peek()
        if v == "(":
            self.next(); e = self.parse_expr(); self.expect(")"); return e
        if v == "{":
            self.next(); first = self.parse_expr()
            if self.at("{"):
                self.next(); inner = self.parse_expr()
                self.expect("}"); self.expect("}")
                return ("repl", first, inner)
            parts = [first]
            while self.accept(","): parts.append(self.parse_expr())
            self.expect("}"); return ("cat", parts)
        if k == "num":
            self.next(); val, w = num_literal(v); return ("num", val, w)
        if k == "str":
            self.next(); return ("str", v)
        if k == "sys":
            self.next()
            if v in ("$time", "$stime"): return ("time",)
            if v == "$random": return ("rnd",)
            if v == "$clog2":
                self.expect("("); e = self.parse_expr(); self.expect(")")
                return ("clog2", e)
            if v == "$urandom":
                self.expect("("); a = self.parse_expr(); self.expect(",")
                b = self.parse_expr(); self.expect(")")
                return ("urand", a, b)
            if v == "$prob":
                self.expect("("); p = self.parse_expr(); self.expect(")")
                return ("prob", p)
            raise HDLSimError(f"line {ln}: {v} not supported in expressions")
        if k == "id":
            self.next(); return ("var", v)
        self.err(f"unexpected '{v}' in expression")
    # statements
    def parse_assign_core(self):
        nm = self.next()
        if nm[0] != "id": self.err("bad assignment target")
        lhs = ("var", nm[1])
        if self.at("["):
            self.next(); e1 = self.parse_expr()
            if self.accept(":"):
                lhs = ("part", lhs, e1, self.parse_expr())
            else:
                lhs = ("bit", lhs, e1)
            self.expect("]")
        op = self.next()
        if op[1] not in ("=", "<="): self.err("expected '=' or '<='")
        return ("assign", lhs, self.parse_expr(), op[1] == "=")
    def parse_stmt(self):
        k, v, ln = self.peek()
        if v == ";": self.next(); return ("nop",)
        if v == "begin":
            self.next()
            if self.accept(":"): self.next()
            body = []
            while not self.at("end"):
                if self.i >= len(self.t): self.err("missing 'end'")
                body.append(self.parse_stmt())
            self.next(); return ("block", body)
        if v == "if":
            self.next(); self.expect("("); c = self.parse_expr()
            self.expect(")")
            th_ = self.parse_stmt(); el = None
            if self.at("else"): self.next(); el = self.parse_stmt()
            return ("if", c, th_, el)
        if v == "assert":
            self.next(); self.expect("("); c = self.parse_expr()
            self.expect(")")
            el = None
            if self.accept("else"): el = self.parse_stmt()
            return ("assert", c, el, ln)
        if v in ("case", "casex", "casez"):
            self.next(); self.expect("("); e = self.parse_expr()
            self.expect(")")
            items, dflt = [], None
            while not self.at("endcase"):
                if self.accept("default"):
                    self.expect(":"); dflt = self.parse_stmt()
                else:
                    labs = [self.parse_expr()]
                    while self.accept(","): labs.append(self.parse_expr())
                    self.expect(":"); items.append((labs, self.parse_stmt()))
                if self.i >= len(self.t): self.err("missing 'endcase'")
            self.next(); return ("case", e, items, dflt)
        if v == "for":
            self.next(); self.expect("(")
            init = self.parse_assign_core(); self.expect(";")
            cond = self.parse_expr(); self.expect(";")
            step = self.parse_assign_core(); self.expect(")")
            return ("for", init, cond, step, self.parse_stmt())
        if v == "#":
            self.next(); kn, nv, _ = self.next()
            if kn != "num": self.err("# delay must be a plain integer")
            st = None
            if not self.at(";"): st = self.parse_stmt()
            self.accept(";"); return ("delay", int(nv), st)
        if k == "sys":
            self.next(); args = []
            if self.accept("("):
                if not self.at(")"):
                    args.append(self.parse_expr())
                    while self.accept(","): args.append(self.parse_expr())
                self.expect(")")
            self.accept(";"); return ("sys", v, args)
        return self.parse_assign_core()
    # module
    def const_val(self, ast, cenv): return _const_eval(ast, cenv)
    def parse_range(self, cenv):
        self.expect("["); msb = self.const_val(self.parse_expr(), cenv)
        self.expect(":"); lsb = self.const_val(self.parse_expr(), cenv)
        self.expect("]"); return abs(msb - lsb) + 1
    def parse_module(self):
        self.expect("module"); name = self.next()[1]
        mod = Module(name); cenv = {}
        if self.accept("#"):
            self.expect("(")
            while not self.at(")"):
                self.accept("parameter"); pn = self.next()
                if pn[0] != "id": self.err("bad parameter name")
                self.expect("="); ast = self.parse_expr()
                mod.params.append((pn[1], ast))
                cenv[pn[1]] = self.const_val(ast, cenv)
                if not self.accept(","): break
            self.expect(")")
        last = None
        if self.accept("("):
            while not self.at(")"):
                if self.peek()[1] in ("input", "output", "inout"):
                    d = self.next()[1]
                elif last: d = last
                else: self.err("port without direction")
                last = d
                while self.peek()[1] in ("wire", "reg", "signed", "tri"):
                    self.next()
                w = self.parse_range(cenv) if self.at("[") else 1
                pn = self.next()
                if pn[0] != "id": self.err("bad port name")
                if self.accept("="): self.parse_expr()
                mod.ports.append(Port(pn[1], d, w))
                mod.nets.setdefault(pn[1], [w, "wire", None, 1])
                if not self.accept(","): break
            self.expect(")")
        self.expect(";")
        while not self.at("endmodule"):
            k, v, ln = self.peek()
            if self.i >= len(self.t):
                raise HDLSimError(f"line {ln}: missing 'endmodule' in '{name}'")
            if v in ("input", "output", "inout"):
                d = self.next()[1]
                while self.peek()[1] in ("wire", "reg", "signed", "tri"):
                    self.next()
                w = self.parse_range(cenv) if self.at("[") else 1
                while True:
                    pn = self.next()[1]
                    mod.ports.append(Port(pn, d, w))
                    mod.nets.setdefault(pn, [w, "wire", None, 1])
                    if not self.accept(","): break
                self.expect(";")
            elif v in ("wire", "reg", "tri", "integer"):
                self.next()
                kind = "reg" if v in ("reg", "integer") else "wire"
                while self.peek()[1] == "signed": self.next()
                w = 32 if v == "integer" else (
                    self.parse_range(cenv) if self.at("[") else 1)
                while True:
                    pn = self.next()[1]
                    depth = self.parse_range(cenv) if self.at("[") else 1
                    init = self.parse_expr() if self.accept("=") else None
                    mod.nets[pn] = [w, kind, init, depth]
                    if not self.accept(","): break
                self.expect(";")
            elif v in ("parameter", "localparam"):
                self.next()
                while True:
                    pn = self.next()[1]; self.expect("=")
                    ast = self.parse_expr()
                    mod.params.append((pn, ast))
                    cenv[pn] = self.const_val(ast, cenv)
                    if not self.accept(","): break
                self.expect(";")
            elif v == "assign":
                self.next(); dl = 0
                if self.accept("#"):
                    kn, nv, _ = self.next()
                    dl = int(nv) if kn == "num" else 0
                if self.accept("{"):
                    names = []
                    while True:
                        names.append(self.next()[1])
                        if not self.accept(","): break
                    self.expect("}"); lhs = ("cat", names)
                else:
                    lhs = ("var", self.next()[1])
                self.expect("=")
                mod.assigns.append((lhs, self.parse_expr(), dl))
                self.expect(";")
            elif v == "always":
                self.next()
                if self.accept("@"):
                    self.expect("(")
                    if self.accept("*"):
                        sens = ("comb", "*")
                    else:
                        names, edges, comb = [], [], True
                        while True:
                            if self.peek()[1] in ("posedge", "negedge"):
                                comb = False; t2 = self.next()[1]
                                edges.append(("pos" if t2 == "posedge"
                                              else "neg", self.next()[1]))
                            else:
                                names.append(self.next()[1])
                            if self.accept("or"): continue
                            break
                        sens = ("edge", edges) if not comb else ("comb", names)
                    self.expect(")")
                    mod.procs.append((sens, self.parse_stmt()))
                elif self.at("#"):
                    d = self.parse_stmt()
                    mod.threads.append({"stmts": ("block",
                        [("delay", d[1], d[2])]), "loop": True})
                else:
                    self.err("always needs @(...) or #delay")
            elif v == "initial":
                self.next()
                mod.threads.append({"stmts": self.parse_stmt(), "loop": False})
            elif v == ";":
                self.next()
            elif k == "id" and v not in _DECL_KW:
                modname = self.next()[1]; povr = {}
                if self.accept("#"):
                    self.expect("(")
                    while not self.at(")"):
                        self.expect("."); pn = self.next()[1]
                        self.expect("(")
                        povr[pn] = self.parse_expr(); self.expect(")")
                        if not self.accept(","): break
                    self.expect(")")
                iname = self.next()[1]; self.expect("("); conns = []
                while not self.at(")"):
                    if self.accept("."):
                        f = self.next()[1]; self.expect("(")
                        conns.append((f, self.next()[1])); self.expect(")")
                    else:
                        conns.append((None, self.next()[1]))
                    if not self.accept(","): break
                self.expect(")"); self.expect(";")
                mod.insts.append((modname, iname, povr, conns))
            else:
                self.err(f"unsupported construct '{v}' (built-in subset)")
        self.next(); return mod
    def parse_top(self):
        out = {}
        while self.i < len(self.t):
            m = self.parse_module(); out[m.name] = m
        return out

def parse_design(text):
    text, unit = preprocess(text)
    toks = tokenize(text)
    if not toks: raise HDLSimError("source is empty")
    return Parser(toks).parse_top(), unit

def mask(w): return (1 << w) - 1

class Ctx:
    __slots__ = ("env", "consts", "widths", "time", "nb", "strict", "warned",
                 "rnd", "arrays", "cover", "written", "_changed", "_cur_nb",
                 "assert_fail", "assert_pass", "assert_total", "assert_msgs",
                 "assert_log", "rng")
    def __init__(self, env, consts, widths, strict=False, arrays=None):
        self.env, self.consts, self.widths = env, consts, widths
        self.time = 0; self.strict = strict; self.nb = None
        self.warned = set(); self.rnd = [0x2F6E2B1]
        self.arrays = arrays or {}; self.cover = {}; self.written = set()
        self._changed = False; self._cur_nb = True
        self.assert_fail = self.assert_pass = self.assert_total = 0
        self.assert_msgs = []; self.assert_log = []
        self.rng = random.Random(0xC0FFEE)

def _warn(ctx, m):
    if m not in ctx.warned: ctx.warned.add(m)

def ev(ast, ctx):
    k = ast[0]
    if k == "num": return ast[1], ast[2]
    if k == "str": return 0, 8
    if k == "var":
        n = ast[1]
        if n in ctx.consts: return ctx.consts[n]
        if n in ctx.env: return ctx.env[n], ctx.widths.get(n, 1)
        if ctx.strict:
            raise HDLSimError(f"'{n}' used where a constant is required")
        _warn(ctx, f"signal '{n}' is read but never driven (treated as 0)")
        return 0, 1
    if k == "time": return ctx.time, 32
    if k == "rnd":
        ctx.rnd[0] = (1103515245 * ctx.rnd[0] + 12345) & 0x7FFFFFFF
        return ctx.rnd[0], 32
    if k == "urand":
        lo, hi = ev(ast[1], ctx)[0], ev(ast[2], ctx)[0]
        if hi < lo: lo, hi = hi, lo
        return lo + (ctx.rng.randrange(hi - lo + 1) if hi > lo else 0), 32
    if k == "prob":
        p = max(0, min(100, ev(ast[1], ctx)[0]))
        return (1 if ctx.rng.randrange(100) < p else 0), 1
    if k == "clog2":
        v = ev(ast[1], ctx)[0]
        return (1 if v <= 1 else (v - 1).bit_length() + 1), 32
    if k == "not":
        v, w = ev(ast[1], ctx); return (~v) & mask(w), w
    if k == "neg":
        v, w = ev(ast[1], ctx); return (-v) & mask(w), w
    if k == "lnot": return (0 if ev(ast[1], ctx)[0] else 1), 1
    if k == "red":
        v, w = ev(ast[2], ctx)
        bits = [(v >> i) & 1 for i in range(w)]; op = ast[1]
        if op == "&": r = int(all(bits))
        elif op == "|": r = int(any(bits))
        else:
            r = 0
            for b in bits: r ^= b
        return r, 1
    if k == "?":
        return ev(ast[2] if ev(ast[1], ctx)[0] else ast[3], ctx)
    if k == "cat":
        v, w = 0, 0
        for part in ast[1]:
            pv, pw = ev(part, ctx); v = (v << pw) | pv; w += pw
        return v & mask(w), w
    if k == "repl":
        n = ev(ast[1], ctx)[0]
        if n < 1 or n > 64: raise HDLSimError("replication count out of range")
        v, w = ev(ast[2], ctx); rv, rw = 0, 0
        for _ in range(n): rv = (rv << w) | v; rw += w
        return rv, rw
    if k == "bit":
        base = ast[1]; i = ev(ast[2], ctx)[0]
        if base[0] == "var" and base[1] in ctx.arrays:
            w, d = ctx.arrays[base[1]]
            if i < 0 or i >= d:
                raise HDLSimError(f"{base[1]}[{i}] out of range")
            key = f"{base[1]}.{i}"
            return ctx.env.get(key, 0), ctx.widths.get(key, w)
        v, _ = ev(base, ctx); return (v >> i) & 1, 1
    if k == "part":
        v, _ = ev(ast[1], ctx)
        hi = ev(ast[2], ctx)[0]; lo = ev(ast[3], ctx)[0]
        if hi < lo: hi, lo = lo, hi
        w = hi - lo + 1
        return (v >> lo) & mask(w), w
    a, b = ev(ast[1], ctx), ev(ast[2], ctx); op = k
    if op in ("lt", "le", "gt", "ge"):
        return int({"lt": a[0] < b[0], "le": a[0] <= b[0],
                    "gt": a[0] > b[0], "ge": a[0] >= b[0]}[op]), 1
    if op == "eq": return int(a[0] == b[0]), 1
    if op == "ne": return int(a[0] != b[0]), 1
    w = max(a[1], b[1])
    if op == "&": return a[0] & b[0], w
    if op == "|": return a[0] | b[0], w
    if op in ("^", "~^"):
        r = a[0] ^ b[0]
        return ((r ^ mask(w)) & mask(w) if op == "~^" else r), w
    if op == "+": return (a[0] + b[0]) & mask(w), w
    if op == "-": return (a[0] - b[0]) & mask(w), w
    if op == "*": return (a[0] * b[0]) & mask(a[1] + b[1]), min(64, a[1] + b[1])
    if op == "/": return ((a[0] // b[0]) if b[0] else 0) & mask(w), w
    if op == "%": return ((a[0] % b[0]) if b[0] else 0) & mask(w), w
    if op == "<<": return (a[0] << min(b[0], 256)) & mask(a[1]), a[1]
    if op == ">>": return a[0] >> min(b[0], 256), a[1]
    raise HDLSimError(f"bad operator {op}")

def _resolve_lhs(ctx, lhs):
    if lhs[0] == "bit":
        base = lhs[1]
        if base[0] == "var" and base[1] in ctx.arrays:
            return ("var", "%s.%d" % (base[1], ev(lhs[2], ctx)[0]))
    return lhs

def write_lhs(ctx, lhs, val):
    if lhs[0] == "cat":
        total = sum(ctx.widths.get(n, 1) for n in lhs[1]); shift = total
        for n in lhs[1]:
            w = ctx.widths.get(n, 1); shift -= w
            _write_simple(ctx, ("var", n), (val >> shift) & mask(w))
        return
    if ctx.nb is not None and getattr(ctx, "_cur_nb", True):
        ctx.nb.append((_resolve_lhs(ctx, lhs), val)); return
    _write_simple(ctx, lhs, val)

def _write_simple(ctx, lhs, val):
    k = lhs[0]
    if k == "var":
        n = lhs[1]; nv = val & mask(ctx.widths.get(n, 1))
        if ctx.env.get(n) != nv: ctx.env[n] = nv; ctx._changed = True
        ctx.written.add(n); return
    if k == "bit":
        base = lhs[1]; i = ev(lhs[2], ctx)[0]
        if base[0] == "var" and base[1] in ctx.arrays:
            w, d = ctx.arrays[base[1]]
            if i < 0 or i >= d:
                raise HDLSimError(f"{base[1]}[{i}] out of range")
            key = f"{base[1]}.{i}"; nv = val & mask(w)
            if ctx.env.get(key) != nv: ctx.env[key] = nv; ctx._changed = True
            ctx.written.add(key); return
        n = base[1]; w = ctx.widths.get(n, 1); cur = ctx.env.get(n, 0)
        nv = (cur & ~(1 << i)) | ((val & 1) << i)
        if ctx.env.get(n) != nv: ctx.env[n] = nv; ctx._changed = True
        ctx.written.add(n); return
    if k == "part":
        n = lhs[1][1]
        hi = ev(lhs[2], ctx)[0]; lo = ev(lhs[3], ctx)[0]
        if hi < lo: hi, lo = lo, hi
        w = ctx.widths.get(n, 1); cur = ctx.env.get(n, 0)
        m = mask(hi - lo + 1) << lo
        nv = (cur & ~m) | ((val & mask(hi - lo + 1)) << lo)
        if ctx.env.get(n) != nv: ctx.env[n] = nv; ctx._changed = True
        ctx.written.add(n); return
    raise HDLSimError("bad assignment target")

def gen_stmts(stmts, ctx):
    for s in stmts: yield from gen_stmt(s, ctx)

def gen_stmt(s, ctx):
    k = s[0]
    if k == "nop": return
    if k == "block":
        yield from gen_stmts(s[1], ctx); return
    if k == "assign":
        ctx._cur_nb = s[3]; write_lhs(ctx, s[1], ev(s[2], ctx)[0])
        ctx._cur_nb = True; return
    if k == "if":
        yield from gen_stmt(s[2] if ev(s[1], ctx)[0] else (s[3] or ("nop",)),
                            ctx)
        return
    if k == "case":
        v = ev(s[1], ctx)[0]; hit = None
        for j, (labs, body) in enumerate(s[2]):
            for lab in labs:
                if ev(lab, ctx)[0] == v: hit = j; break
            if hit is not None: break
        if hit is not None:
            if len(s) > 4: ctx.cover.setdefault(s[4], set()).add(hit)
            yield from gen_stmt(s[2][hit][1], ctx)
        elif s[3] is not None:
            yield from gen_stmt(s[3], ctx)
        return
    if k == "for":
        ctx._cur_nb = True
        write_lhs(ctx, s[1][1], ev(s[1][2], ctx)[0])
        guard = 0
        while ev(s[2], ctx)[0]:
            guard += 1
            if guard > 100000:
                raise HDLSimError("for-loop limit exceeded")
            yield from gen_stmt(s[4], ctx)
            write_lhs(ctx, s[3][1], ev(s[3][2], ctx)[0])
        return
    if k == "assert":
        ctx.assert_total += 1
        if ev(s[1], ctx)[0]:
            ctx.assert_pass += 1
        else:
            ctx.assert_fail += 1; ctx.assert_log.append(s[3])
            if s[2] is not None:
                for item in gen_stmt(s[2], ctx):
                    if item[0] == "sys" and item[1] == "display":
                        a2 = item[2]; has = a2 and a2[0][0] == "str"
                        fmt = a2[0][1] if has else ""
                        rest = a2[1:] if has else a2
                        ctx.assert_msgs.append(
                            f"line {s[3]}: {_vfmt(fmt, rest, ctx).strip()}")
                    elif item[0] == "finish":
                        yield ("finish",)
        return
    if k == "delay":
        yield ("delay", s[1])
        if s[2]: yield from gen_stmt(s[2], ctx)
        return
    if k == "sys":
        name = s[1]
        if name in ("$display", "$write"):
            yield ("sys", "display", s[2], name == "$write")
        elif name in ("$finish", "$stop"): yield ("finish",)
        elif name in ("$readmemh", "$readmemb"):
            yield ("readmem", name, s[2])
        elif name.startswith("$dump"): return
        else:
            raise HDLSimError(f"{name} is not supported by the built-in "
                              "simulator")
        return
    raise HDLSimError(f"unsupported statement {k}")

def drive_comb(stmts, ctx):
    for item in gen_stmts(stmts if isinstance(stmts, list) else [stmts], ctx):
        if item[0] == "delay":
            raise HDLSimError("delay inside a combinational block")
        if item[0] == "sys":
            raise HDLSimError("system tasks only in testbench code")
        if item[0] == "finish":
            raise HDLSimError("$finish inside a comb block")

def _find_rom(fname):
    for d in ROM_DIRS:
        p = os.path.join(d, os.path.basename(fname))
        if os.path.exists(p): return p
    return None

def _do_readmem(name, args, ctx):
    if len(args) < 2 or args[0][0] != "str" or args[1][0] != "var":
        raise HDLSimError(f'{name} needs ("file", memory_name[, start])')
    path = _find_rom(args[0][1])
    if not path:
        raise HDLSimError(f"{name}: file '{args[0][1]}' not found "
                          f"(searched {ROM_DIRS})")
    memname = args[1][1]
    if memname not in ctx.arrays:
        raise HDLSimError(f"{name}: '{memname}' is not declared as an array")
    w, depth = ctx.arrays[memname]
    lo = ev(args[2], ctx)[0] if len(args) > 2 else 0
    hi = ev(args[3], ctx)[0] if len(args) > 3 else depth - 1
    base = 16 if name == "$readmemh" else 2
    with open(path, encoding="utf-8", errors="replace") as f:
        txt = re.sub(r"//[^\n]*|/\*.*?\*/", " ", f.read(), flags=re.S)
    addr, loaded = lo, 0
    for tok in txt.split():
        m = re.fullmatch(r"@([0-9a-fA-F]+)", tok)
        if m: addr = int(m.group(1), 16); continue
        try: v = int(tok, base)
        except ValueError:
            raise HDLSimError(f"{name}: bad token '{tok}' in {path}")
        if lo <= addr <= hi and 0 <= addr < depth:
            key = f"{memname}.{addr}"
            ctx.env[key] = v & mask(w); ctx.written.add(key); loaded += 1
        addr += 1
    if not loaded: raise HDLSimError(f"{name}: no data loaded from {path}")

class Program:
    def __init__(self):
        self.order = []; self.widths = {}; self.inits = {}; self.consts = {}
        self.assigns = []; self.comb = []; self.edges = []; self.threads = []
        self.inputs = []; self.outputs = []; self.arrays = {}
        self.cases = {}; self.case_at = {}

def _rename_ast(a, sm, cm):
    k = a[0]
    if k == "var": return ("var", sm.get(a[1], cm.get(a[1], a[1])))
    if k in ("num", "str", "time", "rnd"): return a
    if k in ("not", "neg", "lnot"): return (k, _rename_ast(a[1], sm, cm))
    if k == "red": return ("red", a[1], _rename_ast(a[2], sm, cm))
    if k == "clog2": return ("clog2", _rename_ast(a[1], sm, cm))
    if k == "urand":
        return ("urand", _rename_ast(a[1], sm, cm), _rename_ast(a[2], sm, cm))
    if k == "prob": return ("prob", _rename_ast(a[1], sm, cm))
    if k == "cat": return ("cat", [_rename_ast(p, sm, cm) for p in a[1]])
    if k == "repl":
        return ("repl", _rename_ast(a[1], sm, cm), _rename_ast(a[2], sm, cm))
    if k == "bit":
        return ("bit", _rename_ast(a[1], sm, cm), _rename_ast(a[2], sm, cm))
    if k == "part":
        return ("part", _rename_ast(a[1], sm, cm), _rename_ast(a[2], sm, cm),
                _rename_ast(a[3], sm, cm))
    return (k, _rename_ast(a[1], sm, cm), _rename_ast(a[2], sm, cm))

def _rename_lhs(lhs, sm):
    if lhs[0] == "cat": return ("cat", [sm.get(n, n) for n in lhs[1]])
    if lhs[0] == "var": return ("var", sm.get(lhs[1], lhs[1]))
    if lhs[0] in ("bit", "part"):
        base = lhs[1]
        nb = ("var", sm.get(base[1], base[1])) if base[0] == "var" else base
        return (lhs[0], nb) + tuple(_rename_ast(x, sm, {}) for x in lhs[2:])
    return lhs

def _rename_stmt(s, sm, cm):
    k = s[0]
    if k == "nop": return s
    if k == "block": return ("block", [_rename_stmt(x, sm, cm) for x in s[1]])
    if k == "assign":
        return ("assign", _rename_lhs(s[1], sm), _rename_ast(s[2], sm, cm),
                s[3])
    if k == "if":
        return ("if", _rename_ast(s[1], sm, cm), _rename_stmt(s[2], sm, cm),
                _rename_stmt(s[3], sm, cm) if s[3] else None)
    if k == "assert":
        return ("assert", _rename_ast(s[1], sm, cm),
                _rename_stmt(s[2], sm, cm) if s[2] else None, s[3])
    if k == "case":
        items = [([_rename_ast(l, sm, cm) for l in labs],
                  _rename_stmt(b, sm, cm)) for labs, b in s[2]]
        return ("case", _rename_ast(s[1], sm, cm), items,
                _rename_stmt(s[3], sm, cm) if s[3] else None)
    if k == "for":
        return ("for", _rename_stmt(s[1], sm, cm), _rename_ast(s[2], sm, cm),
                _rename_stmt(s[3], sm, cm), _rename_stmt(s[4], sm, cm))
    if k == "delay":
        return ("delay", s[1], _rename_stmt(s[2], sm, cm) if s[2] else None)
    if k == "sys":
        return ("sys", s[1], [_rename_ast(x, sm, cm) for x in s[2]])
    return s

def _instrument(stmt, prog, prefix):
    k = stmt[0]
    if k == "block":
        return ("block", [_instrument(x, prog, prefix) for x in stmt[1]])
    if k == "if":
        return ("if", stmt[1], _instrument(stmt[2], prog, prefix),
                _instrument(stmt[3], prog, prefix) if stmt[3] else None)
    if k == "case":
        cid = len(prog.cases); prog.cases[cid] = len(stmt[2])
        prog.case_at[cid] = prefix or "<top>"
        return ("case", stmt[1],
                [(l, _instrument(b, prog, prefix)) for l, b in stmt[2]],
                _instrument(stmt[3], prog, prefix) if stmt[3] else None, cid)
    if k == "for":
        return ("for", _instrument(stmt[1], prog, prefix), stmt[2],
                _instrument(stmt[3], prog, prefix),
                _instrument(stmt[4], prog, prefix))
    return stmt

def _const_eval(ast, cvals):
    ctx = Ctx(env={}, consts={k: (v, 32) for k, v in cvals.items()},
              widths={}, strict=True)
    return ev(ast, ctx)[0]

def flatten(mods, top):
    prog = Program()
    def rec(mname, prefix, pmap, povr, parent_cvals):
        pm = mods[mname]; cvals = dict(parent_cvals)
        for pn, past in pm.params:
            v = (_const_eval(povr[pn], parent_cvals) if pn in povr
                 else _const_eval(past, cvals))
            cvals[pn] = v; prog.consts[prefix + pn] = v
        sm = {}
        for p in pm.ports:
            g = pmap.get(p.name, prefix + p.name); sm[p.name] = g
            prog.widths.setdefault(g, p.width)
            if prefix == "":
                if p.dir == "input": prog.inputs.append(g)
                elif p.dir == "output": prog.outputs.append(g)
        for nm, ent in pm.nets.items():
            w, kind, init = ent[0], ent[1], ent[2]
            depth = ent[3] if len(ent) > 3 else 1
            g = prefix + nm; sm[nm] = g
            if depth > 1:
                prog.arrays[g] = (w, depth)
                for i in range(depth):
                    key = f"{g}.{i}"; prog.widths[key] = w
                    if key not in prog.order: prog.order.append(key)
                continue
            prog.widths.setdefault(g, w)
            if g not in prog.order: prog.order.append(g)
            if init is not None: prog.inits[g] = _const_eval(init, cvals)
        for lhs, ast, dl in pm.assigns:
            prog.assigns.append((_rename_lhs(lhs, sm),
                                 _rename_ast(ast, sm, {}), dl))
        for sens, stmt in pm.procs:
            stmt = _rename_stmt(stmt, sm, {})
            if sens[0] == "comb":
                names = "*" if sens[1] == "*" else [sm[n] for n in sens[1]]
                prog.comb.append((names, _instrument(stmt, prog, prefix)))
            else:
                prog.edges.append([(t2, sm[n], _instrument(stmt, prog, prefix))
                                   for t2, n in sens[1]])
        for th_ in pm.threads:
            body = _rename_stmt(th_["stmts"], sm, {})
            prog.threads.append({"stmts": _instrument(body, prog, prefix),
                                 "loop": th_["loop"]})
        for modn, inst, povrs, conns in pm.insts:
            if modn in VERILOG_PRIMS:
                nets = [sm.get(net, net) for _, net in conns]
                if len(nets) < 2:
                    raise HDLSimError(f"gate {modn} needs out+in(s)")
                out, ins = nets[0], nets[1:]; expr = ins[0]
                for x in ins[1:]: expr = (modn, expr, x)
                if modn == "not": expr = ("not", ins[0])
                elif modn == "buf": expr = ins[0]
                elif modn in ("nand", "nor", "xnor"): expr = ("not", expr)
                prog.assigns.append((("var", out), expr, 0)); continue
            if modn not in mods:
                raise HDLSimError(f"instance '{inst}': unknown module '{modn}'")
            povr_vals = {k2: _const_eval(a2, cvals) for k2, a2 in povrs.items()}
            child = mods[modn]
            if all(c is not None for c, _ in conns):
                got = [c for c, _ in conns]
                want = [p.name for p in child.ports]
                if set(got) != set(want):
                    raise HDLSimError(f"instance '{inst}': ports {got} don't "
                                      f"match '{modn}' {want}")
                cmap = {f: sm[net] for f, net in conns}
            else:
                want = [p.name for p in child.ports]
                if len(conns) != len(want):
                    raise HDLSimError(f"instance '{inst}': {len(conns)} "
                        f"conns, '{modn}' has {len(want)} ports")
                cmap = {want[i]: sm[net] for i, (_, net) in enumerate(conns)}
            rec(modn, prefix + inst + ".", cmap, povr_vals, cvals)
    pm = mods[top]
    rec(top, "", {p.name: p.name for p in pm.ports}, {}, {})
    for g in prog.inputs + prog.outputs:
        if g not in prog.order: prog.order.append(g)
    return prog

def pick_top(mods):
    instd = set()
    for m in mods.values():
        for modn, _, _, _ in m.insts: instd.add(modn)
    for name in mods:
        if re.search(r"(^|_)tb$|(^|_)testbench$|^tb_", name, re.I):
            return name
    tops = [n for n in mods if n not in instd]
    return tops[0] if tops else list(mods)[0]

def make_ctx(prog):
    return Ctx(env={g: prog.inits.get(g, 0) for g in prog.widths},
               consts=prog.consts, widths=prog.widths, arrays=prog.arrays)

def comb_fixpoint(prog, ctx, allow_delay=False):
    for _ in range(400):
        ctx._changed = False
        for lhs, ast, dl in prog.assigns:
            if dl and not allow_delay:
                raise HDLSimError("design uses #delays on assigns — press Run "
                                  "(glitch mode) instead of the truth-table "
                                  "path")
            write_lhs(ctx, lhs, ev(ast, ctx)[0])
        for _sens, stmts in prog.comb: drive_comb(stmts, ctx)
        if not ctx._changed: return
    raise HDLSimError("combinational logic does not settle (loop?)")

class _Finish(Exception):
    pass

def _vfmt(fmt, args, ctx):
    out, i, ai, vals = [], 0, 0, []
    for a in args:
        try: vals.append(a[1] if a[0] == "str" else ev(a, ctx)[0])
        except Exception: vals.append(0)
    while i < len(fmt):
        c = fmt[i]
        if c == "%":
            m = re.match(r"%\d*([bBdDhHxX])", fmt[i:])
            if m:
                spec = m.group(1).lower(); i += m.end()
                v = vals[ai] if ai < len(vals) else 0; ai += 1
                out.append(format(v, "b") if spec == "b" else
                           format(v, "x") if spec in "hx" else str(v))
                continue
            i += 1; out.append("%"); continue
        out.append(c); i += 1
    return "".join(out)

def _settle_step(prog, ctx, prev, logs=None, max_iter=200):
    for _ in range(max_iter):
        ctx._changed = False
        for lhs, ast, dl in prog.assigns: write_lhs(ctx, lhs, ev(ast, ctx)[0])
        for _sens, stmts in prog.comb: drive_comb(stmts, ctx)
        fired = []
        for group in prog.edges:
            for typ, sig, stmts in group:
                pv, cv = prev.get(sig, 0), ctx.env.get(sig, 0)
                if ((typ == "pos" and pv == 0 and cv == 1) or
                        (typ == "neg" and pv == 1 and cv == 0)):
                    fired.append(stmts)
        if not fired and not ctx._changed: return
        nb = []; ctx.nb = nb
        for stmts in fired:
            for item in gen_stmts([stmts], ctx):
                if item[0] == "delay":
                    raise HDLSimError("delays not allowed inside clocked "
                                      "blocks")
                if item[0] == "sys":
                    _2, _3, a2, wr = item
                    has = a2 and a2[0][0] == "str"
                    fmt = a2[0][1] if has else ""
                    rest = a2[1:] if has else a2
                    if logs is not None:
                        logs.append(_vfmt(fmt, rest, ctx) + ("" if wr
                                                             else "\n"))
                        if len(logs) > 800:
                            raise HDLSimError("$display output limit reached")
                    continue
                if item[0] == "finish": raise _Finish()
        ctx.nb = None
        for lhs, v in nb: write_lhs(ctx, lhs, v)
        prev = dict(ctx.env)
    raise HDLSimError("design does not settle (oscillation?)")

def _record(prog, ctx, times, series, disp):
    times.append(ctx.time)
    for it, g in zip(series, disp):
        w = it["width"]
        if g not in ctx.written: it["values"].append("x" * w)
        else:
            v = ctx.env.get(g, 0)
            it["values"].append(format(v, "b").zfill(w) if w > 1 else str(v))

def simulate_gen(prog, unit="ns", max_time=1_000_000):
    if any(dl for _, _, dl in prog.assigns):
        raise HDLSimError("design mixes #delays with always blocks — the "
                          "glitch engine supports assign-only designs")
    ctx = make_ctx(prog); ctx.written |= set(prog.inits)
    logs, times = [], []; seq = [0]; heap = []; finished = {"v": False}
    disp = [g for g in prog.order if prog.widths.get(g, 1) <= 32]
    series = [{"name": g, "width": prog.widths.get(g, 1), "values": []}
              for g in disp]
    def settle(): _settle_step(prog, ctx, dict(ctx.env), logs=logs)
    def advance(gen, t):
        while True:
            try: item = next(gen)
            except StopIteration: return
            except _Finish: finished["v"] = True; return
            if item[0] == "readmem":
                _do_readmem(item[1], item[2], ctx); continue
            if item[0] == "delay":
                heapq.heappush(heap, (t + item[1], seq[0], gen)); seq[0] += 1
                return
            if item[0] == "sys":
                _, _, args, wr = item
                if args and args[0][0] == "str": fmt, rest = args[0][1], args[1:]
                else: fmt, rest = "", args
                logs.append(_vfmt(fmt, rest, ctx) + ("" if wr else "\n"))
                if len(logs) > 800:
                    raise HDLSimError("$display limit (runaway?)")
                continue
            if item[0] == "finish": finished["v"] = True; return
    def push_thread(th_, t0=0):
        def gen():
            while True:
                yield from gen_stmts([th_["stmts"]], ctx)
                if not th_["loop"]: return
        heapq.heappush(heap, (t0, seq[0], gen())); seq[0] += 1
    try: settle()
    except _Finish: pass
    _record(prog, ctx, times, series, disp)
    if not prog.threads and not prog.edges:
        yield {"time": 0, "ctx": ctx, "times": times, "series": series,
               "logs": logs, "done": True, "steady": True}
        return
    if not prog.threads:
        raise HDLSimError("sequential design has no stimulus — add a "
                          "testbench")
    for th_ in prog.threads: push_thread(th_)
    events = 0
    while heap and not finished["v"]:
        t = heap[0][0]
        if t > max_time:
            raise HDLSimError("time limit exceeded — missing $finish?")
        while heap and heap[0][0] == t and not finished["v"]:
            _, _, gen = heapq.heappop(heap); ctx.time = t
            advance(gen, t); events += 1
            if events > 200_000:
                raise HDLSimError("event limit — runaway simulation?")
        if finished["v"]: break
        ctx.time = t
        try: settle()
        except _Finish: finished["v"] = True
        _record(prog, ctx, times, series, disp)
        if len(times) > 20_000:
            raise HDLSimError("too many waveform samples")
        yield {"time": t, "ctx": ctx, "times": times, "series": series,
               "logs": logs, "done": False, "steady": False}
    yield {"time": ctx.time, "ctx": ctx, "times": times, "series": series,
           "logs": logs, "done": True, "steady": False}

def simulate(prog, unit="ns", max_time=1_000_000):
    last = None
    for snap in simulate_gen(prog, unit, max_time): last = snap
    ctx = last["ctx"]; warns = list(ctx.warned)
    unw = [g for g in prog.order if g not in ctx.written
           and g not in prog.inputs and "." not in g][:10]
    if unw: warns.append("never assigned (consider a reset): " +
                         ", ".join(unw))
    return (last["times"], last["series"], last["logs"], warns, unit,
            last.get("steady", False), ctx)

def simulate_gates(prog, unit="ns", max_time=200_000):
    if prog.edges or prog.comb:
        raise HDLSimError("glitch mode supports assign-only designs "
                          "(+ initial stimulus)")
    if not any(dl for _, _, dl in prog.assigns):
        raise HDLSimError("no #delays on assigns — nothing to animate")
    for lhs, _ast, dl in prog.assigns:
        if dl and lhs[0] != "var":
            raise HDLSimError("delayed assigns must target simple nets")
    ctx = make_ctx(prog); ctx.written |= set(prog.inits)
    logs, times = [], []; seq = [0]; pend = {}; heap = []
    disp = [g for g in prog.order if prog.widths.get(g, 1) <= 32]
    series = [{"name": g, "width": prog.widths.get(g, 1), "values": []}
              for g in disp]
    def settle0():
        for _ in range(300):
            ctx._changed = False
            for lhs, ast, dl in prog.assigns:
                if not dl: write_lhs(ctx, lhs, ev(ast, ctx)[0])
            if not ctx._changed: return
        raise HDLSimError("zero-delay logic oscillates")
    def eval_delayed(t):
        for lhs, ast, dl in prog.assigns:
            if not dl: continue
            net = lhs[1]; v = ev(ast, ctx)[0]
            p = pend.get(net)
            if p and p[1] == v: continue
            ent = (t + dl, v, seq[0]); seq[0] += 1; pend[net] = ent
            heapq.heappush(heap, (ent[0], ent[2], "apply", net))
    def push_thread(th_):
        def gen():
            while True:
                yield from gen_stmts([th_["stmts"]], ctx)
                if not th_["loop"]: return
        heapq.heappush(heap, (0, seq[0], "th", gen())); seq[0] += 1
    def advance(gen, t):
        while True:
            try: item = next(gen)
            except StopIteration: return
            except _Finish: return "fin"
            if item[0] == "readmem":
                _do_readmem(item[1], item[2], ctx); continue
            if item[0] == "delay":
                heapq.heappush(heap, (t + item[1], seq[0], "th", gen))
                seq[0] += 1; return
            if item[0] == "sys":
                _, _, args, wr = item
                if args and args[0][0] == "str": fmt, rest = args[0][1], args[1:]
                else: fmt, rest = "", args
                logs.append(_vfmt(fmt, rest, ctx) + ("" if wr else "\n"))
                continue
            if item[0] == "finish": return "fin"
    for th_ in prog.threads: push_thread(th_)
    settle0(); eval_delayed(0); _record(prog, ctx, times, series, disp)
    events = 0
    while heap:
        t = heap[0][0]
        if t > max_time: raise HDLSimError("time limit — missing $finish?")
        ctx.time = t; dead = False
        while heap and heap[0][0] == t:
            _, _, kind, pay = heapq.heappop(heap)
            if kind == "apply":
                p = pend.get(pay)
                if p and p[0] == t:
                    write_lhs(ctx, ("var", pay), p[1]); del pend[pay]
            else:
                if advance(pay, t) == "fin": heap.clear(); dead = True; break
            events += 1
            if events > 300_000: raise HDLSimError("event limit — runaway?")
        settle0(); eval_delayed(t); _record(prog, ctx, times, series, disp)
        if len(times) > 40_000: raise HDLSimError("too many samples")
        if dead: break
    return times, series, logs, [], unit, False, ctx

def coverage_report(prog, ctx):
    return [f"case@{prog.case_at.get(cid, '?')}: "
            f"{len(ctx.cover.get(cid, set()))}/{n} branches"
            for cid, n in sorted(prog.cases.items())]

def truth_table(design_text, want=None):
    mods, _u = parse_design(design_text)
    top = want or pick_top(mods)
    prog = flatten(mods, top)
    if prog.threads or prog.edges:
        raise HDLSimError(f"'{top}' contains initial/posedge code — it is "
                          "sequential: press Run instead of Truth Table")
    if any(dl for _, _, dl in prog.assigns):
        raise HDLSimError("design uses #delays — press Run (glitch mode)")
    ins = [i for i in prog.inputs if prog.widths.get(i, 1) == 1]
    outs = [o for o in prog.outputs if prog.widths.get(o, 1) == 1]
    if not ins: raise HDLSimError(f"module '{top}' has no scalar inputs")
    if not outs: raise HDLSimError(f"module '{top}' has no scalar outputs")
    if len(ins) > MAX_TT_INPUTS:
        raise HDLSimError(f"{len(ins)} inputs is too many "
                          f"(max {MAX_TT_INPUTS})")
    ctx = make_ctx(prog); rows = []; n = len(ins)
    for r in range(1 << n):
        for i, nm in enumerate(ins): ctx.env[nm] = (r >> (n - 1 - i)) & 1
        comb_fixpoint(prog, ctx)
        rows.append([str(ctx.env[x]) for x in ins] +
                    [str(ctx.env[o]) for o in outs])
    return prog, ins, outs, rows

def _settle_clock(prog, ctx, cycles=1):
    for _ in range(max(1, cycles)):
        ctx.env["clk"] = 0
        _settle_step(prog, ctx, dict(ctx.env))
        prev = dict(ctx.env); ctx.env["clk"] = 1
        _settle_step(prog, ctx, prev)

def _trace_expr(times, series, expr, max_samples=2000):
    ast = Parser(tokenize(preprocess(expr)[0])).parse_expr()
    widths = {s["name"]: s["width"] for s in series if s["width"] <= 32}
    keep = [(s["name"], s["values"]) for s in series if s["width"] <= 32]
    stride = max(1, len(times) // max_samples); out = []
    for k in range(0, len(times), stride):
        env = {n: (0 if "x" in v[k] else int(v[k], 2)) for n, v in keep}
        try:
            out.append("1" if ev(ast, Ctx(env=env, consts={},
                                          widths=widths))[0] else "0")
        except HDLSimError: out.append("0")
    return out

def eval_bins(times, series, bins, max_samples=2000):
    asts = {}
    for name, expr in bins:
        try: asts[name] = Parser(tokenize(preprocess(expr)[0])).parse_expr()
        except HDLSimError: asts[name] = None
    widths = {s["name"]: s["width"] for s in series if s["width"] <= 32}
    keep = [(s["name"], s["values"]) for s in series if s["width"] <= 32]
    stride = max(1, len(times) // max_samples)
    hits = {n: 0 for n, _ in bins}; cross = {}
    for k in range(0, len(times), stride):
        env = {n: (0 if "x" in v[k] else int(v[k], 2)) for n, v in keep}
        ctx = Ctx(env=env, consts={}, widths=widths); state = {}
        for name, _e in bins:
            ok = False
            if asts[name] is not None:
                try: ok = bool(ev(asts[name], ctx)[0])
                except HDLSimError: ok = False
            state[name] = ok
            if ok: hits[name] += 1
        names = list(state)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if state[names[i]] and state[names[j]]:
                    key = tuple(sorted((names[i], names[j])))
                    cross[key] = cross.get(key, 0) + 1
    return hits, cross, asts

def activity_report(times, series, top_n=8):
    rows = []
    for s in series:
        if s["width"] > 32: continue
        flips, prev = 0, None
        for v in s["values"]:
            if "x" in v: prev = None; continue
            if prev is not None:
                flips += bin(int(prev, 2) ^ int(v, 2)).count("1")
            prev = v
        if flips: rows.append((flips, s["name"], s["width"]))
    rows.sort(reverse=True)
    return rows[:top_n]

def lint_design(text):
    try:
        t2, _ = preprocess(text); toks = tokenize(t2)
    except HDLSimError as e:
        m = re.search(r"line (\d+):\s*(.*)", str(e))
        return [(int(m.group(1)), "err", m.group(2))] if m else \
            [(1, "err", str(e))]
    issues = []; n = len(toks); proc_targets = {}; assign_targets = set()
    bid = 0; i = 0
    while i < n:
        v = toks[i][1]
        if v == "assign":
            j = i + 1
            if j < n and toks[j][1] == "{":
                while j < n and toks[j][1] != "}":
                    if toks[j][0] == "id": assign_targets.add(toks[j][1])
                    j += 1
            elif j < n: assign_targets.add(toks[j][1])
            i += 1; continue
        if v in ("always", "initial"):
            is_init = v == "initial"; j = i + 1; mode = "tb"
            if not is_init and j < n and toks[j][1] == "@":
                j += 1; sens = []
                if j < n and toks[j][1] == "(":
                    pd = 0
                    while j < n:
                        if toks[j][1] == "(": pd += 1
                        elif toks[j][1] == ")":
                            pd -= 1
                            if pd == 0: break
                        sens.append(toks[j][1]); j += 1
                j += 1
                mode = ("clocked" if any(s in ("posedge", "negedge")
                                         for s in sens) else "comb")
            elif not is_init:
                i += 1; continue
            body, bd, started = [], 0, False
            while j < n:
                tv = toks[j][1]
                if tv == "begin": bd += 1; started = True
                elif tv == "end":
                    if bd == 0 and started: break
                    bd -= 1
                elif tv in ("always", "initial", "endmodule") and not started:
                    break
                body.append(toks[j]); j += 1
                if not started and tv == ";": break
            myb = bid; bid += 1
            if mode == "clocked":
                targets = set()
                for k2, bt in enumerate(body):
                    if bt[1] == "=" and k2 and body[k2 - 1][0] == "id":
                        issues.append((bt[2], "warn",
                            f"blocking '=' on '{body[k2-1][1]}' inside a "
                            "clocked always — use '<=' (race)"))
                    if bt[1] in ("=", "<=") and k2 and body[k2-1][0] == "id":
                        targets.add(body[k2 - 1][1])
                for tn in targets:
                    proc_targets.setdefault(tn, set()).add(myb)
            elif mode == "comb":
                k2 = 0
                while k2 < len(body):
                    bt = body[k2][1]
                    if bt == "<=":
                        issues.append((body[k2][2], "warn",
                            "non-blocking '<=' in combinational always — "
                            "use '='"))
                    elif bt == "case":
                        cd, k3, hasd = 0, k2, False
                        while k3 < len(body):
                            if body[k3][1] == "case": cd += 1
                            elif body[k3][1] == "endcase":
                                cd -= 1
                                if cd == 0: break
                            elif body[k3][1] == "default" and cd == 1:
                                hasd = True
                            k3 += 1
                        if not hasd:
                            issues.append((body[k2][2], "warn",
                                "case without default in combinational "
                                "block — latch risk"))
                        k2 = k3
                    k2 += 1
            i = j; continue
        i += 1
    for tn, blocks in proc_targets.items():
        if len(blocks) > 1:
            issues.append((1, "err", f"'{tn}' is assigned in {len(blocks)} "
                           "procedural blocks — simulation race / synthesis "
                           "error"))
    for tn in proc_targets:
        if tn in assign_targets:
            issues.append((1, "err", f"'{tn}' driven by both assign and an "
                           "always block — multiple drivers"))
    return issues

def parse_vcd(path):
    signals, order, scope, t = {}, [], [], 0
    defs_done, skipping = False, False; unit = "ticks"
    with open(path, errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line: continue
            if skipping:
                if "$end" in line: skipping = False
                continue
            if not defs_done:
                if line.startswith("$var"):
                    parts = line.split()
                    try:
                        w, ident, nm = int(parts[2]), parts[3], parts[4]
                    except (IndexError, ValueError): continue
                    signals[ident] = {"name": ".".join(scope + [nm]),
                                      "width": w, "events": []}
                    order.append(ident)
                elif line.startswith("$scope"):
                    parts = line.split()
                    if len(parts) > 2: scope.append(parts[2])
                elif line.startswith("$upscope"):
                    if scope: scope.pop()
                elif line.startswith("$timescale"):
                    m = re.search(r"(\d+)\s*([munpf]?s)", line)
                    if m: unit = m.group(2)
                    if "$end" not in line: skipping = True
                elif line.startswith("$enddefinitions"): defs_done = True
                elif line.split()[0] in ("$date", "$version", "$comment"):
                    skipping = True
                continue
            if line.startswith("#"):
                try: t = int(line[1:])
                except ValueError: pass
            elif line.startswith("$"): continue
            elif line[0] in "01xzXZ":
                val, ident = line[0].lower(), line[1:].replace(" ", "")
                if ident in signals: signals[ident]["events"].append((t, val))
            elif line[0] in "bBrR":
                parts = line.split()
                if len(parts) >= 2 and parts[1] in signals:
                    val = parts[0][1:].lower() or "x"
                    signals[parts[1]]["events"].append((t, val))
    if not signals: return [], [], "ticks"
    all_times = sorted({tt for s in signals.values() for _, tt in s["events"]})
    if all_times and all_times[0] != 0: all_times = [0] + all_times
    out = []
    for ident in order:
        sig = signals[ident]
        if not sig["events"]: continue
        emap = dict(sig["events"]); cur, values = "x", []
        for tt in all_times:
            if tt in emap: cur = emap[tt]
            values.append(cur)
        out.append({"name": sig["name"], "width": sig["width"],
                    "values": values})
    return all_times, out, unit

PS_PER_LEVEL_ASIC, PS_PER_LEVEL_LUT = 80, 500

def critical_path(nodes):
    drv = {nd["out"]: nd for nd in nodes}; memo = {}
    def rank(net, stack=()):
        if net in memo: return memo[net]
        if net in stack: return 0
        d = drv.get(net)
        r = 0 if d is None else 1 + max(
            (rank(x, stack + (net,)) for x in d["ins"]), default=0)
        memo[net] = r; return r
    sinks = [nd for nd in nodes if nd["kind"] != "alias"]
    if not sinks: return [], set(), set()
    end = max(sinks, key=lambda nd: rank(nd["out"]))
    path, cur, seen = [], end, set()
    while cur is not None and cur["out"] not in seen:
        seen.add(cur["out"]); path.append(cur)
        ins = [drv[x] for x in cur["ins"] if x in drv]
        cur = max(ins, key=lambda d: rank(d["out"]), default=None)
    path.reverse()
    nset = {nd["out"] for nd in path}; wset = set()
    for nd in path:
        for x in nd["ins"]:
            if x in nset: wset.add(x)
    return path, nset, wset

def yosys_to_nodes(data, top):
    mod = data["modules"][top]
    nodes, drv, port_bits = [], {}, {}
    for pname, pinfo in mod.get("ports", {}).items():
        for i, b in enumerate(pinfo["bits"]):
            if isinstance(b, int):
                port_bits.setdefault(b, (pname, i, len(pinfo["bits"]) > 1))
    def netname(b):
        if isinstance(b, int) and b in port_bits:
            p, i, vec = port_bits[b]
            return f"{p}[{i}]" if vec else p
        return f"c{b}" if not isinstance(b, int) else f"n{b}"
    for cname, cell in mod.get("cells", {}).items():
        t2 = cell.get("type", "?").replace("$", "").strip("_")
        nd = {"kind": "box", "label": (t2.split("_")[0] or t2).upper()[:6],
              "out": cname, "ins": []}
        pdirs = cell.get("port_directions", {})
        for port, bits in cell.get("connections", {}).items():
            d = pdirs.get(port)
            if d == "output" or (d is None and port[0] in "YQO"):
                for b in bits:
                    if isinstance(b, int):
                        nd["out"] = netname(b); drv[nd["out"]] = nd
            else:
                nd["ins"].extend(netname(b) for b in bits)
        nodes.append(nd)
    inputs, outputs = [], []
    for pname, pinfo in mod.get("ports", {}).items():
        tgt = inputs if pinfo["direction"] == "input" else outputs
        tgt.extend(netname(b) for b in pinfo["bits"] if isinstance(b, int))
    memo = {}
    def rank(net, stack=()):
        if net in memo: return memo[net]
        if net in stack: return 0
        d = drv.get(net)
        r = 0 if d is None else 1 + max(
            (rank(x, stack + (net,)) for x in d["ins"]), default=0)
        memo[net] = r; return r
    for nd in nodes:
        nd["rank"] = max([rank(x) for x in nd["ins"]] + [0]) + 1
    return nodes, inputs, outputs

def after_txt(w): return f"{w} ticks"

def gen_random_spec(n):
    names = ["a", "b", "c", "d"][:n]
    while True:
        ones = [m for m in range(1 << n) if random.random() < 0.5]
        if 2 <= len(ones) <= (1 << n) - 2: break
    outs = "".join("1" if r in ones else "0" for r in range(1 << n))
    spec = dict(module="rand_fn", inputs=names, outputs={"y": outs})
    starter = ("// Implement y = Sigma m(%s)\nmodule rand_fn(\n%s    output "
               "y\n);\n    assign y = 1'b0;   // TODO\nendmodule\n"
               % (", ".join(map(str, ones)),
                  "".join(f"    input {nm},\n" for nm in names)))
    return spec, starter, ones

# ---- assembler ---------------------------------------------------------
ASM_OPS = {"LDI": 0, "HALT": 1, "STD": 2, "LDD": 3, "ADD": 4, "SUB": 5,
           "JZ": 6, "JMP": 7, "JNZ": 8, "CALL": 9, "RET": 10, "OUT": 11}

def assemble(text):
    stmts = []
    for ln, raw in enumerate(text.splitlines(), 1):
        code = raw.split(";", 1)[0].strip()
        if code: stmts.append((ln, code))
    labels, addr = {}, 0
    for ln, code in stmts:
        m = re.match(r"^(\w+):\s*(.*)$", code)
        if m: labels[m.group(1)] = addr; code = m.group(2).strip()
        if code: addr += 1
    words, srcs, a = [], [], 0
    for ln, code in stmts:
        m = re.match(r"^(\w+):\s*(.*)$", code)
        c2 = m.group(2).strip() if m else code
        if not c2: continue
        parts = c2.split(); op = parts[0].upper()
        if op in ("RET", "HALT", "OUT"): v = ASM_OPS[op] << 4
        elif op in ASM_OPS:
            if len(parts) < 2:
                raise ValueError(f"line {ln}: {op} needs an operand")
            t2 = parts[1]; val = labels.get(t2)
            if val is None:
                try: val = int(t2, 0)
                except ValueError:
                    raise ValueError(f"line {ln}: unknown label '{t2}'")
            if not 0 <= val <= 15:
                raise ValueError(f"line {ln}: operand {val} out of 0..15")
            v = (ASM_OPS[op] << 4) | val
        elif op in (".WORD", "DW"):
            v = int(parts[1], 0) if len(parts) > 1 else 0
        else:
            raise ValueError(f"line {ln}: unknown mnemonic '{op}'")
        words.append(v & 0xFF); srcs.append(code)
    return words, srcs

def disassemble(v):
    names = {0: "LDI", 1: "HALT", 2: "STD", 3: "LDD", 4: "ADD", 5: "SUB",
             6: "JZ", 7: "JMP", 8: "JNZ", 9: "CALL", 10: "RET", 11: "OUT"}
    op, arg = (v >> 4) & 0xF, v & 0xF
    nm = names.get(op)
    if nm is None: return ".word 0x%02X" % v
    return nm if nm in ("HALT", "RET", "OUT") else f"{nm} {arg}"

ASM_SAMPLE = """\
; countdown 3 -> 0  (CPU-II ISA)
        LDI 3
        STD 0
loop:   LDD 0
        JZ done
        SUB 1
        STD 0
        JMP loop
done:   HALT
"""

# ══════════════════════════ WIDGETS / EDITOR ══════════════════════════
_V_KW = ("module endmodule input output inout assign always initial begin end "
         "if else case casex casez endcase default for while repeat forever "
         "wait function endfunction task endtask generate endgenerate posedge "
         "negedge edge signed unsigned disable macromodule always_ff "
         "always_comb always_latch unique priority typedef enum struct packed "
         "assert return").split()
_V_TYPES = ("wire reg tri tri0 tri1 integer real time parameter localparam "
            "genvar event supply0 supply1 logic bit byte int unsigned").split()
_VHDL_KW = ("entity architecture end begin process if then elsif else case "
            "when others for while loop exit next wait after port generic map "
            "component configuration package body library use function "
            "procedure return variable signal constant alias attribute of is "
            "to downto range array type subtype record all with select "
            "and or nand nor xor xnor not mod rem abs").split()
_VHDL_TYPES = ("std_logic std_logic_vector std_ulogic bit bit_vector integer "
               "natural positive real boolean character string time signed "
               "unsigned work ieee std numeric_std std_logic_1164").split()

def _fmt(color, bold=False, italic=False):
    f = QTextCharFormat(); f.setForeground(QColor(color))
    if bold: f.setFontWeight(QFont.Bold)
    if italic: f.setFontItalic(True)
    return f

def _is_dark(): return th("window") == DARK["window"]

def mono_font(size=10):
    f = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    f.setPointSize(size); return f

class HDLHighlighter(QSyntaxHighlighter):
    def __init__(self, doc, lang="verilog"):
        super().__init__(doc)
        self._lang = None; self._rules = []
        self.comment_fmt = _fmt(th("sub"), italic=True)
        self.set_language(lang)
    def set_language(self, lang):
        if lang == self._lang: return
        self._lang = lang; self._rules = []; d = _is_dark()
        if lang == "verilog":
            kw, types = _V_KW, _V_TYPES
            self._rules.append((re.compile(r"\$[A-Za-z_]\w*"), _fmt(th("warn"))))
            self._rules.append((re.compile(
                r"\b(?:%s)\b" % "|".join(sorted(VERILOG_PRIMS))),
                _fmt("#66e0c2" if d else "#0e8060")))
        else:
            kw, types = _VHDL_KW, _VHDL_TYPES
        self._rules.append((re.compile(r"\b(?:%s)\b" %
            "|".join(map(re.escape, kw))),
            _fmt("#c792ea" if d else "#8432c8", bold=True)))
        self._rules.append((re.compile(r"\b(?:%s)\b" %
            "|".join(map(re.escape, types))),
            _fmt("#82aaff" if d else "#2456c8")))
        self._rules.append((re.compile(
            r"\b\d+('[bBoOdDhH][0-9a-fA-FxXzZ_]+)?\b"),
            _fmt("#f78c6c" if d else "#b25000")))
        if lang == "vhdl":
            self._rules.append((re.compile(r"'[^']'"),
                                _fmt("#c3e88d" if d else "#3c7a00")))
        self._rules.append((re.compile(r'"[^"\n]*"'),
                            _fmt("#c3e88d" if d else "#3c7a00")))
        self._rules.append((re.compile(
            r"//[^\n]*" if lang == "verilog" else r"--[^\n]*"),
            self.comment_fmt))
        self.rehighlight()
    def highlightBlock(self, text):
        for rx, fmt in self._rules:
            for m in rx.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)
        if self._lang == "verilog":
            self.setCurrentBlockState(0)
            start = 0 if self.previousBlockState() == 1 else text.find("/*")
            while start >= 0:
                end = text.find("*/", start + 2)
                if end >= 0:
                    length = end - start + 2; self.setCurrentBlockState(0)
                else:
                    length = len(text) - start; self.setCurrentBlockState(1)
                self.setFormat(start, length, self.comment_fmt)
                start = text.find("/*", start + length)

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor); self.editor = editor
        self.setMouseTracking(True)
    def sizeHint(self): return QSize(self.editor.line_number_width(), 0)
    def mouseMoveEvent(self, e):
        blk = self.editor.firstVisibleBlock()
        top = round(self.editor.blockBoundingGeometry(blk)
                    .translated(self.editor.contentOffset()).top())
        ln = -1
        while blk.isValid():
            h = round(self.editor.blockBoundingRect(blk).height())
            if blk.isVisible() and top <= e.position().y() < top + h:
                ln = blk.blockNumber() + 1; break
            top += h; blk = blk.next()
        info = getattr(self.editor, "_issues", {}).get(ln)
        if info:
            QToolTip.showText(e.globalPosition().toPoint(),
                              f"{info[0].upper()}: {info[1]}", self)
        else:
            QToolTip.hideText()
    def paintEvent(self, event): self.editor.paint_line_numbers(event)

KEYWORDS_FOR_COMPLETION = {
    "verilog": sorted(set(_V_KW) | set(_V_TYPES) | VERILOG_PRIMS |
                      {"$display", "$finish", "$dumpvars", "$dumpfile",
                       "$time", "$random", "$readmemh", "$urandom",
                       "$prob"}),
    "vhdl": sorted(set(_VHDL_KW) | set(_VHDL_TYPES)),
}

class CodeEditor(QPlainTextEdit):
    INDENT = "    "
    EXTRA_INDENT_RE = re.compile(
        r"(?:\bbegin\b|\bthen\b|\belse\b|\bis\b|\bloop\b|\()(\s*)$")
    def __init__(self, placeholder=""):
        super().__init__()
        self.setFont(mono_font(10)); self.setPlaceholderText(placeholder)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))
        self.language = "verilog"; self._issues = {}
        self.highlighter = HDLHighlighter(self.document(), "verilog")
        self._lna = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_ln_width)
        self.updateRequest.connect(self._update_ln)
        self.cursorPositionChanged.connect(self._highlight_line)
        self._word_timer = QTimer(self); self._word_timer.setInterval(500)
        self._word_timer.setSingleShot(True)
        self._word_timer.timeout.connect(self._refresh_words)
        self.textChanged.connect(lambda: self._word_timer.start())
        self.completer = QCompleter(self); self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setModel(QStringListModel([], self))
        self.completer.activated.connect(self._insert_completion)
        self._update_ln_width(); self._highlight_line(); self.apply_theme()
    def apply_theme(self):
        self.setStyleSheet(
            f"QPlainTextEdit{{background:{th('editor_bg')};"
            f"color:{th('editor_text')};border:1px solid {th('border')};"
            f"selection-background-color:{th('sel')};}}")
        self.highlighter.set_language(self.language)
    def set_language(self, lang):
        self.language = lang; self.highlighter.set_language(lang)
        self._refresh_words()
    def set_issue_markers(self, issues):
        self._issues = {int(ln): (k, m) for ln, k, m in issues}
        self._lna.update()
    def _refresh_words(self):
        words = set(KEYWORDS_FOR_COMPLETION.get(self.language, []))
        words |= set(re.findall(r"[A-Za-z_]\w{2,}", self.toPlainText()))
        self.completer.setModel(QStringListModel(sorted(words), self))
    def _current_word(self):
        cur = self.textCursor(); block = cur.block().text()
        pos = cur.positionInBlock(); m = None
        for m_ in re.finditer(r"[A-Za-z_$]\w*", block[:pos]):
            if m_.end() == pos: m = m_
        if not m: return "", ""
        m2 = re.match(r"[A-Za-z_$]\w*", block[pos:])
        return m.group(0), m2.group(0) if m2 else ""
    def _insert_completion(self, completion):
        prefix, _ = self._current_word(); cur = self.textCursor()
        for _ in range(len(prefix)): cur.deletePreviousChar()
        cur.insertText(completion)
    def _show_completions(self):
        prefix, _ = self._current_word()
        if not prefix: self.completer.popup().hide(); return
        self.completer.setCompletionPrefix(prefix)
        rect = self.cursorRect()
        rect.setWidth(self.completer.popup().sizeHintForColumn(0) + 30)
        if self.completer.completionCount(): self.completer.complete(rect)
        else: self.completer.popup().hide()
    def line_number_width(self):
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 16 + self.fontMetrics().horizontalAdvance("9") * digits
    def _update_ln_width(self, *_):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)
    def _update_ln(self, rect, dy):
        if dy: self._lna.scroll(0, dy)
        else: self._lna.update(0, rect.y(), self._lna.width(), rect.height())
        if rect.contains(self.viewport().rect()): self._update_ln_width()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._lna.setGeometry(QRect(cr.left(), cr.top(),
                                    self.line_number_width(), cr.height()))
    def paint_line_numbers(self, event):
        painter = QPainter(self._lna)
        painter.fillRect(event.rect(), QColor(th("editor_bg")))
        block = self.firstVisibleBlock(); num = block.blockNumber()
        top = round(self.blockBoundingGeometry(block)
                    .translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        cur = self.textCursor().blockNumber(); painter.setFont(self.font())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor(th("editor_cur")) if num == cur
                               else QColor(th("editor_num")))
                painter.drawText(0, top, self._lna.width() - 8,
                                 self.fontMetrics().height(), Qt.AlignRight,
                                 str(num + 1))
                issue = self._issues.get(num + 1)
                if issue:
                    painter.setPen(QColor(th("err") if issue[0] == "err"
                                          else th("warn")))
                    painter.drawText(1, top, 12,
                                     self.fontMetrics().height(),
                                     Qt.AlignVCenter | Qt.AlignLeft, "●")
            block = block.next(); top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            num += 1
    def _highlight_line(self):
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor(255, 255, 255, 16) if _is_dark()
                                 else QColor(0, 0, 0, 12))
        sel.format.setProperty(QTextFormat.FullWidthSelection, True)
        sel.cursor = self.textCursor(); sel.cursor.clearSelection()
        self.setExtraSelections([sel])
    def toggle_comment(self):
        token = "//" if self.language == "verilog" else "--"
        cur = self.textCursor(); doc = self.document()
        b0, b1 = doc.findBlock(cur.selectionStart()), \
            doc.findBlock(cur.selectionEnd())
        blocks = [doc.findBlock(i) for i in
                  range(b0.blockNumber(), b1.blockNumber() + 1)]
        all_c = all(re.match(rf"\s*{re.escape(token)}", b.text())
                    for b in blocks if b.text().strip())
        cur.beginEditBlock()
        for b in blocks:
            c = QTextCursor(b); text = b.text()
            if all_c:
                m = re.match(rf"(\s*){re.escape(token)} ?", text)
                if m:
                    c.setPosition(b.position() + len(m.group(1)))
                    c.setPosition(b.position() + m.end(),
                                  QTextCursor.KeepAnchor)
                    c.removeSelectedText()
            else:
                c.movePosition(QTextCursor.StartOfBlock)
                m = re.match(r"\s*", text)
                c.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor,
                               m.end())
                c.insertText(token + " ")
        cur.endEditBlock()
    def keyPressEvent(self, e):
        popup = self.completer.popup()
        if popup and popup.isVisible():
            if e.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab):
                self._insert_completion(self.completer.currentCompletion())
                popup.hide(); e.accept(); return
            if e.key() == Qt.Key_Escape: popup.hide(); e.accept(); return
            if e.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp,
                           Qt.Key_PageDown):
                step = {Qt.Key_Up: -1, Qt.Key_Down: 1, Qt.Key_PageUp: -5,
                        Qt.Key_PageDown: 5}[e.key()]
                self.completer.setCurrentRow(
                    max(0, self.completer.currentRow() + step))
                e.accept(); return
        if e.key() in (Qt.Key_Return, Qt.Key_Enter) and not (
                e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier |
                                 Qt.AltModifier)):
            cur = self.textCursor()
            if cur.hasSelection(): super().keyPressEvent(e); return
            line = cur.block().text()
            indent = re.match(r"[ \t]*", line).group(0)
            if self.EXTRA_INDENT_RE.search(line): indent += self.INDENT
            self.insertPlainText("\n" + indent)
            self.ensureCursorVisible(); e.accept(); return
        if e.key() == Qt.Key_Tab and not self.textCursor().hasSelection():
            self.insertPlainText(self.INDENT); e.accept(); return
        if e.key() == Qt.Key_Space and (e.modifiers() & Qt.ControlModifier):
            self._show_completions(); e.accept(); return
        super().keyPressEvent(e)
        if e.text() and (e.text().isalnum() or e.text() == "_"):
            prefix, _ = self._current_word()
            if len(prefix) >= 3: self._show_completions()

class FindBar(QWidget):
    def __init__(self, get_editor, parent=None):
        super().__init__(parent); self.get_editor = get_editor
        h = QHBoxLayout(self); h.setContentsMargins(4, 2, 4, 2)
        self.find_e = QLineEdit(); self.find_e.setPlaceholderText("Find…")
        self.find_e.returnPressed.connect(self.find_next)
        self.repl_e = QLineEdit()
        self.repl_e.setPlaceholderText("Replace with…")
        self.btn_prev = QPushButton("◀"); self.btn_next = QPushButton("▶")
        self.btn_repl = QPushButton("Replace"); self.btn_all = QPushButton("All")
        self.btn_close = QPushButton("✕"); self.case_btn = QPushButton("Aa")
        self.case_btn.setCheckable(True); self.status = QLabel("")
        for wdg in (QLabel("Find:"), self.find_e, self.btn_prev,
                    self.btn_next, QLabel("Replace:"), self.repl_e,
                    self.btn_repl, self.btn_all, self.case_btn, self.status,
                    self.btn_close):
            h.addWidget(wdg)
        self.btn_prev.clicked.connect(self.find_prev)
        self.btn_next.clicked.connect(self.find_next)
        self.btn_repl.clicked.connect(self.replace_one)
        self.btn_all.clicked.connect(self.replace_all)
        self.btn_close.clicked.connect(self.hide); self.hide()
    def _flags(self, backwards=False):
        f = QTextDocument.FindFlag(0)
        if backwards: f |= QTextDocument.FindBackward
        if self.case_btn.isChecked(): f |= QTextDocument.FindCaseSensitively
        return f
    def show_bar(self):
        self.show(); self.find_e.setFocus(); self.find_e.selectAll()
    def _update_status(self):
        ed = self.get_editor(); doc, term = ed.document(), self.find_e.text()
        hits, n = [], 0
        if term:
            cur = QTextCursor(doc); cur.movePosition(QTextCursor.Start)
            while n < 1000:
                cur = doc.find(term, cur, self._flags())
                if cur.isNull(): break
                hits.append(QTextCursor(cur)); n += 1
        self.status.setText(f"{len(hits)} hit(s)" if hits else "no match")
        sels = []
        for c in hits[:400]:
            s = QTextEdit.ExtraSelection()
            s.format.setBackground(QColor(th("sel"))); s.cursor = c
            sels.append(s)
        ed.setExtraSelections(sels)
    def find_next(self, backwards=False):
        ed = self.get_editor()
        found = ed.document().find(self.find_e.text(), ed.textCursor(),
                                   self._flags(backwards))
        if found.isNull():
            cur2 = ed.textCursor()
            cur2.movePosition(QTextCursor.End if not backwards
                              else QTextCursor.Start)
            found = ed.document().find(self.find_e.text(), cur2,
                                       self._flags(backwards))
        if not found.isNull(): ed.setTextCursor(found)
        self._update_status()
    def find_prev(self): self.find_next(True)
    def replace_one(self):
        ed = self.get_editor(); cur = ed.textCursor()
        if cur.hasSelection() and cur.selectedText() == self.find_e.text():
            cur.insertText(self.repl_e.text())
        self.find_next()
    def replace_all(self):
        ed = self.get_editor(); doc = ed.document()
        n, cur = 0, QTextCursor(doc); cur.beginEditBlock()
        cur.movePosition(QTextCursor.Start)
        while n < 5000:
            c = doc.find(self.find_e.text(), cur, self._flags())
            if c.isNull(): break
            c.insertText(self.repl_e.text()); cur = c; n += 1
        cur.endEditBlock(); self.status.setText(f"{n} replaced")

def _nice_step(span, target_count):
    target = max(1e-9, span / max(1, target_count))
    mag = 10 ** math.floor(math.log10(target))
    for m in (1, 2, 5, 10):
        if m * mag >= target: return int(round(m * mag))
    return max(1, int(round(span)))

class WaveformViewer(QWidget):
    NAME_W, LANE_H, PAD, AXIS_H = 150, 40, 8, 30
    def __init__(self):
        super().__init__()
        self._times, self._signals, self._unit = [0], [], "ns"
        self._lanes, self._all = [], []
        self._hidden, self._expand, self._renames = set(), set(), {}
        self._order = []; self._view = None; self._cursors = []
        self._press = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(160)
    def set_data(self, times, signals, unit="ns"):
        self._times = times or [0]; self._signals = signals or []
        self._unit = unit or "ns"; self._cursors, self._view = [], None
        self._rebuild(); self.update()
    def _rebuild(self):
        self._all = []
        for i, s in enumerate(self._signals):
            key = f"s{i}"
            self._all.append(dict(key=key, src=i, bit=None, bus=True,
                width=s["width"],
                label=self._renames.get(key, s["name"])))
            if s["width"] > 1:
                for b in range(s["width"] - 1, -1, -1):
                    bk = f"{key}#{b}"
                    self._all.append(dict(key=bk, src=i, bit=b, bus=False,
                        width=1, parent=key,
                        label=self._renames.get(
                            bk, "  " + s["name"] + f"[{b}]")))
        known = {l["key"] for l in self._all}
        self._order = [k for k in self._order if k in known]
        for l in self._all:
            if l["key"] not in self._order: self._order.append(l["key"])
        byk = {l["key"]: l for l in self._all}
        self._lanes = [byk[k] for k in self._order
                       if k not in self._hidden
                       and not (byk[k].get("parent")
                                and byk[k]["parent"] not in self._expand)]
        self.setMinimumHeight(max(160, self.PAD * 2
                                  + len(self._lanes) * self.LANE_H
                                  + self.AXIS_H))
    def _t_end(self): return max(self._times[-1], 1)
    def _win(self): return self._view or (0.0, float(self._t_end()))
    def _clamp(self, a, b):
        te, w = float(self._t_end()), max(2.0, b - a)
        a = max(-0.02 * te, min(a, te - w * 0.5))
        return (a, a + w)
    def _geom(self):
        a, b = self._win(); x0 = self.NAME_W + self.PAD / 2
        u = max(60.0, self.width() - self.PAD - x0)
        return a, b, x0, u
    def _tx(self, t):
        a, b, x0, u = self._geom()
        return x0 + (t - a) / max(1e-9, b - a) * u
    def _time_at(self, x):
        a, b, x0, u = self._geom()
        return a + (x - x0) / u * (b - a)
    def _val_at(self, lane, t):
        s = self._signals[lane["src"]]
        i = bisect.bisect_right(self._times, t) - 1
        i = max(0, min(i, len(s["values"]) - 1))
        v = s["values"][i]
        if lane["bit"] is not None:
            if "x" in v: return "x"
            return v[len(v) - 1 - lane["bit"]] if lane["bit"] < len(v) else "0"
        return v
    @staticmethod
    def _fmtv(lane, v):
        if "x" in v: return "x"
        if lane["bit"] is not None: return v
        return f"{int(v, 2):X}h" if lane["width"] > 4 else v
    def wheelEvent(self, e):
        if not self._signals: return
        a, b = self._win(); f = 1.3 ** (e.angleDelta().y() / 120.0)
        anchor = self._time_at(e.position().x())
        w = max(2.0, (b - a) / f)
        ra = (anchor - a) / max(1e-9, b - a); na = anchor - ra * w
        self._view = self._clamp(na, na + w); self.update()
    def mousePressEvent(self, e):
        if not self._signals: return
        if e.button() == Qt.LeftButton:
            self._press = (e.position().x(), self._win())
        elif e.button() == Qt.RightButton:
            m = QMenu(self)
            m.addAction("Fit (double-click also resets)", self._fit)
            m.addAction("Clear cursors", self._clear_cursors)
            m.addSeparator()
            m.addAction("Signals…",
                        lambda: SignalManagerDialog(self).exec())
            m.exec(e.globalPosition().toPoint())
    def mouseMoveEvent(self, e):
        if not self._press: return
        dx = e.position().x() - self._press[0]
        if abs(dx) > 4:
            a0, b0 = self._press[1]; _a, _b, _x, u = self._geom()
            dt = -dx / u * (b0 - a0)
            self._view = self._clamp(a0 + dt, b0 + dt); self.update()
    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton or not self._press: return
        moved = abs(e.position().x() - self._press[0]) > 4
        self._press = None
        if moved: return
        if len(self._cursors) >= 2: self._cursors = []
        self._cursors.append(self._time_at(e.position().x())); self.update()
    def mouseDoubleClickEvent(self, _):
        self._cursors = []; self._fit()
    def _fit(self): self._view = None; self.update()
    def _clear_cursors(self): self._cursors = []; self.update()
    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(th("wave_bg")))
        if not self._signals:
            p.setPen(QColor(th("sub")))
            p.drawText(self.rect(), Qt.AlignCenter | Qt.TextWordWrap,
                       "No waveform data.\nRun a simulation. Wheel = zoom, "
                       "drag = pan, click = cursor A/B, double-click = fit, "
                       "right-click = menu.")
            return
        a, b, x0, usable = self._geom()
        i0 = max(0, bisect.bisect_left(self._times, a) - 1)
        i1 = min(len(self._times), bisect.bisect_right(self._times, b + 1e-9))
        idxs = list(range(i0, max(i0 + 1, i1)))
        stride = max(1, len(idxs) // 1500); sel = idxs[::stride]
        if sel and sel[-1] != idxs[-1]: sel.append(idxs[-1])
        p.fillRect(0, 0, self.NAME_W - 4, h, QColor(th("panel")))
        mono = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        mono.setPointSizeF(max(8.0, self.font().pointSizeF() - 1))
        p.setFont(mono); fm = p.fontMetrics()
        total_h = self.PAD * 2 + len(self._lanes) * self.LANE_H
        for i, lane in enumerate(self._lanes):
            lt = self.PAD + i * self.LANE_H
            if i % 2 == 0:
                p.fillRect(self.NAME_W - 4, lt, w, self.LANE_H,
                           QColor(th("wave_alt")))
            name = lane["label"]
            while name and fm.horizontalAdvance(name) > self.NAME_W - 18:
                name = name[:-1]
            if name != lane["label"]: name += "…"
            p.setPen(QColor(th("wave_text")))
            p.drawText(QRect(8, lt, self.NAME_W - 16, self.LANE_H),
                       Qt.AlignVCenter | Qt.AlignLeft, name)
            hi, lo = lt + 8, lt + self.LANE_H - 14; mid = (hi + lo) // 2
            is_vec = lane["width"] > 1 and lane["bit"] is None
            src = self._signals[lane["src"]]["values"]
            prev_y, drew = None, False
            for k in sel:
                ts = self._tx(self._times[k])
                if ts > w + 30: break
                te = (self._tx(self._times[k + 1])
                      if k + 1 < len(self._times) else self._tx(b))
                if te < x0 - 30: prev_y = None; continue
                drew = True
                rv = src[k] if k < len(src) else "x"
                v = self._val_at(lane, self._times[k])
                if is_vec:
                    p.setPen(QPen(QColor(th("wave_bus")), 1.6))
                    p.drawLine(int(ts) + 2, hi, int(te), hi)
                    p.drawLine(int(ts) + 2, lo, int(te), lo)
                    if prev_y is not None and prev_y != hi:
                        p.drawLine(int(ts) - 3, hi, int(ts) + 3, lo)
                        p.drawLine(int(ts) - 3, lo, int(ts) + 3, hi)
                    txt = (rv if "x" in rv else
                           (f"{int(rv, 2):X}h" if lane["width"] > 4 else rv))
                    if te - ts > fm.horizontalAdvance(txt) + 8:
                        p.setPen(QColor(th("wave_text")))
                        p.drawText(QRect(int(ts), lt, int(te - ts),
                                         self.LANE_H), Qt.AlignCenter, txt)
                    prev_y = hi
                else:
                    if v == "0": y, pen = lo, QPen(QColor(th("wave_sig")), 1.6)
                    elif v == "1": y, pen = hi, QPen(QColor(th("wave_sig")), 1.6)
                    else:
                        y = mid; pen = QPen(QColor(th("wave_x")), 1.6)
                        p.fillRect(int(ts), mid - 3, max(1, int(te - ts)), 6,
                                   QColor(255, 166, 87, 60))
                    p.setPen(pen)
                    if prev_y is not None and prev_y != y:
                        p.drawLine(int(ts), prev_y, int(ts), y)
                    p.drawLine(max(int(ts), int(x0 - 30)), y, int(te), y)
                    prev_y = y
            if not drew:
                p.setPen(QColor(th("wave_x")))
                p.drawText(QRect(self.NAME_W, lt, w - self.NAME_W,
                                 self.LANE_H), Qt.AlignVCenter,
                           "outside view — double-click to fit")
        for j, ct in enumerate(self._cursors):
            x = self._tx(ct)
            if x0 - 20 <= x <= w:
                col = th("accent") if j == 0 else th("warn")
                p.setPen(QPen(QColor(col), 1.4, Qt.DashLine))
                p.drawLine(int(x), self.PAD, int(x), total_h + 10)
                p.setPen(QColor(col))
                p.drawText(int(x) + 3, self.PAD - 4, 70, 14,
                           f"{'A' if j == 0 else 'B'}={ct:g}")
        if len(self._cursors) == 2:
            dt = abs(self._cursors[1] - self._cursors[0])
            p.setPen(QColor(th("text")))
            p.drawText(self.NAME_W + 4, 2, 220, 16,
                       f"Δt = {dt:g} {self._unit}")
            for i, lane in enumerate(self._lanes):
                lt = self.PAD + i * self.LANE_H
                va = self._fmtv(lane, self._val_at(lane, self._cursors[0]))
                vb = self._fmtv(lane, self._val_at(lane, self._cursors[1]))
                p.setPen(QColor(th("wave_text")))
                p.drawText(w - 78, lt, 74, self.LANE_H,
                           Qt.AlignVCenter | Qt.AlignRight, f"{va}|{vb}")
        ay = total_h + 12
        if ay < h - 6:
            p.setPen(QColor(th("wave_grid")))
            p.drawLine(int(x0), ay, w - self.PAD, ay)
            step = max(1, _nice_step(b - a, int(usable // 90) or 4))
            t = math.ceil(a / step) * step
            while t <= b:
                xx = int(self._tx(t))
                p.drawLine(xx, ay, xx, ay + 5)
                p.setPen(QColor(th("sub")))
                p.drawText(xx - 24, ay + 7, 48, 14,
                           Qt.AlignHCenter | Qt.AlignTop, str(t))
                p.setPen(QColor(th("wave_grid"))); t += step
            p.setPen(QColor(th("sub")))
            p.drawText(w - 114, ay + 7, 110, 14, Qt.AlignRight | Qt.AlignTop,
                       f"time ({self._unit})")

class SignalManagerDialog(QDialog):
    def __init__(self, wave, parent=None):
        super().__init__(parent or wave); self.wave = wave
        self.setWindowTitle("Signal manager"); self.resize(480, 520)
        v = QVBoxLayout(self); self.listw = QListWidget(); v.addWidget(self.listw, 1)
        hb = QHBoxLayout()
        for txt, fn in (("Up", lambda: self._move(-1)),
                        ("Down", lambda: self._move(1)),
                        ("Show/Hide", self._toggle),
                        ("Expand/Collapse bus", self._expand_bus),
                        ("Rename…", self._rename)):
            b = QPushButton(txt); b.clicked.connect(fn); hb.addWidget(b)
        v.addLayout(hb)
        hh = QHBoxLayout(); hh.addStretch(1)
        ok = QPushButton("Apply & close"); ok.clicked.connect(self._apply_close)
        hh.addWidget(ok); v.addLayout(hh); self._fill()
    def _byk(self): return {l["key"]: l for l in self.wave._all}
    def _fill(self):
        byk = self._byk(); self.listw.clear()
        for k in self.wave._order:
            l = byk[k]; txt = l["label"]
            if l.get("bus") and l["width"] > 1:
                txt += (f"  [{l['width']}]  ▼" if k in self.wave._expand
                        else f"  [{l['width']}]  ▶")
            if k in self.wave._hidden: txt = "◌ " + txt
            it = QListWidgetItem(txt)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Unchecked if k in self.wave._hidden
                             else Qt.Checked)
            it.setData(Qt.UserRole, k); self.listw.addItem(it)
    def _groups(self):
        byk = self._byk(); groups, i = [], 0
        keys = self.wave._order
        while i < len(keys):
            l = byk[keys[i]]
            if l.get("bus") and l["width"] > 1:
                bits, j = [], i + 1
                while j < len(keys) and byk[keys[j]].get("parent") == keys[i]:
                    bits.append(keys[j]); j += 1
                groups.append([keys[i]] + bits); i = j
            else:
                groups.append([keys[i]]); i += 1
        return groups
    def _cur_key(self):
        it = self.listw.currentItem()
        return it.data(Qt.UserRole) if it else None
    def _move(self, d):
        k = self._cur_key()
        if not k: return
        gs = self._groups()
        gi = next(i for i, g in enumerate(gs) if k in g)
        j = gi + d
        if not 0 <= j < len(gs): return
        gs[gi], gs[j] = gs[j], gs[gi]
        self.wave._order = [k2 for g in gs for k2 in g]
        self.wave._rebuild(); self.wave.update(); self._fill()
    def _toggle(self):
        it = self.listw.currentItem()
        if not it: return
        k = it.data(Qt.UserRole)
        if it.checkState() == Qt.Checked:
            self.wave._hidden.add(k); it.setCheckState(Qt.Unchecked)
        else:
            self.wave._hidden.discard(k); it.setCheckState(Qt.Checked)
        it.setText(("◌ " if k in self.wave._hidden
                    else it.text().replace("◌ ", "")))
        self.wave._rebuild(); self.wave.update()
    def _expand_bus(self):
        k = self._cur_key()
        if not k: return
        if "#" in k: k = k.split("#")[0]
        if k in self.wave._expand: self.wave._expand.discard(k)
        else: self.wave._expand.add(k)
        self.wave._rebuild(); self.wave.update(); self._fill()
    def _rename(self):
        k = self._cur_key()
        if not k: return
        cur = self._byk()[k]["label"]
        txt, ok = QInputDialog.getText(self, "Rename signal", "Label:",
                                       text=cur.strip())
        if ok and txt.strip():
            self.wave._renames[k] = txt.strip()
            self.wave._rebuild(); self.wave.update(); self._fill()
    def _apply_close(self):
        for i in range(self.listw.count()):
            it = self.listw.item(i); k = it.data(Qt.UserRole)
            (self.wave._hidden.discard if it.checkState() == Qt.Checked
             else self.wave._hidden.add)(k)
        self.wave._rebuild(); self.wave.update(); self.accept()

PI_COLORS = ["#e5534b", "#2f81f7", "#3fb950", "#bc4c00", "#8957e5",
             "#d29922", "#00a4c4", "#db61a2"]

def gray(n): return [i ^ (i >> 1) for i in range(1 << n)]

def qmc(n, ones):
    if not ones: return []
    cur = {(m, 0) for m in ones}; primes = set()
    while cur:
        nxt, used = set(), set()
        for a, ad in cur:
            for b, bd in cur:
                if a >= b or ad != bd: continue
                diff = a ^ b
                if diff and not (diff & (diff - 1)):
                    used.add((a, ad)); used.add((b, bd))
                    nxt.add((a & b, ad | diff))
        primes |= (cur - used); cur = nxt
    full = (1 << n) - 1
    def cover(p):
        o, d = p
        return {m for m in range(1 << n) if (m & ~d & full) == (o & full)}
    plist = sorted(primes, key=lambda p: (-bin(p[1]).count("1"),
                                          bin(p[0]).count("1")))
    kept = []
    for p in plist:
        cp = cover(p)
        if any(cover(k) >= cp for k in kept): continue
        kept.append(p)
    covers = {p: cover(p) for p in kept}
    selected, uncovered = [], set(ones)
    while uncovered:
        sole = [p for p in kept
                if any(sum(1 for q in kept if m in covers[q]) == 1
                       for m in covers[p] & uncovered)]
        pick = sole or [max(kept, key=lambda q: len(covers[q] & uncovered))]
        for p in pick:
            if p not in selected: selected.append(p)
            uncovered -= covers[p]
    return selected

def pi_term(vars_, pi):
    ones, dc = pi; parts = []
    for i, name in enumerate(vars_):
        bp = len(vars_) - 1 - i
        if (dc >> bp) & 1: continue
        parts.append(name if (ones >> bp) & 1 else f"~{name}")
    return " & ".join(parts) if parts else "1'b1"

class KMapWidget(QWidget):
    CELL, HDR, GAP = 48, 26, 34
    def __init__(self):
        super().__init__()
        self.vars, self.ones, self.pis = [], set(), []
    def set_data(self, vars_, ones, pis):
        self.vars, self.ones, self.pis = vars_, set(ones), pis
        self.setMinimumSize(240, 180); self.update()
    def _layout(self):
        n = len(self.vars); fv = 1 if n == 5 else 0
        rem = n - fv; rk = (rem + 1) // 2; ck = rem - rk
        return fv, rk, ck, 1 << fv
    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing, True)
        p.fillRect(self.rect(), QColor(th("sch_bg")))
        n = len(self.vars)
        if n == 0: return
        fv, rk, ck, panels = self._layout()
        gw, gh = self.CELL * (1 << ck), self.CELL * (1 << rk)
        for panel in range(panels):
            ox, oy = 8, 8 + panel * (self.HDR + gh + 30 + self.GAP)
            f = panel
            if fv:
                p.setPen(QColor(th("sch_text")))
                p.drawText(ox, oy + 12, f"{self.vars[0]} = {panel}")
            p.setPen(QColor(th("sub")))
            col_codes, row_codes = gray(ck), gray(rk)
            for ci, code in enumerate(col_codes):
                p.drawText(ox + self.HDR + ci * self.CELL, oy + 14,
                           self.CELL, 14, Qt.AlignCenter,
                           format(code, f"0{ck}b"))
            for ri, code in enumerate(row_codes):
                p.drawText(ox, oy + self.HDR + 6 + ri * self.CELL,
                           self.HDR - 6, self.CELL,
                           Qt.AlignRight | Qt.AlignVCenter,
                           format(code, f"0{rk}b"))
            for ri in range(1 << rk):
                for ci in range(1 << ck):
                    m = (f << (rk + ck)) | (row_codes[ri] << ck) | col_codes[ci]
                    x, y = (ox + self.HDR + ci * self.CELL,
                            oy + self.HDR + ri * self.CELL)
                    p.fillRect(x, y, self.CELL - 2, self.CELL - 2,
                               QColor(th("panel")))
                    p.setPen(QColor(th("border")))
                    p.drawRect(x, y, self.CELL - 2, self.CELL - 2)
                    p.setPen(QColor(th("ok") if m in self.ones else th("sub")))
                    p.drawText(x, y, self.CELL - 2, self.CELL - 2,
                               Qt.AlignCenter, "1" if m in self.ones else "0")
            for gi, pi in enumerate(self.pis):
                p.setPen(QPen(QColor(PI_COLORS[gi % len(PI_COLORS)]), 2))
                rows_i = self._match(pi, rk, list(range(fv, fv + rk)), n,
                                     row_codes)
                cols_i = self._match(pi, ck,
                                     list(range(fv + rk, fv + rk + ck)), n,
                                     col_codes)
                for (r0, r1) in self._rects(rows_i, rk, row_codes, pi,
                        list(range(fv, fv + rk)), n):
                    for (c0, c1) in self._rects(cols_i, ck, col_codes, pi,
                            list(range(fv + rk, fv + rk + ck)), n):
                        p.drawRoundedRect(
                            ox + self.HDR + c0 * self.CELL - 1,
                            oy + self.HDR + r0 * self.CELL - 1,
                            (c1 - c0 + 1) * self.CELL + 1,
                            (r1 - r0 + 1) * self.CELL + 1, 6, 6)
    def _match(self, pi, kbits, var_idx, n, codes):
        ones, dc = pi; out = []
        for idx, code in enumerate(codes):
            ok = True
            for j, gi in enumerate(var_idx):
                bp = n - 1 - gi
                if (dc >> bp) & 1: continue
                if ((code >> (kbits - 1 - j)) & 1) != ((ones >> bp) & 1):
                    ok = False; break
            if ok: out.append(idx)
        return out
    def _rects(self, idxs, kbits, codes, pi, var_idx, n):
        if not idxs: return []
        if kbits == 0: return [(0, 0)]
        s = set(idxs)
        for a in range(len(codes)):
            b = a + len(s) - 1
            if b < len(codes) and set(range(a, b + 1)) == s: return [(a, b)]
        if len(s) == 2 and 0 in s and (len(codes) - 1) in s:
            return [(0, 0), (len(codes) - 1, len(codes) - 1)]
        return [(i, i) for i in sorted(s)]

class KMapDialog(QDialog):
    def __init__(self, vars_, rows, outputs, out_name, link_cb=None,
                 parent=None):
        super().__init__(parent); self.setWindowTitle(f"K-map — {out_name}")
        self.resize(820, 560)
        n = len(vars_); idx = outputs.index(out_name)
        ones = [r for r, row in enumerate(rows) if row[n + idx] == "1"]
        pis = qmc(n, ones)
        split = QHBoxLayout()
        self.kmap = KMapWidget(); self.kmap.set_data(vars_, ones, pis)
        ksc = QScrollArea(); ksc.setWidgetResizable(True)
        ksc.setWidget(self.kmap); split.addWidget(ksc, 3)
        right = QVBoxLayout()
        right.addWidget(QLabel("Prime implicants (click → schematic):"))
        self.terms = QListWidget()
        for i, p in enumerate(pis):
            it = QListWidgetItem(pi_term(vars_, p))
            it.setForeground(QColor(PI_COLORS[i % len(PI_COLORS)]))
            self.terms.addItem(it)
        self.terms.currentRowChanged.connect(
            lambda r: link_cb(out_name, r) if link_cb else None)
        right.addWidget(self.terms, 1)
        if ones:
            expr = " | ".join(pi_term(vars_, p) for p in pis)
            lbl = QLabel(f"<b>{html.escape(out_name)}</b> = <span "
                "style='font-family:monospace;'>"
                f"{html.escape(expr)}</span>")
            lbl.setWordWrap(True); right.addWidget(lbl)
        else:
            right.addWidget(QLabel(f"<b>{html.escape(out_name)}</b> = 1'b0"))
        wrap = QWidget(); wrap.setLayout(right); split.addWidget(wrap, 2)
        v = QVBoxLayout(self); v.addLayout(split, 1)
        btn = QPushButton("Close"); btn.clicked.connect(self.accept)
        h = QHBoxLayout(); h.addStretch(1); h.addWidget(btn); v.addLayout(h)

def synth_sop_nodes(vars_, pis, out_name):
    nodes = []; cnt = [0]
    def add(kind, ins, rank_, pi=None, out=None):
        net = out or f"$k{cnt[0]}"; cnt[0] += 1
        nd = {"kind": kind, "label": "", "out": net, "ins": ins,
              "rank": rank_}
        if pi is not None: nd["pi"] = pi
        nodes.append(nd); return net
    lit = {}
    def L(v, neg):
        if not neg: return v
        if v not in lit: lit[v] = add("not", [v], 1)
        return lit[v]
    ands = []
    for i, (ones, dc) in enumerate(pis):
        ins = []
        for j, v in enumerate(vars_):
            bp = len(vars_) - 1 - j
            if (dc >> bp) & 1: continue
            ins.append(L(v, not ((ones >> bp) & 1)))
        ands.append(add("and", ins, 2, pi=i))
    o = ands[0] if len(ands) == 1 else add("or", ands, 3)
    add("box", [o], 4, out=out_name)
    return nodes

def build_schematic(prog):
    if prog.comb or prog.edges or prog.threads:
        raise HDLSimError("schematic live view supports pure dataflow/gate "
                          "designs (no always blocks)")
    if prog.arrays:
        raise HDLSimError("schematic view doesn't draw array memories")
    nodes, driver, ncount = [], {}, [0]
    def new_node(kind, label, ins):
        net = f"$n{ncount[0]}"; ncount[0] += 1
        nd = {"kind": kind, "label": label, "out": net, "ins": ins}
        nodes.append(nd); driver[net] = nd; return net
    def lower(a):
        k = a[0]
        if k == "var":
            if a[1] in prog.arrays:
                raise HDLSimError("array reads are not drawn in the schematic")
            return a[1]
        if k == "num": return new_node("const", str(a[1]), [])
        if k in ("not", "lnot"): return new_node("not", "~", [lower(a[1])])
        if k == "red":
            op = {"&": "AND", "|": "OR", "^": "XOR"}.get(a[1], a[1])
            return new_node("box", op, [lower(a[2])])
        if k == "?":
            return new_node("mux", "MUX",
                            [lower(a[1]), lower(a[3]), lower(a[2])])
        if k in ("bit", "part"): return new_node("box", k, [lower(a[1])])
        if k == "cat":
            return new_node("box", "{}", [lower(x) for x in a[1]])
        if k == "repl":
            return new_node("box", "{{}}", [lower(a[1]), lower(a[2])])
        if k == "neg": return new_node("box", "-", [lower(a[1])])
        if k in ("lt", "le", "gt", "ge", "eq", "ne"):
            return new_node("box", {"lt": "<", "le": "<=", "gt": ">",
                "ge": ">=", "eq": "==", "ne": "!="}[k],
                [lower(a[1]), lower(a[2])])
        if k in ("+", "-", "*", "/", "%", "<<", ">>"):
            return new_node("box", k, [lower(a[1]), lower(a[2])])
        if k == "clog2": return new_node("box", "$clog2", [lower(a[1])])
        if k in ("and", "or", "xor"):
            return new_node(k, {"and": "&", "or": "|", "xor": "^"}[k],
                            [lower(a[1]), lower(a[2])])
        return new_node("box", "?", [])
    for lhs, ast, dl in prog.assigns:
        net = lower(ast)
        targets = lhs[1] if lhs[0] == "cat" else [lhs[1]]
        for nm in targets:
            nodes.append({"kind": "alias", "label": "", "out": nm,
                          "ins": [net]})
            driver[nm] = nodes[-1]
    def resolve(net, depth=0):
        while net in driver and driver[net]["kind"] == "alias" and depth < 60:
            net = driver[net]["ins"][0]; depth += 1
        return net
    real = [nd for nd in nodes if nd["kind"] != "alias"]
    for nd in real: nd["ins"] = [resolve(x) for x in nd["ins"]]
    rank_memo = {}
    def rank(net, stack=()):
        if net in rank_memo: return rank_memo[net]
        if net in stack: return 0
        d = driver.get(net)
        r = 0 if d is None else 1 + max(
            (rank(x, stack + (net,)) for x in d["ins"]), default=0)
        rank_memo[net] = r; return r
    for nd in real:
        nd["rank"] = max([rank(x) for x in nd["ins"]] + [0]) + \
            (0 if nd["kind"] == "const" else 1)
    inputs = [i for i in prog.inputs if i not in driver]
    return real, inputs, list(prog.outputs)

class SchematicWidget(QWidget):
    GATE_W = 64
    def __init__(self):
        super().__init__()
        self.nodes, self.inputs, self.outputs = [], [], []
        self.msg = "Load a design and press Schematic (Ctrl+Shift+T)."
        self.live = False; self.values = {}; self.reveal = 10 ** 9
        self.highlight_pi = None; self.toggle_cb = None
        self.crit_nodes, self.crit_wires = set(), set()
        self._anim = QTimer(self); self._anim.setInterval(260)
        self._anim.timeout.connect(self._anim_step)
        self._replay_timer = QTimer(self); self._replay_timer.setInterval(70)
        self._replay_timer.timeout.connect(self._replay_tick)
        self._replay_events, self._replay_i, self._replay_step = [], 0, 1
        self.setMinimumHeight(220); self._in_rects = []; self._net_driver = {}
    def set_msg(self, msg):
        self.nodes, self.inputs, self.outputs = [], [], []
        self.live, self.msg, self.values = False, msg, {}
        self.update()
    def set_circuit(self, nodes, inputs, outputs, live=False):
        self.nodes, self.inputs, self.outputs = nodes, inputs, outputs
        self.live = live; self.msg = ""; self.values = {}
        self.highlight_pi = None
        self.crit_nodes, self.crit_wires = set(), set()
        self._layout(); self.update()
    def set_highlight(self, pi):
        self.highlight_pi = pi; self.update()
    def set_critical(self, node_nets, wire_nets):
        self.crit_nodes, self.crit_wires = set(node_nets), set(wire_nets)
        self.update()
    def refresh(self, ctx, animate=False):
        self.values = {}
        for nd in self.nodes:
            g = nd["out"]
            self.values[g] = (ctx.env.get(g, 0),
                              getattr(self, "prog_widths", {}).get(g, 1))
        if animate:
            self.reveal = 0; self._anim.start()
        else: self.reveal = 10 ** 9
        self.update()
    def _anim_step(self):
        self.reveal += 1
        maxr = max([nd.get("rank", 0) for nd in self.nodes] + [0])
        if self.reveal > maxr + 1: self._anim.stop()
        self.update()
    def replay_series(self, times, series):
        self._anim.stop(); events = []
        for k, t in enumerate(times):
            for s in series:
                prev = s["values"][k - 1] if k else None
                if prev is None or s["values"][k] != prev:
                    v = s["values"][k]
                    val = None if "x" in v else int(v, 2)
                    events.append((s["name"], val, s["width"]))
        if not events: return
        self._replay_events = events[:6000]
        self._replay_step = max(1, len(self._replay_events) // 200)
        self._replay_i = 0; self.values = {}; self.highlight_pi = None
        self._replay_timer.start(); self.update()
    def _replay_tick(self):
        for _ in range(self._replay_step):
            if self._replay_i >= len(self._replay_events):
                self._replay_timer.stop(); return
            name, val, w = self._replay_events[self._replay_i]
            self.values[name] = (val, w); self._replay_i += 1
        self.reveal = 10 ** 9; self.update()
    def _layout(self):
        ranks = {}
        for nd in self.nodes:
            nd.setdefault("rank", 0); ranks.setdefault(nd["rank"], []).append(nd)
        order = {}
        for _ in range(2):
            for r in sorted(ranks):
                ranks[r].sort(key=lambda nd: (
                    sum(order.get(x, 0) for x in nd["ins"] if x in order) /
                    max(1, len([x for x in nd["ins"] if x in order]))))
            idx = 0
            for r in sorted(ranks):
                for nd in ranks[r]:
                    order[nd["out"]] = idx; idx += 1
        ycounts = {}
        for r in sorted(ranks):
            for i, nd in enumerate(ranks[r]):
                nd["x"] = 140 + r * 150
                ycounts[r] = ycounts.get(r, 0) + 1
                nd["y"] = 90 + i * 64
        self._net_driver = {nd["out"]: nd for nd in self.nodes}
        maxy = max([nd["y"] for nd in self.nodes] + [200]) + 140
        maxx = max([nd["x"] for nd in self.nodes] + [300]) + 220
        self.setMinimumSize(min(maxx, 4000), min(maxy, 6000))
    def mousePressEvent(self, e):
        if not self.live or not self.toggle_cb: return
        for nm, rect in self._in_rects:
            if rect.contains(e.position()):
                cur = self.values.get(nm, (0, 1))[0]
                self.toggle_cb(nm, 0 if cur else 1); return
    def _wire_pen(self, net, src):
        if net in self.crit_wires: return QPen(QColor(th("err")), 2.4)
        v = self.values.get(net)
        rv = src.get("rank", 0) if src else 0
        if v is None or rv > self.reveal:
            return QPen(QColor(th("sch_wire")), 1.2)
        if v[0] is None: return QPen(QColor(th("wave_x")), 1.8)
        return (QPen(QColor(th("ok")), 2.2) if v[0] == 1
                else QPen(QColor(th("sch_wire")), 1.6))
    def _draw_gate(self, p, nd, x, y):
        w, h = self.GATE_W, 40; kind = nd["kind"]
        vv = self.values.get(nd["out"], (0, 1))
        active = (vv[0] == 1 and nd.get("rank", 0) <= self.reveal)
        crit = nd["out"] in self.crit_nodes
        p.setPen(QPen(QColor(th("err") if crit else
                             (th("accent") if active else th("sch_text"))),
                      2.4 if crit else 1.8))
        p.setBrush(QColor(th("panel"))); path = QPainterPath()
        if kind == "and":
            path.moveTo(x, y); path.lineTo(x + w * 0.55, y)
            path.arcTo(QRectF(x + w * 0.1, y, w * 0.9, h), 90, -180)
            path.lineTo(x, y + h); path.closeSubpath(); p.drawPath(path)
        elif kind in ("or", "xor"):
            path.moveTo(x, y)
            path.quadTo(x + w * 0.6, y, x + w, y + h / 2)
            path.quadTo(x + w * 0.6, y + h, x, y + h)
            path.quadTo(x + w * 0.35, y + h / 2, x, y)
            p.drawPath(path)
            if kind == "xor":
                p.drawArc(QRectF(x - 10, y, 20, h), 90, -180)
        elif kind == "not":
            path.moveTo(x, y); path.lineTo(x, y + h)
            path.lineTo(x + w, y + h / 2); path.closeSubpath()
            p.drawPath(path); p.drawEllipse(QRectF(x + w, y + h / 2 - 4, 8, 8))
        elif kind == "mux":
            path.moveTo(x, y); path.lineTo(x + w, y + 6)
            path.lineTo(x + w, y + h - 6); path.lineTo(x, y + h)
            path.closeSubpath(); p.drawPath(path)
        else:
            p.drawRect(QRectF(x, y, w, h))
        if nd.get("label"):
            p.setPen(QColor(th("sch_text")))
            if kind == "const":
                p.drawText(QRectF(x - 6, y + h, w + 20, 16), Qt.AlignCenter,
                           nd["label"])
            elif kind == "box":
                p.drawText(QRectF(x, y, w, h), Qt.AlignCenter, nd["label"])
            elif kind == "mux":
                p.drawText(QRectF(x, y, w, h), Qt.AlignCenter, "MUX")
    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing, True)
        p.fillRect(self.rect(), QColor(th("sch_bg")))
        if self.msg:
            p.setPen(QColor(th("sub")))
            p.drawText(self.rect(), Qt.AlignCenter | Qt.TextWordWrap,
                       self.msg)
            return
        self._in_rects = []; fm = p.fontMetrics()
        port_w = max([fm.horizontalAdvance(s) for s in self.inputs +
                      self.outputs] + [30]) + 34
        for i, nm in enumerate(self.inputs):
            y = 56 + i * 44; r = QRectF(8, y, port_w, 24)
            self._in_rects.append((nm, r))
            on = self.live and self.values.get(nm, (0, 1))[0] == 1
            p.setPen(QPen(QColor(th("accent") if on else th("sch_port")), 1.5))
            p.setBrush(QColor(th("ok") if on else th("panel"))); p.drawRect(r)
            p.setBrush(QColor(th("sch_bg")))
            p.drawRect(QRectF(12, y + 6, 12, 12))
            p.setPen(QColor(th("sch_text")))
            p.drawText(QRectF(28, y, port_w - 20, 24),
                       Qt.AlignVCenter | Qt.AlignLeft,
                       (nm + ("=1" if on else "=0")) if self.live else nm)
        for i, nm in enumerate(self.outputs):
            y = 56 + i * 44
            p.setPen(QPen(QColor(th("sch_port")), 1.4))
            p.setBrush(QColor(th("panel")))
            p.drawRect(QRectF(self.width() - port_w - 8, y, port_w, 24))
            p.setPen(QColor(th("sch_text")))
            p.drawText(QRectF(self.width() - port_w - 8, y, port_w, 24),
                       Qt.AlignCenter, nm)
        offset = port_w + 24
        for nd in self.nodes: nd["px"] = offset - 130 + nd["x"]
        if self.highlight_pi is not None:
            p.setBrush(QColor(255, 165, 0, 40))
            p.setPen(QPen(QColor(th("warn")), 2, Qt.DashLine))
            for nd in self.nodes:
                if nd.get("pi") == self.highlight_pi:
                    p.drawRoundedRect(nd["px"] - 8, nd["y"] - 8,
                                      self.GATE_W + 16, 56, 8, 8)
        sinkcount = {}
        for nd in self.nodes:
            if nd.get("rank", 0) > self.reveal + 1: continue
            for net in nd["ins"]:
                src = self._net_driver.get(net)
                if src is None or src is nd: continue
                key = src["out"]
                sinkcount[key] = sinkcount.get(key, 0) + 1
                x1 = src.get("px", src.get("x", 0)) + \
                    (self.GATE_W + 10 if src["kind"] == "not" else self.GATE_W)
                y1 = src["y"] + 20
                x2 = nd["px"] - (18 if nd["kind"] == "not" else 0)
                y2 = nd["y"] + 20
                xm = x1 + 24 + (sinkcount[key] % 5) * 7
                p.setPen(self._wire_pen(net, src))
                for (ax, ay), (bx, by) in zip(
                        [(x1, y1), (xm, y1), (xm, y2), (x2, y2)],
                        [(xm, y1), (xm, y2), (x2, y2), (x2, y2)]):
                    p.drawLine(int(ax), int(ay), int(bx), int(by))
                p.setBrush(QColor(th("sch_wire")))
                p.drawEllipse(int(x2) - 2, int(y2) - 2, 4, 4)
        for nd in self.nodes:
            if nd.get("rank", 0) <= self.reveal:
                self._draw_gate(p, nd, nd.get("px", nd["x"]), nd["y"])

class FramebufferWidget(QWidget):
    def __init__(self):
        super().__init__(); self.pixels = None
        self.info = ("No frame yet. Run a VGA lesson, then press "
                     "'Render last run'.")
        self.setMinimumSize(320, 260)
    def _find(self, series, name):
        for s in series:
            if s["name"] == name or s["name"].endswith("." + name):
                return s["values"]
        return None
    def render(self, times, series, spec):
        w, h = spec.get("w", 64), spec.get("h", 48)
        xv = self._find(series, spec["x"]); yv = self._find(series, spec["y"])
        if xv is None or yv is None:
            self.info = f"signals '{spec['x']}' / '{spec['y']}' not found"
            self.pixels = None; self.update(); return False
        rs = self._find(series, spec["r"]); gs = self._find(series, spec["g"])
        bs = self._find(series, spec["b"]); sb = None
        if rs is not None and gs is not None and bs is not None:
            def col(k):
                return tuple(0 if "x" in s[k] else int(s[k], 2)
                             for s in (rs, gs, bs))
            ndata = min(len(rs), len(gs), len(bs))
        else:
            sb = self._find(series, spec.get("rgb", "rgb"))
            if sb is None:
                self.info = "need 1-bit r/g/b signals (or an 'rgb' bus)"
                self.pixels = None; self.update(); return False
            col = lambda k: (0 if "x" in sb[k] else int(sb[k], 2),) * 3
            ndata = len(sb)
        pix = [0] * (w * h); drawn = 0
        n = min(len(times), len(xv), len(yv), ndata)
        for k in range(n):
            if "x" in xv[k] or "x" in yv[k]: continue
            X, Y = int(xv[k], 2), int(yv[k], 2)
            if 0 <= X < w and 0 <= Y < h:
                r, g, b = col(k)
                pix[Y * w + X] = (r * 210 << 16) | (g * 210 << 8) | (b * 210)
                drawn += 1
        self.pixels = (w, h, pix)
        self.info = f"{drawn} pixel events → {w}×{h} framebuffer"
        self.setMinimumSize(w * 6 + 20, h * 6 + 46); self.update()
        return True
    def paintEvent(self, _):
        p = QPainter(self); p.fillRect(self.rect(), QColor(th("editor_bg")))
        p.setPen(QColor(th("sub"))); p.drawText(8, 16, self.info)
        if not self.pixels: return
        w, h, pix = self.pixels
        sc = max(1, min((self.width() - 16) // w, (self.height() - 32) // h))
        ox, oy = 8, 26
        for y in range(h):
            for x in range(w):
                p.fillRect(ox + x * sc, oy + y * sc, max(1, sc - 1),
                           max(1, sc - 1),
                           QColor(pix[y * w + x] or 0x14171e))

class PipelineDiagramWidget(QWidget):
    def __init__(self):
        super().__init__(); self.data = None
        self.info = ("No pipeline trace yet. Run a pipeline lesson, then "
                     "press 'Render last run'.")
        self.setMinimumSize(340, 220)
    def _find(self, series, name):
        for s in series:
            if s["name"] == name or s["name"].endswith("." + name): return s
        return None
    def render(self, times, series, spec):
        clk = self._find(series, spec.get("clk", "clk"))
        stb = self._find(series, spec["stages"])
        if not clk or not stb:
            self.info = "clock / stages signals not found in the last run"
            self.data = None; self.update(); return False
        names = spec.get("names", ["IF", "ID", "EX", "MEM", "WB"])
        cyc, stalls, flushes = [], [], []
        aux = {k: (self._find(series, spec[k]) if spec.get(k) else None)
               for k in ("stall", "flush")}
        for k in range(min(len(times), len(clk["values"]), len(stb["values"]))):
            if clk["values"][k] != "1": continue
            v = stb["values"][k]
            cyc.append(0 if "x" in v else int(v, 2))
            row = []
            for s in aux.values():
                if s is None: row.append(0)
                else:
                    vv = s["values"][k] if k < len(s["values"]) else "x"
                    row.append(0 if "x" in vv else int(vv, 2))
            stalls.append(row[0]); flushes.append(row[1] if len(row) > 1 else 0)
        self.data = (names, cyc, stalls, flushes)
        self.info = f"{len(cyc)} clock cycles sampled"
        self.setMinimumSize(90 + min(len(cyc), 120) * 22 + 20,
                            70 + len(names) * 22 + 40)
        self.update(); return True
    def paintEvent(self, _):
        p = QPainter(self); p.fillRect(self.rect(), QColor(th("editor_bg")))
        p.setPen(QColor(th("sub"))); p.drawText(8, 16, self.info)
        if not self.data: return
        names, cyc, stalls, flushes = self.data
        cs = 22; ox, oy = 70, 34
        p.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        for j, nm in enumerate(names):
            p.setPen(QColor(th("text")))
            p.drawText(6, oy + j * cs, 60, cs,
                       Qt.AlignVCenter | Qt.AlignRight, nm)
        maxc = min(len(cyc), max(4, (self.width() - ox - 10) // cs))
        for i in range(maxc):
            x = ox + i * cs
            if stalls[i]:
                p.fillRect(x, oy, cs, cs * len(names),
                           QColor(255, 166, 87, 42))
            for j in range(len(names)):
                p.setPen(QColor(th("border")))
                p.drawRect(x, oy + j * cs, cs, cs)
                if cyc[i] >> j & 1:
                    p.fillRect(x + 2, oy + j * cs + 2, cs - 4, cs - 4,
                               QColor(th("accent")))
            if flushes[i]:
                p.setPen(QPen(QColor(th("err")), 2))
                p.drawLine(x + 4, oy + 6, x + cs - 4, oy + cs - 6)
                p.drawLine(x + cs - 4, oy + 6, x + 4, oy + cs - 6)
            if i % 5 == 0:
                p.setPen(QColor(th("sub")))
                p.drawText(x, oy + cs * len(names) + 4, cs, 14,
                           Qt.AlignCenter, str(i))
        if len(cyc) > maxc:
            p.setPen(QColor(th("warn")))
            p.drawText(ox, oy + cs * len(names) + 22, 340, 14,
                       f"… {len(cyc) - maxc} more cycles (widen window)")

class SetupHoldCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.period, self.setup, self.hold, self.off = 20, 3, 2, 5
        self.setMinimumHeight(200)
    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing, True)
        p.fillRect(self.rect(), QColor(th("editor_bg")))
        w, h = self.width(), self.height(); x0, x1 = 46, w - 20
        T = float(self.period); ppx = (x1 - x0) / (2.5 * T)
        X = lambda t: x0 + t * ppx; edge = T
        viol = -self.setup < self.off < self.hold
        band = QColor(229, 83, 75, 46) if viol else QColor(80, 140, 255, 34)
        for a, b in ((edge - self.setup, edge), (edge, edge + self.hold)):
            p.fillRect(int(X(a)), 30, max(1, int(X(b) - X(a))), h - 70, band)
        p.setPen(QColor(th("sub")))
        p.drawText(int(X(edge - self.setup)) - 20, 18, 160, 14, Qt.AlignLeft,
                   "setup window")
        p.drawText(int(X(edge)) + 4, 18, 160, 14, Qt.AlignLeft, "hold window")
        marks = sorted([(0, "r"), (T / 2, "f"), (T, "r"), (1.5 * T, "f"),
                        (2 * T, "r"), (2.5 * T, "f")])
        pts, lvl = [(x0, 52)], 52
        for t, kind in marks:
            xx = X(t); pts.append((xx, lvl))
            lvl = 96 if kind == "f" else 52; pts.append((xx, lvl))
        p.setPen(QPen(QColor(th("wave_sig")), 2))
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            p.drawLine(int(ax), int(ay), int(bx), int(by))
        xd = X(max(0.02, edge + self.off))
        p.setPen(QPen(QColor(th("wave_bus")), 2))
        p.drawLine(x0, 150, int(xd), 150)
        p.drawLine(int(xd), 150, int(xd), 178)
        p.drawLine(int(xd), 178, x1, 178)
        p.setPen(QColor(th("text")))
        p.drawText(8, 60, "clk"); p.drawText(8, 160, "data")
        p.setPen(QColor(th("err") if viol else th("ok")))
        p.drawText(10, h - 8, w - 20, 16,
                   "SETUP/HOLD VIOLATION — data edge lands inside the "
                   "sampling window (metastability risk!)" if viol else
                   "OK — data transition is safely outside the setup/hold "
                   "windows")

class SetupHoldDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Setup / Hold Lab")
        self.resize(760, 380)
        v = QVBoxLayout(self); self.canvas = SetupHoldCanvas()
        v.addWidget(self.canvas, 1)
        form = QHBoxLayout()
        def slider(lo, hi, val, cb):
            s = QSlider(Qt.Horizontal); s.setRange(lo, hi); s.setValue(val)
            s.valueChanged.connect(cb); form.addWidget(s); return s
        form.addWidget(QLabel("Clock period:"))
        slider(12, 40, 20, lambda x: self._set("period", x))
        form.addWidget(QLabel("Setup:"))
        slider(0, 8, 3, lambda x: self._set("setup", x))
        form.addWidget(QLabel("Hold:"))
        slider(0, 6, 2, lambda x: self._set("hold", x))
        form.addWidget(QLabel("Data edge offset:"))
        slider(-12, 12, 5, lambda x: self._set("off", x))
        self.anim_cb = QCheckBox("Animate")
        self.anim_cb.toggled.connect(self._toggle_anim)
        form.addWidget(self.anim_cb); v.addLayout(form)
        self._timer = QTimer(self); self._timer.setInterval(90)
        self._dir = [1]; self._timer.timeout.connect(self._tick)
        close = QPushButton("Close"); close.clicked.connect(self.accept)
        h = QHBoxLayout(); h.addStretch(1); h.addWidget(close); v.addLayout(h)
    def _set(self, attr, val):
        setattr(self.canvas, attr, val); self.canvas.update()
    def _toggle_anim(self, on):
        (self._timer.start if on else self._timer.stop)()
    def _tick(self):
        nv = self.canvas.off + self._dir[0]
        if nv >= 12 or nv <= -12: self._dir[0] *= -1
        self.canvas.off = nv; self.canvas.update()

# ══════════════════════════ DIALOGS ══════════════════════════
class QuizDialog(QDialog):
    def __init__(self, title, questions, parent=None):
        super().__init__(parent); self.setWindowTitle(f"Quiz — {title}")
        self.resize(580, 540); self.questions = questions
        self._answers = []
        outer = QVBoxLayout(self); scroll = QScrollArea()
        scroll.setWidgetResizable(True); inner = QWidget()
        v = QVBoxLayout(inner)
        for i, q in enumerate(questions):
            box = QGroupBox(f"{i + 1}. {q['q']}"); bv = QVBoxLayout(box)
            rbs = []
            for opt in q["options"]:
                rb = QRadioButton(opt); bv.addWidget(rb); rbs.append(rb)
            self._answers.append(rbs); v.addWidget(box)
        v.addStretch(1); scroll.setWidget(inner); outer.addWidget(scroll)
        row = QHBoxLayout(); row.addStretch(1)
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        submit = QPushButton("Submit"); submit.setDefault(True)
        submit.clicked.connect(self._submit)
        row.addWidget(cancel); row.addWidget(submit); outer.addLayout(row)
    def _submit(self):
        score = 0
        for rbs, q in zip(self._answers, self.questions):
            sel = next((i for i, rb in enumerate(rbs) if rb.isChecked()), -1)
            if sel == q["a"]: score += 1
        self.score = score; total = len(self.questions); rows = []
        for i, (rbs, q) in enumerate(zip(self._answers, self.questions)):
            sel = next((j for j, rb in enumerate(rbs) if rb.isChecked()), -1)
            ok = sel == q["a"]
            yours = q["options"][sel] if sel >= 0 else "—"
            line = (f"<p>{'✅' if ok else '❌'} <b>{i+1}. "
                    f"{html.escape(q['q'])}</b><br>your answer: "
                    f"{html.escape(yours)}")
            if not ok:
                line += (f"<br>correct: <b>"
                         f"{html.escape(q['options'][q['a']])}</b>")
            if q.get("why"): line += f"<br><i>{html.escape(q['why'])}</i>"
            rows.append(line + "</p>")
        verdict = ("Perfect! 🎉" if score == total else
                   "Good job — review the misses."
                   if score >= total / 2 else
                   "Keep studying — re-read the lesson and retry.")
        review = QDialog(self)
        review.setWindowTitle(f"Quiz result — {score}/{total}")
        rv = QVBoxLayout(review); web = QTextBrowser()
        web.setHtml(f"<h2>You scored {score} / {total}</h2><p>{verdict}</p>"
                    + "".join(rows)); rv.addWidget(web)
        close = QPushButton("Close"); close.clicked.connect(review.accept)
        h = QHBoxLayout(); h.addStretch(1); h.addWidget(close)
        rv.addLayout(h); review.resize(560, 480); review.exec()
        self.accept()

def predict_dialog(questions, parent=None):
    dlg = QDialog(parent); dlg.setWindowTitle("Predict before running!")
    v = QVBoxLayout(dlg)
    v.addWidget(QLabel("Commit to a prediction — then we run and compare:"))
    edits = []
    for qd in questions:
        v.addWidget(QLabel("• " + qd["q"])); e = QLineEdit()
        e.setPlaceholderText("your prediction"); v.addWidget(e)
        edits.append(e)
    h = QHBoxLayout(); h.addStretch(1)
    ok = QPushButton("Run & compare"); ok.setDefault(True)
    ok.clicked.connect(dlg.accept); h.addWidget(ok); v.addLayout(h)
    dlg.resize(500, 200)
    if dlg.exec() != QDialog.Accepted: return None
    return [e.text().strip() for e in edits]

def _same(val, guess, fmt, width):
    guess = guess.strip().lower().replace("_", "")
    if not guess: return False
    if fmt == "d":
        try: return int(guess, 0) == val
        except ValueError: return False
    want = format(val, "b").zfill(width) if fmt == "b" else format(val, "x")
    return guess.lstrip("0") == want.lstrip("0") or guess == want

class DebugDialog(QDialog):
    def __init__(self, gen, prog, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Step debugger — built-in simulator")
        self.resize(1000, 660)
        self.gen, self.prog, self.snap = gen, prog, None
        v = QVBoxLayout(self); self.wave = WaveformViewer()
        sc = QScrollArea(); sc.setWidgetResizable(True)
        sc.setWidget(self.wave); v.addWidget(sc, 2)
        self.table = QTableWidget(); self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["net", "width", "value"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch); v.addWidget(self.table, 3)
        self.lbl = QLabel("press Step"); self.covlbl = QLabel("")
        v.addWidget(self.lbl); v.addWidget(self.covlbl)
        h = QHBoxLayout()
        for txt, fn in (("Step", lambda: self.step(1)),
                        ("Step ×10", lambda: self.step(10)),
                        ("Run to end", self.run_all)):
            b = QPushButton(txt); b.clicked.connect(fn); h.addWidget(b)
        h.addStretch(1); cl = QPushButton("Close")
        cl.clicked.connect(self.accept); h.addWidget(cl); v.addLayout(h)
        self.step()
    def refresh(self):
        s = self.snap
        if not s: return
        self.lbl.setText(f"time = {s['time']}" +
                         ("   (finished)" if s["done"] else ""))
        self.wave.set_data(list(s["times"]), s["series"])
        ctx = s["ctx"]
        names = [g for g in self.prog.order
                 if self.prog.widths.get(g, 1) <= 16][:250]
        self.table.setRowCount(len(names))
        for r, g in enumerate(names):
            w = self.prog.widths.get(g, 1)
            if g not in ctx.written: shown = "x"
            elif w > 8: shown = format(ctx.env.get(g, 0), "x")
            elif w > 1: shown = format(ctx.env.get(g, 0), "b").zfill(w)
            else: shown = str(ctx.env.get(g, 0))
            for c, txt in enumerate((g, str(w), shown)):
                self.table.setItem(r, c, QTableWidgetItem(txt))
        cov = coverage_report(self.prog, ctx)
        self.covlbl.setText("coverage: " + " · ".join(cov) if cov else "")
    def step(self, n=1):
        for _ in range(n):
            self.snap = next(self.gen, None)
            if self.snap is None or self.snap.get("done"): break
        self.refresh()
    def run_all(self):
        while True:
            self.snap = next(self.gen, None)
            if self.snap is None or self.snap.get("done"): break
        self.refresh()

class RandomExerciseDialog(QDialog):
    def __init__(self, main, parent=None):
        super().__init__(parent or main); self.main = main
        self.setWindowTitle("Random exercise generator")
        self.resize(640, 500)
        v = QVBoxLayout(self); top = QHBoxLayout()
        top.addWidget(QLabel("Inputs:"))
        self.n_in = QSpinBox(); self.n_in.setRange(2, 4)
        self.n_in.setValue(3); top.addWidget(self.n_in)
        b = QPushButton("Generate"); b.clicked.connect(self._gen)
        top.addWidget(b); top.addStretch(1); v.addLayout(top)
        self.view = QTextBrowser(); v.addWidget(self.view, 1)
        h = QHBoxLayout(); h.addStretch(1)
        load = QPushButton("Load starter → editor")
        load.clicked.connect(self._load)
        chk = QPushButton("Check my answer"); chk.clicked.connect(self._check)
        close = QPushButton("Close"); close.clicked.connect(self.reject)
        h.addWidget(load); h.addWidget(chk); h.addWidget(close)
        v.addLayout(h); self._gen()
    def _gen(self):
        self.spec, self.starter, ones = gen_random_spec(self.n_in.value())
        n = self.n_in.value()
        rows = "".join(
            f"<tr><td>{format(r, f'0{n}b')}</td><td><b>"
            f"{'1' if r in ones else '0'}</b></td></tr>"
            for r in range(1 << n))
        self.view.setHtml(
            f"<h3>Implement: <code>y = Σm({', '.join(map(str, ones))})"
            f"</code></h3><p>Module <code>rand_fn</code>, inputs, output "
            f"<code>y</code>. Tip: K-map your way to a minimal SOP.</p>"
            f"<table border='1' cellpadding='4' cellspacing='0'>"
            f"<tr><th>{' '.join(self.spec['inputs'])}</th><th>y</th></tr>"
            f"{rows}</table>")
    def _load(self):
        if self.main._confirm_overwrite(self.main.design_edit):
            self.main.design_edit.setPlainText(self.starter)
            self.main.design_edit.set_language("verilog")
            self.main.editors_tab.setCurrentIndex(0)
    def _check(self):
        self.main._check_against(self.spec, "Random exercise solved! 🎲")

class AssemblerDialog(QDialog):
    def __init__(self, main, parent=None):
        super().__init__(parent or main); self.main = main
        self.setWindowTitle("Mini-assembler — CPU-II ISA")
        self.resize(780, 520)
        split = QHBoxLayout(); lv = QVBoxLayout()
        lv.addWidget(QLabel("Assembly — 'label: MNEMONIC arg' ; comments. "
                            "Ops: " + " ".join(ASM_OPS)))
        self.edit = QPlainTextEdit(); self.edit.setFont(mono_font(10))
        self.edit.setPlainText(ASM_SAMPLE); lv.addWidget(self.edit, 1)
        w1 = QWidget(); w1.setLayout(lv); split.addWidget(w1, 1)
        rv = QVBoxLayout(); self.out = QTableWidget(0, 4)
        self.out.setHorizontalHeaderLabels(["addr", "hex", "binary", "source"])
        self.out.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.out.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.out.setFont(mono_font(9)); rv.addWidget(self.out, 1)
        self.status = QLabel(""); rv.addWidget(self.status)
        hb = QHBoxLayout()
        for txt, fn in (("Assemble", self._asm),
                        ("Write rom.hex", self._write),
                        ("Copy $readmemh line", self._snippet)):
            b = QPushButton(txt); b.clicked.connect(fn); hb.addWidget(b)
        rv.addLayout(hb)
        w2 = QWidget(); w2.setLayout(rv); split.addWidget(w2, 1)
        v = QVBoxLayout(self); v.addLayout(split, 1)
        cl = QPushButton("Close"); cl.clicked.connect(self.accept)
        hh = QHBoxLayout(); hh.addStretch(1); hh.addWidget(cl)
        v.addLayout(hh); self.prog, self.srcs = [], []; self._asm()
    def _asm(self):
        try: self.prog, self.srcs = assemble(self.edit.toPlainText())
        except ValueError as e:
            self.status.setText(f"✘ {e}")
            self.status.setStyleSheet(f"color:{th('err')};"); return
        self.out.setRowCount(len(self.prog))
        for i, (v, s) in enumerate(zip(self.prog, self.srcs)):
            for c, txt in enumerate((str(i), f"{v:02x}",
                                     format(v, "08b"), s)):
                self.out.setItem(i, c, QTableWidgetItem(txt))
        self.status.setText(f"✔ {len(self.prog)} word(s)")
        self.status.setStyleSheet(f"color:{th('ok')};")
    def _write(self):
        if not self.prog: self._asm()
        try:
            with open(os.path.join(SESSION_DIR, "rom.hex"), "w",
                      encoding="utf-8") as f:
                f.write("\n".join(f"{v:02x}" for v in self.prog) + "\n")
            self.status.setText(f"✔ wrote rom.hex ({len(self.prog)} words) — "
                                "press Run")
            self.main._log("[asm] rom.hex written to the session dir — "
                           "$readmemh will find it.", th("ok"))
        except OSError as e:
            QMessageBox.warning(self, "Assembler", str(e))
    def _snippet(self):
        QApplication.clipboard().setText('initial $readmemh("rom.hex", rom);')

class ExamDialog(QDialog):
    def __init__(self, main, parent=None):
        super().__init__(parent or main); self.main = main
        self.setWindowTitle("Exam mode — single attempt")
        self.resize(740, 580); self.stack = QStackedWidget()
        v = QVBoxLayout(self); v.addWidget(self.stack, 1)
        cfg = QWidget(); cv = QVBoxLayout(cfg)
        cv.addWidget(QLabel(
            "Timed assessment: N random quiz questions (no explanations "
            "until the end), then ONE generated logic exercise.\nThe clock "
            "runs through both parts; the result is stored in your progress."))
        f = QFormLayout()
        self.n_q = QSpinBox(); self.n_q.setRange(3, 30); self.n_q.setValue(8)
        self.n_min = QSpinBox(); self.n_min.setRange(1, 60)
        self.n_min.setValue(6)
        f.addRow("Questions:", self.n_q)
        f.addRow("Minutes total:", self.n_min)
        cv.addLayout(f)
        b = QPushButton("Start exam"); b.clicked.connect(self._start)
        cv.addWidget(b, 0, Qt.AlignRight); self.stack.addWidget(cfg)
        qz = QWidget(); qv = QVBoxLayout(qz)
        self.time_lbl = QLabel(""); qv.addWidget(self.time_lbl)
        sc = QScrollArea(); sc.setWidgetResizable(True)
        self.q_inner = QWidget(); self.q_v = QVBoxLayout(self.q_inner)
        sc.setWidget(self.q_inner); qv.addWidget(sc, 1)
        qb = QPushButton("Submit answers"); qb.clicked.connect(self._finish_quiz)
        qv.addWidget(qb, 0, Qt.AlignRight); self.stack.addWidget(qz)
        ex = QWidget(); ev = QVBoxLayout(ex)
        ev.addWidget(QLabel("Part 2 — implement the function below "
                            "(timer still running):"))
        self.ex_info = QTextBrowser(); self.ex_info.setMaximumHeight(210)
        ev.addWidget(self.ex_info)
        self.ex_edit = QPlainTextEdit(); self.ex_edit.setFont(mono_font(10))
        ev.addWidget(self.ex_edit, 1)
        eh = QHBoxLayout()
        chk = QPushButton("Check"); chk.clicked.connect(self._check_ex)
        give = QPushButton("Give up"); give.clicked.connect(self._fail_ex)
        eh.addWidget(chk); eh.addWidget(give); eh.addStretch(1)
        ev.addLayout(eh); self.stack.addWidget(ex)
        res = QWidget(); rv = QVBoxLayout(res)
        self.res_view = QTextBrowser(); rv.addWidget(self.res_view, 1)
        cl = QPushButton("Close"); cl.clicked.connect(self.accept)
        hh = QHBoxLayout(); hh.addStretch(1); hh.addWidget(cl)
        rv.addLayout(hh); self.stack.addWidget(res)
        self._timer = QTimer(self); self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
    def _start(self):
        pool = [(t["title"], q) for t in TASKS for q in t.get("quiz", [])]
        random.shuffle(pool)
        self.questions = pool[:self.n_q.value()]
        if not self.questions:
            QMessageBox.information(self, "Exam", "No quizzes available.")
            return
        while self.q_v.count():
            it = self.q_v.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        self._rbs = []
        for i, (src, q) in enumerate(self.questions):
            box = QGroupBox(f"{i + 1}. {q['q']}   ({src})")
            bv = QVBoxLayout(box); rbs = []
            for opt in q["options"]:
                rb = QRadioButton(opt); bv.addWidget(rb); rbs.append(rb)
            self._rbs.append(rbs); self.q_v.addWidget(box)
        self.q_v.addStretch(1)
        self.total = len(self.questions)
        self._left = self.n_min.value() * 60
        self._timer.start(); self._tick(); self.stack.setCurrentIndex(1)
    def _tick(self):
        m, s = divmod(max(0, self._left), 60)
        self.time_lbl.setText(f"⏱ time left: {m:02d}:{s:02d}")
        if self._left <= 0:
            self._timer.stop()
            if self.stack.currentIndex() == 1: self._finish_quiz()
            elif self.stack.currentIndex() == 2: self._fail_ex()
        self._left -= 1
    def _finish_quiz(self):
        self._timer.stop(); self.score = 0
        for rbs, (_s, q) in zip(self._rbs, self.questions):
            sel = next((i for i, rb in enumerate(rbs) if rb.isChecked()), -1)
            if sel == q["a"]: self.score += 1
        self.spec, starter, ones = gen_random_spec(3)
        rows = "".join(f"<tr><td>{r:03b}</td><td><b>"
                       f"{'1' if r in ones else '0'}</b></td></tr>"
                       for r in range(8))
        self.ex_info.setHtml(
            "<p>Module <code>rand_fn</code>, inputs a b c, output y."
            "<table border='1' cellpadding='4'><tr><th>a b c</th><th>y</th>"
            f"</tr>{rows}</table>")
        self.ex_edit.setPlainText(starter)
        self._timer.start(); self.stack.setCurrentIndex(2)
    def _check_ex(self):
        ok, msg, _p, _i, _o = self.main._grade(self.spec,
                                               self.ex_edit.toPlainText())
        if ok: self.ex_passed = True; self._done()
        else: QMessageBox.warning(self, "Check", msg.splitlines()[0])
    def _fail_ex(self):
        self._timer.stop(); self._done()
    def _done(self):
        self._timer.stop(); passed = getattr(self, "ex_passed", False)
        self.main._record_exam(self.score, self.total, passed)
        ok = self.score >= self.total * 0.7 and passed
        self.res_view.setHtml(
            f"<h2>Exam {'PASSED ✅' if ok else 'not passed'}</h2>"
            f"<p>Quiz: {self.score}/{self.total}</p>"
            f"<p>Exercise: {'solved ✅' if passed else 'not solved ✘'}</p>"
            "<p>Saved to your progress file.</p>")
        self.stack.setCurrentIndex(3)

# ══════════════════════════ ACHIEVEMENTS ══════════════════════════
def _perfect_quiz(mw):
    for k, v in mw.quiz_scores.items():
        t = next((x for x in TASKS if x["id"] == k and x.get("quiz")), None)
        if t and v == len(t["quiz"]): return True
    return False

ACHIEVEMENTS = [
    ("first_run", "⚡ First Spark", "Ran your first simulation",
     lambda mw: mw.runs >= 1),
    ("ten_runs", "🔥 Simulation Habit", "Ran 10 simulations",
     lambda mw: mw.runs >= 10),
    ("first_check", "✅ Graded", "Passed a checked exercise",
     lambda mw: len(mw.ex_passed) >= 1),
    ("five_checks", "🧠 Logic Adept", "Passed 5 exercises",
     lambda mw: len(mw.ex_passed) >= 5),
    ("perfect_quiz", "🎯 Perfect Score", "100% on a quiz", _perfect_quiz),
    ("nand_crafter", "🔶 NAND Crafter", "Built XOR from four NANDs",
     lambda mw: "m2l5" in mw.ex_passed),
    ("bug_hunter", "🐞 Bug Hunter", "Solved all four bug hunts",
     lambda mw: {"bh1", "bh2", "bh3", "bh4"} <= mw.ex_passed),
    ("fsm_tamer", "🤖 FSM Tamer", "Hit the coverage goal",
     lambda mw: "m7l3" in mw.ex_passed),
    ("capstonaut", "🚀 Capstonaut", "Finished any capstone project",
     lambda mw: any(t["id"] in mw.completed and
                    t["module"].startswith("Capstone") for t in TASKS)),
    ("scholar", "🎓 Scholar", "Completed 10 lessons",
     lambda mw: len(mw.completed) >= 10),
    ("streak_7", "📅 Week Streak", "7 days in a row",
     lambda mw: mw.streak() >= 7),
]

REFERENCE_HTML = """<h2>Quick Reference</h2>
<h3>Skeletons</h3><pre>module m #(parameter W=8)(input clk, rst,
  input [W-1:0] d, output reg [W-1:0] q);
  always @(posedge clk) q &lt;= d; endmodule</pre>
<h3>Assignments</h3><pre>assign y = a &amp; b;      // continuous
always @(*) y = a;        // combinational (blocking =)
always @(posedge clk) q &lt;= d;  // sequential (&lt;=)</pre>
<h3>Built-in simulator subset</h3><pre>assign (+ #delay), always @(*) /
@(posedge|negedge ...), initial + #delays, for, if/else, case(+default),
arrays reg [...] mem [0:N], $readmemh/$readmemb, assert(expr) else
 $error(...), $urandom(lo,hi), $prob(pct), $display %b %d %h, $finish,
 $time, $random, $clog2</pre>
<h3>Pitfalls</h3><ul><li>= in clocked blocks; &lt;= in comb ones.</li>
<li>Missing default → latch. Two writers on one reg → race.</li>
<li>Uninitialized registers show x until first written — use resets.</li>
</ul>"""

# ══════════════════════════ MAIN WINDOW ══════════════════════════
def detect_language(code):
    if re.search(r"\bentity\b|\barchitecture\b", code, re.I): return "vhdl"
    return "verilog"

def is_sv(code):
    return bool(re.search(r"\balways_ff\b|\balways_comb\b|\balways_latch\b|"
                          r"\btypedef\b|\blogic\b", code))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Verilog · VHDL · SystemVerilog")
        self.resize(1500, 890); self.setMinimumSize(1080, 660)
        self.settings = QSettings("HDLTutor", "HDLTutor")
        self.iverilog = shutil.which("iverilog")
        self.vvp = shutil.which("vvp")
        self.ghdl = shutil.which("ghdl"); self.yosys = shutil.which("yosys")
        self.nextpnr = shutil.which("nextpnr-ice40")
        self.completed, self.ex_passed, self.quiz_scores = set(), set(), {}
        self.runs, self.days, self.ach, self.lesson_code = 0, [], set(), {}
        self.exams = []; self._sel_task_id = None
        self._load_progress()
        self._build_ui(); self._build_menu_toolbar()
        self._populate_tree(); self._update_status_tools()
        self._log_welcome(); self._restore_session()
        self.apply_theme(self.settings.value("theme", "dark"))
    # ---------------- UI ----------------
    def _build_ui(self):
        central = QWidget(); root = QHBoxLayout(central)
        root.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Horizontal); root.addWidget(self.splitter)
        left = QWidget(); lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        self.tree_filter = QLineEdit()
        self.tree_filter.setPlaceholderText("Filter lessons…")
        self.tree_filter.textChanged.connect(self._filter_tree)
        lv.addWidget(self.tree_filter)
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(["Curriculum"])
        self.tree.setFixedWidth(250)
        self.tree.currentItemChanged.connect(self._on_tree_select)
        self.lesson_view = QTextBrowser()
        self.lesson_view.setOpenExternalLinks(True)
        btns = QHBoxLayout()
        self.btn_example = QPushButton("Load Example")
        self.btn_starter = QPushButton("Load Starter")
        self.btn_check = QPushButton("Check"); self.btn_quiz = QPushButton("Quiz")
        self.btn_done = QPushButton("Mark Complete")
        self.btn_done.setCheckable(True)
        for b in (self.btn_example, self.btn_starter, self.btn_check,
                  self.btn_quiz, self.btn_done): btns.addWidget(b)
        btns2 = QHBoxLayout()
        self.btn_prev_sol = QPushButton("◀ Prev Stage")
        self.btn_solution = QPushButton("Solution")
        for b in (self.btn_prev_sol, self.btn_solution): btns2.addWidget(b)
        btns2.addStretch(1)
        self.btn_example.clicked.connect(self._load_example)
        self.btn_starter.clicked.connect(self._load_starter)
        self.btn_check.clicked.connect(self._check_exercise)
        self.btn_quiz.clicked.connect(self._take_quiz)
        self.btn_done.toggled.connect(self._toggle_done)
        self.btn_prev_sol.clicked.connect(self._load_prev_solution)
        self.btn_solution.clicked.connect(self._load_solution)
        lv.addWidget(self.tree, 3); lv.addWidget(self.lesson_view, 5)
        lv.addLayout(btns); lv.addLayout(btns2)
        self.splitter.addWidget(left)
        mid = QWidget(); mv = QVBoxLayout(mid)
        mv.setContentsMargins(0, 0, 0, 0)
        self.editors_tab = QTabWidget()
        self.design_edit = CodeEditor(
            "// Verilog/VHDL design — pick a lesson, then Load Starter.")
        self.tb_edit = CodeEditor(
            "// Optional testbench ($display, $finish) — used by Run.")
        self.editors_tab.addTab(self.design_edit, "design")
        self.editors_tab.addTab(self.tb_edit, "testbench")
        self.design_edit.textChanged.connect(lambda: self._on_code_changed(0))
        self.tb_edit.textChanged.connect(lambda: self._on_code_changed(1))
        self._lint_timer = QTimer(self); self._lint_timer.setSingleShot(True)
        self._lint_timer.setInterval(900)
        self._lint_timer.timeout.connect(self._run_lint)
        self.design_edit.textChanged.connect(lambda: self._lint_timer.start())
        self.find_bar = FindBar(lambda: (self.design_edit
            if self.editors_tab.currentIndex() == 0 else self.tb_edit))
        mv.addWidget(self.editors_tab, 1); mv.addWidget(self.find_bar)
        self.splitter.addWidget(mid)
        self.results_tab = QTabWidget()
        self.console = QPlainTextEdit(); self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(5000)
        self.console.setFont(mono_font(9))
        self.results_tab.addTab(self.console, "Console")
        # truth table
        tt_widget = QWidget(); tv = QVBoxLayout(tt_widget)
        tv.setContentsMargins(4, 4, 4, 4)
        self.tt_label = QLabel("Truth table")
        self.tt_table = QTableWidget()
        self.tt_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tt_table.setFont(mono_font(9))
        self.tt_table.horizontalHeader().setDefaultSectionSize(52)
        tt_btns = QHBoxLayout()
        kmap_btn = QPushButton("K-map / Minimize…")
        csv_btn = QPushButton("Export CSV")
        kmap_btn.clicked.connect(self._open_kmap)
        csv_btn.clicked.connect(self._export_csv)
        tt_btns.addWidget(self.tt_label, 1); tt_btns.addWidget(kmap_btn)
        tt_btns.addWidget(csv_btn); tv.addLayout(tt_btns)
        tv.addWidget(self.tt_table)
        self.tt_widget = tt_widget
        self.results_tab.addTab(tt_widget, "Truth Table")
        # waveform
        self.wave = WaveformViewer()
        wave_scroll = QScrollArea(); wave_scroll.setWidgetResizable(True)
        wave_scroll.setWidget(self.wave)
        self.results_tab.addTab(wave_scroll, "Waveform")
        # schematic
        sch_widget = QWidget(); sv = QVBoxLayout(sch_widget)
        sv.setContentsMargins(0, 0, 0, 0)
        sch_btns = QHBoxLayout(); self.yosys_lbl = QLabel("")
        sch_crit = QPushButton("Critical path")
        sch_crit.clicked.connect(self._critical_path)
        sch_gate = QPushButton("Gate view (Yosys)")
        sch_gate.setEnabled(bool(self.yosys))
        sch_gate.clicked.connect(self._show_gate_view)
        sch_pnr = QPushButton("FPGA stats")
        sch_pnr.setEnabled(bool(self.yosys and self.nextpnr))
        sch_pnr.clicked.connect(self._fpga_stats)
        sch_replay = QPushButton("▶ Replay")
        sch_replay.clicked.connect(self._replay_waves)
        sch_png = QPushButton("Export PNG")
        sch_png.clicked.connect(self._export_schematic)
        for b in (sch_crit, sch_gate, sch_pnr, sch_replay, sch_png):
            sch_btns.addWidget(b)
        sch_btns.addWidget(self.yosys_lbl, 1)
        self.schematic = SchematicWidget()
        self.schematic.toggle_cb = lambda nm, v: self._sch_toggle(nm, v)
        sch_scroll = QScrollArea(); sch_scroll.setWidgetResizable(True)
        sch_scroll.setWidget(self.schematic)
        sv.addLayout(sch_btns); sv.addWidget(sch_scroll)
        self.results_tab.addTab(sch_widget, "Schematic")
        # memory
        mem_widget = QWidget(); mv2 = QVBoxLayout(mem_widget)
        mv2.setContentsMargins(4, 4, 4, 4)
        mem_top = QHBoxLayout(); mem_top.addWidget(QLabel("Memory:"))
        self.mem_combo = QComboBox()
        self.mem_combo.currentIndexChanged.connect(
            lambda _i: self._fill_mem(self.mem_combo.currentText()))
        mem_top.addWidget(self.mem_combo, 1)
        self.mem_disasm = QCheckBox("disassemble (CPU-II)")
        self.mem_disasm.toggled.connect(
            lambda _i: self._fill_mem(self.mem_combo.currentText()))
        mem_top.addWidget(self.mem_disasm); mv2.addLayout(mem_top)
        self.mem_hint = QLabel("Run a design with arrays (reg […] mem [0:N]), "
                               "then see its contents here.")
        self.mem_hint.setWordWrap(True); mv2.addWidget(self.mem_hint)
        self.mem_table = QTableWidget(); self.mem_table.setColumnCount(5)
        self.mem_table.setHorizontalHeaderLabels(
            ["addr", "hex", "binary", "decimal", "disasm"])
        self.mem_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch)
        self.mem_table.setFont(mono_font(9))
        self.mem_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        mv2.addWidget(self.mem_table, 1)
        self.results_tab.addTab(mem_widget, "Memory")
        # framebuffer
        self.framew = FramebufferWidget()
        fw = QWidget(); fv2 = QVBoxLayout(fw); fv2.setContentsMargins(4, 4, 4, 4)
        fb = QHBoxLayout(); fb.addStretch(1)
        fb_btn = QPushButton("Render last run")
        fb_btn.clicked.connect(self._render_framebuffer); fb.addWidget(fb_btn)
        fv2.addLayout(fb); fv2.addWidget(self.framew, 1)
        self.results_tab.addTab(fw, "Framebuffer")
        # pipeline
        self.pipew = PipelineDiagramWidget()
        pw2 = QWidget(); pv2 = QVBoxLayout(pw2)
        pv2.setContentsMargins(4, 4, 4, 4)
        pb = QHBoxLayout(); pb.addStretch(1)
        pb_btn = QPushButton("Render last run")
        pb_btn.clicked.connect(self._render_pipeline); pb.addWidget(pb_btn)
        pv2.addLayout(pb); pv2.addWidget(self.pipew, 1)
        self.results_tab.addTab(pw2, "Pipeline")
        # playground
        self.playground = self._make_playground()
        self.results_tab.addTab(self.playground, "Playground")
        # reference
        self.reference = QTextBrowser(); self.reference.setHtml(REFERENCE_HTML)
        ref_find = QLineEdit(); ref_find.setPlaceholderText("Search…")
        ref_find.textChanged.connect(self._ref_search)
        ref_widget = QWidget(); rv = QVBoxLayout(ref_widget)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.addWidget(ref_find); rv.addWidget(self.reference)
        self.results_tab.addTab(ref_widget, "Reference")
        self.splitter.addWidget(self.results_tab)
        self.splitter.setSizes([350, 620, 500])
        self.splitter.setChildrenCollapsible(False)
        self.setCentralWidget(central)
        self.status_lesson = QLabel("Welcome!")
        self.status_progress = QLabel(""); self.status_tools = QLabel("")
        self.statusBar().addWidget(self.status_lesson, 1)
        theme_btn = QPushButton("◐ Theme"); theme_btn.setFlat(True)
        theme_btn.clicked.connect(self._toggle_theme)
        self.statusBar().addPermanentWidget(self.status_progress)
        self.statusBar().addPermanentWidget(theme_btn)
        self.statusBar().addPermanentWidget(self.status_tools)
        self._update_progress_label()
    def _make_playground(self):
        w = QWidget(); v = QVBoxLayout(w); top = QHBoxLayout()
        top.addWidget(QLabel("Inputs:"))
        spin = QSpinBox(); spin.setRange(1, 5); spin.setValue(2)
        top.addWidget(spin); top.addStretch(1); v.addLayout(top)
        sw_row = QHBoxLayout(); v.addLayout(sw_row)
        grid = QFormLayout(); v.addLayout(grid)
        state = {"sw": {}, "rows": []}
        info = QLabel("Type Verilog expressions (a & b, sel ? x : y, …); "
                      "outputs recompute live from the switches.")
        info.setWordWrap(True); v.addWidget(info); v.addStretch(1)
        def recalc():
            env = {n: (1 if b.isChecked() else 0)
                   for n, b in state["sw"].items()}
            ctx = Ctx(env=env, consts={}, widths={n: 1 for n in env})
            for name_e, expr_e, val_l in state["rows"]:
                try:
                    toks = tokenize(preprocess(expr_e.text())[0])
                    ast = Parser(toks).parse_expr()
                    val, _w = ev(ast, ctx)
                    env[name_e.text().strip()] = val
                    ctx.consts[name_e.text().strip()] = (val, _w)
                    val_l.setText(str(val))
                    val_l.setStyleSheet(f"color:{th('ok')};font-weight:bold;")
                except Exception:
                    val_l.setText("✗")
                    val_l.setStyleSheet(f"color:{th('err')};")
        def sync_inputs():
            while sw_row.count():
                it = sw_row.takeAt(0)
                if it.widget(): it.widget().deleteLater()
            state["sw"].clear()
            for i in range(spin.value()):
                nm = "abcd"[i]; btn = QToolButton()
                btn.setCheckable(True); btn.setText(f"{nm}=0")
                btn.setFixedSize(64, 34)
                btn.toggled.connect(lambda on, b=btn, n=nm:
                                    b.setText(f"{n}={'1' if on else '0'}"))
                btn.toggled.connect(lambda _o: recalc())
                sw_row.addWidget(btn); state["sw"][nm] = btn
            recalc()
        def add_output():
            name_e = QLineEdit("y"); expr_e = QLineEdit("a & b")
            val = QLabel("0"); row_h = QHBoxLayout()
            row_h.addWidget(name_e, 1); row_h.addWidget(QLabel("="))
            row_h.addWidget(expr_e, 3); row_h.addWidget(QLabel("→"))
            row_h.addWidget(val, 0)
            wrap = QWidget(); wrap.setLayout(row_h); grid.addRow(wrap)
            state["rows"].append((name_e, expr_e, val))
            name_e.textChanged.connect(recalc)
            expr_e.textChanged.connect(recalc)
        def rm_output():
            if not state["rows"]: return
            grid.removeRow(grid.rowCount() - 1)
            state["rows"].pop(); recalc()
        brow = QHBoxLayout()
        add_b = QPushButton("+ output"); rm_b = QPushButton("− output")
        add_b.clicked.connect(add_output); rm_b.clicked.connect(rm_output)
        brow.addWidget(add_b); brow.addWidget(rm_b); brow.addStretch(1)
        v.addLayout(brow)
        spin.valueChanged.connect(lambda _v: sync_inputs())
        sync_inputs(); add_output()
        return w
    def _ref_search(self, text):
        self.reference.moveCursor(QTextCursor.Start)
        if not text: return
        if not self.reference.find(text):
            self.reference.moveCursor(QTextCursor.Start)
    # ---------------- menus ----------------
    def _build_menu_toolbar(self):
        st = self.style(); tb = self.addToolBar("main"); tb.setMovable(False)
        def act(text, slot, icon=None, shortcut=None):
            a = QAction(text, self)
            if icon: a.setIcon(icon)
            if shortcut: a.setShortcut(QKeySequence(shortcut))
            a.triggered.connect(slot); return a
        self.act_open = act("Open", self._open_file,
            st.standardIcon(QStyle.SP_DialogOpenButton), "Ctrl+O")
        self.act_save = act("Save", self._save_file,
            st.standardIcon(QStyle.SP_DialogSaveButton), "Ctrl+S")
        self.act_run = act("Run", self._run,
            st.standardIcon(QStyle.SP_MediaPlay), "Ctrl+R")
        self.act_run_bi = act("Run (built-in)",
            lambda: self._run(force_builtin=True),
            st.standardIcon(QStyle.SP_ComputerIcon), "Ctrl+Shift+R")
        self.act_tt = act("Truth Table", self._show_truth_table,
            st.standardIcon(QStyle.SP_FileDialogListView), "Ctrl+T")
        self.act_sch = act("Schematic", self._show_schematic,
            st.standardIcon(QStyle.SP_FileDialogDetailedView), "Ctrl+Shift+T")
        for a in (self.act_open, self.act_save): tb.addAction(a)
        tb.addSeparator()
        for a in (self.act_run, self.act_run_bi, self.act_tt, self.act_sch):
            tb.addAction(a)
        m = self.menuBar()
        mf = m.addMenu("&File")
        mf.addAction(self.act_open); mf.addAction(self.act_save)
        mf.addSeparator()
        mf.addAction(act("Export Progress…", self._export_progress))
        mf.addAction(act("Import Progress…", self._import_progress))
        mf.addAction(act("Reset Progress…", self._reset_progress))
        mf.addSeparator()
        quit_a = QAction("Quit", self); quit_a.setShortcut("Ctrl+Q")
        quit_a.triggered.connect(self.close); mf.addAction(quit_a)
        ms = m.addMenu("&Simulate")
        for a in (self.act_run, self.act_run_bi, self.act_tt, self.act_sch):
            ms.addAction(a)
        ms.addSeparator()
        ms.addAction(act("Step debugger…", self._open_debugger))
        ms.addAction(act("Lint now", self._lint_now))
        ms.addAction(act("Generate testbench", self._gen_testbench))
        ms.addAction(act("Equivalence check…", self._equivalence))
        ms.addAction(act("Export VCD…", self._export_vcd))
        ms.addAction(act("Toggle-activity report", self._activity))
        ms.addAction(act("Clear Console", self.console.clear))
        mv_ = m.addMenu("&View")
        mv_.addAction(act("Toggle Dark/Light Theme", self._toggle_theme))
        mv_.addAction(act("Setup/Hold Lab…",
                          lambda: SetupHoldDialog(self).exec()))
        ml = m.addMenu("&Lessons")
        ml.addAction(act("Next Lesson", lambda: self._step_lesson(1), None,
                         "Alt+Right"))
        ml.addAction(act("Previous Lesson", lambda: self._step_lesson(-1),
                         None, "Alt+Left"))
        ml.addSeparator()
        ml.addAction(act("Progress Summary…", self._progress_dialog))
        ml.addAction(act("Restore saved work for this lesson",
                         self._restore_lesson_work))
        ml.addAction(act("Export this lesson as JSON…", self._export_lesson))
        ml.addAction(act("Import lesson pack…", self._import_pack))
        mt = m.addMenu("&Tools")
        mt.addAction(act("Mini-assembler…",
                         lambda: AssemblerDialog(self).exec()))
        mt.addAction(act("Exam mode…", lambda: ExamDialog(self).exec()))
        mt.addAction(act("Random exercise…", self._random_exercise))
        mh = m.addMenu("&Help")
        mh.addAction(act("About",
            lambda: QMessageBox.about(self, f"About {APP_NAME}",
                f"<b>{APP_NAME}</b><br>Built-in Verilog simulator, 40+ "
                "lessons, 7 capstones, verification lab, waveforms with "
                "cursors, live schematic, K-maps, exam mode.<br>Optional: "
                "iverilog, ghdl, yosys, nextpnr-ice40.")))
    # ---------------- progress ----------------
    def _load_progress(self):
        try:
            with open(PROGRESS_PATH, encoding="utf-8") as f:
                data = json.load(f)
            self.completed = set(data.get("completed", []))
            self.ex_passed = set(data.get("exercises", []))
            self.quiz_scores = dict(data.get("quiz", {}))
            self.runs = data.get("runs", 0)
            self.days = list(data.get("days", []))
            self.ach = set(data.get("ach", []))
            self.exams = list(data.get("exams", []))
        except (OSError, ValueError): pass
    def streak(self):
        days = set(self.days); s, d = 0, datetime.date.today()
        while d.isoformat() in days:
            s += 1; d -= datetime.timedelta(days=1)
        return s
    def _check_achievements(self):
        for aid, name, desc, fn in ACHIEVEMENTS:
            if aid in self.ach: continue
            try: got = fn(self)
            except Exception: got = False
            if got:
                self.ach.add(aid)
                self._log(f"🏆 Achievement: {name} — {desc}", th("ok"))
                self.statusBar().showMessage(f"🏆 {name}", 4000)
    def _save_progress(self):
        today = datetime.date.today().isoformat()
        if today not in self.days: self.days.append(today)
        try:
            with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
                json.dump({"completed": sorted(self.completed),
                           "exercises": sorted(self.ex_passed),
                           "quiz": self.quiz_scores, "runs": self.runs,
                           "days": self.days, "ach": sorted(self.ach),
                           "exams": self.exams}, f, indent=2)
        except OSError: pass
        self._update_progress_label(); self._check_achievements()
    def _counts(self):
        ex_total = sum(1 for t in TASKS if t.get("check") or
                       t.get("check_console") or t.get("check_wave") or
                       t.get("require_coverage") or t.get("check_model") or
                       t.get("check_assert") or t.get("check_props") or
                       t.get("check_plan") or t.get("cover_bins"))
        q_total = sum(1 for t in TASKS if t.get("quiz"))
        return (len(self.completed), len(TASKS), len(self.ex_passed),
                ex_total, len(self.quiz_scores), q_total)
    def _update_progress_label(self):
        lc, lt, ec, et, qc, qt = self._counts()
        self.status_progress.setText(
            f"Done {lc}/{lt} · Ex {ec}/{et} · Quiz {qc}/{qt} · "
            f"🔥{self.streak()}d")
    def _export_progress(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export progress",
                                              "hdl_progress.json",
                                              "JSON (*.json)")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"completed": sorted(self.completed),
                           "exercises": sorted(self.ex_passed),
                           "quiz": self.quiz_scores, "runs": self.runs,
                           "days": self.days, "ach": sorted(self.ach),
                           "exams": self.exams}, f, indent=2)
        except OSError as e: QMessageBox.warning(self, "Export failed", str(e))
    def _import_progress(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import progress", "",
                                              "JSON (*.json)")
        if not path: return
        try:
            with open(path, encoding="utf-8") as f: data = json.load(f)
            self.completed |= set(data.get("completed", []))
            self.ex_passed |= set(data.get("exercises", []))
            for k, v in dict(data.get("quiz", {})).items():
                self.quiz_scores[k] = max(self.quiz_scores.get(k, 0), v)
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, "Import failed", str(e)); return
        self._save_progress(); self._populate_tree()
    def _reset_progress(self):
        if QMessageBox.question(self, "Reset progress",
                                "Delete ALL progress?") != \
                QMessageBox.StandardButton.Yes: return
        self.completed, self.ex_passed = set(), set()
        self.quiz_scores = {}; self.runs = 0; self.days = []
        self.ach = set(); self.exams = []
        self._save_progress(); self._populate_tree()
    def _record_exam(self, s, n, ex_ok):
        self.exams.append({"date": datetime.date.today().isoformat(),
                           "quiz": [s, n], "exercise": bool(ex_ok)})
        self._save_progress()
        self._log(f"[exam] recorded: quiz {s}/{n}, exercise "
                  f"{'passed' if ex_ok else 'failed'}.", th("warn"))
    def _progress_dialog(self):
        dlg = QDialog(self); dlg.setWindowTitle("Progress summary")
        v = QVBoxLayout(dlg); web = QTextBrowser(); rows = []
        for t in TASKS:
            done = "✅" if t["id"] in self.completed else "⬜"
            star = " ★" if t["id"] in self.ex_passed else ""
            q = (f" · quiz {self.quiz_scores[t['id']]}/{len(t['quiz'])}"
                 if t["id"] in self.quiz_scores and t.get("quiz") else "")
            rows.append(f"<li>{done} {html.escape(t['module'])} — "
                        f"{html.escape(t['title'])}{star}{q}</li>")
        ach_rows = "".join(
            f"<li>{'🏆' if aid in self.ach else '🔒'} <b>"
            f"{html.escape(name)}</b> — {html.escape(desc)}</li>"
            for aid, name, desc, _fn in ACHIEVEMENTS)
        lc, lt, ec, et, qc, qt = self._counts()
        exams = "; ".join(f"{e['date']} quiz {e['quiz'][0]}/{e['quiz'][1]} "
                          f"ex {'✔' if e['exercise'] else '✘'}"
                          for e in self.exams[-5:]) or "none yet"
        web.setHtml(
            f"<h2>Progress</h2><p>Done {lc}/{lt} · Exercises {ec}/{et} · "
            f"Quizzes {qc}/{qt} · Runs {self.runs} · 🔥 Streak: "
            f"{self.streak()} day(s)</p><p>Exams: {exams}</p>"
            f"<h3>Achievements</h3><ul>{ach_rows}</ul>"
            f"<h3>Lessons</h3><ul>{''.join(rows)}</ul>")
        v.addWidget(web)
        h = QHBoxLayout()
        reset = QPushButton("Reset all progress")
        reset.clicked.connect(lambda: (dlg.reject(), self._reset_progress()))
        close = QPushButton("Close"); close.clicked.connect(dlg.accept)
        h.addWidget(reset); h.addStretch(1); h.addWidget(close)
        v.addLayout(h); dlg.resize(540, 580); dlg.exec()
    # ---------------- lessons ----------------
    def _populate_tree(self):
        self._task_items = {}; self.tree.clear(); module_items = {}
        for i, t in enumerate(TASKS):
            top = module_items.get(t["module"])
            if top is None:
                top = QTreeWidgetItem([t["module"]])
                top.setFlags(Qt.ItemIsEnabled)
                self.tree.addTopLevelItem(top); module_items[t["module"]] = top
            child = QTreeWidgetItem([t["title"]])
            child.setData(0, Qt.UserRole, i); top.addChild(child)
            self._task_items[t["id"]] = child
        self.tree.expandAll(); self._refresh_tree_marks()
    def _refresh_tree_marks(self):
        for t in TASKS:
            item = self._task_items.get(t["id"])
            if item is None: continue
            marks = ""
            if t["id"] in self.ex_passed: marks += "★ "
            if t["id"] in self.completed: marks += "✓ "
            item.setText(0, marks + t["title"])
    def _filter_tree(self, q):
        q = q.strip().lower()
        for t in TASKS:
            item = self._task_items.get(t["id"])
            if item:
                item.setHidden(bool(q) and q not in
                               (t["title"] + " " + t["module"]).lower())
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            if top.childCount():
                top.setHidden(all(top.child(j).isHidden()
                                  for j in range(top.childCount())))
    def _current_task(self):
        item = self.tree.currentItem()
        if item is None: return None
        idx = item.data(0, Qt.UserRole)
        return TASKS[idx] if idx is not None else None
    def _on_tree_select(self, cur, _prev):
        t = self._current_task()
        if t is None: return
        prev_id = self._sel_task_id
        if prev_id and prev_id != t["id"]: self._stash_code_for(prev_id)
        self._sel_task_id = t["id"]
        self.lesson_view.setHtml(t["body"])
        self.btn_example.setEnabled(bool(t.get("ex")))
        self.btn_starter.setEnabled(bool(t.get("starter")))
        self.btn_check.setEnabled(bool(
            t.get("check") or t.get("check_model") or t.get("check_assert")
            or t.get("check_props") or t.get("check_plan")
            or t.get("cover_bins")))
        self.btn_quiz.setEnabled(bool(t.get("quiz")))
        self.btn_prev_sol.setEnabled(bool(t.get("cap")))
        self.btn_solution.setEnabled(bool(t.get("solution")))
        self.btn_done.blockSignals(True)
        self.btn_done.setChecked(t["id"] in self.completed)
        self.btn_done.setText("✓ Completed" if t["id"] in self.completed
                              else "Mark Complete")
        self.btn_done.blockSignals(False)
        self.status_lesson.setText(f"{t['module']} — {t['title']}")
        st = self.lesson_code.get(t["id"])
        if st and not self.design_edit.toPlainText().strip():
            self.design_edit.setPlainText(st.get("design", ""))
            self.tb_edit.setPlainText(st.get("tb", ""))
            self._log(f"Restored your saved work for '{t['title']}'.",
                      th("ok"))
    def _step_lesson(self, delta):
        cur = self._current_task()
        if not cur: return
        idx = next((i for i, t in enumerate(TASKS)
                    if t["id"] == cur["id"]), 0)
        n = max(0, min(len(TASKS) - 1, idx + delta))
        self.tree.setCurrentItem(self._task_items[TASKS[n]["id"]])
    def _toggle_done(self, checked):
        t = self._current_task()
        if t is None: return
        (self.completed.add if checked else self.completed.discard)(t["id"])
        self._refresh_tree_marks()
        self.btn_done.setText("✓ Completed" if checked else "Mark Complete")
        self._save_progress()
    def _confirm_overwrite(self, editor):
        if editor.toPlainText().strip():
            return QMessageBox.question(
                self, "Overwrite editor?",
                "The editor already contains code. Replace it?") == \
                QMessageBox.StandardButton.Yes
        return True
    def _write_task_files(self, t):
        for nm, content in ((t.get("files") or {}).items()):
            try:
                with open(os.path.join(SESSION_DIR, nm), "w",
                          encoding="utf-8") as f:
                    f.write(content)
            except OSError: pass
    def _load_example(self):
        t = self._current_task()
        if not t or not t.get("ex"): return
        if not self._confirm_overwrite(self.design_edit): return
        self._write_task_files(t)
        self.design_edit.setPlainText(t["ex"])
        if t.get("ex_tb") and self._confirm_overwrite(self.tb_edit):
            self.tb_edit.setPlainText(t["ex_tb"])
        self._log("Example loaded.", th("ok"))
    def _load_starter(self):
        t = self._current_task()
        if not t or not t.get("starter"): return
        if not self._confirm_overwrite(self.design_edit): return
        self._write_task_files(t)
        self.design_edit.setPlainText(t["starter"])
        self._log("Starter loaded. Good luck!", th("ok"))
    def _load_prev_solution(self):
        t = self._current_task()
        if not t or not t.get("cap"): return
        idx = next(i for i, x in enumerate(TASKS) if x["id"] == t["id"])
        self.design_edit.setPlainText(TASKS[idx - 1]["solution"])
        self._log("Previous stage solution loaded — continue from here.",
                  th("ok"))
    def _load_solution(self):
        t = self._current_task()
        if not t or not t.get("solution"): return
        if QMessageBox.question(self, "Show solution?",
                "Reveal the reference solution for this stage?") != \
                QMessageBox.StandardButton.Yes: return
        self.design_edit.setPlainText(t["solution"])
        self._log("Reference solution loaded.", th("warn"))
    def _take_quiz(self):
        t = self._current_task()
        if not t or not t.get("quiz"): return
        dlg = QuizDialog(t["title"], t["quiz"], self)
        if dlg.exec():
            self.quiz_scores[t["id"]] = max(self.quiz_scores.get(t["id"], 0),
                                            dlg.score)
            if dlg.score == len(t["quiz"]) and t["id"] not in self.completed:
                self.btn_done.setChecked(True)
            else: self._save_progress()
    def _random_exercise(self):
        RandomExerciseDialog(self).exec()
    # ---------------- grading ----------------
    def _award(self, t):
        if t["id"] not in self.ex_passed:
            self.ex_passed.add(t["id"]); self._refresh_tree_marks()
            self._save_progress()
        if t["id"] not in self.completed: self.btn_done.setChecked(True)
    def _grade(self, spec, code):
        try:
            mods, _ = parse_design(code); top = pick_top(mods)
            prog = flatten(mods, top)
            if prog.threads or prog.edges:
                raise HDLSimError("graded on combinational logic — remove "
                                  "initial/posedge blocks")
            ins = [i for i in prog.inputs if prog.widths.get(i, 1) == 1]
            outs = [o for o in prog.outputs if prog.widths.get(o, 1) == 1]
        except HDLSimError as e:
            return None, str(e), None, None, None
        problems = []
        if top != spec["module"]:
            problems.append(f"module name is '{top}', expected "
                            f"'{spec['module']}'")
        if set(ins) != set(spec["inputs"]):
            problems.append(f"inputs {sorted(ins)} should be "
                            f"{sorted(spec['inputs'])}")
        if set(outs) != set(spec["outputs"]):
            problems.append(f"outputs {sorted(outs)} should be "
                            f"{sorted(spec['outputs'])}")
        if problems:
            return False, ("Fix the interface first:\n• " +
                           "\n• ".join(problems)), prog, ins, outs
        ctx = make_ctx(prog); n = len(spec["inputs"]); mm = []
        for r in range(1 << n):
            for i, nm in enumerate(spec["inputs"]):
                ctx.env[nm] = (r >> (n - 1 - i)) & 1
            try: comb_fixpoint(prog, ctx)
            except HDLSimError as e:
                return None, str(e), None, None, None
            for oname, exp in spec["outputs"].items():
                got = str(ctx.env[oname])
                if got != exp[r]: mm.append((dict(ctx.env), oname, exp[r],
                                             got))
        if not mm:
            return True, f"'{top}' matches all {1 << n} rows.", prog, ins, outs
        shown = "\n".join(
            f"{', '.join(k + '=' + v for k, v in env.items())} → {o}: "
            f"expected {e}, got {g}" for env, o, e, g in mm[:8])
        more = f"\n… and {len(mm) - 8} more." if len(mm) > 8 else ""
        return False, f"{len(mm)} row(s) differ:\n{shown}{more}", prog, ins, outs
    def _check_against(self, spec, celebrate="Exercise passed ✅"):
        ok, msg, prog, ins, outs = self._grade(
            spec, self.design_edit.toPlainText())
        if prog is not None: self._show_tt_prog(prog, ins, outs)
        if ok is None: QMessageBox.warning(self, "Check failed", msg)
        elif ok:
            self._log(f"[check] {msg}", th("ok"))
            QMessageBox.information(self, "Passed ✅", msg + "\n\n" + celebrate)
        else:
            self._log(f"[check] {msg.splitlines()[0]}", th("warn"))
            QMessageBox.warning(self, "Not quite yet", msg)
    def _check_exercise(self):
        t = self._current_task()
        if not t: return
        if t.get("check_model"): return self._check_model(t)
        if t.get("check_assert"): return self._check_assert(t)
        if t.get("check_props"): return self._check_props(t)
        if t.get("check_plan") or t.get("cover_bins"):
            return self._check_plan(t)
        if not t.get("check"): return
        ok, msg, prog, ins, outs = self._grade(
            t["check"], self.design_edit.toPlainText())
        if prog is not None: self._show_tt_prog(prog, ins, outs)
        if ok is None:
            self._log(f"[check] {msg}", th("err"))
            QMessageBox.warning(self, "Check failed", msg); return
        if ok:
            self._log(f"[check] {msg} — exercise complete!", th("ok"))
            self._award(t)
            text = msg + (f"\n\n💡 {t['bughint']}" if t.get("bughint") else "")
            QMessageBox.information(self, "Exercise passed ✅", text)
        else:
            self._log(f"[check] {msg.splitlines()[0]}", th("warn"))
            text = msg
            if t.get("bughint") and "interface" not in msg:
                text += f"\n\n💡 Hint: {t['bughint']}"
            QMessageBox.warning(self, "Not quite yet", text)
    def _run_quiet(self):
        mods, unit = parse_design(self.design_edit.toPlainText() + "\n" +
                                  self.tb_edit.toPlainText())
        prog = flatten(mods, pick_top(mods))
        if any(dl for _, _, dl in prog.assigns) and not prog.edges \
                and not prog.comb:
            res = simulate_gates(prog, unit)
        else:
            res = simulate(prog, unit)
        times, series, logs, warns, unit2, steady, ctx = res
        if not series:
            raise HDLSimError("nothing recorded — add a testbench with "
                              "stimulus, then Run once")
        return prog, ctx, times, series
    def _check_model(self, t):
        spec = t["check_model"]
        try:
            mods, _ = parse_design(self.design_edit.toPlainText())
            prog = flatten(mods, pick_top(mods))
        except HDLSimError as e:
            QMessageBox.warning(self, "Golden model", str(e)); return
        for nm in spec["inputs"] + list(spec["outputs"]):
            if nm not in prog.widths:
                QMessageBox.warning(self, "Golden model",
                    f"the design has no signal '{nm}' — ports must match the "
                    "exercise spec"); return
        in_w = [prog.widths[n] for n in spec["inputs"]]
        out_w = {o: prog.widths[o] for o in spec["outputs"]}
        total = sum(in_w); nrand = spec.get("random_n", 0)
        if nrand or total > 12:
            vecs = [[(random.randrange(1 << w)) for w in in_w]
                    for _ in range(nrand or 256)]
            mode = f"{len(vecs)} random vectors ({total} input bits)"
        else:
            vecs = []
            for r in range(1 << total):
                v, rem = [], r
                for w in reversed(in_w):
                    v.append(rem & ((1 << w) - 1)); rem >>= w
                vecs.append(v[::-1])
            mode = f"all {len(vecs)} input combinations"
        cyc = spec.get("cycles", 0); ctx = make_ctx(prog); mism = []
        try:
            for vec in vecs:
                for nm, val in zip(spec["inputs"], vec): ctx.env[nm] = val
                if cyc or prog.edges: _settle_clock(prog, ctx, cyc or 1)
                else: comb_fixpoint(prog, ctx, allow_delay=True)
                exp = spec["model"](*vec)
                if not isinstance(exp, (tuple, list)): exp = (exp,)
                for o, e in zip(spec["outputs"], exp):
                    if ctx.env[o] != (e & ((1 << out_w[o]) - 1)):
                        mism.append((vec, o, e, ctx.env[o]))
        except HDLSimError as e:
            QMessageBox.warning(self, "Golden model", str(e)); return
        self._log(f"[golden] '{spec['module']}' vs Python model — {mode}.",
                  th("ok"))
        if not mism:
            self._award(t)
            QMessageBox.information(self, "Golden model ✅",
                f"Hardware matches the reference model ({mode}).")
        else:
            shown = "\n".join(
                "in=[" + ",".join(map(str, v)) + f"]  {o}: want {w}, got {g}"
                for v, o, w, g in mism[:8])
            more = f"\n… and {len(mism) - 8} more." if len(mism) > 8 else ""
            QMessageBox.warning(self, "Mismatches",
                f"{len(mism)} vector(s) differ:\n\n{shown}{more}")
    def _check_assert(self, t):
        spec = t["check_assert"]
        try: _p, ctx, *_ = self._run_quiet()
        except HDLSimError as e:
            QMessageBox.warning(self, "Assertions", str(e)); return
        self.results_tab.setCurrentWidget(self.console)
        for m in ctx.assert_msgs:
            self._log(f"[assert] VIOLATION {m}", th("err"))
        col = th("ok") if not ctx.assert_fail else th("err")
        self._log(f"[assert] {ctx.assert_pass}/{ctx.assert_total} passed, "
                  f"{ctx.assert_fail} failed.", col)
        if (ctx.assert_fail <= spec.get("max_fail", 0)
                and ctx.assert_pass >= spec.get("min_pass", 1)):
            self._award(t)
            QMessageBox.information(self, "Assertions ✅",
                f"{ctx.assert_pass}/{ctx.assert_total} assertions passed.")
        else:
            QMessageBox.warning(self, "Assertions",
                f"{ctx.assert_fail} failure(s) (allowed "
                f"{spec.get('max_fail', 0)}), {ctx.assert_pass} passes "
                f"(need ≥ {spec.get('min_pass', 1)}).")
    def _check_props(self, t, quiet=False):
        props = t["check_props"]
        try: _p, _c, times, series = self._run_quiet()
        except HDLSimError as e:
            if not quiet: QMessageBox.warning(self, "Properties", str(e))
            return
        stride = max(1, len(times) // 2000)
        tt = [times[i] for i in range(0, len(times), stride)]
        ok_all, report = True, []
        for prop in props:
            tr = {k: _trace_expr(times, series, prop[k])
                  for k in ("after", "when", "expr") if k in prop}
            if "after" in prop:
                within = prop.get("within", 1)
                fails = occ = 0
                for i in range(1, len(tt)):
                    if tr["after"][i - 1] == "0" and tr["after"][i] == "1":
                        occ += 1; dl = tt[i] + within
                        if not any(tr["expr"][j] == "1" and tt[j] <= dl
                                   for j in range(i, len(tt))):
                            fails += 1
                            report.append(
                                f"✘ '{prop['expr']}' missing within {within} "
                                f"of '{prop['after']}' rise @ {tt[i]}")
                ok = fails == 0 and occ >= prop.get("min_occ", 1)
                report.insert(0, f"{'✔' if ok else '✘'} response "
                    f"'{prop['expr']}' within {after_txt(within)} of "
                    f"'{prop['after']}' — {occ} rise(s), {fails} violation(s)")
            else:
                viols = occ = 0
                for i in range(len(tt)):
                    if tr["when"][i] == "1":
                        occ += 1
                        if tr["expr"][i] != "1": viols += 1
                ok = viols == 0 and occ >= prop.get("min_occ", 1)
                report.append(f"{'✔' if ok else '✘'} invariant "
                    f"'{prop['when']}' → '{prop['expr']}' — {occ} checked, "
                    f"{viols} violation(s)")
            ok_all &= ok
        self.results_tab.setCurrentWidget(self.console)
        for r in report:
            self._log("[props] " + r,
                      th("ok") if r.startswith("✔") else th("err"))
        if ok_all:
            self._award(t)
            if not quiet:
                QMessageBox.information(self, "Properties ✅",
                                        "All properties held.")
        elif not quiet:
            QMessageBox.warning(self, "Properties",
                                "Some properties failed — see console.")
    def _check_plan(self, t, quiet=False):
        spec = t.get("check_plan")
        if spec is None:
            cb = t["cover_bins"]
            spec = [dict(name=n, expr=e, desc="") for n, e in cb.get("bins",
                                                                     [])]
            require_all = cb.get("require_all", True)
        else:
            require_all = True
        bins = [(it["name"], it["expr"]) for it in spec]
        try: _p, _c, times, series = self._run_quiet()
        except HDLSimError as e:
            if not quiet: QMessageBox.warning(self, "Test plan", str(e))
            return
        hits, cross, asts = eval_bins(times, series, bins)
        self.results_tab.setCurrentWidget(self.console)
        self._log("[plan] scenario checklist:")
        done = True
        for it in spec:
            h = hits.get(it["name"], 0)
            okflag = h > 0 and asts.get(it["name"]) is not None
            if require_all: done &= okflag
            self._log(f"   {'✔' if okflag else '✘'} {it['name']} — "
                      f"{it.get('desc', '')} (hit {h} sample(s))",
                      th("ok") if okflag else th("err"))
        if cross:
            self._log("[plan] cross: " + "; ".join(
                f"{a}×{b}={n}" for (a, b), n in sorted(cross.items())))
        if done:
            self._award(t)
            if not quiet:
                QMessageBox.information(self, "Test plan ✅",
                    "Every scenario in the plan was exercised.")
        elif not quiet:
            QMessageBox.warning(self, "Test plan",
                "Some scenarios were never exercised — see the checklist.")
    def _maybe_console_check(self):
        t = self._current_task(); spec = (t or {}).get("check_console")
        if not spec: return
        lines = self._run_lines; pos, missing = 0, []
        for pat in spec:
            found = None
            for j in range(pos, len(lines)):
                if re.search(pat, lines[j]): found = j; break
            if found is None: missing.append(pat)
            else: pos = found + 1
        if not missing:
            self._log("[console-check] output matches the specification — "
                      "stage complete!", th("ok"))
            self._award(t)
        else:
            self._log("[console-check] missing expected output:", th("warn"))
            for p in missing:
                self._log(f"    expected a line matching: {p}", th("warn"))
    def _maybe_wave_check(self, series):
        t = self._current_task(); spec = (t or {}).get("check_wave")
        if not spec: return
        sig = next((s for s in series if s["name"] == spec["signal"]), None)
        if sig is None:
            sig = next((s for s in series
                        if s["name"].endswith("." + spec["signal"])), None)
        if sig is None:
            self._log(f"[wave-check] signal '{spec['signal']}' not recorded",
                      th("warn")); return
        seq, prev = [], None
        for v in sig["values"]:
            if "x" in v and not seq: continue
            if v != prev: seq.append(v); prev = v
        got = "".join(seq) if sig["width"] == 1 else " ".join(seq)
        if got == spec["changes"]:
            self._log("[wave-check] waveform matches ✔ — exercise complete!",
                      th("ok"))
            self._award(t)
        else:
            self._log(f"[wave-check] expected changes '{spec['changes']}', "
                      f"got '{got}'", th("warn"))
    def _maybe_coverage_check(self, prog, ctx):
        t = self._current_task(); need = (t or {}).get("require_coverage")
        if not need: return
        hit = sum(len(ctx.cover.get(c, set())) for c in prog.cases)
        total = sum(prog.cases.values())
        if hit >= need:
            self._log(f"[coverage-check] {hit}/{total} branches — goal "
                      f"({need}) reached, exercise complete!", th("ok"))
            self._award(t)
        else:
            self._log(f"[coverage-check] {hit}/{total} branches covered — "
                      f"goal is {need}. Add stimulus for the missing "
                      "states/branches.", th("warn"))
    # ---------------- editing ----------------
    def _on_code_changed(self, tab):
        editor = self.design_edit if tab == 0 else self.tb_edit
        lang = detect_language(editor.toPlainText())
        if editor.language != lang: editor.set_language(lang)
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_F and (e.modifiers() & Qt.ControlModifier):
            self.find_bar.show_bar(); return
        super().keyPressEvent(e)
    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open source file", "",
            "HDL sources (*.v *.sv *.vhd *.vhdl);;All files (*)")
        if not path: return
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            QMessageBox.warning(self, "Open failed", str(e)); return
        editor = (self.design_edit if self.editors_tab.currentIndex() == 0
                  else self.tb_edit)
        editor.setPlainText(text); editor.set_language(detect_language(text))
    def _save_file(self):
        editor = (self.design_edit if self.editors_tab.currentIndex() == 0
                  else self.tb_edit)
        path, _ = QFileDialog.getSaveFileName(self, "Save source file", "",
            "Verilog (*.v);;SystemVerilog (*.sv);;VHDL (*.vhd *.vhdl);;"
            "All files (*)")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())
            self._log(f"Saved {path}", th("ok"))
        except OSError as e:
            QMessageBox.warning(self, "Save failed", str(e))
    def _stash_code_for(self, task_id):
        self.lesson_code[task_id] = {
            "design": self.design_edit.toPlainText(),
            "tb": self.tb_edit.toPlainText()}
    def _restore_lesson_work(self):
        t = self._current_task()
        st = self.lesson_code.get(t["id"]) if t else None
        if not st:
            QMessageBox.information(self, "Restore",
                                    "No saved work for this lesson yet.")
            return
        self.design_edit.setPlainText(st.get("design", ""))
        self.tb_edit.setPlainText(st.get("tb", ""))
        self._log("Saved work restored.", th("ok"))
    def _export_lesson(self):
        t = self._current_task()
        if not t: return
        path, _ = QFileDialog.getSaveFileName(self, "Export lesson",
                                              t["id"] + ".json", "JSON (*.json)")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"lessons": [t]}, f, indent=2)
            self._log(f"[pack] exported '{t['title']}'.", th("ok"))
        except OSError as e: QMessageBox.warning(self, "Export failed", str(e))
    def _import_pack(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import lesson pack", "",
                                              "JSON (*.json)")
        if not path: return
        try:
            with open(path, encoding="utf-8") as f: data = json.load(f)
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, "Import failed", str(e)); return
        les = data.get("lessons") if isinstance(data, dict) else data
        if not isinstance(les, list):
            QMessageBox.warning(self, "Import failed",
                                'Expected {"lessons": [...]}'); return
        existing = {t["id"] for t in TASKS}; added = 0
        for l in les:
            if not isinstance(l, dict) or "title" not in l: continue
            lid = l.get("id") or ("pack_" + re.sub(r"\W+", "_",
                                                   l["title"]).lower())
            base, k = lid, 2
            while lid in existing: lid, k = f"{base}_{k}", k + 1
            l["id"] = lid; l.setdefault("module", "Imported")
            TASKS.append(l); existing.add(lid); added += 1
        self._populate_tree(); self._update_progress_label()
        self._log(f"[pack] imported {added} lesson(s).", th("ok"))
    # ---------------- logging ----------------
    def _log(self, text, color=None):
        if color:
            self.console.appendHtml(
                f"<span style='color:{color};'>{html.escape(text)}</span>")
        else:
            self.console.appendPlainText(text)
        if getattr(self, "_capture_lines", False):
            self._run_lines.append(text)
    def _log_welcome(self):
        self._log(f"Welcome to {APP_NAME}!", th("ok"))
        self._log("Built-in simulator ready: combinational + sequential + "
                  "arrays + $readmemh + assertions + #delay glitch mode. "
                  "Run works with zero setup.")
        self._log(f"Icarus: {'found' if self.iverilog else 'not found'} · "
                  f"GHDL: {'found' if self.ghdl else 'not found'} · "
                  f"Yosys: {'found' if self.yosys else 'not found'} · "
                  f"nextpnr: {'found' if self.nextpnr else 'not found'}")
        self._log("Tip: pick a lesson or Capstone stage, Load Starter, then "
                  "Run (Ctrl+R). Wheel-zoom the waveform, click twice for "
                  "measurement cursors.")
    def _update_status_tools(self):
        def mark(ok):
            return (f"<span style='color:{th('ok') if ok else th('err')};'>"
                    f"{'✔' if ok else '✘'}</span>")
        self.status_tools.setText(
            f"Icarus {mark(bool(self.iverilog and self.vvp))}  "
            f"GHDL {mark(bool(self.ghdl))}  Yosys {mark(bool(self.yosys))}")
    # ---------------- lint / tools ----------------
    def _run_lint(self):
        code = self.design_edit.toPlainText()
        issues = lint_design(code) if code.strip() else []
        self.design_edit.set_issue_markers(issues)
        self._lint_issues = issues
    def _lint_now(self):
        self._run_lint(); self.results_tab.setCurrentWidget(self.console)
        iss = getattr(self, "_lint_issues", [])
        if not iss: self._log("[lint] no issues found 🎉", th("ok"))
        for ln, kind, msg in iss:
            self._log(f"[lint] line {ln}: {msg}",
                      th("err") if kind == "err" else th("warn"))
    def _gen_testbench(self):
        code = self.design_edit.toPlainText()
        try: mods, _ = parse_design(code)
        except HDLSimError as e:
            QMessageBox.warning(self, "Testbench", str(e)); return
        duts = [m for m in mods if not re.search(r"tb|testbench", m, re.I)]
        if not duts:
            QMessageBox.information(self, "Testbench",
                                    "No DUT module found."); return
        top, m = duts[0], mods[duts[0]]
        lines = ["`timescale 1ns/1ps", "", "module tb;",
                 "    // stimulus regs / observed wires:"]
        for p in m.ports:
            rng = f"[{p.width - 1}:0] " if p.width > 1 else ""
            lines.append(f"    reg {rng}{p.name} = 0;"
                         if p.dir == "input"
                         else f"    wire {rng}{p.name};")
        conns = ", ".join(f".{p.name}({p.name})" for p in m.ports)
        lines += ["", f"    {top} uut ({conns});", ""]
        if any(p.name == "clk" for p in m.ports):
            lines += ["    always #5 clk = ~clk;   // 10 ns clock", ""]
        lines += ["    initial begin"]
        if any(p.name == "rst" for p in m.ports):
            lines += ["        rst = 1;", "        #12 rst = 0;"]
        lines += ["        // TODO: apply stimulus, #delay, $display",
                  "        #100 $finish;", "    end", "endmodule", ""]
        if self._confirm_overwrite(self.tb_edit):
            self.tb_edit.setPlainText("\n".join(lines))
            self.tb_edit.set_language("verilog")
            self.editors_tab.setCurrentIndex(1)
            self._log(f"[tb] generated a skeleton for '{top}'.", th("ok"))
    def _equivalence(self):
        code = self.design_edit.toPlainText()
        try: mods, _ = parse_design(code)
        except HDLSimError as e:
            QMessageBox.warning(self, "Equivalence", str(e)); return
        names = list(mods)
        if len(names) < 2:
            QMessageBox.information(self, "Equivalence",
                "Put TWO modules in the design editor (your optimized "
                "version AND the reference), then run this again."); return
        a, ok = QInputDialog.getItem(self, "Equivalence", "Module A:",
                                     names, 0, False)
        if not ok: return
        b, ok = QInputDialog.getItem(self, "Equivalence", "Module B:",
                                     names, 0, False)
        if not ok or a == b: return
        self.results_tab.setCurrentWidget(self.console)
        try:
            _pa, ia, oa, ra = truth_table(code, want=a)
            _pb, ib, ob, rb = truth_table(code, want=b)
        except HDLSimError as e:
            QMessageBox.warning(self, "Equivalence", str(e)); return
        if ia != ib:
            self._log(f"[equiv] input sets differ: {ia} vs {ib}", th("err"))
            return
        if oa != ob:
            self._log(f"[equiv] output sets differ: {oa} vs {ob}", th("err"))
            return
        for i, (x, y) in enumerate(zip(ra, rb)):
            if x != y:
                self._log(f"[equiv] first difference at minterm {i}: {x} vs "
                          f"{y}", th("err"))
                QMessageBox.warning(self, "Equivalence",
                    f"NOT equivalent — first difference at minterm {i}.")
                return
        self._log(f"[equiv] '{a}' ≡ '{b}' across all {len(ra)} rows ✅",
                  th("ok"))
        QMessageBox.information(self, "Equivalence",
                                f"'{a}' and '{b}' are logically equivalent "
                                f"({len(ra)} rows).")
    # ---------------- truth table ----------------
    def _show_tt_prog(self, prog, inputs, outputs):
        ctx = make_ctx(prog); header = inputs + outputs
        n_in = len(inputs); rows = []
        for r in range(1 << len(inputs)):
            for i, nm in enumerate(inputs):
                ctx.env[nm] = (r >> (len(inputs) - 1 - i)) & 1
            comb_fixpoint(prog, ctx, allow_delay=True)
            rows.append([str(ctx.env[nm]) for nm in header])
        self._render_tt(inputs, rows, outputs)
        self._last_tt = (inputs, rows, outputs)
    def _show_truth_table(self):
        code = self.design_edit.toPlainText()
        if not code.strip():
            QMessageBox.information(self, "Truth Table",
                                    "The design editor is empty."); return
        if detect_language(code) != "verilog":
            self.results_tab.setCurrentWidget(self.console)
            self._log("[truth-table] VHDL needs GHDL — use Run.", th("warn"))
            return
        try: _prog, ins, outs, rows = truth_table(code)
        except HDLSimError as e:
            self.results_tab.setCurrentWidget(self.console)
            self._log(f"[truth-table] {e}", th("err")); return
        self._last_tt = (ins, rows, outs)
        self._render_tt(ins, rows, outs)
        self._log(f"[truth-table] generated {len(rows)} rows.")
    def _render_tt(self, ins, rows, outs):
        n_in = len(ins)
        self.tt_label.setText(f"Module — {len(rows)} combinations")
        self.tt_table.clear()
        self.tt_table.setColumnCount(n_in + len(outs))
        self.tt_table.setHorizontalHeaderLabels(ins + outs)
        self.tt_table.setRowCount(len(rows))
        for r_i, row in enumerate(rows):
            for c_i, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if c_i >= n_in:
                    f = item.font(); f.setBold(True); item.setFont(f)
                    item.setForeground(QColor(th("ok") if val == "1"
                                              else th("sub")))
                else:
                    item.setForeground(QColor(th("text") if val == "1"
                                              else th("sub")))
                self.tt_table.setItem(r_i, c_i, item)
        self.tt_table.resizeColumnsToContents()
        self.results_tab.setCurrentWidget(self.tt_widget)
    def _open_kmap(self):
        tt = getattr(self, "_last_tt", None)
        if not tt or not tt[1]:
            self._show_truth_table()
            tt = getattr(self, "_last_tt", None)
            if not tt or not tt[1]: return
        ins, rows, outs = tt
        sel, ok = QInputDialog.getItem(self, "K-map", "Output:",
                                       list(outs), 0, False)
        if not ok: return
        KMapDialog(ins, rows, outs, sel, link_cb=self._kmap_link,
                   parent=self).exec()
    def _kmap_link(self, out_name, row):
        tt = getattr(self, "_last_tt", None)
        if not tt or row < 0: return
        ins, rows, outs = tt
        if out_name not in outs: return
        idx = outs.index(out_name)
        ones = [r for r, row in enumerate(rows) if row[len(ins) + idx] == "1"]
        pis = qmc(len(ins), ones)
        if row >= len(pis): return
        nodes = synth_sop_nodes(ins, pis, out_name)
        self.schematic.prog_widths = {}
        self.schematic.set_circuit(nodes, ins, [out_name], live=False)
        self.schematic.set_highlight(row)
        self.results_tab.setCurrentIndex(3)
    def _export_csv(self):
        tt = getattr(self, "_last_tt", None)
        if not tt or not tt[1]:
            QMessageBox.information(self, "Export CSV",
                                    "Generate a truth table first (Ctrl+T).")
            return
        ins, rows, outs = tt
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV",
                                              "truth_table.csv", "CSV (*.csv)")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(",".join(ins + outs) + "\n")
                for row in rows: f.write(",".join(row) + "\n")
            self._log(f"[csv] wrote {path}", th("ok"))
        except OSError as e: QMessageBox.warning(self, "Export failed", str(e))
    # ---------------- schematic / timing ----------------
    def _show_schematic(self):
        code = self.design_edit.toPlainText()
        if not code.strip():
            QMessageBox.information(self, "Schematic",
                                    "Design editor is empty."); return
        if detect_language(code) != "verilog":
            self.schematic.set_msg("Schematic supports Verilog designs.")
            self.results_tab.setCurrentIndex(3); return
        try:
            mods, _u = parse_design(code)
            prog = flatten(mods, pick_top(mods))
            nodes, inputs, outputs = build_schematic(prog)
            self._sch_prog = prog; ctx = make_ctx(prog)
            ctx.written = set(prog.widths)
            comb_fixpoint(prog, ctx, allow_delay=True)
            self._sch_ctx = ctx
            self.schematic.prog_widths = prog.widths
            self.schematic.set_circuit(nodes, inputs, outputs, live=True)
            self.schematic.refresh(ctx, animate=True)
            self.results_tab.setCurrentIndex(3)
            if inputs:
                self._log("[schematic] live mode: click the input switches "
                          "and watch values propagate.", th("ok"))
        except HDLSimError as e:
            self.schematic.set_msg(str(e))
            self.results_tab.setCurrentIndex(3)
    def _sch_toggle(self, name, val):
        ctx = self._sch_ctx; ctx.env[name] = val
        try: comb_fixpoint(self._sch_prog, ctx, allow_delay=True)
        except HDLSimError as e:
            self._log(f"[schematic] {e}", th("err")); return
        self.schematic.refresh(ctx, animate=True)
    def _export_schematic(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export schematic PNG",
                                              "schematic.png", "PNG (*.png)")
        if not path: return
        if self.schematic.grab().save(path):
            self._log(f"[schematic] wrote {path}", th("ok"))
    def _critical_path(self):
        if not self.schematic.nodes: self._show_schematic()
        if not self.schematic.nodes: return
        path, nset, wset = critical_path(self.schematic.nodes)
        self.schematic.set_critical(nset, wset)
        levels = max(0, len(path) - 1)
        if levels == 0:
            self._log("[timing] trivial path.", th("warn")); return
        f_asic = 1e12 / (levels * PS_PER_LEVEL_ASIC) / 1e6
        f_lut = 1e12 / (levels * PS_PER_LEVEL_LUT) / 1e6
        self.results_tab.setCurrentWidget(self.console)
        self._log(f"[timing] longest combinational path: {levels} levels · "
                  f"≈{f_asic/1000:.2f} GHz (80 ps/lvl ASIC) · ≈{f_lut:.0f} "
                  "MHz (LUT+route 500 ps/lvl) — path highlighted red.",
                  th("warn"))
    def _show_gate_view(self):
        if not self.yosys:
            QMessageBox.information(self, "Gate view",
                                    "Install Yosys for netlist synthesis.")
            return
        code = self.design_edit.toPlainText()
        if not code.strip(): return
        try:
            mods, _ = parse_design(code); top = pick_top(mods)
        except HDLSimError as e:
            QMessageBox.warning(self, "Gate view", str(e)); return
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "d.v")
            with open(f, "w", encoding="utf-8") as fh: fh.write(code)
            j = os.path.join(d, "d.json")
            try:
                cp = subprocess.run(
                    [self.yosys, "-q", "-p",
                     f"read_verilog {f}; hierarchy -check -top {top}; "
                     "proc; opt; techmap; opt; abc -g AND,OR,XOR; opt; "
                     f"write_json {j}"],
                    capture_output=True, text=True, errors="replace",
                    timeout=120)
            except Exception as e:
                self._log(f"[yosys] {e}", th("err")); return
            if cp.returncode != 0:
                self._log((cp.stderr or "synthesis failed").rstrip(),
                          th("err")); return
            try:
                with open(j, encoding="utf-8") as fh: data = json.load(fh)
                nodes, inputs, outputs = yosys_to_nodes(data, top)
            except Exception as e:
                self._log(f"[gate] render failed: {e}", th("err")); return
        counts = {}
        for nd in nodes: counts[nd["label"]] = counts.get(nd["label"], 0) + 1
        summary = " · ".join(f"{k}×{v}" for k, v in
                             sorted(counts.items(), key=lambda x: -x[1])[:8])
        self.yosys_lbl.setText(f"gate netlist: {len(nodes)} cells — {summary}")
        self._log(f"[gate] '{top}': {len(nodes)} cells ({summary})", th("ok"))
        self.schematic.set_circuit(nodes, inputs, outputs, live=False)
        self.results_tab.setCurrentIndex(3)
    def _fpga_stats(self):
        if not (self.yosys and self.nextpnr):
            QMessageBox.information(self, "FPGA stats",
                "Install Yosys + nextpnr-ice40 (icestorm toolchain)."); return
        code = self.design_edit.toPlainText()
        if not code.strip(): return
        try:
            mods, _ = parse_design(code); top = pick_top(mods)
        except HDLSimError as e:
            QMessageBox.warning(self, "FPGA stats", str(e)); return
        self.results_tab.setCurrentWidget(self.console)
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "d.v")
            with open(f, "w", encoding="utf-8") as fh: fh.write(code)
            j, a = os.path.join(d, "d.json"), os.path.join(d, "d.asc")
            try:
                cp = subprocess.run(
                    [self.yosys, "-q", "-p",
                     f"read_verilog {f}; synth_ice40 -top {top} -json {j}"],
                    capture_output=True, text=True, errors="replace",
                    timeout=180)
                if cp.returncode != 0:
                    self._log((cp.stderr or "synth_ice40 failed").rstrip(),
                              th("err")); return
                self._log("[pnr] fitting to iCE40 LP384…")
                rp = subprocess.run(
                    [self.nextpnr, "--lp384", "--device", "CM81",
                     "--json", j, "--asc", a, "--freq", "12",
                     "--ignore-loops", "--timing-allow-fail"],
                    capture_output=True, text=True, errors="replace",
                    timeout=180)
            except Exception as e:
                self._log(f"[pnr] {e}", th("err")); return
        out = (rp.stdout or "") + (rp.stderr or "")
        fm = re.search(r"Max frequency for clock[^:]*:\s*([\d.]+)\s*(\w+)", out)
        util = re.findall(r"^\s*(\w+):\s*(\d+)\s*/\s*(\d+)", out, re.M)
        for line in out.splitlines():
            if "ERROR" in line.upper() or "Warning" in line:
                self._log("[pnr] " + line.strip(), th("warn"))
        if util:
            self._log("[pnr] utilization: " +
                      ", ".join(f"{n} {u}/{t}" for n, u, t in util[:6]))
        if fm:
            self.yosys_lbl.setText(
                f"Fmax {fm.group(1)} {fm.group(2)} (iCE40) · " +
                (f"{util[0][0]} {util[0][1]}/{util[0][2]}" if util else ""))
            self._log(f"[pnr] achieved Fmax: {fm.group(1)} {fm.group(2)}",
                      th("ok"))
    def _activity(self):
        waves = getattr(self, "_last_waves", None)
        if not waves or not waves[1]:
            QMessageBox.information(self, "Activity",
                                    "Run a simulation first."); return
        rows = activity_report(waves[0], waves[1])
        self.results_tab.setCurrentWidget(self.console)
        if not rows: self._log("[activity] nothing toggled.", th("warn")); return
        self._log("[activity] toggle ranking (bit-flips ≈ dynamic power):")
        for i, (flips, name, w) in enumerate(rows, 1):
            self._log(f"   {i}. {name:<16} {flips:5} bit-flips  ({w}b)")
    def _replay_waves(self):
        waves = getattr(self, "_last_waves", None)
        if not waves or not waves[1]:
            QMessageBox.information(self, "Replay",
                                    "Run a simulation first."); return
        self.schematic.replay_series(waves[0], waves[1])
        self.results_tab.setCurrentIndex(3)
        self._log("[replay] animating recorded events rank-by-rank.", th("ok"))
    # ---------------- memory tab ----------------
    def _populate_mem(self):
        pair = getattr(self, "_last_sim", None)
        self.mem_combo.blockSignals(True); self.mem_combo.clear()
        if not pair or not pair[0].arrays:
            self.mem_combo.blockSignals(False)
            self.mem_combo.addItem("no memories in last run")
            self.mem_table.setRowCount(0); return
        names = list(pair[0].arrays)
        self.mem_combo.addItems(names); self.mem_combo.blockSignals(False)
        self._fill_mem(names[0])
    def _fill_mem(self, name):
        pair = getattr(self, "_last_sim", None)
        if not pair or name not in pair[0].arrays: return
        prog, ctx = pair; w, d = prog.arrays[name]
        dis = self.mem_disasm.isChecked()
        self.mem_table.setColumnCount(5 if dis else 4)
        self.mem_table.setHorizontalHeaderLabels(
            ["addr", "hex", "binary", "decimal"] + (["disasm"] if dis else []))
        self.mem_table.setRowCount(d)
        for i in range(d):
            v = ctx.env.get(f"{name}.{i}", 0)
            row = [str(i), format(v, "02x") if w <= 8 else format(v, "x"),
                   format(v, f"0{w}b") if w <= 16 else "…", str(v)]
            if dis: row.append(disassemble(v))
            for c, txt in enumerate(row):
                self.mem_table.setItem(i, c, QTableWidgetItem(txt))
    # ---------------- debugger / renders ----------------
    def _open_debugger(self):
        design = self.design_edit.toPlainText()
        tb = self.tb_edit.toPlainText()
        if not design.strip() and not tb.strip():
            QMessageBox.information(self, "Step debugger",
                                    "Load a design first."); return
        if detect_language(design or tb) == "vhdl":
            QMessageBox.information(self, "Step debugger",
                "The debugger runs Verilog on the built-in simulator."); return
        try:
            mods, unit = parse_design(design + "\n" + tb)
            prog = flatten(mods, pick_top(mods))
            if any(dl for _, _, dl in prog.assigns):
                raise HDLSimError("#delayed designs use the glitch engine — "
                                  "just press Run")
            if not prog.threads and not prog.edges:
                raise HDLSimError("design has no initial/always blocks — "
                                  "nothing to step through")
        except HDLSimError as e:
            QMessageBox.warning(self, "Step debugger", str(e)); return
        DebugDialog(simulate_gen(prog, unit), prog, self).exec()
    def _render_framebuffer(self):
        waves = getattr(self, "_last_waves", None)
        spec = (self._current_task() or {}).get("framebuffer")
        if not waves or not spec:
            QMessageBox.information(self, "Framebuffer",
                "Run a lesson that defines a framebuffer first."); return
        self.framew.render(waves[0], waves[1], spec)
        self.results_tab.setCurrentWidget(
            self.framew.parentWidget())
    def _render_pipeline(self):
        waves = getattr(self, "_last_waves", None)
        spec = (self._current_task() or {}).get("pipeline")
        if not waves or not spec:
            QMessageBox.information(self, "Pipeline",
                "Run a lesson that defines a pipeline trace first."); return
        self.pipew.render(waves[0], waves[1], spec)
        self.results_tab.setCurrentWidget(self.pipew.parentWidget())
    # ---------------- simulation ----------------
    def _run(self, force_builtin=False):
        design = self.design_edit.toPlainText()
        tb = self.tb_edit.toPlainText()
        if not design.strip() and not tb.strip():
            QMessageBox.information(self, "Run", "The editors are empty.")
            return
        task = self._current_task(); answers = None
        if task and task.get("predict"):
            force_builtin = True
            answers = predict_dialog(task["predict"], self)
            if answers is None: return
        lang = detect_language(design or tb)
        self.results_tab.setCurrentWidget(self.console)
        self._run_lines = []; self._capture_lines = True; self.runs += 1
        try:
            if lang == "vhdl":
                if self.ghdl: self._run_ghdl(design, tb)
                else:
                    self._log("[run] GHDL not found — install it to simulate "
                              "VHDL.", th("err"))
            elif self.iverilog and self.vvp and not force_builtin:
                self._run_iverilog(design, tb, sv=is_sv(design + tb))
            else:
                self._run_builtin(design, tb)
        finally:
            self._capture_lines = False
        if answers is not None and getattr(self, "_last_ctx", None):
            self._report_predict(task["predict"], answers, self._last_ctx)
        self._maybe_console_check()
        t2 = self._current_task()
        if t2 and (t2.get("check_plan") or t2.get("cover_bins")):
            self._check_plan(t2, quiet=True)
        if t2 and t2.get("check_props"): self._check_props(t2, quiet=True)
        self._save_progress()
    def _report_predict(self, spec, answers, ctx):
        for qd, ans in zip(spec, answers):
            if not ans:
                self._log(f"[predict] (skipped) {qd['q']}", th("sub"))
                continue
            sig = qd["signal"]
            if sig not in ctx.env:
                self._log(f"[predict] signal '{sig}' not found", th("warn"))
                continue
            val = ctx.env[sig]; w = ctx.widths.get(sig, 1)
            f = qd.get("fmt", "d")
            actual = (format(val, "b").zfill(w) if f == "b" else
                      format(val, "x") if f == "h" else str(val))
            ok = _same(val, ans, f, w)
            self._log(f"[predict] {'✅' if ok else '❌'} you said '{ans}' — "
                      f"actual: {actual}", th("ok") if ok else th("warn"))
    @staticmethod
    def _subprocess(cmd, cwd, timeout=60):
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                              errors="replace", timeout=timeout)
    def _run_builtin(self, design, tb):
        self._log("[built-in] simulating…")
        try:
            mods, unit = parse_design(design + "\n" + tb)
            top = pick_top(mods); prog = flatten(mods, top)
            gate = (any(dl for _, _, dl in prog.assigns)
                    and not prog.edges and not prog.comb)
            if gate:
                self._log("[glitch-mode] inertial #delays detected — "
                          "event-driven gate simulation", th("ok"))
                res = simulate_gates(prog, unit)
            else:
                res = simulate(prog, unit)
        except HDLSimError as e:
            self._log(f"[built-in] {e}", th("err")); return
        times, series, logs, warns, unit, steady, ctx = res
        for line in logs:
            for ln in line.splitlines(): self._log(ln)
        for w in warns: self._log(f"[note] {w}", th("warn"))
        for c in coverage_report(prog, ctx): self._log("[coverage] " + c)
        self._last_sim = (prog, ctx); self._last_ctx = ctx
        self._last_waves = (times, series, unit)
        self._populate_mem()
        if series:
            self.wave.set_data(times, series, unit)
            self.results_tab.setCurrentIndex(2)
            self._log(f"[built-in] done — {len(series)} signals over "
                      f"{times[-1]} {unit} (Waveform tab).", th("ok"))
        elif steady:
            self._log("[built-in] steady state — press Ctrl+T for the truth "
                      "table.", th("ok"))
        self._maybe_wave_check(series)
        self._maybe_coverage_check(prog, ctx)
        t3 = self._current_task()
        if t3 and t3.get("framebuffer"):
            self.framew.render(times, series, t3["framebuffer"])
        if t3 and t3.get("pipeline"):
            self.pipew.render(times, series, t3["pipeline"])
    def _run_iverilog(self, design, tb, sv=False):
        with tempfile.TemporaryDirectory() as d:
            files = []
            for name, text in (("design.v", design), ("tb.v", tb)):
                if text.strip():
                    p = os.path.join(d, name)
                    with open(p, "w", encoding="utf-8") as f: f.write(text)
                    files.append(p)
            out_bin = os.path.join(d, "sim.out")
            flags = ["-g2012"] if sv else []
            self._log(f"[iverilog] compiling {len(files)} file(s)" +
                      (" (SystemVerilog)" if sv else "") + "…")
            try:
                cp = self._subprocess([self.iverilog] + flags +
                                      ["-o", out_bin] + files, d)
            except subprocess.TimeoutExpired:
                self._log("[iverilog] compile timed out.", th("err")); return
            if cp.stdout.strip(): self._log(cp.stdout.rstrip())
            if cp.returncode != 0:
                self._log(cp.stderr.rstrip() or "compilation failed", th("err"))
                return
            if cp.stderr.strip(): self._log(cp.stderr.rstrip(), th("warn"))
            self._log("[iverilog] compiled OK — running…", th("ok"))
            try:
                rp = self._subprocess([self.vvp, "sim.out"], d, timeout=30)
            except subprocess.TimeoutExpired:
                self._log("[vvp] timed out — does your testbench call "
                          "$finish?", th("err")); return
            if rp.stdout.strip(): self._log(rp.stdout.rstrip())
            if rp.stderr.strip(): self._log(rp.stderr.rstrip(), th("warn"))
            if rp.returncode != 0:
                self._log(f"[vvp] exit code {rp.returncode}", th("err"))
            vcds = [f for f in os.listdir(d) if f.endswith(".vcd")]
            if vcds: self._load_vcd(os.path.join(d, vcds[0]))
            elif tb.strip() and "$dump" not in design + tb:
                self._log("[wave] no VCD — add $dumpvars, or use Run "
                          "(built-in), which always records waveforms.",
                          th("warn"))
    def _run_ghdl(self, design, tb):
        with tempfile.TemporaryDirectory() as d:
            files = []
            for name, text in (("design.vhd", design), ("tb.vhd", tb)):
                if text.strip():
                    p = os.path.join(d, name)
                    with open(p, "w", encoding="utf-8") as f: f.write(text)
                    files.append(p)
            def entities(text):
                return re.findall(r"\bentity\s+(\w+)\s+is", text, re.I)
            all_ent = []
            for pth in files:
                with open(pth, encoding="utf-8", errors="replace") as f:
                    all_ent += entities(f.read())
            tb_ents = [e for e in all_ent if re.search(
                r"(^|_)tb$|(^|_)testbench$|^tb_", e, re.I)]
            top = (tb_ents[-1] if tb_ents else
                   (entities(tb)[-1] if tb.strip() and entities(tb) else
                    (all_ent[-1] if all_ent else None)))
            if not top:
                self._log("[ghdl] no entity to elaborate.", th("err")); return
            try:
                for cmd, label in (([self.ghdl, "-a", "--std=08"] + files,
                                    "analyze"),
                                   ([self.ghdl, "-e", "--std=08", top],
                                    "elaborate")):
                    cp = self._subprocess(cmd, d)
                    if cp.stdout.strip(): self._log(cp.stdout.rstrip())
                    if cp.returncode != 0:
                        self._log(cp.stderr.rstrip() or
                                  f"[ghdl] {label} failed", th("err"))
                        return
                    if cp.stderr.strip():
                        self._log(cp.stderr.rstrip(), th("warn"))
                self._log(f"[ghdl] elaborated '{top}' — running…", th("ok"))
                rp = self._subprocess(
                    [self.ghdl, "-r", "--std=08", "--vcd=waves.vcd", top],
                    d, timeout=20)
            except subprocess.TimeoutExpired:
                self._log("[ghdl] simulation timed out.", th("err")); return
            if rp.stdout.strip(): self._log(rp.stdout.rstrip())
            if rp.stderr.strip(): self._log(rp.stderr.rstrip(), th("warn"))
            vcd = os.path.join(d, "waves.vcd")
            if os.path.exists(vcd): self._load_vcd(vcd)
    def _load_vcd(self, path):
        try: times, sigs, unit = parse_vcd(path)
        except OSError as e:
            self._log(f"[wave] could not read VCD: {e}", th("err")); return
        if not sigs:
            self._log("[wave] VCD contained no changing signals.", th("warn"))
            return
        self._last_waves = (times, sigs, unit)
        self.wave.set_data(times, sigs, unit)
        self.results_tab.setCurrentIndex(2)
        self._log(f"[wave] showing {len(sigs)} signal(s) over {times[-1]} "
                  f"{unit}.", th("ok"))
    def _export_vcd(self):
        waves = getattr(self, "_last_waves", None)
        if not waves or not waves[1]:
            QMessageBox.information(self, "Export VCD",
                                    "Run a simulation first."); return
        times, series, unit = waves
        path, _ = QFileDialog.getSaveFileName(self, "Export VCD", "waves.vcd",
                                              "VCD (*.vcd)")
        if not path: return
        ids = {s["name"]: f"${i + 1}" for i, s in enumerate(series)}
        with open(path, "w", encoding="utf-8") as f:
            f.write("$date now $end\n$version HDL Tutor $end\n"
                    f"$timescale 1{unit} $end\n$scope module top $end\n")
            for s in series:
                nm = s["name"].split(".")[-1].replace("$", "_")
                f.write(f"$var wire {s['width']} {ids[s['name']]} {nm} $end\n")
            f.write("$upscope $end\n$enddefinitions $end\n")
            prev = {}
            for k, t in enumerate(times):
                f.write(f"#{t}\n")
                for s in series:
                    v = s["values"][k] if k < len(s["values"]) else "x"
                    if prev.get(s["name"]) == v: continue
                    prev[s["name"]] = v
                    if s["width"] == 1: f.write(f"{v}{ids[s['name']]}\n")
                    else: f.write(f"b{v} {ids[s['name']]}\n")
        self._log(f"[vcd] wrote {path} — open it in GTKWave.", th("ok"))
    # ---------------- theme / session ----------------
    def apply_theme(self, name):
        theme = DARK if name == "dark" else LIGHT
        app = QApplication.instance(); app.setProperty("theme", theme)
        app.setStyleSheet(build_qss(theme))
        for ed in (self.design_edit, self.tb_edit): ed.apply_theme()
        self.console.setStyleSheet(
            f"QPlainTextEdit{{background:{theme['console_bg']};"
            f"color:{theme['console_text']};"
            f"border:1px solid {theme['border']};}}")
        sheet = (f"QTextBrowser{{background:{theme['lesson_bg']};"
                 f"color:{theme['lesson_text']};"
                 f"border:1px solid {theme['border']};}}")
        css = (f"body{{color:{theme['lesson_text']};}}"
               f"code{{color:{theme['lesson_code']};}}"
               f"h2{{color:{theme['lesson_head']};}}"
               f"h3{{color:{theme['lesson_head']};}}")
        for w in (self.lesson_view, self.reference):
            w.setStyleSheet(sheet); w.document().setDefaultStyleSheet(css)
        self.settings.setValue("theme", name)
        self.wave.update(); self.schematic.update()
        self._update_status_tools()
    def _toggle_theme(self):
        self.apply_theme("light"
                         if self.settings.value("theme", "dark") == "dark"
                         else "dark")
    def _restore_session(self):
        s = self.settings
        geo = s.value("geom")
        if geo: self.restoreGeometry(geo)
        sizes = s.value("split")
        if sizes:
            try: self.splitter.setSizes([int(x) for x in sizes])
            except (TypeError, ValueError): pass
        try: self.lesson_code = json.loads(s.value("lesson_code", "{}"))
        except ValueError: self.lesson_code = {}
        design = s.value("design_text", ""); tbtext = s.value("tb_text", "")
        if design: self.design_edit.setPlainText(design)
        if tbtext: self.tb_edit.setPlainText(tbtext)
        lesson_id = s.value("lesson", "")
        cur = next((t for t in TASKS if t["id"] == lesson_id), TASKS[0])
        self.tree.setCurrentItem(self._task_items.get(
            cur["id"], next(iter(self._task_items.values()))))
        self.editors_tab.setCurrentIndex(int(s.value("edit_tab", 0)))
        self.results_tab.setCurrentIndex(int(s.value("res_tab", 0)))
        self.apply_theme(s.value("theme", "dark"))
    def closeEvent(self, event):
        if self._sel_task_id: self._stash_code_for(self._sel_task_id)
        s = self.settings
        s.setValue("geom", self.saveGeometry())
        s.setValue("split", self.splitter.sizes())
        s.setValue("design_text", self.design_edit.toPlainText())
        s.setValue("tb_text", self.tb_edit.toPlainText())
        cur = self._current_task()
        s.setValue("lesson", cur["id"] if cur else "")
        s.setValue("edit_tab", self.editors_tab.currentIndex())
        s.setValue("res_tab", self.results_tab.currentIndex())
        s.setValue("lesson_code", json.dumps(self.lesson_code))
        super().closeEvent(event)

# ══════════════════════════ ENTRY ══════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion"); app.setApplicationName(APP_NAME)
    app.setProperty("theme", DARK)
    win = MainWindow(); win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()