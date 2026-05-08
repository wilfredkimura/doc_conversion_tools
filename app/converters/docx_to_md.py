import os
from pathlib import Path
from markitdown import MarkItDown
from .base import BaseConverter

class DocxToMarkdownConverter(BaseConverter):
    """
    Converts Word (.docx) files to Markdown (.md) using MarkItDown.
    """

    def __init__(self):
        self.md = MarkItDown()

    def convert(self, input_path: Path, output_dir: Path) -> Path:
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        base_name = input_path.stem
        output_md = output_dir / f"{base_name}.md"

        try:
            # MarkItDown handles docx automatically
            result = self.md.convert(str(input_path))
            content = result.text_content
            
            with open(output_md, "w", encoding='utf-8') as f:
                f.write(content)
            
            return output_md
            
        except Exception as e:
            raise RuntimeError(f"Failed to convert {input_path.name}: {str(e)}")
