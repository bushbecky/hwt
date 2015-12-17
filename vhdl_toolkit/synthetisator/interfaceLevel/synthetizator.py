from vhdl_toolkit.parser import entityFromFile
from vhdl_toolkit.synthetisator.interfaceLevel.stdInterfaces import allInterfaces
from vhdl_toolkit.synthetisator.signalLevel.context import Context
from vhdl_toolkit.architecture import Component
from copy import deepcopy


class Connection():
    def __init__(self, *args, src=None, hasExtern=False):
        if not src and not hasExtern:
            raise Exception("Connection has no driver")
        self._src = src
        self._destinations = args
        self._hasExtern = hasExtern
        if not self._src:
            self._src = deepcopy(self._destinations[0]) #create external port signals
        
        for d in self._destinations:
            if d.__class__ != self._src.__class__:
                raise Exception("Can connect only same interfaces (%s), one of destinations is %s" % (str(self._src), str(d.__class__)))
        
class Unit():
    """
    Class members:
    origin  - origin vhdl file
    """
    _entity = None
    _origin = None
    _component = None
    
    def __init__(self):
        if self._origin:
            assert(not self._entity)
            assert(not self._component)
            self._entity = entityFromFile(self._origin)
            #self.component = VHDLUnit(self.entity)
            for intfCls in allInterfaces:
                for intfName, interface in intfCls._tryToExtract(self._entity):
                    if hasattr(self, intfName):
                        raise  Exception("Already has "+ intfName)
                    setattr(self, intfName, interface)
    
    def _build(self, name):
        """
        Sort out informations about sub units and connections from class body
        """
        self._name = name
        self._connections = {}
        self._subUnits = {}
        for propName, prop in self.__class__.__dict__.items():
            if isinstance(prop, Connection):
                self._connections[propName] = prop
            elif issubclass(prop.__class__, Unit):
                self._subUnits[propName] = prop
                    
    def _synthetize(self, name):
        """
        synthetize all subunits, make connections between them, build entity and component for this unit
        """
        self._build(name)
        if self._origin:
            assert(self._entity)
            with open(self._origin) as f:
                yield f.read()  
        else:  
            cntx = Context(name)
            externInterf = [] 
            for subUnitName, subUnit in self._subUnits.items():
                yield from subUnit._synthetize(subUnitName)
                
            for connectionName, connection in self._connections.items():
                if connection._hasExtern:
                    externInterf.extend(connection._src._signalsForInterface(cntx, connectionName))
                for intf in connection._destinations:
                    pass
                    #print(intf)
            s = cntx.synthetize(externInterf)
            self._entity = s[1]
            self._architecture = s[2]
            yield from s
        self._component = Component(self._entity)
               
