import os
from pathlib import Path
from .base import BaseConverter

try:
    import aspose.slides as slides
    HAS_ASPOSE = True
except ImportError:
    HAS_ASPOSE = False

class PptxToPdfConverter(BaseConverter):
    """
    Converts PowerPoint (.pptx) files to PDF using Aspose.Slides (Cross-Platform).
    """

    def convert(self, input_path: Path, output_dir: Path) -> Path:
        if not HAS_ASPOSE:
            raise RuntimeError("aspose-slides is required for PPTX to PDF conversion on Linux.")
            
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        base_name = input_path.stem
        output_pdf = output_dir / f"{base_name}.pdf"

        try:
            # Load the presentation
            with slides.Presentation(str(input_path)) as presentation:
                # Save as PDF
                presentation.save(str(output_pdf), slides.export.SaveFormat.PDF)
            
            return output_pdf
            
        except Exception as e:
            raise RuntimeError(f"Failed to convert PPTX to PDF {input_path.name}: {str(e)}")
