from abc import ABC, abstractmethod
from pathlib import Path

class BaseConverter(ABC):
    """
    Abstract base class for all document converters.
    """
    
    @abstractmethod
    def convert(self, input_path: Path, output_dir: Path) -> Path:
        """
        Converts the input file and returns the path to the resulting file.
        """
        pass
