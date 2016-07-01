from hdl_toolkit.samples.iLvl.ram import Ram_sp
from hdl_toolkit.simulator.shortcuts import simUnitVcd, write, read
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator

if __name__ == "__main__":
    u = Ram_sp()
    u.ADDR_WIDTH.set(8)
    s = HdlSimulator

    def stimulus(env):
        yield from write(False, u.a.clk)
        
        while True:
            # alias wait in VHDL
            yield env.timeout(10*s.ns)    
            yield from write(~read(u.a.clk), u.a.clk)
    
    def dataStimul(env):
        yield from write(0, u.a.addr)
        yield from write(0, u.a.din)
        yield from write(1, u.a.we)
        yield from write(1, u.a.en)
        
        yield env.timeout(10*s.ns)
        
        yield from write(1, u.a.din)
        
        yield env.timeout(10*s.ns)  
        
        
    
    simUnitVcd(u, [stimulus, dataStimul], "tmp/ram_sp.vcd", time=50 * s.ns)
    print("done")