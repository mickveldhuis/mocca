# Calculating Aperture Obstruction

To calculate the obstruction, we consider the light collected by the aperture as a cylindrical beam along the optical axis. We approximate this beam as a collection of rays originating from the (circular) aperture. 

To quantify the obstruction, we find the intersection of these rays with the dome, modeled as the upper half of a capsule. Depending on the location of this intersetion, we can infer whether a ray, or rather part of the aperture, is blocked by the dome, provided a particular orientation of the telescope and the rotation of the dome.

Each aperture is simulated as a circular collection of rays, with the following pointing direction as a function of the hour angle ($h$) and declination ($\delta$):

$$\mathbf{d}={}^0\text{H}_n\,\big[\,\text{Trans}(0, 1, 0)-\text{I}_{4\times4}\,\big]\, \mathbf{o}_0$$

These rays, originating from points $\mathbf{o}_i$ inside of the aperture, intersect the hemispherical dome at points $\mathbf{p}_i(t)=\mathbf{o}_i+t\mathbf{d}$; $t$ is determined using the equations from the document about [Ray Tracing](ray-tracing.md).

![Dome cross-section](../_static/dome_intersection_sketch.png)

The figure above this paragraph shows a schematic of the dome in the $xy$-plane, with the slit and its dimensions highlighted by the red dashed box. The slit has a width $w$ and depth $R+r$, where $R$ is the radius of the dome and $r$ the amount of the slit that extends past zenith.

Given the dimensions of the dome and the location of the slit, rays that meet the following condition are **not** obstructed by the dome when $-w/2<p_x(t)<w/2$ and $-r<p_y(t)<R$. To account for the rotation of the dome, we rotate the intersection points $\mathbf{p}_i(t)$ in the clock-wise direction, by the rotation of the dome or rather the dome azimuth $A_d$.
