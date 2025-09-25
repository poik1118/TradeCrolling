# Requirements: pip install selenium helium python-dotenv
# .env: userEMAIL = "Your_TrainingView_Account_Email" / userPASSWORD = "Your_TrainingView_Account_Password"

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv
from helium import start_chrome, click, write, press, ENTER, find_all, S  # Helium으로 간소화 (선택적)

load_dotenv()
userEMAIL = os.getenv("userEMAIL")
userPASSWORD = os.getenv("userPASSWORD")

driver = start_chrome('https://www.tradingview.com/', headless=False)  # headless=True로 백그라운드 실행
print("브라우저 열림\n")

# 로그인
wait = WebDriverWait(driver, 10)
user_menu_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.tv-header__user-menu-button.tv-header__user-menu-button--anonymous.js-header-user-menu-button')))
user_menu_button.click()
time.sleep(1)  # 메뉴 로드 대기 (테스트용)

click('Sign in')    # 로그인 버튼 클릭
time.sleep(1)
click('Email')      # 이메일 입력 클릭
time.sleep(1)
write(userEMAIL, into='Email')  # 이메일 입력
write(userPASSWORD, into='Password')  # 비밀번호 입력
press(ENTER)  # 제출
time.sleep(10)  # 로그인 완료 대기
print("로그인 완료\n")

# GOOG 차트 페이지로 이동
sym = "GOOG"
url = f"https://www.tradingview.com/chart/?symbol={sym}"
driver.get(url)
time.sleep(5)
print(f"{sym} 차트 페이지로 이동\n")


# 주(Week) 데이터 선택
click('10m')  # 시간 프레임 메뉴
time.sleep(2)
click('1 week')  # 주간 선택
time.sleep(5)
print("1주 선택 완료\n")

# 엑셀파일로 다운로드
#click(S('.menu-button'))       # 메뉴 클릭
elem = driver.find_element("xpath", "/html/body/div[2]/div/div[3]/div/div/div[3]/div[1]/div/div/div/div/div[14]/div/div/div/button")
elem.click()
time.sleep(1)

#click('Export chart data...')  # 내보내기 옵션
elem = driver.find_element("xpath", "/html/body/div[6]/div[2]/span/div[1]/div/div/div[4]")
elem.click()
time.sleep(1)

#click('Time format (UTC)')     # 타임 스탬프 버튼
elem = driver.find_element("xpath", "/html/body/div[6]/div[2]/div/div[1]/div/div[2]/div/div[3]/span/span[1]")
elem.click()
time.sleep(1)

# 타임 스탬프 ISO 선택
click('ISO time')               
time.sleep(1)

#click('Export')
elem = driver.find_element("xpath", "/html/body/div[6]/div[2]/div/div[1]/div/div[3]/div/span/button")
elem.click() 
time.sleep(1)
print(".csv 다운로드 완료")