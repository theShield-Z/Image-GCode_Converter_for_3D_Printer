# Image-GCode_Converter_for_3D_Printer
Convert Images to GCode to print them using a 3D printer. Supports both raster and vector (svg) images.

The raster converter works with just a simple function call to `convert_image()`. This returns a string that contains the converted GCode, which you can then pass into `to_file()` to save to a .gcode file. See [raster_converter.py](theShield-Z/Image-GCode_Converter_for_3D_Printer/raster_converter.py) for parameters, and see the main function at the bottom for an example use.

The svg converter is not currently packaged into a single function. Adjust the parameters & file names at the top of [svg_converter.py](theShield-Z/Image-GCode_Converter_for_3D_Printer/svg_converter.py) as needed, then simply run the file.

Some examples are contained within the [Examples](theShield-Z/Image-GCode_Converter_for_3D_Printer/Examples) subfolder, though I still need to add more.

To Do:
- Add example images of final print
- Update svg converter to match with raster converter
