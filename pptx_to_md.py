import os
import re
import base64
import argparse
from pathlib import Path
from markitdown import MarkItDown

class PptxToMarkdownConverter:
    """
    A tool to convert PowerPoint (.pptx) files to Markdown (.md)
    optimized for NotebookLM and general use.
    """

    def __init__(self, output_images_dir="images"):
        self.md = MarkItDown()
        self.output_images_dir = Path(output_images_dir)

    def _extract_and_replace_images(self, content, base_name, sub_images_dir):
        """
        Finds base64 data URIs in the content, saves them as files,
        and replaces the URIs with local relative paths.
        """
        # Pattern for data URIs: ![](data:image/png;base64,...)
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
                # Return relative path using forward slashes for cross-platform MD
                return f"![{alt_text}]({self.output_images_dir.name}/{base_name}/{img_filename})"
            except Exception as e:
                print(f"  [!] Error saving image {img_filename}: {e}")
                return match.group(0)

        replace_with_local.counter = 0
        return re.sub(img_pattern, replace_with_local, content)

    def convert_file(self, pptx_path):
        pptx_path = Path(pptx_path)
        if not pptx_path.exists():
            print(f"[!] File not found: {pptx_path}")
            return

        print(f"[*] Converting: {pptx_path.name}")
        base_name = pptx_path.stem
        output_md = pptx_path.parent / f"{base_name}.md"
        
        # Create image subdirectory for this specific file
        sub_images_dir = pptx_path.parent / self.output_images_dir / base_name
        sub_images_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Convert keeping data URIs to handle them manually
            result = self.md.convert(str(pptx_path), keep_data_uris=True)
            content = result.text_content
            
            # Process images
            final_content = self._extract_and_replace_images(content, base_name, sub_images_dir)
            
            # Write final Markdown
            with open(output_md, "w", encoding='utf-8') as f:
                f.write(final_content)
            
            print(f"  [+] Success: Created {output_md.name}")
            
        except Exception as e:
            print(f"  [!] Failed to convert {pptx_path.name}: {e}")

    def convert_directory(self, dir_path):
        dir_path = Path(dir_path)
        pptx_files = [f for f in dir_path.glob("*.pptx") if not f.name.startswith("~$")]
        
        if not pptx_files:
            print(f"No .pptx files found in {dir_path}")
            return

        print(f"[*] Found {len(pptx_files)} files in {dir_path}")
        for pptx_file in pptx_files:
            self.convert_file(pptx_file)

def main():
    parser = argparse.ArgumentParser(description="Convert PPTX files to Markdown for NotebookLM.")
    parser.add_argument("input", nargs='?', default=".", help="Input .pptx file or directory containing .pptx files (default: current dir)")
    parser.add_argument("-i", "--images", default="images", help="Directory name for extracted images (default: images)")

    args = parser.parse_args()
    
    converter = PptxToMarkdownConverter(output_images_dir=args.images)
    
    input_path = Path(args.input)
    if input_path.is_dir():
        converter.convert_directory(input_path)
    else:
        converter.convert_file(input_path)

if __name__ == "__main__":
    main()
