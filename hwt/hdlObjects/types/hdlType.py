from hwt.synthesizer.exceptions import TypeConversionErr


class HdlType():
    def __init__(self):
        self.constrain = None

    def __eq__(self, other):
        return type(self) is type(other)

    def __hash__(self):
        return hash((self.name, self.constrain))

    def fromPy(self, v):
        return self.getValueCls().fromPy(v, self)

    def convert(self, sigOrVal, toType):
        if sigOrVal._dtype == toType:
            return sigOrVal

        try:
            c = self._convert
        except AttributeError:
            c = self.getConvertor()
            self._convertor = c

        return c(self, sigOrVal, toType)

    @classmethod
    def getConvertor(cls):
        return HdlType.defaultConvert

    def defaultConvert(self, sigOrVal, toType):
        raise TypeConversionErr("Conversion of %r of type \n%r to type %r is not implemented"
                                % (sigOrVal, self, toType))

    def __repr__(self):
        return "<HdlType %s>" % (self.__class__.__name__)
