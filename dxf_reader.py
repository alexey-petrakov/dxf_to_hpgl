#!/usr/bin/python
# -*- coding: utf-8 -*-

CODE_ENTITY_TYPE = 0
CODE_LAYER_NAME = 8
CODE_LINETYPE_NAME = 6
CODE_COLOR_NUMBER = 62
CODE_VISIBILITY = 60
CODE_THICKNESS = 39
CODE_X = 10
CODE_Y = 20
CODE_X2 = 11
CODE_Y2 = 21
CODE_RADIUS = 40



class DXFError(Exception): pass



class DXFEntity(object):
    def __init__(self, pairs):
        self._pairs = pairs

    def entityType(self):
        return self._pairs[CODE_ENTITY_TYPE]

    def thickness(self):
        return self._pairs[CODE_THICKNESS]

    def x(self):
        return float(self._pairs[CODE_X])

    def y(self):
        return float(self._pairs[CODE_Y])


    def __unicode__(self):
        return u"Entity({}, {})".format(self.x(), self.y())


class DXFLine(DXFEntity):
    def __init__(self, pairs):
        DXFEntity.__init__(self, pairs)
        assert self.entityType() == "LINE"

    def x2(self):
        return float(self._pairs[CODE_X2])

    def y2(self):
        return float(self._pairs[CODE_Y2])


    def __unicode__(self):
        return u"Line({}, {} - {}, {})".format(self.x(), self.y(), self.x2(), self.y2())


class DXFCircle(DXFEntity):
    def __init__(self, pairs):
        DXFEntity.__init__(self, pairs)
        assert self.entityType() == "CIRCLE"

    def radius(self):
        return float(self._pairs[CODE_RADIUS])


    def __unicode__(self):
        return u"Circle({}, {} - {})".format(self.x(), self.y(), self.radius())



ENTITY_CLASSES = {"LINE": DXFLine, "CIRCLE": DXFCircle}

def createEntity(pairs):
    try:
        e = ENTITY_CLASSES[pairs[CODE_ENTITY_TYPE]](pairs)
    except KeyError:
        print "Unknown entity code:", pairs[CODE_ENTITY_TYPE]
        e = DXFEntity(pairs)
    return e


class DXFReader(object):
    def __init__(self, file_name):
        self._file_name = file_name

    def iterPairs(self):
        with open(self._file_name, "r") as f:
            while True:
                try:
                    code = int(f.readline().strip())
                except ValueError:
                    break
                value = f.readline().strip()
                yield code, value


    def section(self, sec_name):
        cur_sec = None
        pairs_iter = self.iterPairs()
        for code, value in pairs_iter:
            if code == 0 and value == "SECTION":
                code, value = pairs_iter.next()
                assert code == 2
                if value == sec_name:
                    cur_sec = []
                    break
        else:
            raise DXFError("No such section \"{}\"!".format(sec_name))

        for code, value in pairs_iter:
            if code == 0 and value == "ENDSEC":
                break
            else:
                cur_sec.append((code, value))
        return cur_sec


    def entities(self):
        cur_entity = None
        ent = []
        for code, value in self.section("ENTITIES"):
            if code == 0:
                if cur_entity is not None:
                    ent.append(createEntity(cur_entity))
                cur_entity = {}
            cur_entity[code] = value
        ent.append(createEntity(cur_entity))
        return ent



if __name__ == "__main__":
    r = DXFReader(u"/home/lex/Development/dxf_to_hpgl/Data/1/Звезда.DXF")

    entities = r.entities()
    for e in entities:
        print e.entityType(), unicode(e)
