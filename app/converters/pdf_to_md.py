from pathlib import Path
from markitdown import MarkItDown
from .base import BaseConverter

class PdfToMarkdownConverter(BaseConverter):
    """
    Converts PDF files to Markdown (.md)
    """

    def __init__(self):
        self.md = MarkItDown()

    def convert(self, input_path: Path, output_dir: Path) -> Path:
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        base_name = input_path.stem
        output_md = output_dir / f"{base_name}.md"

        try:
            # MarkItDown handles PDF to Markdown directly
            result = self.md.convert(str(input_path))
            content = result.text_content
            
            with open(output_md, "w", encoding='utf-8') as f:
                f.write(content)
            
            return output_md
            
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF {input_path.name}: {str(e)}")
