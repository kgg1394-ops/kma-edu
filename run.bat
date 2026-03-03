@echo off
chcp 65001 > nul
echo [1/3] 의협 데이터 수집 시작...

rem 폴더에 있는 파일 이름이 update_kma.py 인지 확인해 보세요!
python update_kma.py

echo [2/3] GitHub 사이트에 파일 업로드 중...
git add .
git commit -m "Auto-update: %date% %time%"
git push origin main

echo [3/3] 모든 작업이 완료되었습니다! 1분 뒤 사이트를 확인하세요.
pause