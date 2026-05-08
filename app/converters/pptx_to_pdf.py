import os
from pathlib import Path
from .base import BaseConverter

try:
    import comtypes.client
    import win32com.client
    HAS_COM = True
except ImportError:
    HAS_COM = False

class PptxToPdfConverter(BaseConverter):
    """
    Converts PowerPoint (.pptx) files to PDF using Microsoft PowerPoint COM API.
    """

    def convert(self, input_path: Path, output_dir: Path) -> Path:
        if not HAS_COM:
            raise RuntimeError("comtypes and pywin32 are required for PPTX to PDF conversion on Windows.")
            
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        base_name = input_path.stem
        output_pdf = output_dir / f"{base_name}.pdf"

        # Ensure absolute paths for COM
        input_abs = str(input_path.absolute())
        output_abs = str(output_pdf.absolute())

        powerpoint = None
        presentation = None
        
        try:
            # Initialize PowerPoint
            # We use Dispatch to handle existing instances or create new one
            powerpoint = win32com.client.Dispatch("Powerpoint.Application")
            
            # Open presentation without window
            presentation = powerpoint.Presentations.Open(input_abs, WithWindow=False, ReadOnly=True)
            
            # Save as PDF (Type 32 = ppSaveAsPDF)
            presentation.SaveAs(output_abs, 32)
            
            return output_pdf
            
        except Exception as e:
            raise RuntimeError(f"Failed to convert PPTX to PDF {input_path.name}: {str(e)}")
        finally:
            if presentation:
                presentation.Close()
            if powerpoint:
                # Only quit if we created it and there are no other presentations? 
                # For safety in a server environment, we might want to be careful.
                # But here we'll just quit.
                powerpoint.Quit()
