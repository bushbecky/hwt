from hdl_toolkit.hdlObjects.operatorDefs import AllOps
from hdl_toolkit.hdlObjects.types.defs import BOOL
from hdl_toolkit.hdlObjects.types.typeCast import toHVal
from hdl_toolkit.hdlObjects.assignment import Assignment
from hdl_toolkit.hdlObjects.value import Value
from hdl_toolkit.synthetisator.rtlLevel.signalUtils.exceptions import MultipleDriversExc
from hdl_toolkit.synthetisator.rtlLevel.mainBases import RtlSignalBase

        
def tv(signal):
    """
    Value class for type of signal
    """
    return signal._dtype.getValueCls()

class RtlSignalOps():
    def _convert(self, toT):
        return tv(self)._convert(self, toT)
    
    def naryOp(self, operator, opCreateDelegate, *otherOps):
        k = (operator, *otherOps)
        try:
            return self._usedOps[k]
        except KeyError:
            o = opCreateDelegate(self, *otherOps)
            self._usedOps[k] = o
            return o
        
        return o
    
    def __invert__(self):
        return self.naryOp(AllOps.NOT, tv(self).__invert__)
        
    def _onRisingEdge(self, now=None):
        return self.naryOp(AllOps.RISING_EDGE, tv(self)._onRisingEdge, now)
    
    def _onFallingEdge(self, now=None):
        return self.naryOp(AllOps.FALLIGN_EDGE, tv(self)._onFallingEdge, now)
    
    def _hasEvent(self, now=None):
        raise self.naryOp(AllOps.EVENT, tv(self)._hasEvent, now)
    
    def _isOn(self):
        return self._dtype.convert(self, BOOL)
    
    
    # conversions
    def _convSign(self, signed):
        return tv(self)._convSign(self, signed)
    
    def _signed(self):
        return tv(self)._signed(self)
    
    def _unsigned(self):
        return tv(self)._unsigned(self)
    
    def _vec(self):
        return tv(self)._vec(self)
       
    # logic    
    def __and__(self, other):
        return self.naryOp(AllOps.AND_LOG, tv(self).__and__, other)
    
    def __xor__(self, other):
        return self.naryOp(AllOps.XOR, tv(self).__xor__, other)

    def __or__(self, other):
        return self.naryOp(AllOps.OR_LOG, tv(self).__or__, other)

    # cmp
    def _eq(self, other):
        """__eq__ is not overloaded because it will destroy hashability of object"""
        return self.naryOp(AllOps.EQ, tv(self)._eq, other)

    def __ne__(self, other):
        return self.naryOp(AllOps.NEQ, tv(self).__ne__, other)
    
    def __ge__(self, other):
        return self.naryOp(AllOps.GE, tv(self).__ge__, other)
    
    def __gt__(self, other):
        return self.naryOp(AllOps.GREATERTHAN, tv(self).__gt__, other)
    
    def __lt__(self, other):
        return self.naryOp(AllOps.LOWERTHAN, tv(self).__lt__, other)
    
    def __le__(self, other):
        return self.naryOp(AllOps.LE, tv(self).__le__, other)
    
    
    # arithmetic
    def __add__(self, other):
        return self.naryOp(AllOps.ADD, tv(self).__add__, other)
    
    def __sub__(self, other):
        return self.naryOp(AllOps.SUB, tv(self).__sub__, other)
    
    def __mul__(self, other):
        return self.naryOp(AllOps.MUL, tv(self).__mul__, other)

    def __floordiv__(self, divider):
        return self.naryOp(AllOps.DIV, tv(self).__floordiv__, divider)
    
    # selections
    def _downto(self, to):
        return self.naryOp(AllOps.DOWNTO, tv(self)._downto, to)
    
    def __getitem__(self, key):
        operator = AllOps.INDEX
        if isinstance(key, slice):
            hashableKey = (key.start, key.stop, key.step)
        else:
            hashableKey = key
        k = (operator, hashableKey)
        try:
            return self._usedOps[k]
        except KeyError:
            o = tv(self).__getitem__(self, key)
            self._usedOps[k] = o
            return o  
        
        return o


    def _concat(self, *operands):
        return self.naryOp(AllOps.CONCAT, tv(self)._concat, *operands)
    
    
    def _ternary(self, ifTrue, ifFalse):
        return self.naryOp(AllOps.TERNARY, tv(self)._ternary, ifTrue, ifFalse)
    
    def _tryMyIndexToEndpoint(self):
        """
        Try if I now drive index operator which was my driver.
        """
        from hdl_toolkit.hdlObjects.operator import Operator # [TODO] import like this is not ideal
        try:
            # now I am result of the index  xxx[xx] <= source
            # get index op
            d = self.singleDriver()
            if isinstance(d, Operator) and d.operator == AllOps.INDEX:
                # get signal on which is index applied
                indexedOn = d.ops[0]
                if isinstance(indexedOn, RtlSignalBase):
                    d = d.asDrived()
                    self = d.result
                else:
                    raise Exception("can not drive static value")
        except MultipleDriversExc:
            pass
        
        return self
    
    def _assignFrom(self, source):
        source = toHVal(source)
        self = self._tryMyIndexToEndpoint()
        a = Assignment(source, self)
        a.cond = set()
        
        self.drivers.append(a)
        if not isinstance(source, Value):
            source.endpoints.append(a)
        
        return a
    
    def _same(self):
        return [self._assignFrom(self)]
