from hwt.interfaces.agents.signal import SignalAgent
from hwt.interfaces.agents.vldSynced import VldSyncedAgent
from hwt.simulator.agentBase import SyncAgentBase
from hwtSimApi.agents.base import AgentBase


class RegCntrlAgent(SyncAgentBase):
    """
    Simulation/verification agent for RegCntrl interface
    """

    def __init__(self, sim, intf):
        super().__init__(sim, intf)

        self._din = SignalAgent(sim, intf.din)
        self._dout = VldSyncedAgent(sim, intf.dout, allowNoReset=True)

    def setEnable_asDriver(self, en: bool):
        AgentBase.setEnable(self, en)
        self._din.setEnable(en)
        self._dout.setEnable(en)

    def setEnable_asMonitor(self, en: bool):
        AgentBase.setEnable(self, en)
        self._din.setEnable(en)
        self._dout.setEnable(en)

    def din_getter(self):
        return self._din.data

    def din_setter(self, newVal):
        self._din.data = newVal

    din = property(din_getter, din_setter)

    def dout_getter(self):
        return self._dout.data

    def dout_setter(self, newVal):
        self._dout.data = newVal

    dout = property(dout_getter, dout_setter)

    def getDrivers(self):
        yield from self._din.getMonitors()
        yield from self._dout.getDrivers()

    def getMonitors(self):
        yield from self._din.getDrivers()
        yield from self._dout.getMonitors()
