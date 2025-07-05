from abc import ABC, abstractmethod
from pathlib import Path
from ..models import ExtractionResult, ExtractionTask, StrategyType

class BaseExtractionStrategy(ABC):
    """
    Abstract base class for all extraction strategies.
    Defines the common interface and properties for different extraction methods.
    """
    def __init__(self, strategy_type: StrategyType, cost_tier: int):
        self.strategy_type = strategy_type
        self.cost_tier = cost_tier

    @abstractmethod
    async def extract(self, pdf_path: Path, task: ExtractionTask) -> ExtractionResult:
        """
        The main method for an extraction strategy. It must be implemented by all subclasses.
        
        Args:
            pdf_path: The path to the PDF file to be processed.
            task: The ExtractionTask object containing details about the job.

        Returns:
            An ExtractionResult object containing the outcome of the extraction.
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.strategy_type}, tier={self.cost_tier})" 