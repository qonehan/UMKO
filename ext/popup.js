var out = document.getElementById("out");
var inp = document.getElementById("inp");

function send(msg, done) {
  chrome.runtime.sendNativeMessage("com.local.pyhost", msg, function (res) {
    if (chrome.runtime.lastError) {
      out.textContent = "ERR: " + chrome.runtime.lastError.message;
    } else if (!res.ok) {
      out.textContent = res.error;
    } else {
      done(res);
    }
  });
}

document.getElementById("save").onclick = function () {
  send({ cmd: "write", text: inp.value }, function () {
    out.textContent = "저장됨";
  });
};

document.getElementById("load").onclick = function () {
  send({ cmd: "read" }, function (res) {
    inp.value = res.text;
    out.textContent = "읽음";
  });
};

// [추가] 확장 변수를 xlsx 의 지정한 칸에 쓴다.
// 항목을 늘리려면 이 표에만 [이름, 셀] 을 추가하면 된다.
var VARS = [
  ["관측일시", "B2"],
  ["기온",     "B3"],
  ["습도",     "B4"],
  ["기압",     "B5"]
];

document.getElementById("vars").innerHTML = VARS.map(function (v) {
  return '<tr><td>' + v[0] + '</td><td><input id="v_' + v[1] + '" style="width:100%"></td></tr>';
}).join("");

// 숫자로 보이면 숫자로 보낸다. "0900" 처럼 되돌렸을 때 달라지면 문자열 그대로.
function num(s) {
  return String(Number(s)) === s ? Number(s) : s;
}

document.getElementById("xl").onclick = function () {
  var cells = {};
  VARS.forEach(function (v) {
    var s = document.getElementById("v_" + v[1]).value;
    if (s !== "") cells[v[1]] = num(s);
  });
  send({ cmd: "xlsx", cells: cells }, function (res) {
    out.textContent = "저장됨: " + res.path;
  });
};
