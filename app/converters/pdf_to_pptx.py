import os
from pathlib import Path
from .base import BaseConverter

try:
    import aspose.slides as slides
    HAS_ASPOSE = True
except ImportError:
    HAS_ASPOSE = False

class PdfToPptxConverter(BaseConverter):
    """
    Converts PDF files to PowerPoint (.pptx) using Aspose.Slides (Cross-Platform).
    """

    def convert(self, input_path: Path, output_dir: Path) -> Path:
        if not HAS_ASPOSE:
            raise RuntimeError("aspose-slides is required for PDF to PPTX conversion.")
            
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        base_name = input_path.stem
        output_pptx = output_dir / f"{base_name}.pptx"

        try:
            # Create a new presentation
            with slides.Presentation() as pres:
                # Remove the first default slide
                pres.slides.remove_at(0)
                
                # Import the PDF as slides
                # Note: aspose-slides handles PDF import directly
                pres.slides.add_from_pdf(str(input_path))
                
                # Save the presentation
                pres.save(str(output_pptx), slides.export.SaveFormat.PPTX)
            
            return output_pptx
            
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF to PPTX {input_path.name}: {str(e)}")
