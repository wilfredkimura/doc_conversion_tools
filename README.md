# PPTX to Markdown Converter for NotebookLM

This tool converts PowerPoint files into Markdown format, making them easy to upload into NotebookLM or use in other Markdown-based tools.

## Features
- Extracts slide text and structure.
- Extracts images and saves them into a structured subfolder.
- Replaces embedded image data with relative Markdown links.
- Batch processing of directories or single-file conversion.

## Installation

Ensure you have Python installed, then install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Convert all PPTX in current directory
```bash
python pptx_to_md.py
```

### Convert a specific file
```bash
python pptx_to_md.py "my_lecture.pptx"
```

### Convert all PPTX in another folder
```bash
python pptx_to_md.py "C:/path/to/lectures"
```

## Tips for NotebookLM
NotebookLM works best with clean text. These Markdown files provide a clear slide-by-slide breakdown which helps the model cite specific parts of your lecture notes accurately.
