from jinja2 import Environment, PackageLoader


class VHDLTemplates(object):
    '''
    Class for loading vhdl templates
    '''
    env = Environment(loader=PackageLoader('vhdl_toolkit', 'templates_vhdl'))
    architecture = env.get_template('architecture.vhd')
    entity = env.get_template('entity.vhd')
    process = env.get_template('process.vhd')
    component = env.get_template('component.vhd')
    componentInstance = env.get_template('component_instance.vhd')
    
    tb = env.get_template('tb.vhd')
    If = env.get_template('if.vhd')
    AXI4_slave_read_resp = env.get_template('AXI4_slave_read_resp.vhd')
    AXI4_slave_write_accept = env.get_template('AXI4_slave_write_accept.vhd')
    axi_lite_read = env.get_template('axi_lite_read.vhd')
    axi_lite_write = env.get_template('axi_lite_write.vhd')
    axi4_init = env.get_template('axi4_init.vhd')
    basic_include = """
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
"""
        
        
