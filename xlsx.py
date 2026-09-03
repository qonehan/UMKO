# -*- coding: utf-8 -*-
"""xlsx 를 새로 만들거나, 템플릿의 지정한 칸에 값을 넣어 저장. 표준 라이브러리만."""
import re, zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
Q = "{%s}" % NS
ET.register_namespace("", NS)


def colnum(ref):
    """'AA7' -> 27. 칸 주소의 열을 숫자로."""
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(ch) - 64
    return n


def colname(n):
    """27 -> 'AA'. colnum 의 반대."""
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def rownum(ref):
    return int(re.search(r"\d+", ref).group())


def slot(parent, tag, ref, key):
    """parent(sheetData 또는 row) 에서 r=ref 인 자식을 찾거나 순서에 맞게 새로 만든다."""
    kids = list(parent)
    for i, e in enumerate(kids):
        if e.get("r") == ref:
            return e
        if key(e.get("r")) > key(ref):
            break
    else:
        i = len(kids)
    e = ET.Element(Q + tag, {"r": ref})
    parent.insert(i, e)
    return e


def setcell(root, ref, value):
    """ref 칸에 값을 넣는다. 서식(s 속성)은 그대로 보존."""
    row = slot(root.find(Q + "sheetData"), "row", str(rownum(ref)), int)
    c = slot(row, "c", ref, colnum)
    for old in list(c):
        c.remove(old)
    if isinstance(value, (int, long, float)):
        c.attrib.pop("t", None)
        ET.SubElement(c, Q + "v").text = str(value)
    else:
        c.set("t", "inlineStr")            # sharedStrings 를 건드리지 않으려고
        ET.SubElement(ET.SubElement(c, Q + "is"), Q + "t").text = value


def fill(template, out, sheet, cells):
    """cells: {'B7': u'맑음', 'C7': 12.3}. sheet 는 1부터."""
    name = "xl/worksheets/sheet%d.xml" % sheet
    zin = zipfile.ZipFile(template)
    root = ET.fromstring(zin.read(name))
    for ref in cells:
        setcell(root, ref, cells[ref])
    new = ET.tostring(root, "utf-8")
    zout = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)
    for it in zin.infolist():
        zout.writestr(it, new if it.filename == name else zin.read(it.filename))
    zout.close()
    zin.close()


# ---- 처음부터 만들기 -------------------------------------------------------
# 엑셀이 요구하는 최소 구성은 이 4개 + 시트 1장. styles/sharedStrings 는 없어도 열린다.
P = "http://schemas.openxmlformats.org/"
CT = "application/vnd.openxmlformats-officedocument.spreadsheetml"

PARTS = [
    ("[Content_Types].xml",
     '<Types xmlns="%spackage/2006/content-types">'
     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package'
     '.relationships+xml"/>'
     '<Override PartName="/xl/workbook.xml" ContentType="%s.sheet.main+xml"/>'
     '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="%s.worksheet+xml"/>'
     '</Types>' % (P, CT, CT)),
    ("_rels/.rels",
     '<Relationships xmlns="%spackage/2006/relationships"><Relationship Id="rId1"'
     ' Type="%sofficeDocument/2006/relationships/officeDocument"'
     ' Target="xl/workbook.xml"/></Relationships>' % (P, P)),
    ("xl/_rels/workbook.xml.rels",
     '<Relationships xmlns="%spackage/2006/relationships"><Relationship Id="rId1"'
     ' Type="%sofficeDocument/2006/relationships/worksheet"'
     ' Target="worksheets/sheet1.xml"/></Relationships>' % (P, P)),
]

BOOK = ('<workbook xmlns="%s" xmlns:r="%sofficeDocument/2006/relationships">'
        '<sheets><sheet name=%%s sheetId="1" r:id="rId1"/></sheets></workbook>' % (NS, P))


def create(out, cells, title=u"Sheet1"):
    """템플릿 없이 새 xlsx 를 만든다.
    cells: {'B2': 12.3} 또는 [[u'이름', u'값'], [u'기온', 12.5]] (A1 부터 채움)."""
    if isinstance(cells, list):
        cells = dict((colname(j + 1) + str(i + 1), v)
                     for i, row in enumerate(cells)
                     for j, v in enumerate(row) if v is not None and v != "")
    root = ET.fromstring('<worksheet xmlns="%s"><sheetData/></worksheet>' % NS)
    for ref in cells:
        setcell(root, ref, cells[ref])
    z = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)
    for name, xml in PARTS:
        z.writestr(name, xml)
    z.writestr("xl/workbook.xml", (BOOK % quoteattr(title)).encode("utf-8"))
    z.writestr("xl/worksheets/sheet1.xml", ET.tostring(root, "utf-8"))
    z.close()


if __name__ == "__main__":                 # 자가 점검
    assert (colnum("A1"), colnum("Z9"), colnum("AA1")) == (1, 26, 27)
    assert (colname(1), colname(26), colname(27)) == ("A", "Z", "AA")
    r = ET.fromstring('<worksheet xmlns="%s"><sheetData><row r="2">'
                      '<c r="B2" s="3" t="s"><v>0</v></c></row></sheetData></worksheet>' % NS)
    setcell(r, "B2", u"값")                # 기존 칸 덮어쓰기
    setcell(r, "A2", 12.5)                 # 같은 행 앞에 삽입
    setcell(r, "A1", u"위")                # 새 행을 위에 삽입
    x = ET.tostring(r)
    assert x.index('r="A1"') < x.index('r="A2"') < x.index('r="B2"'), x
    assert 's="3"' in x and "inlineStr" in x, x

    import os, tempfile                    # 새로 만들기 점검
    p = os.path.join(tempfile.gettempdir(), "xlsx_new_test.xlsx")
    create(p, [[u"이름", u"값"], [u"기온", 12.5]], u"관측")
    z = zipfile.ZipFile(p)
    assert z.testzip() is None
    assert len(z.namelist()) == 5, z.namelist()
    s = z.read("xl/worksheets/sheet1.xml")
    assert 'r="A1"' in s and 'r="B2"' in s and ">12.5<" in s, s
    assert "관측" in z.read("xl/workbook.xml")
    z.close()
    print "ok", p
