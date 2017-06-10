from hwt.hdlObjects.operatorDefs import AllOps
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwt.serializer.exceptions import SerializerException
from hwt.hdlObjects.types.defs import BIT

# http://www.asicguru.com/verilog/tutorial/operators/57/
opPrecedence = {AllOps.NOT: 3,
                AllOps.NEG: 5,
                AllOps.EVENT: 0,
                AllOps.RISING_EDGE: 0,
                AllOps.DIV: 6,
                AllOps.ADD: 7,
                AllOps.SUB: 7,
                AllOps.MUL: 3,
                AllOps.EQ: 10,
                AllOps.NEQ: 10,
                AllOps.AND_LOG: 11,
                AllOps.XOR: 12,
                AllOps.OR_LOG: 13,
                AllOps.DOWNTO: 2,
                AllOps.GREATERTHAN: 9,
                AllOps.LOWERTHAN: 9,
                AllOps.GE: 9,
                AllOps.LE: 9,
                AllOps.CONCAT: 5,
                AllOps.INDEX: 1,
                AllOps.TERNARY: 16,
                AllOps.CALL: 2,
                # AllOps.SHIFTL:8,
                # AllOps.SHIFTR:8,
                # AllOps.DOWNTO:
                # AllOps.TO:
                }


class UnsupportedEventOpErr(SerializerException):
    """
    Verilog does not have event operators like vhdl, they have to be replaced by correct
    expression of sensitivity list of always statement
    """
    pass


class VerilogSerializer_ops():
    @classmethod
    def Operator(cls, op, createTmpVarFn, indent=0):
        def p(operand):
            s = cls.asHdl(operand, createTmpVarFn)
            if isinstance(operand, RtlSignalBase):
                try:
                    o = operand.singleDriver()
                    if o.operator != op.operator and opPrecedence[o.operator] <= opPrecedence[op.operator]:
                        return " (%s) " % s
                except Exception:
                    pass
            return " %s " % s

        ops = op.ops
        o = op.operator

        def _bin(name):
            return (" %s " % (name,)).join(map(lambda x: x.strip(), map(p, ops)))

        if o == AllOps.AND_LOG:
            return _bin('&')
        elif o == AllOps.OR_LOG:
            return _bin('|')
        elif o == AllOps.XOR:
            return _bin('^')
        elif o == AllOps.NOT:
            assert len(ops) == 1
            return "~" + p(ops[0])
        elif o == AllOps.CALL:
            return "%s(%s)" % (cls.FunctionContainer(ops[0]), ", ".join(map(p, ops[1:])))
        elif o == AllOps.CONCAT:
            return _bin('&')
        elif o == AllOps.DIV:
            return _bin('/')
        elif o == AllOps.DOWNTO:
            return _bin(':')
        elif o == AllOps.TO:
            return _bin(':')
        elif o == AllOps.EQ:
            return _bin('==')
        elif o == AllOps.GREATERTHAN:
            return _bin('>')
        elif o == AllOps.GE:
            return _bin('>=')
        elif o == AllOps.LE:
            return _bin('<=')
        elif o == AllOps.INDEX:
            assert len(ops) == 2
            o1 = ops[0]
            return "%s[%s]" % (cls.asHdl(o1, createTmpVarFn).strip(), p(ops[1]))
        elif o == AllOps.LOWERTHAN:
            return _bin('<')
        elif o == AllOps.SUB:
            return _bin('-')
        elif o == AllOps.MUL:
            return _bin('*')
        elif o == AllOps.NEQ:
            return _bin('!=')
        elif o == AllOps.ADD:
            return _bin('+')
        elif o == AllOps.TERNARY:
            zero, one = BIT.fromPy(0), BIT.fromPy(1)
            if ops[1] == one and ops[2] == zero:
                return cls.condAsHdl([ops[0]], True, createTmpVarFn)
            else:
                return "%s ? %s : %s" % (cls.condAsHdl([ops[0]], True, createTmpVarFn),
                                         p(ops[1]),
                                         p(ops[2]))
        elif o == AllOps.RISING_EDGE or o == AllOps.FALLIGN_EDGE or o == AllOps.EVENT:
            raise UnsupportedEventOpErr()
        elif o == AllOps.BitsAsSigned:
            assert len(ops) == 1
            return "$signed(" + p(ops[0]) + ")"
        elif o == AllOps.BitsAsUnsigned:
            assert len(ops) == 1
            return "$unsigned(" + p(ops[0]) + ")"
        elif o == AllOps.BitsAsVec:
            assert len(ops) == 1
            return "$unsigned(" + p(ops[0]) + ")"
        elif o == AllOps.BitsToInt:
            # no conversion required
            return cls.asHdl(ops[0], createTmpVarFn)
        elif o == AllOps.IntToBits:
            # no conversion required
            return cls.asHdl(ops[0], createTmpVarFn)

        elif o == AllOps.POW:
            assert len(ops) == 2
            return _bin('**')
        else:
            raise NotImplementedError("Do not know how to convert %s to vhdl" % (o))
