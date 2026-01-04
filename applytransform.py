#!/usr/bin/env python3
#
# License: GPL2
# Copyright Mark "Klowner" Riedesel
# https://github.com/Klowner/inkscape-applytransforms
#
import math

import inkex

# For Inkscape 1.0+
from inkex.paths import CubicSuperPath, Path
from inkex.styles import Style
from inkex.transforms import Transform

NULL_TRANSFORM = Transform([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


class ApplyTransform(inkex.EffectExtension):
    def __init__(self):
        super(ApplyTransform, self).__init__()

    def effect(self):
        if self.svg.selected:
            for _, shape in self.svg.selected.items():
                self.recursiveFuseTransform(shape)
        else:
            self.recursiveFuseTransform(self.document.getroot())

    @staticmethod
    def objectToPath(node):
        if node.tag == inkex.addNS("g", "svg"):
            return node

        if node.tag == inkex.addNS("path", "svg") or node.tag == "path":
            for attName in node.attrib.keys():
                if ("sodipodi" in attName) or ("inkscape" in attName):
                    del node.attrib[attName]
            return node

        return node

    def scaleStyleAttrib(self, node, transf, attrib):
        if "style" in node.attrib:
            style = node.attrib.get("style")
            style = dict(Style.parse_str(style))
            update = False

            if attrib in style:
                try:
                    attrib_val = self.svg.unittouu(
                        style.get(attrib)
                    ) / self.svg.unittouu("1px")
                    attrib_val *= math.sqrt(
                        abs(transf.a * transf.d - transf.b * transf.c)
                    )
                    style[attrib] = str(attrib_val)
                    update = True
                except AttributeError as e:
                    pass

            if update:
                node.attrib["style"] = Style(style).to_str()

    def scaleMultiple(self, transf, string, kind=float):
        if string is None:
            return None
        return " ".join(
            [
                str(
                    kind(val)
                    * math.sqrt(abs(transf.a * transf.d - transf.b * transf.c))
                )
                for val in string.replace(",", " ")
                .replace("-", " -")
                .replace("e ", "e")
                .split()
                if val
            ]
        )

    def scaleStrokeWidth(self, node, transf):
        if "style" in node.attrib:
            self.scaleStyleAttrib(node, transf, "stroke-width")
        if "stroke-width" in node.attrib:
            try:
                stroke_width = self.svg.unittouu(
                    node.get("stroke-width")
                ) / self.svg.unittouu("1px")
                stroke_width *= math.sqrt(
                    abs(transf.a * transf.d - transf.b * transf.c)
                )
                node.set("stroke-width", str(stroke_width))
            except AttributeError as e:
                pass

    def transformRectangle(self, node, transf: Transform):
        x = float(node.get("x", "0"))
        y = float(node.get("y", "0"))
        width = float(node.get("width", "0"))
        height = float(node.get("height", "0"))
        rx = float(node.get("rx", "0"))
        ry = float(node.get("ry", "0"))

        # Extract translation, scaling and rotation
        a, b, c, d = transf.a, transf.b, transf.c, transf.d
        tx, ty = transf.e, transf.f
        sx = math.sqrt(a**2 + b**2)
        sy = math.sqrt(c**2 + d**2)
        angle = math.degrees(math.atan2(b, a))

        # Calculate the center of the rectangle
        cx = x + width / 2
        cy = y + height / 2

        # Apply the transformation to the center point
        new_cx, new_cy = transf.apply_to_point((cx, cy))
        new_x = new_cx - (width * sx) / 2
        new_y = new_cy - (height * sy) / 2

        # Update rectangle attributes
        node.set("x", str(new_x))
        node.set("y", str(new_y))
        node.set("width", str(width * sx))
        node.set("height", str(height * sy))

        # Apply scale to rx and ry if they exist
        if rx > 0:
            node.set("rx", str(rx * sx))
        if ry > 0:
            node.set("ry", str(ry * sy))

        # Add rotation if it exists
        if abs(angle) > 1e-6:
            tr = Transform(f"rotate({angle:.6f},{new_cx:.6f},{new_cy:.6f})")
            node.set("transform", tr)

    def transformText(self, node, transf: Transform):
        x, y = transf.apply_to_point((float(node.get("x", 0)), float(node.get("y", 0))))
        node.set("x", str(x))
        node.set("y", str(y))

        # Extract scaling and rotation
        a, b, c, d = transf.a, transf.b, transf.c, transf.d
        sx = math.sqrt(a**2 + b**2)
        sy = math.sqrt(c**2 + d**2)
        angle = math.degrees(math.atan2(b, a))

        if abs(angle) > 1e-6:
            tr = Transform(f"rotate({angle:.6f},{x:.6f},{y:.6f})")
            node.set("transform", tr)

        node.set("dx", self.scaleMultiple(transf, node.get("dx")))
        node.set("dy", self.scaleMultiple(transf, node.get("dy")))

    def transformTspan(self, node, transf: Transform):
        parent = node.getparent()
        x, y = transf.apply_to_point(
            (
                float(node.get("x", parent.get("x", 0))),
                float(node.get("y", parent.get("y", 0))),
            )
        )
        node.set("x", str(x))
        node.set("y", str(y))
        node.set("dx", self.scaleMultiple(transf, node.get("dx")))
        node.set("dy", self.scaleMultiple(transf, node.get("dy")))

    def isequal(self, a, b, tol=1e-6):
        return abs(a - b) <= tol

    def recursiveFuseTransform(self, node, transf=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]):
        transf = Transform(transf) @ Transform(node.get("transform", None))

        if "transform" in node.attrib:
            del node.attrib["transform"]

        node = ApplyTransform.objectToPath(node)

        if transf == NULL_TRANSFORM:
            # Don't do anything if there is effectively no transform applied
            # reduces alerts for unsupported nodes
            pass
        elif "d" in node.attrib:
            d = node.get("d")
            p = CubicSuperPath(d)
            p = Path(p).to_absolute().transform(transf, True)
            node.set("d", str(Path(CubicSuperPath(p).to_path())))

            self.scaleStrokeWidth(node, transf)

        elif node.tag in [
            inkex.addNS("polygon", "svg"),
            inkex.addNS("polyline", "svg"),
        ]:
            points = node.get("points")
            points = points.strip().split(" ")
            for k, p in enumerate(points):
                if "," in p:
                    p = p.split(",")
                    p = [float(p[0]), float(p[1])]
                    p = transf.apply_to_point(p)
                    p = [str(p[0]), str(p[1])]
                    p = ",".join(p)
                    points[k] = p
            points = " ".join(points)
            node.set("points", points)

            self.scaleStrokeWidth(node, transf)

        elif node.tag in [inkex.addNS("ellipse", "svg"), inkex.addNS("circle", "svg")]:
            if (
                self.isequal(transf.b, 0)
                and self.isequal(transf.c, 0)
                and self.isequal(transf.a, transf.d)
            ):
                # simple translation and uniform scaling
                if node.tag == inkex.addNS("ellipse", "svg"):
                    rx = float(node.get("rx")) * transf.a
                    ry = float(node.get("ry")) * transf.d
                    node.set("rx", str(rx))
                    node.set("ry", str(ry))
                else:
                    r = float(node.get("r")) * transf.a
                    node.set("r", str(r))

                cx = float(node.get("cx"))
                cy = float(node.get("cy"))
                new_cx, new_cy = transf.apply_to_point((cx, cy))
                node.set("cx", str(new_cx))
                node.set("cy", str(new_cy))
            else:
                if node.tag == inkex.addNS("ellipse", "svg"):
                    rx = float(node.get("rx"))
                    ry = float(node.get("ry"))
                else:
                    rx = float(node.get("r"))
                    ry = rx

                cx = float(node.get("cx"))
                cy = float(node.get("cy"))
                sqxy1 = (cx - rx, cy - ry)
                sqxy2 = (cx + rx, cy - ry)
                sqxy3 = (cx + rx, cy + ry)
                newxy1 = transf.apply_to_point(sqxy1)
                newxy2 = transf.apply_to_point(sqxy2)
                newxy3 = transf.apply_to_point(sqxy3)

                node.set("cx", (newxy1[0] + newxy3[0]) / 2)
                node.set("cy", (newxy1[1] + newxy3[1]) / 2)
                edgex = math.sqrt(
                    abs(newxy1[0] - newxy2[0]) ** 2 + abs(newxy1[1] - newxy2[1]) ** 2
                )
                edgey = math.sqrt(
                    abs(newxy2[0] - newxy3[0]) ** 2 + abs(newxy2[1] - newxy3[1]) ** 2
                )

                if not self.isequal(edgex, edgey) and (
                    node.tag == inkex.addNS("circle", "svg")
                    or not self.isequal(newxy2[0], newxy3[0])
                    or not self.isequal(newxy1[1], newxy2[1])
                ):
                    inkex.utils.errormsg(
                        f"Warning: Shape {node.tag} ({node.get('id')}) is approximate only, try Object to path first for better results"
                    )

                if node.tag == inkex.addNS("ellipse", "svg"):
                    node.set("rx", edgex / 2)
                    node.set("ry", edgey / 2)
                else:
                    node.set("r", edgex / 2)

        elif node.tag == inkex.addNS("rect", "svg"):
            self.transformRectangle(node, transf)
            self.scaleStrokeWidth(node, transf)

        elif node.tag == inkex.addNS("text", "svg"):
            self.transformText(node, transf)
            self.scaleStyleAttrib(node, transf, "font-size")

        elif node.tag == inkex.addNS("tspan", "svg"):
            self.transformTspan(node, transf)
            self.scaleStyleAttrib(node, transf, "font-size")

        elif node.tag in [
            inkex.addNS("image", "svg"),
            inkex.addNS("use", "svg"),
            inkex.addNS("clipPath", "svg"),
            inkex.addNS("linearGradient", "svg"),
        ]:
            node.attrib["transform"] = str(transf)
            inkex.utils.errormsg(
                f"Shape {node.tag} ({node.get('id')}) not supported. Transform will be applied to the element, but not its children. Try Object to path first"
            )

        else:
            # e.g. <g style="...">
            self.scaleStrokeWidth(node, transf)

        for child in node.getchildren():
            self.recursiveFuseTransform(child, transf)


if __name__ == "__main__":
    ApplyTransform().run()
