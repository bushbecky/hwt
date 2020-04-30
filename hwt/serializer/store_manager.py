from io import StringIO
import os
from typing import Type, Optional, Union

from hdlConvertor.hdlAst._bases import iHdlObj
from hdlConvertor.translate.common.name_scope import NameScope
from hwt.pyUtils.uniqList import UniqList
from hwt.serializer.serializer_config import DummySerializerConfig
from hwt.serializer.serializer_filter import SerializerFilter
from hwt.synthesizer.unit import HdlConstraintList


class StoreManager(object):
    """
    A base class for an objects which manage
    how the output of the serialization is stored by serializer_cls
    """

    def __init__(self,
                 serializer_cls: DummySerializerConfig,
                 _filter: Type["SerializerFilter"] = None,
                 name_scope: Optional[NameScope]= None):
        self.serializer_cls = serializer_cls
        self.as_hdl_ast = serializer_cls.TO_HDL_AST(name_scope=name_scope)
        self.name_scope = self.as_hdl_ast.name_scope
        if _filter is None:
            _filter = SerializerFilter()
        self.filter = _filter

    def hierarchy_push(self, obj: "Unit") -> NameScope:
        c = self.name_scope.level_push(obj.name)
        self.name_scope = c
        return c

    def hierarchy_pop(self, obj: "Unit") -> NameScope:
        p = self.name_scope.parent
        assert p is not None
        self.name_scope = p
        return p

    def write(self, obj: Union[iHdlObj, HdlConstraintList]):
        pass


class SaveToStream(StoreManager):
    """
    Store all produced code to an output stream
    """

    def __init__(self,
                 serializer_cls: DummySerializerConfig,
                 stream: StringIO,
                 _filter: "SerializerFilter" = None,
                 name_scope: Optional[NameScope]=None):
        super(SaveToStream, self).__init__(
            serializer_cls, _filter=_filter, name_scope=name_scope)
        self.stream = stream

    def write(self, obj: Union[iHdlObj, HdlConstraintList]):
        self.as_hdl_ast.name_scope = self.name_scope
        if isinstance(obj, HdlConstraintList):
            if self.serializer_cls.TO_CONSTRAINTS is not None:
                to_constr = self.serializer_cls.TO_CONSTRAINTS(self.stream)
                to_constr.visit_HdlConstraintList(obj)
        else:
            hdl = self.as_hdl_ast.as_hdl(obj)
            ser = self.serializer_cls.TO_HDL(self.stream)
            if hasattr(ser, "stm_outputs"):
                ser.stm_outputs = self.as_hdl_ast.stm_outputs

            ser.visit_iHdlObj(hdl)


class SaveToFilesFlat(StoreManager):
    """
    Store all produced code to a single directory, file per component.
    """

    def __init__(self,
                 serializer_cls: DummySerializerConfig,
                 root: str,
                 _filter: "SerializerFilter"=None,
                 name_scope: Optional[NameScope]=None):
        super(SaveToFilesFlat, self).__init__(
            serializer_cls, _filter=_filter, name_scope=name_scope)
        self.root = root
        self.files = UniqList()
        os.makedirs(root, exist_ok=True)

    def write(self, obj: Union[iHdlObj, HdlConstraintList]):
        if isinstance(obj, HdlConstraintList):
            fName = "constraints" + self.serializer_cls.TO_CONSTRAINTS.fileExtension
        else:
            fName = obj.name + self.serializer_cls.fileExtension

        fp = os.path.join(self.root, fName)
        self.files.append(fp)
        with open(fp, "w") as f:
            s = SaveToStream(self.serializer_cls, f,
                             self.filter, self.name_scope)
            s.write(obj)
