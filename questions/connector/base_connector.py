import abc

from schedule.generators import Session


class ConnectorInterface(abc.ABC):
    @abc.abstractmethod
    def transfer(self, sessions: list[Session]):
        pass
