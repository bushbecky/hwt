#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from vhdl_toolkit.templates import VHDLTemplates 
from vhdl_toolkit.hdlContext import HDLCtx

class Entity(object):
    def __init__(self):
        self.port = []
        self.ctx = {}
        self.generics = []
        self.name = None
    
    def injectCtxWithGenerics(self, ctx):
        for g in self.generics:
            ctx[g.name] = g.defaultVal
        return ctx
    def __str__(self):
        self.port.sort(key=lambda x: x.name)
        self.generics.sort(key=lambda x: x.name)
        return VHDLTemplates.entity.render(self.__dict__)
    
    
