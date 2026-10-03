# Configuring MOCCA

As mentioned in [General usage](usage.md), MOCCA uses an INI file to describe the properties of the telescope, dome, and observatory to determine, for example, determine the orientation of the telescope with respect to the dome.

The confguration (INI) file, contains a number of sections:

- `[mount]`: describes the dimensions of the equatorial telescope mount, from the base of the observatory to the centroid of the main aperture.
- `[telescope]`: describes the size of the main aperture and the secondary mirror.
- `[guider]`: describes the aperture size of the guider and the secondary mirror, along with the offset with respect to the main aperture.
- `[finder]`: describes the diameter of the finder scope, along with the offset with respect to the guider.
- `[dome]`: a hemispherical dome can be described by its diameter, the width of the opening (slit), and the height of the cylindrical walls of the observatory (dubbed the extent).
- `[observatory]`: contains the location of the observatory on the surface of the Earth, used to calculate the orientation of the equatorial mount.

The default `mocca.ini`, based on the properties of the Blaauw Observatory, has the following structure:

```
[mount]
; Lengths of the axes in meters
length_1 = 0.814
length_2 = 1.098
length_3 = 0.439

[telescope]
; Refer to the OA manual
diameter = 0.4
sec_diameter = 0.175

[guider]
; see: https://www.orionoptics.co.uk/OMC/omc140maksutovca.html
diameter = 0.15
sec_diameter = 0.044
offset = 0.356
angle = 45

[finder]
; see: https://www.orionoptics.co.uk/OMC/omc140maksutovca.html
diameter = 0.05
offset = 0.2
angle = 45

[dome]
; Measured properties of the dome
slit_width = 1.84
extent = 1.66
diameter = 6.25

[observatory]
; Long/lat in degrees
longitude = 6.54
latitude = 53.24
```
