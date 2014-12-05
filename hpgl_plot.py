#!/usr/bin/python
# -*- coding: utf-8

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys

class BadParameter(Exception):
    def __init__(self, line_num, p_val):
        Exception.__init__(self)
        self._line_num = line_num
        self._param_value = p_val

    def __str__(self):
        return "Bad parameter value {} at line {}!". format(repr(self._param_value), self._line_num)


class HPGLReader(object):
    def __init__(self, file_name):
        self._file_name = file_name
        self._separator = "\n"


    def iterCommands(self):
        with open(self._file_name, "r") as f:
            hpgl_commands = f.read().split(self._separator)
            for i, line in enumerate(hpgl_commands):
                line = line.strip()
                cmd_code = line[:2].upper()
                params = line[2:].split(",")
                try:
                    params = [float(p) for p in params if len(p) > 0]
                except ValueError:
                    raise BadParameter(i, p)
                yield (cmd_code, params)



class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction("&Open", self.openFile)
        file_menu.addAction("&Quit", self.close)


    def openFile(self):
        file_name = QFileDialog.getOpenFileName(self, u"Open...", "", "HPGL (*.plt *.hpgl)")
        if not file_name.isEmpty():
            reader = HPGLReader(unicode(file_name))
            try:
                self.centralWidget().setReader(reader)
            except:
                self.statusBar().showMessage("Error! See console.", 5000)
                raise
            else:
                self.statusBar().showMessage("Ok!", 5000)



class HPGLWidget(QWidget):
    def __init__(self, parent=None):
        super(HPGLWidget, self).__init__(parent)
        self.setPath(None)
        self.setReader(None)
        self._old_move = None


    def resetView(self):
        self._zoom = 1
        self._dx = 0
        self._dy = 0


    def setReader(self, r):
        self._reader = r
        if self._reader is not None:
            self._hpgl_commands = list(self._reader.iterCommands())
        else:
            self._hpgl_commands = []
        self.resetView()
        self.update()


    def setPath(self, p):
        self._path = p


    def paintEvent(self, evt):
        p = QPainter(self)
        p.translate(self.width()/2 + self._dx, self.height()/2 + self._dy)
        p.scale(self._zoom, - self._zoom)
        p.drawEllipse(-3, -3, 6, 6)

        if self._reader is not None:
            cur_pos = QPointF(0, 0)
            i = 0
            for cmd, params in self._hpgl_commands:
                if cmd == "IN":
                    cur_pos = QPointF(0, 0)
                elif cmd == "PU" and len(params) > 1:
                    p2 = QPointF(params[0]/40, params[1]/40)
                    p.save()
                    p.setPen(Qt.DotLine)
                    p.drawLine(cur_pos, p2)
                    i += 1
                    p.restore()
                    cur_pos = p2
                elif cmd == "PD":
                    p2 = QPointF(params[0]/40, params[1]/40)
                    p.drawLine(cur_pos, p2)
                    cur_pos = p2
                #~ else:
                    #~ print "Ignoring command \"{}\"".format(cmd)
   

    def wheelEvent(self, evt):
        self._zoom += 0.05 * cmp(evt.delta(), 0)
        self._zoom = max(self._zoom, 0.01)
        self.update()


    def mousePressEvent(self, evt):
        if evt.button() == Qt.LeftButton:
            self._old_move = evt.pos()


    def mouseReleaseEvent(self, evt):
        self._old_move = None


    def mouseMoveEvent(self, evt):
        if self._old_move is not None:
            self._dx -= self._old_move.x() - evt.x()
            self._dy -= self._old_move.y() - evt.y()
            self._old_move = evt.pos()
            self.update()



app = QApplication(sys.argv)
hpgl_widget = HPGLWidget()

main_window = MainWindow()
main_window.setCentralWidget(hpgl_widget)
main_window.resize(1024, 768)
main_window.show()
sys.exit(app.exec_())
