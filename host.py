# -*- coding: utf-8 -*-
import sys, os, json, struct, msvcrt, traceback
import xlsx                                    # [추가] 같은 폴더의 xlsx.py

msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

TARGET = r"C:\pyhost\test.txt"

# [추가] xlsx: 템플릿을 열어 값만 채우고 새 파일로 저장. 템플릿은 손대지 않는다.
TEMPLATE = r"C:\pyhost\tpl.xlsx"
OUT      = r"C:\pyhost\out.xlsx"
SHEET    = 1                                   # 몇 번째 시트에 쓸지 (1부터)

def read_message():
    raw = sys.stdin.read(4)
    if len(raw) < 4:
        return None
    n = struct.unpack("=I", raw)[0]
    return json.loads(sys.stdin.read(n))

def send_message(obj):
    data = json.dumps(obj)
    sys.stdout.write(struct.pack("=I", len(data)))
    sys.stdout.write(data)
    sys.stdout.flush()

def read_file():
    if not os.path.exists(TARGET):
        return u""
    f = open(TARGET, "rb")
    raw = f.read()
    f.close()
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("cp949", "replace")

def write_file(text, mode):
    f = open(TARGET, mode)
    f.write(text.encode("utf-8"))
    f.close()

while True:
    msg = read_message()
    if msg is None:
        break
    try:
        cmd = msg.get("cmd")
        if cmd == "read":
            send_message({"ok": True, "text": read_file()})
        elif cmd == "write":
            write_file(msg["text"], "wb")
            send_message({"ok": True})
        elif cmd == "append":
            write_file(msg["text"], "ab")
            send_message({"ok": True})
        elif cmd == "xlsx":                    # [추가] {"cmd":"xlsx","cells":{"B3":12.3,...}}
            xlsx.fill(TEMPLATE, OUT, SHEET, msg["cells"])
            send_message({"ok": True, "path": OUT})
        else:
            send_message({"ok": False, "error": "unknown cmd"})
    except Exception:
        send_message({"ok": False, "error": traceback.format_exc()})
