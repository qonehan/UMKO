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

# [추가] 호스트->확장 메시지는 1MB 제한. JSON 에서 한글 1자 = "\uXXXX" 6바이트라
# 10만 자면 최대 600KB. 안전하게 이 단위로 잘라 보낸다.
CHUNK = 100000

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
        if cmd == "read":                      # [수정] 청크 로딩
            text = read_file()                 # off 부터 CHUNK 글자만 보낸다
            off = msg.get("off", 0)
            part = text[off:off + CHUNK]
            send_message({"ok": True, "text": part, "off": off + len(part),
                          "more": off + len(part) < len(text)})
        elif cmd == "write":
            write_file(msg["text"], "wb")
            send_message({"ok": True})
        elif cmd == "append":
            write_file(msg["text"], "ab")
            send_message({"ok": True})
        elif cmd == "xlsx":                    # [추가] {"cmd":"xlsx","cells":{"B3":12.3,...}}
            xlsx.fill(TEMPLATE, OUT, SHEET, msg["cells"])
            send_message({"ok": True, "path": OUT})
        elif cmd == "xlsx_new":                # [추가] 템플릿 없이 새로 만들기
            # {"cmd":"xlsx_new","cells":{"B3":12.3} 또는 [[행],[행]],"out":...,"title":...}
            path = msg.get("out") or OUT
            xlsx.create(path, msg["cells"], msg.get("title", u"Sheet1"))
            send_message({"ok": True, "path": path})
        else:
            send_message({"ok": False, "error": "unknown cmd"})
    except Exception:
        send_message({"ok": False, "error": traceback.format_exc()})
