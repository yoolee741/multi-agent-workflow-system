# Agent 공통 베이스 
import logging
from pathlib import Path
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, workflow_id: str, input_path: Path, output_path: Path):
        self.workflow_id = workflow_id
        self.input_path = input_path 
        self.output_path = output_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.agent_id = None  # 필요하면 DB 저장용 식별자 할당

    @abstractmethod
    async def run(self):
        """
        각 Agent가 구현해야 할 핵심 실행 메서드.
        """
        pass