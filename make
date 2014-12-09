#!/usr/bin/python

import os
import subprocess

UI_COMPILER = "pyuic4"


def makeGeneric(target_name, source_name, make_cmd):
    try:
        target_mtime = os.stat(target_name).st_mtime
    except OSError:
        target_mtime = 0
    source_mtime = os.stat(source_name).st_mtime
    if source_mtime > target_mtime:
        print "Making %s..." % target_name
        rc = subprocess.call(make_cmd)
        if rc == 0:
            print "OK"
            return True
        else:
            print "Error!"
    return False


def makeUi(ui_name):
    ui_path, ui_file = os.path.split(ui_name)
    ui_file_name = os.path.join(ui_path, "%s.ui" % ui_file)
    py_file_name = os.path.join(ui_path, "Ui_%s.py" % ui_file)
    make_cmd = [UI_COMPILER, ui_file_name, "-o", py_file_name]
    return makeGeneric(py_file_name, ui_file_name, make_cmd)


makeUi("mainWindow")
