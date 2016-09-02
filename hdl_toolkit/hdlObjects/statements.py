
class ReturnCalled(Exception):
    """
    Exception which is used as return statement while executing of hdl functions
    """
    def __init__(self, val):
        self.val = val

class ReturnContainer():
    """
    Stuctural container of return statement in hdl
    """
    
    def __init__(self, val=None):
        self.val = val

    def seqEval(self):
        raise ReturnCalled(self.val.staticEval())       

def seqEvalCond(cond):
    _cond = True
    for c in cond:
        _cond = _cond and bool(c.staticEval())
        
    return _cond

def simEvalCond(cond, simulator):
    _cond = True
    _vld = True
    for c in cond:
        v = c.simEval(simulator)
        val = bool(v.val)
        fullVld = v._isFullVld()
        if not val and fullVld:
            return False, True
        
        _cond = _cond and val
        _vld = _vld and fullVld
        
        
    return _cond, _vld


def _invalidated(origUpadater):
    """
    disable validity on updater result
    """
    def __invalidated(val):
        _, v = origUpadater(val)
        v.vldMask = 0
        return True, v
    return __invalidated

class IfContainer():
    """
    Structural container of if statement for hdl rendering
    """
    def __init__(self, cond, ifTrue=[], ifFalse=[], elIfs=[]):
        self.cond = cond
        self.ifTrue = ifTrue
        self.elIfs = elIfs
        self.ifFalse = ifFalse
        
    @staticmethod
    def evalCase(simulator, stm, condVld):
        for r in stm.simEval(simulator):
            if not condVld:
                r = (r[0], _invalidated(r[1]), r[2])
            yield r
    
    def simEval(self, simulator):
        """
        Same like seqEval but does not assign to signal instead of
        if schedueles updater in simulator
        """
        condRes, condVld = simEvalCond(self.cond, simulator)
        if condRes or not condVld:
            for stm in self.ifTrue:
                yield from IfContainer.evalCase(simulator, stm, condVld)
        else:
            for c in self.elIfs:
                subCondRes, subCondVld = simEvalCond(c[0], simulator)
                if subCondRes or not subCondVld:
                    for stm in c[1]:
                        yield from IfContainer.evalCase(simulator, stm, subCondVld)
                    raise StopIteration()
            
            for stm in self.ifFalse:
                yield from IfContainer.evalCase(simulator, stm, condVld)
        
    def seqEval(self):
        if seqEvalCond(self.cond):
            for s in self.ifTrue:
                s.seqEval()
        else:
            for c in self.elIfs:
                if seqEvalCond(c[0]):
                    for s in c[1]:
                        s.seqEval()
                    return
            
            for s in self.ifFalse:
                s.seqEval()
        
    def __repr__(self):
        from hdl_toolkit.serializer.vhdlSerializer import VhdlSerializer
        return VhdlSerializer.IfContainer(self)

class SwitchContainer():
    """
    Structural container for switch statement for hdl rendering
    """
    def __init__(self, switchOn, cases):
        self.switchOn = switchOn
        self.cases = cases
    
    def simEval(self, simulator):
        """
        scheduele updater in simulator with effect of this statement
        """
        v = self.switchOn.simEval(simulator)
        vld = v.vldMask == v._dtype.all_mask()
        if not vld:
            c = self.cases[0]
            stmnts = c[1]
        else:
            for c in self.cases:
                val = c[0]
                stmnts = c[1]
                if val is None:
                    break
                elif v.val == val.val:
                    break
        
        for stm in stmnts:
            yield from IfContainer.evalCase(simulator, stm, vld)  
                      
    def seqEval(self):
        raise NotImplementedError()
    
    def __repr__(self):
        from hdl_toolkit.serializer.vhdlSerializer import VhdlSerializer
        return VhdlSerializer.SwitchContainer(self)
 
class WhileContainer():
    """
    Structural container of while statement for hdl rendering
    """
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body
    
    def simEval(self, simulator):
        raise NotImplementedError()
    
    def seqEval(self):
        while seqEvalCond(self.cond):
            for s in self.body:
                s.seqEval()

class WaitStm():
    """
    Structural container of wait statemnet for hdl rendering
    """
    def __init__(self, waitForWhat):
        self.isTimeWait = isinstance(waitForWhat, int)
        self.waitForWhat = waitForWhat
        
