import subprocess
from typing import List
import xml.etree.ElementTree as ET
from config import config as opt
import argparse
import cairosvg
import os

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __str__(self):
        return f'({self.x}, {self.y})'
    
    def __repr__(self) -> str:
        return self.__str__()

class Line:
    def __init__(self, p1: Point, p2: Point):
        self.p1 = p1
        self.p2 = p2
    
    def __str__(self):
        return f'{self.p1} - {self.p2}'
    
    def __repr__(self) -> str:
        return self.__str__()

class Area:
    # B . -------> . C
    # ^              |
    # |              
    # A . <------- . D
    def __init__(self, a: Point, b: Point, c: Point, d: Point, orientation: str):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.orientation = orientation
    
    def __str__(self):
        return f'{self.a} - {self.b} - {self.c} - {self.d}'
    
    def __repr__(self) -> str:
        return self.__str__()

def draw_walls(input_file):
    svg_temp_file = 'output.svg'
    mount_path = '%cd%' if os.name == 'nt' else '$(pwd)'
    result = convert_to_svg(input_file, svg_temp_file, mount_path)
    if result == 0:
        tree = ET.parse(svg_temp_file)
        root = tree.getroot()
        horizontal_lines, vertical_lines, horizontal_markers, vertical_markers, gray_filled, transform = parse_svg(root)
        horizontal_walls = extract_horizontal_walls_candidates(sorted(horizontal_lines, key=lambda x: x.p1.y))
        vertical_walls = extract_vertical_walls_candidates(sorted(vertical_lines, key=lambda x: x.p1.x))
        
        # filter walls that are not intersecting with markers
        horizontal_walls = list(filter(lambda x: enough_markers_inside(x, horizontal_markers, vertical_markers), horizontal_walls))
        vertical_walls = list(filter(lambda x: enough_markers_inside(x, horizontal_markers, vertical_markers), vertical_walls))
        
        # draw walls
        for wall in horizontal_walls:
            root.append(wall_element(wall, transform))
        for wall in vertical_walls:
            root.append(wall_element(wall, transform))
        for gray in gray_filled:
            root.append(wall_element(gray))
    
        # delete temp svg file
        os.remove(svg_temp_file)
    
        # convert to pdf
        cairosvg.svg2pdf(bytestring=ET.tostring(root), write_to=input_file.replace('.pdf', '_walls.pdf'))

def gray_filled_inside(wall: Area, gray_filled: List[Area]):
    for area in gray_filled:
        if is_inside(area.a, wall) and is_inside(area.b, wall) and is_inside(area.c, wall) and is_inside(area.d, wall):
            return True
    return False

def enough_markers_inside(wall: Area, horizontal_markers: List[Line], vertical_markers: List[Line]):
    # count number of markers that are inside the wall
    markers_inside = 0
    for marker in horizontal_markers:
        if is_inside(marker.p1, wall) and is_inside(marker.p2, wall):
            markers_inside += 1
    for marker in vertical_markers:
        if is_inside(marker.p1, wall) and is_inside(marker.p2, wall):
            markers_inside += 1
    return markers_inside > opt.needed_markers_count

def is_inside(point: Point, wall: Area):
    return wall.a.x <= point.x <= wall.c.x and wall.a.y <= point.y <= wall.c.y

def wall_element(wall: Area, transform=None):
    x1 = wall.a.x if wall.orientation == 'h' else (wall.a.x + wall.d.x)//2 
    y1 = (wall.a.y + wall.b.y)//2 if wall.orientation == 'h' else wall.a.y 
    x2 = wall.c.x if wall.orientation == 'h' else (wall.b.x + wall.c.x)//2
    y2 = (wall.a.y + wall.b.y)//2 if wall.orientation == 'h' else wall.c.y
    return ET.Element('path', attrib={'d': 'M ' + str(x1) + ' ' + str(y1) + ' L ' + str(x2) + ' ' + str(y2), 'stroke-width': opt.draw_width if transform else opt.no_transformation_draw_width, 'stroke' : opt.red_color, 'transform': transform if transform else ''})

def convert_to_svg(input_file, svg_temp_file, mount_path):
    result = subprocess.call(f'docker run --rm  -v {mount_path}:/app -w /app minidocks/poppler pdf2svg {input_file} {svg_temp_file}', shell=True)
    return result

def parse_svg(root):
    horizontal_lines, vertical_lines, horizontal_markers, vertical_markers, gray_filled = [], [], [], [], []
    transform = None
    for elem in root.iter():
        if is_stroke(elem):
            parsed_coordinates = elem.attrib['d'].split(' ')
            x1, y1, x2, y2 = float(parsed_coordinates[1]), float(parsed_coordinates[2]), float(parsed_coordinates[4]), float(parsed_coordinates[5])
            if transform is None and 'transform' in elem.attrib:
                transform = elem.attrib['transform']
            
            if elem.attrib["stroke-width"] in opt.walls_stroke_widths and elem.attrib["stroke"] == opt.wall_color:
                if y1 == y2:
                    horizontal_lines.append(Line(Point(min(x1, x2), y1), Point(max(x1, x2), y2)))
                elif x1 == x2:
                    vertical_lines.append(Line(Point(x1, min(y1, y2)), Point(x2, max(y1, y2))))
            
            if elem.attrib["stroke-width"] in opt.walls_markers_widths and elem.attrib["stroke"] == opt.wall_marker_color:
                if y1 == y2 and abs(x1 - x2) >= opt.wall_marker_min_length:
                    horizontal_markers.append(Line(Point(min(x1, x2), y1), Point(max(x1, x2), y2)))
                elif x1 == x2 and abs(y1 - y2) >= opt.wall_marker_min_length:
                    vertical_markers.append(Line(Point(x1, min(y1, y2)), Point(x2, max(y1, y2))))

        if "fill" in elem.attrib and elem.attrib["fill"] != "none":
            rgb = parse_rgb(elem.attrib["fill"])
            # check if all rbg values are in the gray range
            if rgb and all(opt.gray_lower <= x <= opt.gray_upper for x in rgb):
                d = elem.attrib["d"]
                # parse 'M x1 y1 L x2 y2 L x3 y3 L x4 y4 Z M x1 y1 ' to ((x1, y1), (x2, y2), (x3, y3), (x4, y4))
                splited = d.split(' ')
                if len(splited) == 17 and splited[12] == 'Z':
                    x1, y1, x2, y2, x3, y3, x4, y4 = float(splited[1]), float(splited[2]), float(splited[4]), float(splited[5]), float(splited[7]), float(splited[8]), float(splited[10]), float(splited[11])
                    a = Point(min(x1, x2, x3, x4), min(y1, y2, y3, y4))
                    b = Point(min(x1, x2, x3, x4), max(y1, y2, y3, y4))
                    c = Point(max(x1, x2, x3, x4), max(y1, y2, y3, y4))
                    d = Point(max(x1, x2, x3, x4), min(y1, y2, y3, y4))
                    # check if the area is rectangular
                    if a.x == b.x and c.x == d.x and a.y == d.y and b.y == c.y:
                        height = abs(a.y - b.y)
                        width = abs(a.x - d.x)
                        if(min(height, width) > opt.gray_width_lower_bound):
                            gray_filled.append(Area(a, b, c, d, 'v' if height >= width else 'h'))
    return horizontal_lines, vertical_lines, horizontal_markers, vertical_markers, gray_filled, transform

def parse_rgb(rgb):
    # parse 'rgb(49.804688%, 49.804688%, 49.804688%)' to rgb percent values
    if rgb.startswith('rgb('):
        r, g, b = rgb[4:-1].split(',')
        r = float(r[:-1])
        g = float(g[:-1])
        b = float(b[:-1])
        return r, g, b
    return None

def extract_vertical_walls_candidates(sorted_vertical_lines: List[Line]) -> List[Area]:
    vertical_wall_lines = []
    for index, line in enumerate(sorted_vertical_lines[0:-1]):
        for next_line in sorted_vertical_lines[index + 1:]:
            # skip if next line is on the same level as the current line
            if abs(float(line.p1.x) - float(next_line.p1.x)) < opt.same_level_bound:
                continue
            # skip if next line is not intersecting with y coordinate of the current line
            if next_line.p1.y > line.p2.y or next_line.p2.y < line.p1.y:
                continue
            # break if next line is less than width lower bound apart from the current line
            if abs(float(line.p1.x) - float(next_line.p1.y)) < opt.width_lower_bound:
                break
            # append intersection if width is ok
            if abs(float(line.p1.x) - float(next_line.p1.x)) <= opt.width_upper_bound:
                y1 = max(line.p1.y, next_line.p1.y)
                y2 = min(line.p2.y, next_line.p2.y)
                vertical_wall_lines.append(Area(Point(line.p1.x, y1), Point(line.p1.x, y2), Point(next_line.p1.x, y2), Point(next_line.p1.x, y1), 'v'))
    return vertical_wall_lines

def extract_horizontal_walls_candidates(sorted_horizontal_lines: List[Line]) -> List[Area]:
    horizontal_walls = []
    for index, line in enumerate(sorted_horizontal_lines[0:-1]):
        for next_line in sorted_horizontal_lines[index + 1:]:
            # skip if next line is on the same level as the current line
            if abs(float(line.p1.y) - float(next_line.p1.y)) < opt.same_level_bound:
                continue
            # skip if next line is not intersecting with x coordinate of the current line
            if next_line.p1.x > line.p2.x or next_line.p2.x < line.p1.x:
                continue
            # break if next line is less than width lower bound apart from the current line
            if abs(float(line.p1.y) - float(next_line.p1.y)) < opt.width_lower_bound:
                break
            # append intersection if width is ok
            if abs(float(line.p1.y) - float(next_line.p1.y)) <= opt.width_upper_bound:
                x1 = max(line.p1.x, next_line.p1.x)
                x2 = min(line.p2.x, next_line.p2.x)
                horizontal_walls.append(Area(Point(x1, line.p1.y), Point(x1, next_line.p1.y), Point(x2, next_line.p1.y), Point(x2, line.p1.y), 'h'))
    return horizontal_walls

def is_stroke(elem):
    return elem.tag.endswith('path') and 'stroke-width' in elem.attrib and 'stroke' in elem.attrib
                    
if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument('--input', type=str, default='A252.pdf')
    args = args.parse_args()
    draw_walls(args.input)
