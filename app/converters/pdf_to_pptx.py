import subprocess
import sys
from pathlib import Path
from .base import BaseConverter

class PdfToPptxConverter(BaseConverter):
    """
    Converts PDF files to PowerPoint (.pptx) by rendering pages as images.
    """

    def convert(self, input_path: Path, output_dir: Path) -> Path:
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        base_name = input_path.stem
        # pdf2pptx usually creates a file with the same name in the current directory or specified one
        output_pptx = output_dir / f"{base_name}.pptx"

        try:
            # We call the CLI tool directly for simplicity and reliability
            # Command: pdf2pptx -o output.pptx input.pdf
            # Note: Checking the exact CLI arguments for pdf2pptx
            result = subprocess.run(
                [sys.executable, "-m", "pdf2pptx", "-o", str(output_pptx), str(input_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"pdf2pptx failed: {result.stderr}")
            
            return output_pptx
            
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF to PPTX {input_path.name}: {str(e)}")
