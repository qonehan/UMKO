# 고층기상 자동화 시스템 설계 메모

> 고층 센서 TXT → 파싱 → 전문(UMKO/UFKO) + xlsx + hwpx → 인트라넷 자동 업로드

## 1. 제약

- Python **2.7.2**, **표준 라이브러리만** (외부 패키지 반입 불가)
- 코드를 **인쇄 후 손으로 타이핑**해야 함 → 줄 수가 곧 비용. 짧고 읽기 쉽게
- 인트라넷 PC, Windows, Chrome **MV2**, 확장 개발자 모드 로드 가능
- 유지보수 우선. 고정값 금지, 설정은 전부 설정 탭에서 조정

## 2. 파이프라인

```
[브라우저 관측 시작 버튼]
        ↓ native messaging
   host.py (진입점)
        ├ parse.py  TXT → 관측 데이터
        ├ code.py   TTAA/TTBB/PPBB/TTCC/TTDD/PPDD
        └ fill.py   xlsx/hwpx 템플릿 삽입
        ↓ (auto | review)
   확장 → 인트라넷 사이트 업로드
```

## 3. 확정 사항

| 항목 | 결정 |
|---|---|
| 트리거 | 브라우저 버튼 → 확장이 호스트를 띄움. 별도 감시 데몬 없음 |
| 프로세스 | 브라우저를 **계속 켜둠** → 상태파일·워커·재개 로직 불필요 |
| 전문 | UMKO = `TTAA TTBB PPBB`, UFKO = `TTCC TTDD PPDD` |
| 기준 | 공본지침서(고층기상관측법) |
| 특이점 | 센서가 제공. **우리가 계산하지 않음** |
| 발신 | `auto` / `review` 모드 선택 (config.ini) |
| 설정 | `config.ini` 가 유일한 진실원천. 팝업 폼은 ini에서 자동 생성 |
| xlsx | 특정 시트에 파싱 데이터 삽입. 템플릿 준비됨 |
| xlsx 생성 | 템플릿이 없거나 서식이 필요 없을 땐 `xlsx.create` 로 처음부터 생성 |
| hwpx | 정해진 위치에 정해진 텍스트. 템플릿 준비됨. **hwp(구 바이너리)는 불가** |
| 삽입 방식 | xlsx·hwpx 모두 zip+xml → `zipfile` + 문자열 치환 |

## 4. 미정 (샘플 받은 뒤 확정)

1. 센서 TXT 샘플 — 컬럼, 구분자, 인코딩(cp949/utf-8), 결측값 표기, 파일명 규칙
2. 실제 발신 전문 1~2건 — 부호화 세부 검증용
3. xlsx / hwpx 템플릿 실물
4. 인트라넷 사이트 — 파일 첨부 폼인지 전문 텍스트 붙여넣기인지, 로그인 세션
5. TXT가 관측 중 append 되는지, 종료 후 완성본 1개가 떨어지는지
6. 전문 발신 단위 — 3건을 한 필드에 묶는지 각각 따로인지
7. ~~산출물 크기 — 호스트→확장 1MB 제한~~ → **청크 로딩으로 해결** (아래 6절)

## 5. 파일 구조

```
umko/
  host.py            120줄  프로토콜 + 설정 + 명령 디스패치   [완료]
  config.ini          20줄  설정                              [완료]
  host.bat             2줄  윈도우는 .py를 직접 못 띄움       [완료]
  com.umko.host.json   7줄  네이티브 호스트 등록              [완료]
  parse.py           ~80줄  TXT → 관측 데이터                 [대기: 샘플]
  code.py           ~250줄  전문 부호화                       [대기: 지침서/샘플]
  fill.py         40~80줄  템플릿 삽입                        [대기: 템플릿]
  ext/
    manifest.json      8줄  MV2                               [완료]
    background.js     21줄  connectNative 포트 유지 + 중계    [완료]
    popup.html        21줄  관측/설정 2탭                     [완료]
    popup.js          43줄  로그 + 설정 폼 자동생성           [완료]
```

현재 242줄 완료. 최종 예상 500~650줄.

## 6. 메시지 프로토콜

4바이트 리틀엔디안 길이 + JSON 본문. 그게 전부.

```
확장 → 호스트   {cmd:"read", off:0}          off 부터 CHUNK 글자
                {cmd:"xlsx", cells:{"B3":12.3}}       템플릿에 채우기
                {cmd:"xlsx_new", cells:[[행],[행]], title:"관측"}  처음부터 생성
                {cmd:"start"}
                {cmd:"status"}
                {cmd:"get_config"}
                {cmd:"set_config", cfg:{섹션:{키:값}}}

호스트 → 확장   {ok:true, text:"...", off:N, more:bool}   more 면 off 로 재요청
                {ev:"step",   msg:"..."}
                {ev:"config", cfg:{...}}
                {ev:"status", running:bool, step:"..."}
                {ev:"error",  msg:"..."}
```

- `json.dumps` 기본값(ensure_ascii)이라 한글은 `\uXXXX`. 길이 = 바이트 수로 안전
- 작업 스레드와 메인 스레드가 동시에 쓰므로 `send()` 는 락으로 보호
- 확장 내부: 팝업 ↔ 배경은 `chrome.runtime.sendMessage`, 배경 ↔ 호스트는 포트

## 7. 설치

1. `C:\umko\` 에 파이썬 파일 배치
2. `chrome://extensions` → 개발자 모드 → 압축해제된 확장 로드 (`ext/`)
3. 확장 ID를 `com.umko.host.json` 의 `allowed_origins` 에 기입
4. 레지스트리 등록 (관리자 권한 불필요)

```
reg add "HKCU\Software\Google\Chrome\NativeMessagingHosts\com.umko.host" ^
    /ve /t REG_SZ /d "C:\umko\com.umko.host.json"
```

5. 점검: `python host.py -t` → `ok`

## 8. 타이핑 오류 대책

- 파일당 100줄 이하로 나눠 한 번에 하나씩 완성·검증
- 각 파일에 자가 점검(`-t`) 을 둬서 타이핑 직후 확인
- 긴 상수표는 코드가 아니라 데이터 파일로 분리

## 9. 알려진 함정

- **placeholder 분할**: xlsx/hwpx 템플릿에 `{{KEY}}` 를 입력할 때 중간에 서식이
  바뀌면 XML상 여러 run 으로 쪼개져 치환이 실패함. 한 번에 이어서 입력할 것
- **값 이스케이프**: 삽입 값의 `& < >` 는 `xml.sax.saxutils.escape` 로 처리
- **1MB 제한**: 호스트→확장 단일 메시지 상한. `CHUNK = 100000` 글자로 잘라 보낸다.
  한글은 JSON 에서 `\uXXXX` 6바이트라 한 청크가 최대 600KB (실측 600,053바이트)
- **`cp.write()` 는 주석을 지움**: config.ini 의 `;` 주석은 저장 시 유실

## 10. 다음 단계

1. 배관 타이핑 후 왕복 확인 (버튼 → 로그에 `step: 관측 시작`)
2. 센서 TXT 샘플 → `parse.py`
3. 전문 샘플 + 지침서 → `code.py`
4. 템플릿 실물 → `fill.py`
5. 사이트 구조 → 확장에 업로드 로직 + 발신 버튼
