#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdl_toolkit.hdlContext import HDLCtx, BaseVhdlContext, HDLParseErr, FakeStd_logic_1164, \
    RequireImportErr, BaseVerilogContext

from hdl_toolkit.hdlObjects.reference import HdlRef
from hdl_toolkit.hdlObjects.operator import Operator
from hdl_toolkit.hdlObjects.operatorDefs import AllOps
from hdl_toolkit.hdlObjects.portItem import PortItem
from hdl_toolkit.hdlObjects.entity import Entity
from hdl_toolkit.hdlObjects.package import PackageHeader, PackageBody
from hdl_toolkit.hdlObjects.architecture import Architecture
from hdl_toolkit.hdlObjects.component import ComponentInstance
from hdl_toolkit.hdlObjects.value import Value

from hdl_toolkit.synthetisator.param import Param
from hdl_toolkit.synthetisator.rtlLevel.signal import SignalNode, Signal

from hdl_toolkit.hdlObjects.typeDefs import STR, Std_logic_vector, Wire
from hdl_toolkit.hdlObjects.typeShortcuts import hInt, vec
from hdl_toolkit.hdlObjects.function import Function
from hdl_toolkit.synthetisator.rtlLevel.codeOp import IfContainer, ReturnContainer, \
    WhileContainer
from hdl_toolkit.hdlObjects.assignment import Assignment

"""
Parser is generated by antlr4, and is in Java because in Python it is incredibly slow (20min vs 0.2s)

https://github.com/antlr/antlr4/blob/master/doc/getting-started.md
https://github.com/antlr/antlr4
https://github.com/antlr/grammars-v4/blob/master/vhdl/vhdl.g4
https://github.com/loranbriggs/Antlr/blob/master/The%20Definitive%20ANTLR%204%20Reference.pdf
"""

class ParserException(Exception):
    pass

class VhdlParser():

    def packageHeaderFromJson(self, jPh, ctx):
        ph = PackageHeader(jPh['name'], ctx)
        if not self.functionsOnly:
            for _, jComp in jPh['components'].items():
                c = self.entityFromJson(jComp, ctx)
                ph.insertObj(c, self.caseSensitive)
        for jFn in jPh['functions']:
            fn = self.functionFromJson(jFn, ctx)
            ph.insertObj(fn, self.caseSensitive, hierarchyOnly=self.hierarchyOnly)
        # [TODO] types constants etc
        # if not self.hierarchyOnly:
        #    raise NotImplementedError()
        return ph

    def packageBodyFromJson(self, jPack, ctx):
        pb = PackageBody(jPack['name'], ctx)
        
        # [TODO] types constants etc
        for jFn in jPack['functions']:
            fn = self.functionFromJson(jFn, ctx)
            pb.insertObj(fn, self.caseSensitive, hierarchyOnly=self.hierarchyOnly)
        # if not self.hierarchyOnly:
        #    raise NotImplementedError()
        return pb

class Parser(VhdlParser):
    VERILOG = 'verilog'
    VHDL = 'vhdl'
    _cache = {}  # key = (hierarchyOnly, fileName) 
    def __init__(self, caseSensitive, hierarchyOnly=False, primaryUnitsOnly=True, functionsOnly=False):
        self.caseSensitive = caseSensitive
        self.hierarchyOnly = hierarchyOnly
        self.primaryUnitsOnly = primaryUnitsOnly
        self.functionsOnly = functionsOnly
    
    def exprFromJson(self, jExpr, ctx):
        lit = jExpr.get("literal", None)
        if lit:
            # vhldConvertor.vhdlSymbolType
            t = lit['type']
            v = lit['value']
            if t == 'ID':
                if isinstance(v[0], str):  # [TODO] not clear
                    ref = HdlRef([v], self.caseSensitive)
                else:
                    ref = HdlRef.fromJson(v, self.caseSensitive)
                v = ctx.lookupLocal(ref)
            elif t == 'INT':
                bits = lit.get("bits", None)
                if bits is None:
                    v = hInt(v)
                else:
                    v = vec(v, bits)
            elif t == 'STRING':
                v = Value.fromPyVal(str(v), STR)
            else:
                raise HDLParseErr("Unknown type of literal %s" % (t))
            return v
        binOp = jExpr['binOperator']
        if binOp:
            operator = AllOps.opByName(binOp['operator'])
            op0 = self.exprFromJson(binOp['op0'], ctx)
            ops = [op0]
            if operator == AllOps.TERNARY or operator == AllOps.CALL:
                for jOperand in binOp['operands']:
                    operand = self.exprFromJson(jOperand, ctx) 
                    ops.append(operand)
                # [TODO] extract this vhdl stuff somewhere else
                if isinstance(ops[0], Signal):
                    operator = AllOps.INDEX
            else:
                if operator == AllOps.DOT:
                    l = binOp['op1']['literal']
                    assert(l['type'] == "ID")
                    ops.append(l['value'])
                else:
                    ops.append(self.exprFromJson(binOp['op1'], ctx)) 
            return SignalNode.resForOp(Operator(operator, ops))
        raise HDLParseErr("Unparsable expression %s" % (str(jExpr)))

    def portFromJson(self, jPort, ctx):
        v = jPort['variable']
        var_type = self.typeFromJson(v['type'], ctx)
        p = PortItem(v['name'], jPort['direction'], var_type)
        val = v['value']
        if val is not None:
            p.defaultVal = self.exprFromJson(val, ctx)
        return p

    # [TODO] width resolution is a mess
    def typeFromJson(self, jType, ctx):
        try:
            t_name_str = jType['literal']['value']
        except KeyError:
            op = jType['binOperator']
            t_name = HdlRef.fromJson(op['op0'], self.caseSensitive)
            t = ctx.lookupLocal(t_name)
            if isinstance(t, Wire):
                width = self.exprFromJson(op['operands'][0], ctx)
            elif isinstance(t, Std_logic_vector):
                width = self.exprFromJson(op['op1'], ctx)
            else:
                raise NotImplementedError("Type conversion is not implemented for type %s" % t)
                
            return t(width)
        t_name = HdlRef([t_name_str], self.caseSensitive)
        return ctx.lookupLocal(t_name)

    def varDeclrJson(self, jVar, ctx):
        """parse generics, const arguments of functions etc.."""
        name = jVar['name']
        t = jVar["type"]
        t = self.typeFromJson(t, ctx)
        if type(t) is Std_logic_vector:
            try:
                t.derivedWidth = int(jVar['value']['literal']["bits"])
            except KeyError:
                pass
            except TypeError:
                pass
        v = jVar['value']
        if v is not None:
            defaultVal = self.exprFromJson(v, ctx)
            # convert it to t of variable (type can be different for example 1 as Natural or Integer)
            defaultVal = defaultVal.dtype.convert(defaultVal, t)
        else:
            defaultVal = Value.fromPyVal(None, t)
        g = Param(defaultVal)
        g.dtype = t
        g.setHdlName(name)
        g._name = self._hdlId(name)
        return g

    def _hdlId(self, _id):
        if self.caseSensitive:
            return _id
        else:
            return _id.lower()
         
    def entityFromJson(self, jEnt, ctx):
        e = Entity()
        e.name = jEnt['name']
        if not self.hierarchyOnly:
            entCtx = HDLCtx(e.name, ctx)
            for jGener in jEnt['generics']:
                g = self.varDeclrJson(jGener, entCtx)
                e.generics.append(g)
                entCtx[g._name] = g
                
            # entCtx.update(ctx)
            for jPort in jEnt['ports']:
                p = self.portFromJson(jPort, entCtx)
                e.ports.append(p)
            
            e.generics.sort(key=lambda x: x.name)
            e.ports.sort(key=lambda x: x.name)
        return e

    def componentInstanceFromJson(self, jComp, ctx):
        ci = ComponentInstance(jComp['name'], None)
        ci.entityRef = HdlRef.fromJson(jComp['entityName'], self.caseSensitive)
        if not self.hierarchyOnly:
            pass
            # raise NotImplementedError()
            # [TODO] port, generics maps
        return ci

    def archFromJson(self, jArch, ctx):
        a = Architecture(None)
        a.entityName = jArch["entityName"]
        a.name = jArch['name']
        for jComp in jArch['componentInstances']:
            ci = self.componentInstanceFromJson(jComp, ctx)
            a.componentInstances.append(ci)
        if not self.hierarchyOnly:
            pass  # [TODO]
            # raise NotImplementedError()
        return a
    
    def statementFromJson(self, jStm, ctx):
        t = jStm['type']
        expr = lambda name: self.exprFromJson(jStm[name], ctx)
        stList = lambda name: [ self.statementFromJson(x, ctx) for x in jStm[name]] 
        
        if t == 'ASSIGMENT':
            src = expr('src')
            dst = expr('dst')
            return Assignment(src, dst)                        
        elif t == 'IF':
            cond = [expr('cond')]    
            ifTrue = stList('ifTrue')
            ifFalse = stList('ifFalse')
            return IfContainer(cond, ifTrue, ifFalse)
        elif t == 'RETURN':
            return ReturnContainer(expr('val'))
        elif t == 'WHILE':
            cond = [expr('cond')]
            body = stList('body')
            return WhileContainer(cond, body)
        else:
            raise NotImplementedError(t)
    
    def functionFromJson(self, jFn, ctx):
        name = jFn['name']
        isOperator = jFn['isOperator']
        returnT = None 
        params = []
        exprList = []
        _locals = []
        fnCtx = HDLCtx(name, ctx)
        if not self.hierarchyOnly:
            returnT = self.typeFromJson(jFn['returnT'], fnCtx)
            
            for jP in jFn['params']:
                p = self.varDeclrJson(jP, fnCtx) 
                params.append(p)
                fnCtx.insertObj(p, self.caseSensitive, self.hierarchyOnly)
                
            for jL in jFn['locals']:
                l = self.varDeclrJson(jL, fnCtx)
                _locals.append(l)
                fnCtx.insertObj(l, self.caseSensitive, self.hierarchyOnly)
                
            
            
            for jStm in jFn['body']:
                exprList.append(self.statementFromJson(jStm, fnCtx))
                
        return Function(name, returnT, fnCtx, params, _locals, exprList, isOperator)

    def parse(self, jsonctx, fileName, ctx):
        """
        @param fileName: vhdl filename
        @param ctx: parent HDL context
        @param hierarchyOnly: discover only presence of entities, architectures
                and component instances inside, packages and components inside, packages
        @param primaryUnitsOnly: parse only entities and package headers
        """
        dependencies = set()
        try:
            for jsnU in jsonctx['imports']:
                u = HdlRef.fromJson(jsnU, self.caseSensitive)
                dependencies.add(u)
                # if ctx.lookupGlobal(u) is None:
                if not self.hierarchyOnly:
                    ctx.importLibFromGlobal(u)
        except RequireImportErr as e:
            e.fileName = fileName
            raise e

        for _, jPh in jsonctx["packageHeaders"].items():
            ph = self.packageHeaderFromJson(jPh, ctx)
            
            n = self._hdlId(ph.name) 
            if n not in ctx.packages:
                ctx.insertObj(ph, self.caseSensitive)
            else:
                ctx.packages[n].update(ph)
                
        if not self.functionsOnly:
            for _, jE in jsonctx["entities"].items():
                ent = self.entityFromJson(jE, ctx)
                ent.parent = ctx
                ent.dependencies = dependencies
                ctx.insertObj(ent, self.caseSensitive)

        if not self.primaryUnitsOnly:
            for _, jpBody in jsonctx["packages"].items():
                pb = self.packageBodyFromJson(jpBody, ctx)
                n = self._hdlId(pb.name) 
                if n not in ctx.packages:
                    ph = PackageHeader(n, ctx, isDummy=True)
                    ph.insertBody(pb)
                    ctx.insertObj(ph, self.caseSensitive)
                else:
                    ctx.packages[n].insertBody(pb)
            if not self.functionsOnly:
                for jArch in jsonctx['architectures']:
                    arch = self.archFromJson(jArch, ctx)
                    arch.parent = ctx
                    arch.dependencies = dependencies
                    ctx.insertObj(arch, self.caseSensitive)

