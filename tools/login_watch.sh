#!/bin/sh
# 等待用户扫码登录腾讯问卷，成功后自动抓取问卷结构
OUT="D:/03.其他应用/01.感谢卡/output"
STATE="D:/03.其他应用/01.感谢卡/auth_state.json"
URL="https://wj.qq.com/s2/28268428/3awq/"
TICK='(() => { const c = document.querySelector("input[type=checkbox]"); if (c && !c.checked) c.click(); return "box:" + (c ? c.checked : "none"); })()'

playwright-cli open --browser=msedge --headed --persistent "$URL"
sleep 8
playwright-cli screenshot --filename="$OUT/login_qr.png"
playwright-cli eval "$TICK"
echo "QR_SAVED"

i=0
while [ $i -lt 120 ]; do
  sleep 5
  i=$((i+1))
  url=$(playwright-cli eval "location.href" 2>/dev/null | grep -o 'https://[^"\\ ]*' | head -1)
  echo "check $i: $url"
  case "$url" in
    *"/r/login"*)
      if [ $((i % 10)) -eq 0 ]; then
        playwright-cli reload
        sleep 6
        playwright-cli screenshot --filename="$OUT/login_qr.png"
        playwright-cli eval "$TICK"
        echo "QR_REFRESHED"
      fi
      ;;
    "")
      echo "eval_failed_$i"
      ;;
    *)
      echo "LOGGED_IN: $url"
      playwright-cli state-save "$STATE" && echo "STATE_SAVED"
      break
      ;;
  esac
done

# 登录后浏览器保持常驻（供后续预填命令跨调用复用）
echo "KEEPER_ACTIVE"
sleep 5400

sleep 4
playwright-cli eval "document.body.innerText" > "$OUT/survey_text.txt" 2>&1
playwright-cli screenshot --filename="$OUT/survey_logged.png"
echo "SURVEY_DUMPED"
