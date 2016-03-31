-- File: AxiStreamReg/AxiStreamReg.vhd
-- Generated by MyHDL 0.9.0
-- Date: Thu Mar 24 00:21:30 2016


library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use std.textio.all;

use work.pck_myhdl_090.all;

entity AxiStreamReg is
    port (
        axiIn_ready: out std_logic;
        axiIn_data: in std_logic_vector(63 downto 0);
        axiIn_valid: in std_logic;
        axiIn_strb: in std_logic_vector(7 downto 0);
        axiOut_ready: in std_logic;
        axiOut_data: out std_logic_vector(63 downto 0);
        axiOut_valid: out std_logic;
        axiOut_strb: out std_logic_vector(7 downto 0);
        self_reset: in std_logic;
        self_clock: in std_logic
    );
end entity AxiStreamReg;


architecture MyHDL of AxiStreamReg is





signal axiIn_data_num: unsigned(63 downto 0);
signal reg_strb: unsigned(7 downto 0);
signal reg_valid: std_logic;
signal axiOut_data_num: unsigned(63 downto 0);
signal axiOut_strb_num: unsigned(7 downto 0);
signal reg_data: unsigned(63 downto 0);
signal axiIn_strb_num: unsigned(7 downto 0);

begin

axiIn_data_num <= unsigned(axiIn_data);
axiIn_strb_num <= unsigned(axiIn_strb);
axiOut_data <= std_logic_vector(axiOut_data_num);
axiOut_strb <= std_logic_vector(axiOut_strb_num);





axiOut_data_num <= reg_data;
axiOut_strb_num <= reg_strb;
axiOut_valid <= reg_valid;


AXISTREAMREG_INTOREG: process (self_clock, self_reset) is
begin
    if (self_reset = '0') then
        reg_data <= to_unsigned(0, 64);
        axiIn_ready <= '0';
        reg_strb <= to_unsigned(0, 8);
        reg_valid <= '0';
    elsif rising_edge(self_clock) then
        if ((not bool(reg_valid)) or bool(axiOut_ready)) then
            reg_data <= axiIn_data_num;
            reg_strb <= axiIn_strb_num;
            reg_valid <= axiIn_valid;
            axiIn_ready <= '1';
        end if;
        axiIn_ready <= '0';
    end if;
end process AXISTREAMREG_INTOREG;

end architecture MyHDL;
