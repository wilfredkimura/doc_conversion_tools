import os
import re
import base64
from pathlib import Path
from markitdown import MarkItDown
from .base import BaseConverter

class PptxToMarkdownConverter(BaseConverter):
    """
    Converts PowerPoint (.pptx) files to Markdown (.md)
    """

    def __init__(self, images_dirname="images"):
        self.md = MarkItDown()
        self.images_dirname = images_dirname

    def _extract_and_replace_images(self, content, base_name, sub_images_dir):
        """
        Finds base64 data URIs in the content, saves them as files,
        and replaces the URIs with local relative paths.
        """
        img_pattern = r'!\[(.*?)\]\(data:image/(?P<ext>.*?);base64,(?P<data>.*?)\)'
        
        def replace_with_local(match):
            alt_text = match.group(1)
            ext = match.group('ext')
            data = match.group('data')
            
            img_index = getattr(replace_with_local, "counter", 0)
            replace_with_local.counter = img_index + 1
            
            img_filename = f"image_{img_index}.{ext}"
            img_path = sub_images_dir / img_filename
            
            try:
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(data))
                # Return relative path for Markdown
                return f"![{alt_text}]({self.images_dirname}/{base_name}/{img_filename})"
            except Exception as e:
                return match.group(0)

        replace_with_local.counter = 0
        return re.sub(img_pattern, replace_with_local, content)

    def convert(self, input_path: Path, output_dir: Path) -> Path:
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        base_name = input_path.stem
        output_md = output_dir / f"{base_name}.md"
        
        # Create image subdirectory
        sub_images_dir = output_dir / self.images_dirname / base_name
        sub_images_dir.mkdir(parents=True, exist_ok=True)

        try:
            result = self.md.convert(str(input_path), keep_data_uris=True)
            content = result.text_content
            
            # Process images
            final_content = self._extract_and_replace_images(content, base_name, sub_images_dir)
            
            # Write final Markdown
            with open(output_md, "w", encoding='utf-8') as f:
                f.write(final_content)
            
            return output_md
            
        except Exception as e:
            raise RuntimeError(f"Failed to convert {input_path.name}: {str(e)}")
