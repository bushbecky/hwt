from vhdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from vhdl_toolkit.interfaces.std import Ap_none
from vhdl_toolkit.synthetisator.shortcuts import synthetizeCls
from vhdl_toolkit.synthetisator.interfaceLevel.interfaceUtils import connect


class SimpleComentedUnit(Unit):
    """
    This is comment for SimpleComentedUnit entity, it will be rendered up to entity.
    Implementation allows you to use what ever you wont.
    Do not forget that inherited classes have it's own docstring even if it was not specified (None). 
    """
    
    def _declr(self):
        self.a = Ap_none(isExtern=True)
        self.b = Ap_none(isExtern=True)
    
    def _impl(self):
        connect(self.a, self.b)


class SimpleComentedUnit2(SimpleComentedUnit):
    """single line"""
    pass

class SimpleComentedUnit3(SimpleComentedUnit2):
    pass

SimpleComentedUnit3.__doc__ = "dynamically generated, for example loaded from file or builded from unit content"


if __name__ == "__main__":
    print(synthetizeCls(SimpleComentedUnit))
    print(synthetizeCls(SimpleComentedUnit2))
    print(synthetizeCls(SimpleComentedUnit3))