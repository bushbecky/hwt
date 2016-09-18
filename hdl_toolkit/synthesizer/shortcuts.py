#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import chain
import os
import shutil

import hdlConvertor
from hdl_toolkit.hdlObjects.architecture import Architecture
from hdl_toolkit.hdlObjects.entity import Entity
from hdl_toolkit.parser.loader import langFromExtension, ParserFileInfo
from hdl_toolkit.serializer.exceptions import SerializerException
from hdl_toolkit.serializer.vhdlSerializer import VhdlSerializer
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.interfaceLevel.unitFromHdl import UnitFromHdl
from hdl_toolkit.synthesizer.interfaceLevel.unitUtils import defaultUnitName
from hdl_toolkit.synthesizer.uniqList import UniqList
from hdl_toolkit.synthesizer.vhdlCodeWrap import VhdlCodeWrap
from python_toolkit.fileHelpers import find_files


def toRtl(unitOrCls, name=None, serializer=VhdlSerializer):
    """
    convert unit to rtl string using specified serializer
    """
    if not isinstance(unitOrCls, Unit):
        u = unitOrCls()
    else:
        u = unitOrCls
    
    assert not u._wasSynthetised()
    
    u._loadDeclarations()
    if name is not None:
        u._name = name
    
    globScope = serializer.getBaseNameScope()
    codeBuff = []
    mouduleScopes = {}

    # unitCls : unitobj
    serializedClasses = {}
    
    # (unitCls, paramsValues) : unitObj
    # where paramsValues are dict name:value
    serializedConfiguredUnits = {}
    
    doSerialize = True
    for obj in u._toRtl():
        doSerialize = serializer.serializationDecision(obj, serializedClasses, serializedConfiguredUnits)
        if doSerialize:
            if isinstance(obj, Entity):
                s = globScope.fork(1)
                s.setLevel(2)
                mouduleScopes[obj] = s
                sc = serializer.Entity(obj, s)
            elif isinstance(obj, Architecture):
                try:
                    s = mouduleScopes[obj.entity]
                except KeyError:
                    raise SerializerException("Entity should be serialized before architecture of %s" % 
                                              (obj.getEntityName()))
                sc = serializer.Architecture(obj, s)
            elif isinstance(obj, VhdlCodeWrap):
                sc = serializer.asHdl(obj)
            elif isinstance(obj, UnitFromHdl):
                sc = str(obj)
            else:
                raise NotImplementedError("Unexpected object %r" % (obj))
        
            codeBuff.append(sc)
        else:
            try:
                name = "(" + obj.name + ")"
            except AttributeError:
                name = ""
                
            codeBuff.append(serializer.comment("Object of class %s%s was not serialized due its serializer mode" % (obj.__class__.__name__, name)))
    
    return serializer.formater(
                     "\n".join(codeBuff)
                     )

def synthesised(u):
    assert not u._wasSynthetised()
    if not hasattr(u, "_interfaces"):
        u._loadDeclarations()

    for _ in u._toRtl():
        pass
    return u


def toRtlAndSave(unit, folderName='.', name=None, serializer=VhdlSerializer):
    unit._loadDeclarations()
    os.makedirs(folderName, exist_ok=True)
    files = UniqList()
    if name is not None:
        unit._name = name
        
    globScope = serializer.getBaseNameScope()
    mouduleScopes = {}
    
    # unitCls : unitobj
    serializedClasses = {}
    
    # (unitCls, paramsValues) : unitObj
    # where paramsValues are dict name:value
    serializedConfiguredUnits = {}
    
    doSerialize = True
    for obj in unit._toRtl():
        doSerialize = serializer.serializationDecision(obj, serializedClasses, serializedConfiguredUnits)
        if doSerialize:
            if isinstance(obj, Entity):
                # we need to serialize before we take name, before name can change
                s = globScope.fork(1)
                s.setLevel(2)
                mouduleScopes[obj] = s
                
                sc = serializer.Entity(obj, s)
                fName = obj.name + serializer.fileExtension
                fileMode = 'w'
                
            elif isinstance(obj, Architecture):
                try:
                    s = mouduleScopes[obj.entity]
                except KeyError:
                    raise SerializerException("Entity should be serialized before architecture of %s" % 
                                              (obj.getEntityName()))
                sc = serializer.Architecture(obj, s)
                fName = obj.getEntityName() + serializer.fileExtension
                fileMode = 'a'
                
            elif isinstance(obj, UnitFromHdl):
                fName = None
                for fn in obj._hdlSources:
                    if isinstance(fn, str):
                        shutil.copy2(fn, folderName)
                        files.append(fn)
            else:
                raise Exception("Do not know how to serialize %r" % (obj))
        
            if fName is not None:
                fp = os.path.join(folderName, fName)
                files.append(fp)
                
                with open(fp, fileMode) as f:
                    if fileMode == 'a':
                        f.write("\n")
                    f.write(
                        serializer.formater(sc)
                        )
    return files

def fileSyntaxCheck(fileInfo, timeoutInterval=20):
    """
    Perform syntax check on whole file
    """
    return hdlConvertor.parse(fileInfo.fileName, fileInfo.lang) 


def _syntaxCheckUnitFromHdl(u):
    for f in u._hdlSources:
        if isinstance(f, str):
            fi = ParserFileInfo(f, 'work')
        else:
            fi = ParserFileInfo(f[1], f[0])
        fileSyntaxCheck(fi)


def syntaxCheck(unitOrFileName):
    if issubclass(unitOrFileName, UnitFromHdl):
        unitOrFileName._buildFileNames()
        _syntaxCheckUnitFromHdl(unitOrFileName)
        
    elif isinstance(unitOrFileName, UnitFromHdl):
        _syntaxCheckUnitFromHdl(unitOrFileName)
    elif isinstance(unitOrFileName, Unit):
        try:
            unitName = unitOrFileName._name
        except AttributeError:
            unitName = defaultUnitName(unitOrFileName)
        
        d = "__pycache__/" + unitName
        toRtlAndSave(unitOrFileName, d)
        for f in chain(find_files(d, '*.vhd', recursive=True), find_files(d, '*.v', recursive=True)):
            fileSyntaxCheck(ParserFileInfo(d, 'work'))
        
    elif isinstance(unitOrFileName, str):
        fileSyntaxCheck(f, langFromExtension(unitOrFileName))
    else:
        raise  NotImplementedError("Not implemented for '%'" % (repr(unitOrFileName)))
    
def serializeAsIpcore(unit, folderName=".", name=None, serializer=VhdlSerializer):
    from cli_toolkit.ip_packager.packager import Packager
    p = Packager(unit, name=name)
    p.createPackage(folderName)
    return p
    
    
