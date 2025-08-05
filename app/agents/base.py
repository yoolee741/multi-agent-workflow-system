# Agent 공통 베이스
import logging
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def run(self):
        """
        각 Agent가 구현해야 할 핵심 실행 메서드.
        """
        pass
