import re
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Function to format the coordinate values
def format_coord(value):
    rounded_value = round(value, 3)
    if rounded_value.is_integer():
        return str(int(rounded_value))
    return str(rounded_value)

# Function to parse the 'd' attribute in SVG and convert it to GLIF format
def svg_to_glif(glyph_name, unicode_value, path_data, advance_width=1000, advance_height=1000):
    glif = ET.Element('glyph', {'name': glyph_name, 'format': '2'})
    advance = ET.SubElement(glif, 'advance', {'width': str(int(advance_width)), 'height': str(int(advance_height))})

    if unicode_value:
        unicode_hex = format(ord(unicode_value), 'X')
        ET.SubElement(glif, 'unicode', {'hex': unicode_hex})

    outline = ET.SubElement(glif, 'outline')
    path_data = path_data.strip()
    commands = re.findall(r'([MmLlHhVvZzCcSsQqTt][^MmLlHhVvZzCcSsQqTt]*)', path_data)

    contour = None
    current_pos = [0, 0]
    is_first_point = True

    for command in commands:
        cmd_type = command[0]
        points = list(map(float, re.findall(r'-?\d*\.?\d+', command[1:])))
        if not points:
            continue

        # Handle move command (M or m)
        if cmd_type.lower() == 'm':
            if contour:
                outline.append(contour)
            contour = ET.Element('contour')
            current_pos = [points[0], points[1]]
            if glyph_name == "tok.linja":
                ET.SubElement(contour, 'point', {'x': format_coord(current_pos[0]), 'y': format_coord(current_pos[1]), 'type': 'curve', 'smooth': 'yes'})
            else:
                ET.SubElement(contour, 'point', {'x': format_coord(current_pos[0]), 'y': format_coord(current_pos[1]), 'type': 'line'})
            is_first_point = False

        # Handle line command (L, l)
        elif cmd_type.lower() == 'l':
            for i in range(0, len(points), 2):
                if cmd_type == 'L':
                    current_pos = [points[i], points[i+1]]
                else:
                    current_pos = [current_pos[0] + points[i], current_pos[1] + points[i+1]]
                ET.SubElement(contour, 'point', {'x': format_coord(current_pos[0]), 'y': format_coord(current_pos[1]), 'type': 'line'})

        # Handle vertical line command (V or v)
        elif cmd_type.lower() == 'v':
            for i in range(len(points)):
                if cmd_type == 'V':
                    current_pos[1] = points[i]
                else:
                    current_pos[1] += points[i]
                ET.SubElement(contour, 'point', {'x': format_coord(current_pos[0]), 'y': format_coord(current_pos[1]), 'type': 'line'})

        # Handle horizontal line command (H or h)
        elif cmd_type.lower() == 'h':
            for i in range(len(points)):
                if cmd_type == 'H':
                    current_pos[0] = points[i]
                else:
                    current_pos[0] += points[i]
                ET.SubElement(contour, 'point', {'x': format_coord(current_pos[0]), 'y': format_coord(current_pos[1]), 'type': 'line'})

        # Handle cubic Bézier curve command (C or c)
                # Handle cubic Bézier curve command (C or c)
        elif cmd_type.lower() == 'c':
            for i in range(0, len(points), 6):
                if cmd_type == 'C':
                    control1 = [points[i], points[i+1]]
                    control2 = [points[i+2], points[i+3]]
                    end_point = [points[i+4], points[i+5]]
                else:
                    control1 = [current_pos[0] + points[i], current_pos[1] + points[i+1]]
                    control2 = [current_pos[0] + points[i+2], current_pos[1] + points[i+3]]
                    end_point = [current_pos[0] + points[i+4], current_pos[1] + points[i+5]]
                ET.SubElement(contour, 'point', {'x': format_coord(control1[0]), 'y': format_coord(control1[1])})
                ET.SubElement(contour, 'point', {'x': format_coord(control2[0]), 'y': format_coord(control2[1])})

                # Check if the end point is the same as the first point before adding it
                if not (contour[0].attrib['x'] == format_coord(end_point[0]) and contour[0].attrib['y'] == format_coord(end_point[1])):
                    ET.SubElement(contour, 'point', {'x': format_coord(end_point[0]), 'y': format_coord(end_point[1]), 'type': 'curve', 'smooth': 'yes'})
                current_pos = end_point

        # Handle close path command (Z or z)
        elif cmd_type.lower() == 'z':
            if contour:
                first_point = contour[0].attrib
                last_point = contour[-1].attrib if contour else None
                if last_point and (first_point['x'] == last_point['x'] and first_point['y'] == last_point['y']):
                    contour.remove(contour[-1])  # Remove redundant last point
                outline.append(contour)
                contour = None

    if contour and len(contour) > 1:
        outline.append(contour)

    # Convert the XML structure to a string with pretty formatting
    rough_string = ET.tostring(glif, encoding="unicode")
    reparsed = minidom.parseString(rough_string)

    # Remove the extra space in the XML declaration
    xml_output = reparsed.toprettyxml(indent="  ").replace('<?xml version="1.0" ?>', '<?xml version="1.0"?>')

    return xml_output

# Function to save the .glif content to a file
def save_glif_to_file(glyph_name, glif_data, output_dir="output"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = os.path.join(output_dir, f"{glyph_name}.glif")
    with open(file_path, "w", encoding="utf-8") as glif_file:
        glif_file.write(glif_data)

    print(f"Saved {glyph_name}.glif to {file_path}")

# Function to parse the SVG file and convert all glyphs to .glif files
def convert_svg_glyphs_to_glif(svg_file, output_dir="output"):
    tree = ET.parse(svg_file)
    root = tree.getroot()

    font = root.find(".//{http://www.w3.org/2000/svg}font")
    if font is None:
        print("No font element found in the SVG.")
        return

    for glyph in font.findall("{http://www.w3.org/2000/svg}glyph"):
        glyph_name = glyph.attrib.get("glyph-name", "unnamed_glyph")
        unicode_value = glyph.attrib.get("unicode", "")
        path_data = glyph.attrib.get("d", "")

        if path_data:
            glif_output = svg_to_glif(glyph_name, unicode_value, path_data)
            save_glif_to_file(glyph_name, glif_output, output_dir)

# Example usage: Convert glyphs in 'linja-suwi.svg' to .glif files
svg_file = "linja-suwi.svg"  # Replace with the path to your SVG file
convert_svg_glyphs_to_glif(svg_file, output_dir="glif_output")
