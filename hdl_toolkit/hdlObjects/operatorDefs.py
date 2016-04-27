from hdl_toolkit.hdlObjects.typeDefs import BOOL, INT, RANGE, PINT, UINT, BIT, \
    Std_logic, Boolean, Std_logic_vector, Std_logic_vector_contrained, \
    Integer
from hdl_toolkit.hdlObjects.value import Value

def convOpsToType(t):
        def addOperand(operator, operand):
            convertedOp = operand.dtype.convert(operand, t)
            if not isinstance(convertedOp, Value):
                convertedOp.endpoints.add(operator)
            operator.ops.append(convertedOp)
        return addOperand

addOperand_logic = convOpsToType(BOOL)    

def addOperand_concat(operator, operand):
    if isinstance(operand.dtype, (Std_logic, Boolean)):
        opAsVec = operand.convert()
    elif isinstance(operand.dtype, Std_logic_vector):
        opAsVec = operand
    else:
        raise NotImplementedError("Not implemented for type %s of %s" % 
                                  (repr(operand.dtype), repr(operand)))
    operator.ops.append(opAsVec)

def getReturnType_default(op):
    t = op.ops[0].dtype
    if(t == UINT or t == PINT):
        return INT
    else:
        return t


def addOperand_default(operator, operand):
    t = operand.dtype
    try:
        opType = operator.getReturnType()
    except IndexError:
        opType = t
        
    typeConvertedOp = t.convert(operand, opType)
    operator.ops.append(typeConvertedOp)
    if not isinstance(typeConvertedOp, Value):
        typeConvertedOp.endpoints.add(operator)

def addOperand_eq(operator, operand):
    t = operand.dtype
    try:
        opType = getReturnType_default(operator)
    except IndexError:
        opType = t
        
    typeConvertedOp = t.convert(operand, opType)
    operator.ops.append(typeConvertedOp)
    if not isinstance(typeConvertedOp, Value):
        typeConvertedOp.endpoints.add(operator)

def addOperand_event(operator, operand):
    t = operand.dtype
    assert(t == BIT)
        
    typeConvertedOp = t.convert(operand, t)
    operator.ops.append(typeConvertedOp)
    if not isinstance(typeConvertedOp, Value):
        typeConvertedOp.endpoints.add(operator)


def getReturnType_concat(op):
    raise NotImplementedError()

def getReturnType_index(op):
    base = op.ops[0]
    index = op.ops[1]
    if isinstance(base.dtype, Std_logic_vector):
        if isinstance(index.dtype, Integer):
            return BIT
        if hasattr(index, "dtype") and index.dtype == RANGE:
            return Std_logic_vector_contrained(index)
        
    raise NotImplementedError()

def addOperand_index(operator, operand):
    if not operator.ops:
        operand.drivers.add(operator)
        
    operator.ops.append(operand)
    
def getReturnType_ternary(op):
    return op.ops[1].dtype

def addOperand_ternary(operator, operand):
    if not operator.ops:
        return addOperand_logic(operator, operand)
    else:
        operator.ops.append(operand)

def getReturnType_hdlFn(op):
    fnCont = op.ops[0]
    fn = fnCont.lookup(op.ops[1:])
    return fn.returnT

class OpDefinition():
    
    def __init__(self, evalFn,
                 getReturnType=getReturnType_default ,
                 addOperand=addOperand_default):
        self.id = None  # assigned automatically in AllOps  
        self._evalFn = evalFn
        self.getReturnType = getReturnType
        self.addOperand = addOperand
        
    def __eq__(self, other):
        return self.id == other.id
    
    def  __hash__(self):
        return hash(self.id)
    
    def eval(self, operator):
        """Load all operands and process them by self._evalFn"""
        # it = iter(operator.ops)
        def getVal(v):
            while not isinstance(v, Value):
                v = v._val
            
            return v
        
        if self == AllOps.CALL:
            origOps = operator.ops[1:]
            fnCont = operator.ops[0]
            fn = fnCont.parent.body[fnCont.name].lookup(origOps)
            ops = list(map(getVal, origOps))
            return fn.call(*ops)
        else:
            ops = list(map(getVal, operator.ops))
            return self._evalFn(*ops)

    def __repr__(self):
        return "<OpDefinition %s>" % (self.id)
            
class AllOps():
    _idsInited = False
    """
    @attention: Remember that and operator is & and or is |, 'and' and 'or' can not be used because
    they can not be overloaded
    @attention: These are operators of internal AST, the are not equal to verilog or vhdl operators
    """
    
    NOT = OpDefinition(lambda a :~a,
                       getReturnType=lambda op: BOOL,
                       addOperand=addOperand_logic)
    EVENT = OpDefinition(lambda a : NotImplemented(),
                        getReturnType=lambda op: BOOL,
                        addOperand=addOperand_event)
    RISING_EDGE = OpDefinition(lambda a : NotImplemented(),
                        getReturnType=lambda op: BOOL,
                        addOperand=addOperand_event)  # unnecessary
    DIV = OpDefinition(lambda a, b : a // b)
    PLUS = OpDefinition(lambda a, b : a + b)
    MINUS = OpDefinition(lambda a, b : a - b)
    MUL = OpDefinition(lambda a, b : a * b)
    NEQ = OpDefinition(lambda a, b : a != b,
                        getReturnType=lambda op: BOOL)
    XOR = OpDefinition(lambda a, b : a != b,
                       getReturnType=lambda op: BOOL,
                       addOperand=addOperand_logic)
    EQ = OpDefinition(lambda a, b : a == b,
                        getReturnType=lambda op: BOOL,
                        addOperand=addOperand_eq)
    
    AND_LOG = OpDefinition(lambda a, b : a & b,
                       getReturnType=lambda op: BOOL,
                       addOperand=addOperand_logic)
    
    OR_LOG = OpDefinition(lambda a, b : a | b,
                       getReturnType=lambda op: BOOL,
                       addOperand=addOperand_logic)
    
    DOWNTO = OpDefinition(lambda a, b : Value.fromPyVal([b, a], RANGE),  # [TODO]
                        getReturnType=lambda op: RANGE,
                        addOperand=convOpsToType(INT))
    
    GREATERTHAN = OpDefinition(lambda a, b : a > b,
                       getReturnType=lambda op: BOOL,
                       addOperand=addOperand_eq)
    
    LOWERTHAN = OpDefinition(lambda a, b : a < b,
                       getReturnType=lambda op: BOOL,
                       addOperand=addOperand_eq)
    
    CONCAT = OpDefinition(lambda a, b : NotImplemented(),
                       getReturnType=getReturnType_concat,
                       addOperand=addOperand_concat)

    INDEX = OpDefinition(lambda a, b : a[b],
                       getReturnType=getReturnType_index,
                       addOperand=addOperand_index)
    
    TERNARY = OpDefinition(lambda a, b, c : b if a else c,
                       getReturnType=getReturnType_ternary,
                       addOperand=addOperand_ternary)
    
    CALL = OpDefinition(None,
                       getReturnType=getReturnType_hdlFn,
                       addOperand=lambda operator, operand : operator.ops.append(operand))
    
    allOps = {}
        
    @classmethod
    def opByName(cls, name):
        return getattr(cls, name)
    
if not AllOps._idsInited:
    for a in dir(AllOps):
        o = getattr(AllOps, a)
        if isinstance(o, OpDefinition):
            o.id = a
            
    AllOps._idsInited = True
