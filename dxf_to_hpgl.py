#!/usr/bin/python

import argparse
import dxf_reader
import os, sys
import math


def dist(p1, p2):
    return ((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)**0.5


class HPGLWriter(object):
    def __init__(self, file_name):
        self._file_name = file_name
        self._f = open(file_name, "w")
        self._cur_pos = None


    def cmd(self, cmd_name, cmd_params=[]):
        cmd_params = [unicode(p) for p in cmd_params]
        cmd_str = "{}{}\n".format(cmd_name, ",".join(cmd_params))
        self._f.write(cmd_str)


    def init(self):
        self.cmd("IN")
        self.cmd("SP", (1,))
        self._cur_pos = (0, 0)


    def penUp(self):
        self.cmd("PU")


    def move(self, x, y):
        x = int(round(x * 40))
        y = int(round(y * 40))
        if dist(self._cur_pos, (x, y)) > 0:
            self.cmd("PU", (x, y))
            self._cur_pos = (x, y)


    def lineTo(self, x, y):
        x = int(round(x * 40))
        y = int(round(y * 40))
        if dist(self._cur_pos, (x, y)) > 0:
            self.cmd("PD", (x, y))
            self._cur_pos = (x, y)


    def circle(self, r):
        r = int(round(r * 40))
        self.cmd("CI", (r,))


    def curPos(self):
        return self._cur_pos


    def __del__(self):
        self._f.close()



def getEntity(ent_list, w):
    d_min = None
    i_min = None
    dist_map = []
    cur_pos = (w.curPos()[0] / 40.0, w.curPos()[1] / 40.0)
    for i, e in enumerate(ent_list):
        key_points = []
        if isinstance(e, dxf_reader.DXFLine):
            key_points.append((e.x(), e.y()))
            key_points.append((e.x2(), e.y2()))
        elif isinstance(e, dxf_reader.DXFCircle):
            key_points.append((e.x(), e.y()-e.radius()))
        else:
            key_points.append((e.x(), e.y()))
        for p in key_points:
            dist_map.append((dist(p, cur_pos), i))
    d_min, i_min = min(dist_map)
    return ent_list[i_min], ent_list[:i_min]+ent_list[i_min+1:]


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="DXF to HPGL converter.")
    arg_parser.add_argument("dxf_name")
    arg_parser.add_argument("hpgl_name", default=None, nargs="?")
    arg_parser.add_argument("--tol", default=0.1, type=float)
    args = arg_parser.parse_args()

    dxf_name = args.dxf_name
    hpgl_name = args.hpgl_name

    if hpgl_name is not None:
        hpgl_root, hpgl_ext = os.path.splitext(hpgl_name)
        if len(hpgl_ext.strip()) == 0:
            print "Adding \".plt\" extension to {}.".format(hpgl_root)
            hpgl_name = "{}{}".format(hpgl_root, ".plt")
    else:
        dxf_root, dxf_ext = os.path.splitext(dxf_name)
        hpgl_name = "{}{}".format(dxf_root, ".plt")

    print "Converting \"{}\" to \"{}\".".format(dxf_name, hpgl_name)

    reader = dxf_reader.DXFReader(dxf_name)
    writer = HPGLWriter(hpgl_name)
    writer.init()

    entities = list(reader.section("ENTITIES"))

    while entities:
        e, entities = getEntity(entities, writer)
        print ".",
        if isinstance(e, dxf_reader.DXFLine):
            p1 = (e.x(), e.y())
            p2 = (e.x2(), e.y2())
            cur_pos = (writer.curPos()[0]/40, writer.curPos()[1]/40)
            if dist(cur_pos, p1) > dist(cur_pos, p2):
                p1, p2 = p2, p1
            writer.move(*p1)
            writer.lineTo(*p2)
        elif isinstance(e, dxf_reader.DXFCircle):
            r = float(e.radius())
            if args.tol < r:
                N = int(round(math.pi / math.acos(1.0 - args.tol/r)))
            else:
                N = 3
            da = 2*math.pi / N
            writer.move(e.x(), e.y()+r)
            for i in xrange(1, N+1):
                x = r * math.sin(i*da) + e.x()
                y = r * math.cos(i*da) + e.y()
                writer.lineTo(x, y)

    writer.penUp()

    print ""
    print "Done!"
