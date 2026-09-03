import subprocess, struct, json, os

BAT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pyhost.bat")

def call(msg):
    p = subprocess.Popen(BAT, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,   # [수정] 파이썬 오류는 stdout 이 아니라 stderr 로 나온다
                         shell=True)
    data = json.dumps(msg)
    p.stdin.write(struct.pack("=I", len(data)) + data)
    p.stdin.flush()
    raw = p.stdout.read(4)
    if len(raw) < 4:
        p.stdin.close()               # [수정] 먼저 닫아야 아래 read() 가 EOF 로 끝난다 (안 닫으면 무한 대기)
        print "NO RESPONSE"
        print p.stdout.read()
        print p.stderr.read()         # [수정] 트레이스백은 여기 찍힌다
        p.wait()                      # [수정] kill 은 cmd.exe 만 죽이고 python.exe 를 남긴다
        return None
    n = struct.unpack("=I", raw)[0]
    res = json.loads(p.stdout.read(n))
    p.stdin.close()                   # [수정] stdin 이 닫히면 호스트가 스스로 끝난다
    p.wait()                          # [수정] kill 대신
    return res

print call({"cmd": "write", "text": u"hello from test"})
r = call({"cmd": "read"})
print r["ok"], repr(r["text"])
