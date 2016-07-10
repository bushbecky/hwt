from hdl_toolkit.hdlObjects.variables import SignalItem
from hdl_toolkit.hdlObjects.specialValues import DIRECTION

class PortItem(SignalItem):
    """basic vhdl entity port item"""
    def __init__(self, name, direction, dtype, unit):
        self.name = name
        self.unit = unit
        self.direction = direction
        self._dtype = dtype
        self.src = None
        self.dst = None
    
    
    def connectSig(self, signal):
        """
        Connect to port item on subunit
        """
        if self.direction == DIRECTION.IN:
            if self.src is not None:
                raise Exception("Port %s is already associated with %s" % (self.name, str(self.src)))
            self.src = signal
            
            signal.endpoints.append(self)
        elif self.direction == DIRECTION.OUT:
            if self.dst is not None:
                raise Exception("Port %s is already associated with %s" % (self.name, str(self.dst)))
            self.dst = signal
            
            signal.drivers.append(self)
        else:
            raise NotImplementedError()
    
    
    def connectInternSig(self, signal):
        """
        Connect internal signal to port item,
        this connection is used by simulator and only output port items will be connected
        """
        if self.direction == DIRECTION.OUT:
            if self.src is not None:
                raise Exception("Port %s is already associated with %s" % (self.name, str(self.src)))
            self.src = signal
            
            signal.endpoints.append(self)
        elif self.direction == DIRECTION.IN:
            if self.dst is not None:
                raise Exception("Port %s is already associated with %s" % (self.name, str(self.dst)))
            self.dst = signal
            
            signal.drivers.append(self)
        else:
            raise NotImplementedError()

    
        
    def __repr__(self):
        from hdl_toolkit.serializer.vhdlSerializer import VhdlSerializer
        return VhdlSerializer.PortItem(self) 

