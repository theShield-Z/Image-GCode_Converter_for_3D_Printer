from warnings import warn
from svgpathtools import svg2paths2, parse_path, path as path_pkg
import cmath
import math
import numpy as np


# Parameters to Adjust ##############################################

input_file = "svg_test_file.svg"            # Example file name
output_file = "svg2gcode_output.gcode"

CURVE_RESOLUTION = 50       # Points per curve
z_offset = .1               # Height of marker/head above the bed/paper
x = 0                       # x-position of top-left corner
y = 0                       # y-position of top-left corner


# Algorithms ########################################################

def append_line(file, start, end):
    sx = width - start.real + x
    sy = start.imag + y
    ex = width - end.real + x
    ey = end.imag + y

    file.writelines(f"; Line\n"
                    f"G1 X{sx} Y{sy} F1500\n"
                    f"G1 Z{z_offset} F600\n"
                    f"G1 X{ex} Y{ey} F1500\n\n")


def append_curve(file, curve: path_pkg.Arc | path_pkg.CubicBezier | path_pkg.QuadraticBezier):
    # distance = math.ceil(cmath.sqrt((curve.end - curve.start)**2).real * 10)  # alternative to const CURVE_RESOLUTION

    movements = []

    points = [curve.point(t) for t in np.linspace(0, 1, CURVE_RESOLUTION)]

    movements.append(f"; {str(type(curve))[26:-2]}\n"
                     f"G1 X{width - points[0].real + x} Y{points[0].imag + y} F1500\n"
                     f"G1 Z{z_offset} F600")

    for point in points[1:]:
        movements.append(f"G1 X{width - point.real + x} Y{point.imag + y}")

    movements.append(f"\n")

    file.writelines('\n'.join(movements))


# Most common 3D printers only support straight lines, handled in append_curve().
# def append_arc(file, arc: path_pkg.Arc):
#
#     movements = []
#
#     points = [arc.point(t) for t in np.linspace(0, 1, CURVE_RESOLUTION)]
#     movements.append(f"G1 X{width - points[0].real} Y{points[0].imag} F1500\n"
#                      f"G1 Z{.1} F600")
#     for point in points[1:]:
#         movements.append(f"G1 X{width - point.real} Y{point.imag}")
#
#     movements.append(f"G1 Z{2} F600\n")
#
#     file.writelines('\n'.join(movements))
#
#
# def append_cubic(file, curve: path_pkg.CubicBezier):
#
#     movements = []
#
#     points = [curve.point(t) for t in np.linspace(0, 1, CURVE_RESOLUTION)]
#     movements.append(f"G1 X{width - points[0].real} Y{points[0].imag} F1500\n"
#                      f"G1 Z{.1} F600")
#     for point in points[1:]:
#         movements.append(f"G1 X{width - point.real} Y{point.imag}")
#
#     movements.append(f"G1 Z{2} F600\n")
#
#     file.writelines('\n'.join(movements))
#
#
# def append_quadratic(file, curve: path_pkg.QuadraticBezier):
#
#     movements = []
#
#     points = [curve.point(t) for t in np.linspace(0, 1, CURVE_RESOLUTION)]
#     movements.append(f"G1 X{width - points[0].real} Y{points[0].imag} F1500\n"
#                      f"G1 Z{.1} F600")
#     for point in points[1:]:
#         movements.append(f"G1 X{width - point.real} Y{point.imag}")
#
#     movements.append(f"G1 Z{2} F600\n")
#
#     file.writelines('\n'.join(movements))


paths, attrs, svg_attrs = svg2paths2(input_file)

width = float(svg_attrs['width'][:-2])
height = float(svg_attrs['height'][:-2])

with open(output_file, 'w') as output_file:

    # Header
    output_file.writelines("G28 ; Home all axes\n"
                           "G90 ; Use absolute positioning\n"
                           "G21 ; Set units to millimeters\n"
                           "\n\n"
                           "; Move to starting position\n"
                           "G1 Z5 F600       ; Lift nozzle 5mm\n"
                           f"G1 X{x} Y{y} F3000 ; Move to front-left corner\n\n")

    # Trace Outline
    output_file.writelines(f"; Trace outline\n"
                           f"G1 X{x} Y{y} F1000\n"
                           f"G1 X{x} Y{height + y} F1000\n"
                           f"G1 X{width + x} Y{height + y} F1000\n"
                           f"G1 X{width + x} Y{y} F1000\n"
                           f"G1 X{x} Y{y} F1000\n\n")

    for path in paths:

        output_file.writelines(f"; Start of Path\n\n")

        parsed_path = parse_path(path.d())
        for el in parsed_path:

            if isinstance(el, path_pkg.Line):
                append_line(output_file, el.start, el.end)

            elif isinstance(el, path_pkg.CubicBezier):
                append_curve(output_file, el)

            elif isinstance(el, path_pkg.Arc):
                append_curve(output_file, el)

            elif isinstance(el, path_pkg.QuadraticBezier):
                append_curve(output_file, el)

            else:
                warn(f"Paths of type {type(el)} are not currently supported by this program. "
                     "Any paths of this type will be skipped.")

        output_file.writelines(f"G1 Z{2} F600\n\n\n")

