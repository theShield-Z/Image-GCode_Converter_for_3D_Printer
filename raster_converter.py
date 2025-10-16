"""Convert images into circloO objects."""

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


def convert_image(img_path: str,
                  x: int | float = 0,
                  y: int | float = 0,
                  mode: str = "reduced",
                  downsample_factor: int | float = 1,
                  z_offset: int | float = .1,
                  scale: int | float = 1,
                  threshold: int | float = .5,
                  channel_weights: tuple[int, int, int] = (1, 1, 1),
                  show_img: bool = True
                  ) -> str:
    """
    Convert an image to gcode for printing.
    :param img_path:            Path of image.
    :param x:                   Initial x position. Default is 0.
    :param y:                   Initial y position. Default is 0.
    :param mode:                Printing mode. Default is "reduced". Refer to documentation for details on each mode.
    :param downsample_factor:   Factor by which to reduce image size. Default is 1, no change.
    :param z_offset:            Drawing height. Default is .1
    :param scale:               Size of each pixel in mm. Default is 1 mm.
    :param threshold:           Threshold to turn a cell on after averaging channels. Default is .5
    :param channel_weights:     Weighting of each channel. Default is (1, 1, 1), equal weighting.
    :param show_img:            Show the final image that will be printed. Default is True.
    :return:                    String of gcode.
    """

    # Open Image.
    img = Image.open(f"{img_path}")

    # Convert to numpy array.
    data = np.array(img).astype(np.float32) / 255  # normalize values as floats b/w 0 & 1
    if len(data.shape) == 2:  # add new channel if B&W image to preserve algorithms
        data = data[:, :, np.newaxis]

    # Process Image.
    data_smaller = downsample(data, downsample_factor)
    data_adjusted = floyd_steinberg(data_smaller)
    data_avg = average_array(data_adjusted, channel_weights, threshold)

    if show_img:
        plt.imshow(data_avg, cmap='Grays')
        plt.show()

    match mode:
        case "normal":
            gcode = to_gcode(data_avg, x, y, z_offset, scale)
        case "reduced":
            data_reduced = reduce_by_row(data_avg)
            gcode = to_gcode_reduced(data_reduced, x, y, z_offset, scale)
        case _:
            # Default to normal
            gcode = to_gcode(data_avg, x, y, z_offset, scale)

    return gcode


# IMAGE PROCESSING #####################################################################################################

def floyd_steinberg(image: np.array) -> np.array:
    """Floyd-Steinberg dithering algorithm, adjusted to give more contrast.
    https://research.cs.wisc.edu/graphics/Courses/559-s2004/docs/floyd-steinberg.pdf"""
    lx, ly, lc = image.shape
    for j in range(ly):
        for i in range(lx):
            for c in range(lc):
                rounded = round(image[i, j, c])
                err = image[i, j, c] - rounded
                image[i, j, c] = rounded
                if i < lx - 1:
                    image[i + 1, j, c] += (7 / 24) * err  # Original factor from paper: 7/16
                if j < ly - 1:
                    image[i, j + 1, c] += (5 / 24) * err  # Original: 5/16
                    if i > 0:
                        image[i - 1, j + 1, c] += (1 / 24) * err  # Original: 1/16
                    if i < lx - 1:
                        image[i + 1, j + 1, c] += (3 / 24) * err  # Original: 3/16
    return image


def downsample(image: np.array, factor: int) -> np.array:
    """Reduce image size by factor."""
    return image.copy()[::factor, ::factor, :]


def average_array(arr: np.array, weights=(1, 1, 1), threshold=.5) -> np.array:
    """
    Reduce three-channel (RGB) binary array into a single channel using a weighted average.
    :param arr:         Three-channel binary array.
    :param weights:     Weighting of each channel. Default is (1, 1, 1), equal weighting.
    :param threshold:   Threshold to turn a cell on after averaging. Default is .5
    :return:            Single-channel binary array.
    """
    avg = np.dot(arr[:, :, :3], weights) / sum(weights)
    binary_image = (avg <= threshold).astype(np.float32)
    return binary_image


def reduce_by_row(arr: np.array) -> np.array:
    """
    Reduce binary array for faster printing. Reduced form contains the number of consecutive 1's in the original array.
    :param arr: Binary array to be reduced.
    :return:    Reduced Binary Array.
    """
    new_arr = arr.copy()
    for i in range(new_arr.shape[0]):
        point = None

        for j in range(new_arr.shape[1]):
            cur = new_arr[i, j]

            if cur == 1:
                if point is None:
                    point = (i, j)
                else:
                    new_arr[point] += 1
                    new_arr[i, j] = 0
            else:
                point = None
    return new_arr


# GCODE ################################################################################################################

def to_gcode(arr: np.array, x=0, y=0, z_offset=.1, scale=1) -> str:
    """
    Convert binary array into gcode.
    :param arr:         Binary array to be reduced.
    :param x:           Initial x position. Default is 0.
    :param y:           Initial y position. Default is 0.
    :param z_offset:    Drawing height. Default is .1
    :param scale:       Size of each pixel in mm. Default is 1 mm.
    :return:            String of gcode.
    """
    header = ("G28 ; Home all axes\n"
              "G90 ; Use absolute positioning\n"
              "G21 ; Set units to millimeters\n"
              "\n"
              "; Move to starting position\n"
              "G1 Z5 F600       ; Lift nozzle 5mm\n"
              f"G1 X{x} Y{y} F3000 ; Move to front-left corner\n")

    outline = (f"; Trace outline\n"
               f"G1 X{x} Y{y} F1000\n"
               f"G1 X{x + len(arr) * scale} Y{y} F1000\n"
               f"G1 X{x + len(arr) * scale} Y{y + len(arr[0]) * scale} F1000\n"
               f"G1 X{x} Y{y + len(arr[0]) * scale} F1000\n"
               f"G1 X{x} Y{y} F1000\n")
               # f"M25\n\n")

    lines = [header, outline, "; Start printing\n"]

    for i in range(arr.shape[0]):

        lines.append(f"; Row {i}")
        for j in range(arr.shape[1]):

            if arr[i, j] == 1:
                lines.append(f"G1 X{i * scale + x} Y{j * scale + y} F1500\n"
                             f"G1 Z{z_offset} F600\n"
                             f"G1 Z2 F600\n")

    lines.append("M84 ; Disable motors")

    return '\n'.join(lines)


def to_gcode_reduced(arr: np.array, x=0, y=0, z_offset=.1, scale=1) -> str:
    """
    Convert reduced binary array (obtained from reduce_by_row() function) into gcode.
    :param arr:         Reduced Binary Array.
    :param x:           Initial x position. Default is 0.
    :param y:           Initial y position. Default is 0.
    :param z_offset:    Drawing height. Default is .1
    :param scale:       Size of each pixel in mm. Default is 1 mm.
    :return:            String of gcode.
    """
    header = ("G28 ; Home all axes\n"
              "G90 ; Use absolute positioning\n"
              "G21 ; Set units to millimeters\n"
              "\n"
              "; Move to starting position\n"
              "G1 Z5 F600       ; Lift nozzle 5mm\n"
              f"G1 X{x} Y{y} F3000 ; Move to front-left corner\n")

    outline = (f"; Trace outline\n"
               f"G1 X{x} Y{y} F1000\n"
               f"G1 X{x + len(arr) * scale} Y{y} F1000\n"
               f"G1 X{x + len(arr) * scale} Y{y + len(arr[0]) * scale} F1000\n"
               f"G1 X{x} Y{y + len(arr[0]) * scale} F1000\n"
               f"G1 X{x} Y{y} F1000\n")
    # f"M25\n\n")

    lines = [header, outline, "; Start printing\n"]

    for i in range(arr.shape[0]):

        lines.append(f"; Row {i}")
        for j in range(arr.shape[1]):
            factor = arr[i, j]

            if factor > 0:
                lines.append(f"G1 X{i * scale + x} Y{j * scale + y} F1500\n"
                             f"G1 Z{z_offset} F600\n"
                             f"G1 X{i * scale + x} Y{(j + factor - 1) * scale + y} F1500\n"
                             f"G1 Z2 F600\n")

    lines.append("M84 ; Disable motors")

    return '\n'.join(lines)


def to_file(text: str, path: str) -> None:
    """
    Converts the input text into a text file at the specified path.
    :param text: String to convert.
    :param path: Destination path.
    :return: None
    """
    with open(path, 'w') as f:
        f.writelines(text)


# EXAMPLE ##############################################################################################################

def main():
    text = convert_image("mona_lisa.webp", 50, 100, "reduced", 1, .1, 1)
    to_file(text, "print_mona_lisa.gcode")


if __name__ == "__main__":
    main()
