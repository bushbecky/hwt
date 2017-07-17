from hwt.hdlObjects.entity import Entity
from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.types.enum import Enum
from hwt.serializer.exceptions import SerializerException
from hwt.serializer.generic.serializer import GenericSerializer
from hwt.serializer.serializerClases.indent import getIndent
from hwt.serializer.serializerClases.mapExpr import MapExpr
from hwt.serializer.serializerClases.nameScope import LangueKeyword
from hwt.serializer.serializerClases.portMap import PortMap
from hwt.serializer.utils import maxStmId
from hwt.serializer.verilog.context import VerilogSerializerCtx
from hwt.serializer.verilog.keywords import VERILOG_KEYWORDS
from hwt.serializer.verilog.ops import VerilogSerializer_ops
from hwt.serializer.verilog.statements import VerilogSerializer_statements
from hwt.serializer.verilog.tmplContainer import VerilogTmplContainer
from hwt.serializer.verilog.types import VerilogSerializer_types
from hwt.serializer.verilog.utils import SIGNAL_TYPE, verilogTypeOfSig
from hwt.serializer.verilog.value import VerilogSerializer_Value
from hwt.synthesizer.param import getParam
from hwt.hdlObjects.operator import Operator
from hwt.hdlObjects.operatorDefs import AllOps
from hwt.hdlObjects.process import HWProcess
from hwt.hdlObjects.statements import SwitchContainer
from hwt.hdlObjects.types.typeCast import toHVal


class VerilogSerializer(VerilogTmplContainer, VerilogSerializer_types, VerilogSerializer_Value,
                        VerilogSerializer_statements, VerilogSerializer_ops, GenericSerializer):
    _keywords_dict = {kw: LangueKeyword() for kw in VERILOG_KEYWORDS}
    fileExtension = '.v'

    @classmethod
    def getBaseContext(cls):
        return VerilogSerializerCtx(cls.getBaseNameScope(), 0, None, None)

    @classmethod
    def Entity(cls, ent, ctx):
        ports = []
        generics = []
        ent.ports.sort(key=lambda x: x.name)
        ent.generics.sort(key=lambda x: x.name)

        ent.name = ctx.scope.checkedName(ent.name, ent, isGlobal=True)
        for p in ent.ports:
            p.name = ctx.scope.checkedName(p.name, p)
            p.getSigInside().name = p.name
            ports.append(cls.PortItem(p, ctx))

        for g in ent.generics:
            g.name = ctx.scope.checkedName(g.name, g)
            generics.append(cls.GenericItem(g, ctx))

        entVerilog = cls.moduleHeadTmpl.render(
                indent=getIndent(ctx.indent),
                name=ent.name,
                ports=ports,
                generics=generics
                )

        doc = ent.__doc__
        if doc and id(doc) != id(Entity.__doc__):
            doc = cls.comment(doc) + "\n"
            return doc + entVerilog
        else:
            return entVerilog

    @classmethod
    def hardcodeRomIntoProcess(cls, rom):
        """
        Due to verilog restrictions it is not posible to use array constants
        and rom memories has to be hardcoded as process
        """
        processes = []
        signals = []
        for e in rom.endpoints:
            assert isinstance(e, Operator) and e.operator == AllOps.INDEX, e
            me, index = e.ops
            assert me is rom

            # construct output of the rom
            romValSig = rom.ctx.sig(rom.name, dtype=e.result._dtype)
            signals.append(romValSig)
            romValSig.hidden = False

            # construct process which will represent content of the rom
            cases = [(toHVal(i), romValSig ** v)
                     for i, v in enumerate(rom.defaultVal.val)]
            statements = [SwitchContainer(index, cases), ]

            p = HWProcess(rom.name, statements, {index, },
                          {index, }, {romValSig, })
            processes.append(p)

            # override usage of original index operator on rom
            # to use signal generated from this process
            def replaceOrigRomIndexExpr(x):
                if x is e.result:
                    return romValSig
                else:
                    return x
            for _e in e.result.endpoints:
                _e.ops = tuple(map(replaceOrigRomIndexExpr, _e.ops))
                e.result = romValSig

        return processes, signals

    @classmethod
    def Architecture_var(cls, v, serializerVars, extraTypes,
                         extraTypes_serialized, ctx, childCtx):
        """
        :return: list of extra discovered processes
        """
        t = v._dtype
        # if type requires extra definition
        if isinstance(t, Enum) and t not in extraTypes:
            extraTypes.add(v._dtype)
            s = cls.HdlType(t, childCtx, declaration=True)
            extraTypes_serialized.append(s)
        elif isinstance(t, Array) and v.defaultVal.vldMask:
            if v.drivers:
                raise SerializerException("Verilog does not support RAMs"
                                          " with initialized value")
            eProcs, eVars = cls.hardcodeRomIntoProcess(v)
            for _v in eVars:
                _procs = cls.Architecture_var(_v, serializerVars, extraTypes,
                                              extraTypes_serialized, ctx, childCtx)
                eProcs.extend(_procs)
            return eProcs

        v.name = ctx.scope.checkedName(v.name, v)
        serializedVar = cls.SignalItem(v, childCtx, declaration=True)
        serializerVars.append(serializedVar)

        return []

    @classmethod
    def Architecture(cls, arch, ctx):
        serializerVars = []
        procs = []
        extraTypes = set()
        extraTypes_serialized = []
        arch.variables.sort(key=lambda x: (x.name, x._instId))
        arch.componentInstances.sort(key=lambda x: x._name)

        childCtx = ctx.withIndent()
        extraProcesses = []
        for v in arch.variables:
            _eProc = cls.Architecture_var(v,
                                          serializerVars,
                                          extraTypes,
                                          extraTypes_serialized,
                                          ctx,
                                          childCtx)

            extraProcesses.extend(_eProc)

        arch.processes.extend(extraProcesses)
        arch.processes.sort(key=lambda x: (x.name, maxStmId(x)))
        for p in arch.processes:
            procs.append(cls.HWProcess(p, childCtx))

        # architecture names can be same for different entities
        # arch.name = scope.checkedName(arch.name, arch, isGlobal=True)
        componentInstances = list(map(lambda c: cls.ComponentInstance(c, childCtx),
                                      arch.componentInstances))

        return cls.moduleBodyTmpl.render(
            indent=getIndent(ctx.indent),
            entityName=arch.getEntityName(),
            name=arch.name,
            variables=serializerVars,
            extraTypes=extraTypes_serialized,
            processes=procs,
            componentInstances=componentInstances
            )

    @classmethod
    def ComponentInstance(cls, entity, ctx):
        portMaps = []
        for pi in entity.ports:
            pm = PortMap.fromPortItem(pi)
            portMaps.append(pm)

        genericMaps = []
        for g in entity.generics:
            gm = MapExpr(g, g._val)
            genericMaps.append(gm)

        if len(portMaps) == 0:
            raise SerializerException("Incomplete component instance")

        # [TODO] check component instance name
        return cls.componentInstanceTmpl.render(
                indent=getIndent(ctx.indent),
                instanceName=entity._name,
                entity=entity,
                portMaps=[cls.PortConnection(x, ctx) for x in portMaps],
                genericMaps=[cls.MapExpr(x, ctx) for x in genericMaps]
                )

    @classmethod
    def comment(cls, comentStr):
        return "\n".join(["/*", comentStr, "*/"])

    @classmethod
    def GenericItem(cls, g, ctx):
        s = "%s %s" % (cls.HdlType(g._dtype, ctx.forPort()), g.name)
        if g.defaultVal is None:
            return s
        else:
            return "parameter %s = %s" % (s, cls.Value(getParam(g.defaultVal).staticEval(), ctx))

    @classmethod
    def PortItem(cls, pi, ctx):
        if verilogTypeOfSig(pi.getSigInside()) == SIGNAL_TYPE.REG:
            f = "%s reg %s %s"
        else:
            f = "%s %s %s"

        return f % (cls.DIRECTION(pi.direction),
                    cls.HdlType(pi._dtype, ctx.forPort()),
                    pi.name)

    @classmethod
    def PortConnection(cls, pc, ctx):
        if pc.portItem._dtype != pc.sig._dtype:
            raise SerializerException("Port map %s is nod valid (types does not match)  (%s, %s)" % (
                      "%s => %s" % (pc.portItem.name, cls.asHdl(pc.sig, ctx)),
                      repr(pc.portItem._dtype), repr(pc.sig._dtype)))
        return ".%s(%s)" % (pc.portItem.name, cls.asHdl(pc.sig, ctx))

    @classmethod
    def MapExpr(cls, m, createTmpVar):
        return ".%s(%s)" % (m.compSig.name, cls.asHdl(m.value, createTmpVar))
