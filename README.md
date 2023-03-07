# Pdf schme vertical and horizontal walls parser

This is a simple parser which takes a pdf file as input and outputs a pdf file with the walls drawn on it.

## Getting started

### Prerequisites

Docker installed on your machine.
Python 3.7 or higher.

1. Clone the project / repo:
```bash
git clone 
```

2. cd into the project folder:
```bash
cd drawer-ai
```

3. Install the requirements:
```bash
pip install -r requirements.txt
```

4. Run the tool:
```bash
python draw_walls.py --input A252.pdf
```

## Notes

This tool recognizes only horizontal and vertical walls. It does not recognize diagonal walls(solution can be improved).
It recognizes walls with configurable width. See config.py for more details.

## U-Net research
Should be also considered utilizing of U-Net architecture for the task of wall detection(collect dataset with masks).
It requires converting the pdf file to a pixel image and vice versa(is it costly?, can it be done without losing quality?).