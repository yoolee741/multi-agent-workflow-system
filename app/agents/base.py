# Agent 공통 베이스
import logging
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    에이전트들의 공통 베이스 클래스.

    Attributes:
        workflow_id (str): 실행 중인 워크플로우의 고유 ID.
        logger (logging.Logger): 에이전트 별 로그 기록을 위한 로거 인스턴스.

    Methods:
        run(): 각 에이전트가 반드시 구현해야 하는 비동기 실행 메서드.
    """

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def run(self):
        """
        각 Agent가 구현해야 할 핵심 실행 메서드.
        """
        pass
