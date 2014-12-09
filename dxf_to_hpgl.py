#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from Ui_mainWindow import Ui_MainWindow

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



class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)

        self.convert_pushButton.clicked.connect(self.convert)
        self.source_browse_toolButton.clicked.connect(self.browseSource)
        self.target_browse_toolButton.clicked.connect(self.browseTarget)
        self.source_lineEdit.editingFinished.connect(self.checkConvert)
        self.target_lineEdit.editingFinished.connect(self.checkConvert)


    def checkConvert(self):
        enabled = True
        if self.source_lineEdit.text().isEmpty() or self.target_lineEdit.text().isEmpty():
            enabled = False
        self.convert_pushButton.setEnabled(enabled)


    def browseSource(self):
        file_name = QFileDialog.getOpenFileName(self, "Select DXF", "", "DXF files(*.dxf)")
        if not file_name.isEmpty():
            file_name = unicode(file_name)
            self.source_lineEdit.setText(file_name)
            if self.target_lineEdit.text().isEmpty():
                dxf_root, dxf_ext = os.path.splitext(file_name)
                self.target_lineEdit.setText(dxf_root + ".plt")
        self.checkConvert()


    def browseTarget(self):
        file_name = QFileDialog.getSaveFileName(self, "Save to", "", "HPGL files(*.plt *.hpgl)")
        if not file_name.isEmpty():
            file_name = unicode(file_name)
            plt_root, plt_ext = os.path.splitext(file_name)
            if len(plt_ext) == 0:
                file_name = plt_root + ".plt"
            self.target_lineEdit.setText(file_name)
        self.checkConvert()



    def convert(self):
        dxf_name = unicode(self.source_lineEdit.text())
        hpgl_name = unicode(self.target_lineEdit.text())

        tol = self.tol_SpinBox.value()

        reader = dxf_reader.DXFReader(dxf_name)
        writer = HPGLWriter(hpgl_name)
        writer.init()

        entities = list(reader.section("ENTITIES"))

        while entities:
            e, entities = getEntity(entities, writer)
            #~ print ".",
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
                if tol < r:
                    N = int(round(math.pi / math.acos(1.0 - tol/r)))
                else:
                    N = 3
                da = 2*math.pi / N
                writer.move(e.x(), e.y()+r)
                for i in xrange(1, N+1):
                    x = r * math.sin(i*da) + e.x()
                    y = r * math.cos(i*da) + e.y()
                    writer.lineTo(x, y)
        writer.penUp()
        del writer
        self.statusBar().showMessage(u"Преобразование завершено.", 5000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
