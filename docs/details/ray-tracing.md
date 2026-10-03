# Ray Tracing

This document describes how MOCCA uses ray-tracing techiques to determine aperture obstruction. For the interested reader, the theory used in this document is based the following book: [3D Game Engine Design by David Eberly (2006)](https://doi.org/10.1201/b18212).

## Modelling the Telescope and Dome System with Rays and Capsules

### Rays

Rays are line segments,

$$\mathbf{P}+t\mathbf{D}$$

where $t\in[0,\infty)$; $\mathbf{P}$ is the origin of the ray and $\mathbf{D}$ its direction (could be a unit vector).

### Spheres

Spheres can (mathematically) be described by,

$$|\mathbf{X}-\mathbf{C}|^2=r^2$$

where $r$ is the radius, $\mathbf{X}$ some point on the sphere, and $\mathbf{C}$ the center of the sphere.

### Capsules

A capsule, with center $\mathbf{C}$, extent $e$ (height of the cylindrical part is $2e$), and radius $r$, can be described by,

$$
\begin{array}{ll}
    x^2+y^2=r^2 & \quad -e\le &z\le e \\
    x^2+y^2+(z-e)^2=r^2 & \quad &z>e \\
    x^2+y^2+(z+e)^2=r^2 & \quad &z<e
\end{array}
$$

## Ray-Sphere Intersection

The intersection between a line and sphere is given by substituting $\mathbf{X}=\mathbf{P}+t\mathbf{D}$ into the equation for a sphere and solving the quadratic equation in $t$. I.e. solving,

$$|\mathbf{P}+t\mathbf{D}-\mathbf{C}|^2-r^2=t^2+2t\mathbf{D}\cdot (\mathbf{P}-\mathbf{C})+|\mathbf{P}-\mathbf{C}|^2-r^2=t^2+2a_1t+a_0=0$$

We find that the line and sphere intersect for,

$$t=-a_1\pm\sqrt{a_1^2-a_0}$$

where $\Delta = a_1^2-a_0$. Such that when,

- $\Delta <0$: No intersection, due to complex roots.
- $\Delta =0$: 1 intersection point; ray is tangent to the sphere.
- $\Delta >0$: 2 intersections.

### Test Query

*Test queries: figuring out whether there is an intersection between, e.g., rays and solids.*

Thus, to test whether the line and sphere intersect, we simply check whether $\Delta <0$ or not. Or (initially) check the sign of $a_0$, when $a_0\le$ the point $\mathbf{P}$ is inside the sphere and thus necessarily intersects the sphere!

Note that if the ray was outside the sphere, it could be that the ray is moving away from the sphere, in that case there doesn't need to be an intersection for $t\ge 0$


### Find Query

*Find queries: finding the position of the intersection between, e.g., rays and solids.*

Thus, to find the intersection of the sphere and ray (or rather the more general case of a line), we compute $t$ using the formula given above and find the intersection(s) $\mathbf{X}_i=\mathbf{P}+t_i\mathbf{D}$ where $i=0,1$ or $i=0$ depending on the value of $\Delta$. 

Note that in the case of a ray inside a sphere (as is always the case inside the dome), only the largest value for $t\ge 0$ needs to be considered, as the smaller value will point in the opposite direction of the aperture. *See chapter 15.4.2 (Eberly 2006) for more information.*

## Ray-Capsule Intersection

First we consider the intersections with a line $\mathbf{P}+t\mathbf{D}$ and a capsule, with center $\mathbf{C}$, and unit-length direction $\mathbf{W}$, extent $e$, and radius $r$. We associate an orthogonal/right-handed coordinate system with the capsule. Any point $\mathbf{P}$ in this coordinate system can be written as:

$$\mathbf{P}=\mathbf{C}+x\mathbf{U}+y\mathbf{V}+z\mathbf{W}$$

Furthermore, we consider the capsule as described earlier.

### Test Query

When the distance between line and capsule is smaller than or equal to the radius of the capsule, $r$, the line intersects the capsule. And similarly for a ray.

### Find Query

Consider the point $\mathbf{P}$ in the reference frame of the capsule, i.e., such that it can be described by the set $(x_p,y_p,z_p)$. And similarly for the direction vector, with $(x_d,y_d,z_d)$. 

We consider two cases: 

1. When the line/ray is parallel to the capsule axis (i.e. the $z$-axis).
2. When the line/ray is **not** parallel to the capsule axis.

First, consider **case 1**, when $|z_d|=1$. The line intersects an infinite solid cylinder with $x^2+y^2\le r^2$, with intersection for $x_p^2+y_p^2\le r^2$. The intersection with the top cap is at $(x_p,y_p,z_\text{top})$, where $x_p^2+y_p^2+(z_\text{top}^2-e)^2=r^2$ with,

$$z_\text{top}=e+\sqrt{r^2-x_p^2-y_p^2}$$

noting that $z_\text{top}\le e$. And with the bottom hemisphere, $x_p^2+y_p^2+(z_\text{bottom}^2+e)^2=r^2$, at,

$$z_\text{bottom}=-z_\text{top}$$

where $z_\text{bottom}\le -e$.

The *find query* needs to return the $t$-value. Which, respectively, is given by $t_\text{top}=z_\text{top}-z_p$ and $t_\text{bottom}=z_\text{bottom}-z_p$ when $z_d=1$. For $z_d=-1$, e.g., $t_\text{top}=z_p-z_\text{top}$.


For **case 2**, consider the line in capsule coordinates: $(x_p,y_p,z_p)+t(x_d,y_d,z_d)$. It intersects with an infinite cylinder for $x^2+y^2=r^2$, for $x=x_p+tx_d$ and $y=y_p+tx_d$. With,

$$a_2 t^2+2a_1 t+a_0=(x_d^2+y_d^2)t^2=2(x_px_d+y_py_d)t+(x_p^2+y_p^2-r^2)=0$$

Note $a_2>0$ always, otherwise the line would be parallel to the capsule axis! We find the following roots,

$$t=\frac{-a_1\pm\sqrt{a_1^2-a_0a_2}}{a_2}$$

We define $\Delta\equiv a_1^2-a_0a_2$, 

- $\Delta <0$: No intersection.
- $\Delta \ge 0$: 1 or 2 intersections.

If $|z|=|z_p+tz_d|\le e$, then the line intersects the cylindrical part of the capsule. Otherwise, when $|z|\ge e$ it intersects the hemispheres.

For the bottom hemisphere: $x^2+y^2+(z+e)^2-r^2=0$, $z\le e$, substituting the parametric line into this equation we find:

$$t=-a_1\pm\sqrt{a_1^2-a_0}$$

where $a_0=x_p^2+y_p^2+(z_p+e)^2-r^2$ and $a_1=x_px_d+y_py_d+(z_p+e)z_d$.

For the top hemisphere: $x^2+y^2+(z+e)^2-r^2=0$, with $z\ge e$. We again have,

$$t=-a_1\pm\sqrt{a_1^2-a_0}$$

but now with $a_0=x_p^2+y_p^2+(z_p-e)^2-r^2$ and $a_1=x_px_d+y_py_d+(z_p-e)z_d$.
