# -*- coding: utf-8 -*-
"""템플릿이 진짜 xlsx(zip) 인지 판별. 사용: python probe.py C:\sonde\tpl\obs.xlsx"""
import sys, zipfile

head = open(sys.argv[1], "rb").read(4)
print "머리 4바이트:", repr(head)
print {"PK\x03\x04": "정상 xlsx (zip)",
       "\xd0\xcf\x11\xe0": "CFB - 구형 .xls 이거나 문서보안(DRM) 암호화"}.get(head, "알 수 없음")
if head == "PK\x03\x04":
    print zipfile.ZipFile(sys.argv[1]).namelist()[:6]
