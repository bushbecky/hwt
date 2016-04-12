#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
import json, inspect, os

from vhdl_toolkit.hdlContext import HDLCtx, BaseVhdlContext, HDLParseErr, FakeStd_logic_1164, \
    RequireImportErr, BaseVerilogContext

from vhdl_toolkit.hdlObjects.reference import HdlRef
from vhdl_toolkit.hdlObjects.operator import Operator
from vhdl_toolkit.hdlObjects.operatorDefs import AllOps
from vhdl_toolkit.hdlObjects.portItem import PortItem
from vhdl_toolkit.hdlObjects.entity import Entity
from vhdl_toolkit.hdlObjects.package import PackageHeader, PackageBody
from vhdl_toolkit.hdlObjects.architecture import Architecture
from vhdl_toolkit.hdlObjects.component import ComponentInstance
from vhdl_toolkit.hdlObjects.value import Value

from vhdl_toolkit.synthetisator.param import Param
from vhdl_toolkit.synthetisator.rtlLevel.signal import SignalNode

from vhdl_toolkit.hdlObjects.typeDefs import STR, Std_logic_vector, Wire
from vhdl_toolkit.hdlObjects.typeShortcuts import hInt, vec
from vhdl_toolkit.hdlObjects.function import Function
import sys
from vhdl_toolkit.synthetisator.rtlLevel.codeOp import IfContainer, ReturnContainer
import cmd

"""
Parser is generated by antlr4, and is in Java because in Python it is incredibly slow (20min vs 0.2s)

https://github.com/antlr/antlr4/blob/master/doc/getting-started.md
https://github.com/antlr/antlr4
https://github.com/antlr/grammars-v4/blob/master/vhdl/vhdl.g4
https://github.com/loranbriggs/Antlr/blob/master/The%20Definitive%20ANTLR%204%20Reference.pdf
"""


def entityFromFile(fileName, debug=False):
    if fileName.lower().endswith('.v'):
        lang = Parser.VERILOG
    else:
        lang = Parser.VHDL
    
    ctx = Parser.parseFiles([fileName], lang, primaryUnitsOnly=True, debug=debug)
    if lang == Parser.VHDL:
        ctx = ctx['work']
    
    
    assert(len(ctx.entities.items()) == 1)
    ent = list(ctx.entities.items())[0][1]

    return ent

baseDir = os.path.dirname(inspect.getfile(entityFromFile))
assert(os.path.dirname(__file__))  # [TODO] check if matches under any condition and replace inspect
JAVA = 'java'
CONVERTOR = os.path.join(baseDir, "vhdlConvertor", "hdlConvertor.jar")


class ParserException(Exception):
    pass

class VhdlParser():

    def packageHeaderFromJson(self, jPh, ctx):
        ph = PackageHeader(jPh['name'], ctx)
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
    
    def __init__(self, caseSensitive, hierarchyOnly=False, primaryUnitsOnly=True):
        self.caseSensitive = caseSensitive
        self.hierarchyOnly = hierarchyOnly
        self.primaryUnitsOnly = primaryUnitsOnly
    
    def exprFromJson(self, jExpr, ctx):
        lit = jExpr.get("literal", None)
        if lit:
            # vhldConvertor.vhdlSymbolType
            t = lit['type']
            v = lit['value']
            if t == 'ID':
                if not self.caseSensitive:
                    v = v.lower()
                if isinstance(v[0], str):
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
            if operator == AllOps.TERNARY:
                for jOperand in binOp['operands']:
                    operand = self.exprFromJson(jOperand, ctx) 
                    ops.append(operand)
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
            if t != FakeStd_logic_1164.std_logic_vector and not isinstance(t, Wire):
                raise NotImplementedError("Type conversion is not implemented for type %s" % t)
            if t == FakeStd_logic_1164.std_logic_vector:
                width = self.exprFromJson(op['op1'], ctx)
            else:
                width = self.exprFromJson(op['operands'][0], ctx)
            return t(width)
        t_name = HdlRef([t_name_str], self.caseSensitive)
        return ctx.lookupLocal(t_name)

    def varDeclrJson(self, jVar, ctx):
        """parse generics, const arguments of functions etc.."""
        t = jVar["type"]
        name = jVar['name']
        if not self.caseSensitive:
            name = name.lower()
        t = self.typeFromJson(t, ctx)
        if type(t) is Std_logic_vector:
            try:
                t.derivedWidth = int(jVar['value']['literal']["bits"])
            except KeyError:
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
        g.setHdlName(jVar['name'])
        g._name = name
        return g

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
        ci.entityRef = HdlRef.fromExprJson(jComp['entityName'], self.caseSensitive)
        if not self.hierarchyOnly:
            raise NotImplementedError()
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
            raise NotImplementedError()
        return a
    
    def statementFromJson(self, jStm, ctx):
        t = jStm['type']
        if t == 'IF':
            cond = [self.exprFromJson(jStm['cond'], ctx)]
            ifTrue = [ self.statementFromJson(x, ctx) for x in jStm['ifTrue']]
            ifFalse = [ self.statementFromJson(x, ctx) for x in jStm['ifFalse']]
            return IfContainer(cond, ifTrue, ifFalse)
        elif  t == 'RETURN':
            return ReturnContainer(self.exprFromJson(jStm['val'], ctx))
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
            returnT = self.typeFromJson(jFn['returnT'], ctx)
            
            for jP in jFn['params']:
                p = self.varDeclrJson(jP, ctx) 
                params.append(p)
                fnCtx.insertObj(p, self.caseSensitive, self.hierarchyOnly)
                
            for jL in jFn['locals']:
                l = self.varDeclrJson(jL, ctx)
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

        for phName, jPh in jsonctx["packageHeaders"].items():
            ph = self.packageHeaderFromJson(jPh, ctx)
            assert(ph.name == phName)
            n = ph.name
            if not self.caseSensitive:
                n = n.lower()
            if n not in ctx.packages:
                ctx.insertObj(ph, self.caseSensitive)
            else:
                ctx.packages[n].update(ph)

        for eName, jE in jsonctx["entities"].items():
            ent = self.entityFromJson(jE, ctx)
            assert(ent.name == eName)
            ent.fileName = fileName
            ent.dependencies = dependencies
            ctx.insertObj(ent, self.caseSensitive)

        if not self.primaryUnitsOnly:
            for pbName, jpBody in jsonctx["packages"].items():
                pb = self.packageBodyFromJson(jpBody, ctx)
                assert(pb.name == pbName)
                n = pb.name
                if not self.caseSensitive:
                    n = n.lower()
                if n not in ctx.packages:
                    ph = PackageHeader(n, ctx, isDummy=True)
                    ph.insertBody(pb)
                    ctx.insertObj(ph, self.caseSensitive)
                else:
                    ctx.packages[n].insertBody(pb)

            for jArch in jsonctx['architectures']:
                arch = self.archFromJson(jArch, ctx)
                arch.fileName = fileName
                arch.dependencies = dependencies
                ctx.insertObj(arch, self.caseSensitive)

    @staticmethod
    def parseFiles(fileList: list, lang, hdlCtx=None, libName="work", timeoutInterval=20,
                  hierarchyOnly=False, primaryUnitsOnly=False, ignoreErrors=False, debug=False):
        """
        @param fileList: list of files to parse in same context
        @param lang: hdl language name (currently supported are vhdl and verilog)
        @param hdlCtx: parent HDL context
        @param libName: name of actual library
        @param timeoutInterval: timeout for process of external vhdl parser
        @param hierarchyOnly: discover only presence of entities, architectures
               and component instances inside, packages and components inside, packages
        @param primaryUnitsOnly: parse only entities and package headers
        """
        if lang == Parser.VHDL:
            caseSensitivity = False
            baseCtxCls = BaseVhdlContext
        elif lang == Parser.VERILOG:
            caseSensitivity = True
            baseCtxCls = BaseVerilogContext
        else:
            raise ParserException("Invalid lang specification \"%s\" is not supported" % (str(lang)))
        
        parser = Parser(caseSensitivity, hierarchyOnly=hierarchyOnly, primaryUnitsOnly=primaryUnitsOnly)
        
        if isinstance(fileList, str):
            fileList = [fileList]
        # if hdlCtx is not specified create base context and "work" contex nested inside 
        if hdlCtx is None:
            topCtx = baseCtxCls.getBaseCtx()
            baseCtxCls.importFakeLibs(topCtx)
            if lang == Parser.VHDL:
                # in vhdl current context is nested in global as 'work'
                hdlCtx = HDLCtx(libName, topCtx)
                topCtx.insert(HdlRef([libName], parser.caseSensitive), hdlCtx)
            else:
                hdlCtx = topCtx
        # start parsing all files    
        p_list = []
        for fname in fileList:
            cmd = [JAVA, "-jar", str(CONVERTOR), fname]
            if hierarchyOnly:
                cmd.append('-h')
            if debug:
                cmd.append("-d")
            cmd.extend(('-langue', lang))
    
            p = Popen(cmd, stdout=PIPE)
    
            p.fileName = fname
            p_list.append(p)
    
        # collect parsed json from java parser and construct python objects
        for p in p_list:
            stdoutdata, stdErrData = p.communicate(timeout=timeoutInterval)
    
            if p.returncode != 0:
                raise ParserException("Failed to parse file %s" % (p.fileName))
            try:
                if stdoutdata == b'':
                    j = None
                else:
                    j = json.loads(stdoutdata.decode("utf-8"))
            except ValueError:
                raise ParserException(("Failed to parse file %s, ValueError while parsing" + 
                                " json from convertor\n%s") % (p.fileName, stdErrData.decode()))
                
            if not ignoreErrors and (stdErrData != b'' and stdErrData is not None):
                sys.stderr.write(stdErrData.decode()) 
                
            if j:
                parser.parse(j, p.fileName, hdlCtx)
    
        return topCtx
