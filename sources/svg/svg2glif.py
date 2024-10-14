import re
import xml.etree.ElementTree as ET
import os
from xml.dom import minidom

# Function to parse the 'd' attribute in SVG and convert it to GLIF format
def svg_to_glif(glyph_name, unicode_value, path_data, advance_width=1000):
    # Initialize the root element for the .glif file
    glif = ET.Element('glyph', {'name': glyph_name, 'format': '2'})
    
    # Add the advance width
    advance = ET.SubElement(glif, 'advance', {'width': str(advance_width)})
    
    # Create the outline element
    outline = ET.SubElement(glif, 'outline')

    # Parse the path data
    path_data = path_data.strip()
    
    # Regular expression for matching SVG path commands
    commands = re.findall(r'([MmLlHhVvZz][^MmLlHhVvZz]*)', path_data)

    contour = None
    current_pos = [0, 0]  # Initialize current position

    # Iterate over the commands and convert them to GLIF format
    for command in commands:
        cmd_type = command[0]
        points = list(map(float, re.findall(r'-?\d*\.?\d+', command)))
        
        if cmd_type.lower() == 'm':  # Move command
            if contour:  # If there's an existing contour, close it
                outline.append(contour)
            contour = ET.Element('contour')
            current_pos = [points[0], points[1]]
            ET.SubElement(contour, 'point', {'x': str(current_pos[0]), 'y': str(current_pos[1]), 'type': 'move'})
        elif cmd_type.lower() == 'l':  # Line command
            current_pos = [points[0], points[1]]
            ET.SubElement(contour, 'point', {'x': str(current_pos[0]), 'y': str(current_pos[1]), 'type': 'line'})
        elif cmd_type.lower() == 'h':  # Horizontal line
            current_pos[0] = points[0]
            ET.SubElement(contour, 'point', {'x': str(current_pos[0]), 'y': str(current_pos[1]), 'type': 'line'})
        elif cmd_type.lower() == 'v':  # Vertical line
            current_pos[1] = points[0]
            ET.SubElement(contour, 'point', {'x': str(current_pos[0]), 'y': str(current_pos[1]), 'type': 'line'})
        elif cmd_type.lower() == 'z':  # Close path
            if contour:
                outline.append(contour)
                contour = None  # Close the contour

    # Add any final contour if open
    if contour:
        outline.append(contour)

    # Convert the XML structure to a string with pretty formatting
    rough_string = ET.tostring(glif, encoding="unicode")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

# Function to save the .glif content to a file
def save_glif_to_file(glyph_name, glif_data, output_dir="output"):
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Construct the file path for the .glif file
    file_path = os.path.join(output_dir, f"{glyph_name}.glif")
    
    # Save the .glif data to a file
    with open(file_path, "w", encoding="utf-8") as glif_file:
        # Write the XML declaration and the glif data
        glif_file.write(glif_data)
    
    print(f"Saved {glyph_name}.glif to {file_path}")

# Example SVG glyph data
glyph_name = "tok.nanpa"
unicode_value = "U+F701D"  # Private Use Area Unicode
svg_path_data = "m 52.318359,684.62695 v -69.2539 h 34.626953 829.794918 34.62696 v 69.2539 H 916.74023 86.945312 Z m -0.33789,-299.98047 v -69.29296 h 34.646484 830.746097 34.64648 v 69.29296 H 917.37305 86.626953 Z M 610.50977,949.50586 V 910.01562 89.74023 50.25 h 78.98046 v 39.49023 820.27539 39.49024 z M 311,950 V 910.02278 89.97718 49.99995 h 78 V 89.97718 910.02278 950 Z"

# Convert to .glif format
glif_output = svg_to_glif(glyph_name, unicode_value, svg_path_data)

# Save the .glif formatted data to a file
save_glif_to_file(glyph_name, glif_output)

