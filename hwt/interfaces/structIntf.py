from hwt.hdl.constants import DIRECTION
from hwt.hdl.types.array import HArray
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.agents.structIntf import StructIntfAgent
from hwt.interfaces.std import Signal
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.typePath import TypePath
from pycocotb.hdlSimulator import HdlSimulator
from hwt.doc_markers import internal
from typing import Optional, Union
from hwt.code import And, Or
from hwt.hdl.types.structValBase import StructValBase


class StructIntf(Interface):
    """
    Create dynamic interface based on HStruct or HUnion description

    :ivar ~._fieldsToInterfaces: dictionary {field_path: sub interface for it}
        field path is a tuple of HStructFields which leads to this interface
    :ivar ~._dtype: HStruct instance used as template for this interface
    :param _instantiateFieldFn: function(FieldTemplateItem instance)
        return interface instance
    :attention: _instantiateFieldFn should also share _fieldsToInterfaces
        with all other instances of StructIntf on this interface
    """

    def __init__(self, structT: HStruct,
                 field_path: TypePath,
                 instantiateFieldFn,
                 masterDir=DIRECTION.OUT,
                 loadConfig=True):
        Interface.__init__(self,
                           masterDir=masterDir,
                           loadConfig=loadConfig)
        if not field_path:
            field_path = TypePath()
        else:
            assert isinstance(field_path, TypePath), field_path

        self._field_path = field_path
        self._dtype = structT
        self._instantiateFieldFn = instantiateFieldFn
        self._fieldsToInterfaces = {}

    def _declr(self):
        _t = self._dtype
        if isinstance(_t, HStruct):
            fields = _t.fields
        else:
            fields = _t.fields.values()

        self._fieldsToInterfaces[self._field_path] = self

        for field in fields:
            # skip padding
            if field.name is not None:
                # generate interface based on struct field
                intf = self._instantiateFieldFn(self, field)
                p = self._field_path / field.name
                assert p not in self._fieldsToInterfaces, p
                self._fieldsToInterfaces[p] = intf

                setattr(self, field.name, intf)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = StructIntfAgent(sim, self)

    def _eq(self, other: Union["StructIntf", StructValBase]):
        if isinstance(other, self.__class__):
            assert self._dtype == other._dtype
            return And(*(si._eq(oi) for si, oi in zip(self._interfaces, other._interfaces)))
        else:
            return And(*(si._eq(getattr(other, si._name)) for si in self._interfaces))

    def __ne__(self, other: Union["StructIntf", StructValBase]):
        if isinstance(other, self.__class__):
            assert self._dtype == other._dtype
            return Or(*(si != oi for si, oi in zip(self._interfaces, other._interfaces)))
        else:
            return Or(*(si != getattr(other, si._name) for si in self._interfaces))


@internal
def _HdlTypeToIntf_instantiateFieldFn(intf, fieldInfo) -> Interface:
    if isinstance(intf, StructIntf):
        c = HdlTypeToIntf(fieldInfo.dtype, field_path=intf._field_path / fieldInfo.name)
        c._fieldsToInterfaces = intf._fieldsToInterfaces
    return c


def HdlTypeToIntf(dtype: HdlType, field_path: Optional[TypePath]=None) -> Interface:
    if isinstance(dtype, HStruct):
        return StructIntf(dtype, field_path, instantiateFieldFn=_HdlTypeToIntf_instantiateFieldFn)
    elif isinstance(dtype, (Bits, HEnum)):
        return Signal(dtype=dtype)
    elif isinstance(dtype, HArray):
        return HObjList(HdlTypeToIntf(dtype.elem_t) for _ in range(dtype.size))
    else:
        raise NotImplementedError(dtype)
