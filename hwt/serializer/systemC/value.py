from hwt.bitmask import mask
from hwt.hdlObjects.types.bits import Bits
from hwt.hdlObjects.types.defs import BOOL, BIT
from hwt.hdlObjects.value import Value
from hwt.serializer.exceptions import SerializerException
from hwt.serializer.generic.value import GenericSerializer_Value
from hwt.serializer.serializerClases.indent import getIndent
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase


class SystemCSerializer_value(GenericSerializer_Value):

    @classmethod
    def SignalItem(cls, si, ctx, declaration=False):
        if declaration:
            v = si.defaultVal
            if si.virtualOnly:
                raise NotImplementedError()
            elif si.drivers:
                raise NotImplementedError()
            elif si.endpoints or si.simSensProcs:
                raise NotImplementedError()
                if not v.vldMask:
                    raise SerializerException("Signal %s is constant and has undefined value" % si.name)
            else:
                raise SerializerException("Signal %s should be declared but it is not used" % si.name)

            s = "%s%s %s : %s" % (getIndent(ctx.indent), prefix, si.name, cls.HdlType(si._dtype, ctx))
            if isinstance(v, RtlSignalBase):
                return s + " := %s" % cls.asHdl(v, ctx)
            elif isinstance(v, Value):
                if si.defaultVal.vldMask:
                    return s + " := %s" % cls.Value(si.defaultVal, ctx)
                else:
                    return s
            else:
                raise NotImplementedError(v)

        else:
            if si.hidden and hasattr(si, "origin"):
                return cls.asHdl(si.origin, ctx)
            else:
                if ctx.isTarget:
                    return si.name
                else:
                    return "%s.read()" % si.name

    @classmethod
    def condAsHdl(cls, cond, forceBool, createTmpVarFn):
        if isinstance(cond, RtlSignalBase):
            cond = [cond]
        else:
            cond = list(cond)
        if len(cond) == 1:
            c = cond[0]
            if not forceBool or c._dtype == BOOL:
                return cls.asHdl(c, createTmpVarFn)
            elif c._dtype == BIT:
                return "(%s)==%s" % (cls.asHdl(c, createTmpVarFn), cls.BitLiteral(1, 1))
            elif isinstance(c._dtype, Bits):
                width = c._dtype.bit_length()
                return "(%s)!=%s" % (cls.asHdl(c, createTmpVarFn), cls.BitString(0, width))
            else:
                raise NotImplementedError()
        else:
            return " && ".join(map(lambda x: cls.condAsHdl(x, forceBool, createTmpVarFn), cond))

    @classmethod
    def BitString(cls, v, width, vldMask=None):
        if vldMask is None:
            vldMask = mask(width)
        # if can be in hex
        if width % 4 == 0 and vldMask == (1 << width) - 1:
            t = cls.HdlType_bits(Bits(width), None)
            return ('%s("0x%0' + str(width // 4) + 'x")') % (t, v)
        else:  # else in binary
            return cls.BitString_binary(v, width, vldMask)

    @classmethod
    def BitLiteral(cls, v, vldMask):
        if vldMask:
            return "'%d'" % int(bool(v))
        else:
            return "'X'"

    @classmethod
    def BitString_binary(cls, v, width, vldMask=None):
        t = cls.HdlType_bits(Bits(width), None)
        buff = [t, '("']
        for i in range(width - 1, -1, -1):
            mask = (1 << i)
            b = v & mask

            if vldMask & mask:
                s = "1" if b else "0"
            else:
                s = "X"
            buff.append(s)
        buff.append('")')
        return ''.join(buff)

