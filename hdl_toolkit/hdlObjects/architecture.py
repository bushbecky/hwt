#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Architecture(object):
    """basic vhdl architecture"""
    def __init__(self, entity):
        self.entity = entity
        if entity: 
            self.entityName = entity.name 
        else:
            self.entityName = None
        self.name = "rtl"
        self.variables = []
        self.processes = []
        self.components = []
        self.componentInstances = []
        
        
    def __repr__(self):
        from hdl_toolkit.serializer.vhdlSerializer import VhdlSerializer
        from hdl_toolkit.serializer.formater import formatVhdl
        return formatVhdl(VhdlSerializer.Architecture(self))
