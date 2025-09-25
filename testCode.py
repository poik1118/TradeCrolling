# pip install selenium helium
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
import time
from helium import start_chrome, click, write, press, ENTER, S

# 쿠키 파일 경로
COOKIES_FILE = "tradingview_cookies.json"

def save_cookies(driver):
    """현재 브라우저의 쿠키를 파일에 저장"""
    cookies = driver.get_cookies()
    with open(COOKIES_FILE, 'w') as f:
        json.dump(cookies, f)
    print("쿠키 저장 완료")

def load_cookies(driver):
    """저장된 쿠키를 브라우저에 로드"""
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, 'r') as f:
            cookies = json.load(f)
        
        # TradingView 메인 페이지로 먼저 이동
        driver.get('https://www.tradingview.com/')
        time.sleep(3)
        
        # 쿠키 로드
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass
        
        print("쿠키 로드 완료")
        return True
    return False

def setup_driver_with_profile():
    """사용자 프로필을 사용하여 Chrome 드라이버 설정"""
    chrome_options = Options()
    
    # 사용자 데이터 디렉토리 설정 (브라우저 프로필 저장)
    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    
    # 기타 옵션
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def manual_login(driver):
    """사용자 수동 로그인"""
    print("쿠키 로그인이 실패했습니다.")
    print("브라우저에서 직접 로그인을 진행해주세요.")
    
    # 사용자가 Enter 입력 대기
    input("로그인 완료 후 Enter를 눌러주세요: ")
    print("로그인 완료 후 쿠키를 저장합니다.")
    # 로그인 성공 후 쿠키 저장
    save_cookies(driver)

# 메인 실행 부분
def main():
    driver = setup_driver_with_profile()
    
    try:
        # 먼저 저장된 쿠키로 로그인 시도
        if load_cookies(driver):
            # 쿠키 로드 후 차트 페이지로 이동하여 로그인 상태 확인
            driver.get('https://www.tradingview.com/chart/?symbol=GOOG')
            time.sleep(5)
            
            # 로그인 상태 확인 (사용자 메뉴 버튼이 있는지 확인)
            try:
                wait = WebDriverWait(driver, 10)
                user_menu = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.tv-header__user-menu-button')))
                print("쿠키로 자동 로그인 성공!")
                
            except:
                print("쿠키 로그인 실패, 수동 로그인 필요")
                # 사용자 수동 로그인
                manual_login(driver)
        else:
            print("저장된 쿠키 없음, 수동 로그인")
            manual_login(driver)
            
        # 여기서 기존 차트 크롤링 코드 실행
        sym = "GOOG"
        url = f"https://www.tradingview.com/chart/?symbol={sym}"
        print(f"{sym} 차트 페이지로 이동\n")

        # Timeframes: (short_name, menu_label,label_xpath, is_short for lazy load)
        timeframes = [
            ('12M', '12 months', "/html/body/div[6]/div[2]/span/div[1]/div/div/div/div[38]", False),
            ('M', '1 month', "/html/body/div[6]/div[2]/span/div[1]/div/div/div/div[35]", False),
            ('W', '1 week', "/html/body/div[6]/div[2]/span/div[1]/div/div/div/div[34]", False),
            ('D', '1 day', "/html/body/div[6]/div[2]/span/div[1]/div/div/div/div[33]", True),
            ('1h', '1 hour', "/html/body/div[6]/div[2]/span/div[1]/div/div/div/div[27]", True),
            ('10m', '10 minutes', "/html/body/div[6]/div[2]/span/div[1]/div/div/div/div[21]", True)
        ]

        for tf_short, tf_label, label_xpath, is_short in timeframes:
            driver.get(url)
            time.sleep(3)
            print(f"{sym} 차트 페이지로 이동\n")

            # Select timeframe - 현재 시간 프레임 버튼을 클릭하여 메뉴 열기
            elem = driver.find_element("xpath", "/html/body/div[2]/div/div[3]/div/div/div[3]/div[1]/div/div/div/div/div[4]/div/button")
            elem.click()
            time.sleep(2)
            # click(tf_short)
            # time.sleep(2)
            elem = driver.find_element("xpath", label_xpath)
            elem.click()
            time.sleep(3)
            print(f"{tf_label} 선택 완료\n")

            # Lazy load for short timeframes: Scroll left to load history
            if is_short:
                try:
                    # 캔버스 요소 찾기
                    canvas = driver.find_element(By.XPATH, "/html/body/div[2]/div/div[5]/div[1]/div[1]/div/div[2]/div[1]/div[2]/div/canvas[1]")
                    
                    # 캔버스에 포커스를 주기 위해 클릭
                    canvas.click()
                    time.sleep(1)
                    
                    # ActionChains를 사용하여 Ctrl+왼쪽 방향키 10초간 누르기
                    from selenium.webdriver.common.action_chains import ActionChains
                    from selenium.webdriver.common.keys import Keys
                    
                    actions = ActionChains(driver)
                    
                    # Ctrl키를 누른 상태로 왼쪽 방향키를 10초간 반복
                    actions.key_down(Keys.CONTROL).perform()
                    
                    start_time = time.time()
                    while time.time() - start_time < 10:  # 10초간 반복
                        actions.send_keys(Keys.LEFT).perform()
                        time.sleep(0.1)  # 0.1초마다 키 입력
                    
                    # Ctrl키 해제
                    actions.key_up(Keys.CONTROL).perform()
                    
                    print(f"{tf_label} Ctrl+왼쪽 방향키 10초간 완료\n")
                    
                except Exception as e:
                    print(f"Ctrl+왼쪽 방향키 실패: {e}")
                    # 기존 스크롤 방법으로 대체
                    try:
                        chart_container = driver.find_element(By.CSS_SELECTOR, '.chart-container')
                        for _ in range(30):
                            driver.execute_script("arguments[0].scrollLeft -= 1500;", chart_container)
                            time.sleep(0.5)
                    except:
                        print("기존 스크롤 방법도 실패")

            # Export CSV
            elem = driver.find_element("xpath", "/html/body/div[2]/div/div[3]/div/div/div[3]/div[1]/div/div/div/div/div[14]/div/div/div/button")
            elem.click()
            time.sleep(2)

            elem = driver.find_element("xpath", "/html/body/div[6]/div[2]/span/div[1]/div/div/div[4]")
            elem.click()
            time.sleep(2)

            elem = driver.find_element("xpath", "/html/body/div[6]/div[2]/div/div[1]/div/div[2]/div/div[3]/span/span[1]")
            elem.click()
            time.sleep(2)

            click('ISO time')
            time.sleep(2)

            elem = driver.find_element("xpath", "/html/body/div[6]/div[2]/div/div[1]/div/div[3]/div/span/button")
            elem.click()
            time.sleep(5)  # Wait for download

            print(f"{tf_short} 다운로드 완료\n")
            time.sleep(1)
            
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        # 프로그램 종료 전에 쿠키 저장
        save_cookies(driver)
        driver.quit()

if __name__ == "__main__":
    main()