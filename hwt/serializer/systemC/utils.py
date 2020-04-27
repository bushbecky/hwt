from hdlConvertor.to.verilog.constants import SIGNAL_TYPE
from hwt.hdl.portItem import HdlPortItem
from hwt.hdl.statement import HdlStatement
from hwt.pyUtils.arrayQuery import arr_any
from ipCorePackager.constants import DIRECTION
from hdlConvertor.hdlAst._defs import HdlVariableDef
from hwt.synthesizer.param import Param


def systemCTypeOfSig(s):
    """
    Check if is register or wire
    """
    if isinstance(s, HdlVariableDef):
        s = s.origin

    if isinstance(s, HdlPortItem):
        if s.direction == DIRECTION.IN or s.direction == DIRECTION.INOUT:
            return SIGNAL_TYPE.PORT_WIRE

        t = systemCTypeOfSig(s.getInternSig())
        if t == SIGNAL_TYPE.WIRE:
            return SIGNAL_TYPE.PORT_WIRE
        elif t == SIGNAL_TYPE.REG:
            return SIGNAL_TYPE.PORT_REG
        else:
            raise ValueError(t)
    elif isinstance(s, Param):
        return SIGNAL_TYPE.PORT_REG
    elif s._const or\
        arr_any(s.drivers,
                lambda d: isinstance(d, HdlStatement)
                and d._now_is_event_dependent):

        return SIGNAL_TYPE.REG
    else:
        return SIGNAL_TYPE.WIRE
