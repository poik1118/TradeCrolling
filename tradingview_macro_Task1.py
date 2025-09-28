# -*- coding: utf-8 -*-
"""
# ================================================================
# Task 1: TradingView 구글(GOOG) 주(Week) 데이터 CSV 다운로드 매크로 (수정판)
# ================================================================
# 구현 내용:
# 1) 트레이딩뷰(TradingView) 접속
# 2) 구글(종목코드 GOOG) 종목 선택
# 3) 주 데이터를 엑셀로 다운로드하는 매크로 구현
# 
# 프로그램 출력물: GOOG 종목에 대한 주 데이터 CSV 파일
# 상금: 과제 완료시 오프라인 미팅 후 5만원 지급(선착순 3팀)
#
# 수정사항: Task2, Task3에서 검증된 실제 XPath 경로 적용
#
# 사전 요구사항:
# - Python 3.9+
# - pip install selenium webdriver-manager
# - 크롬 브라우저 설치
# ================================================================
"""

import os
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ================================================================
# 상수 정의
# ================================================================
COOKIES_FILE = "tradingview_cookies.json"
DOWNLOAD_ROOT = Path(os.environ.get("TV_DOWNLOAD_ROOT", "./downloads")).resolve()

# Task2, Task3에서 검증된 실제 XPath 경로들
TIMEFRAME_WEEK_XPATH = "html/body/div[6]/div[2]/span/div[1]/div/div/div/div[34]"  # Task2에서 확인된 1 week XPath
EXPORT_BUTTON_XPATH = "html/body/div[2]/div/div[3]/div/div/div[3]/div[1]/div/div/div/div/div[14]/div/div/div/button"  # Task2 Export 버튼
EXPORT_MENU_ITEM_XPATH = "html/body/div[6]/div[2]/span/div[1]/div/div/div[4]"  # Task2 Export chart data 메뉴
BARS_OPTION_XPATH = "html/body/div[6]/div[2]/div/div[1]/div/div[2]/div/div[3]/span/span[1]"  # Task2 Bars 옵션
EXPORT_CONFIRM_XPATH = "html/body/div[6]/div[2]/div/div[1]/div/div[3]/div/span/button"  # Task2 Export 확인 버튼

# ================================================================
# 헬퍼 함수들
# ================================================================

def ensure_dir(p: Path) -> None:
    """디렉토리 생성 보장"""
    p.mkdir(parents=True, exist_ok=True)

def setup_driver_with_profile() -> webdriver.Chrome:
    """크롬 드라이버 설정 (Task2 방식 적용)"""
    chrome_options = Options()
    
    # 사용자 데이터 디렉토리 설정 (Task2 방식)
    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    
    # 기본 옵션들
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # 다운로드 설정
    ensure_dir(DOWNLOAD_ROOT)
    prefs = {
        "download.default_directory": str(DOWNLOAD_ROOT),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # 크롬 드라이버 설정
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"ChromeDriver 설치 오류: {e}")
        print("ChromeDriver를 수동으로 설치하거나 Chrome 브라우저를 업데이트하세요.")
        # webdriver-manager 없이 시도
        driver = webdriver.Chrome(options=chrome_options)
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def save_cookies(driver: webdriver.Chrome) -> None:
    """쿠키 저장"""
    try:
        cookies = driver.get_cookies()
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f)
        print("[INFO] 쿠키가 저장되었습니다.")
    except Exception as e:
        print(f"[WARN] 쿠키 저장 실패: {e}")

def load_cookies(driver: webdriver.Chrome) -> bool:
    """쿠키 로드 (Task2 방식)"""
    if not os.path.exists(COOKIES_FILE):
        return False
    
    try:
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
        
        # TradingView에 먼저 접속
        driver.get("https://www.tradingview.com")
        time.sleep(3)
        
        # TradingView 쿠키 로드 시도
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass
        
        print("[INFO] 쿠키가 로드되었습니다.")
        return True
    except Exception as e:
        print(f"[WARN] 쿠키 로드 실패: {e}")
        return False

def manual_login(driver: webdriver.Chrome) -> None:
    """수동 로그인 처리 (Task2 방식)"""
    print("[INFO] 수동 로그인이 필요합니다.")
    print("브라우저에서 TradingView에 로그인 후 아무 키나 누르세요...")
    
    # ChromeDriver 경고 무시
    input("Enter 키를 눌러 계속...")
    print("[INFO] 로그인이 완료되었습니다.")
    
    # 로그인 완료 후 쿠키 저장
    save_cookies(driver)

def go_to_goog_chart(driver: webdriver.Chrome) -> None:
    """GOOG 차트로 이동"""
    try:
        # 쿠키 로드 시도
        if load_cookies(driver):
            # 쿠키가 있으면 직접 GOOG 차트로
            driver.get("https://www.tradingview.com/chart/?symbol=GOOG")
            time.sleep(5)
            
            # 로그인 확인 - 이미지 요소로 로그인 상태 체크
            try:
                wait = WebDriverWait(driver, 5)
                # 로그인되지 않은 상태를 나타내는 이미지 요소 확인
                img_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "html/body/div[2]/div/div[2]/div/div/div/div/img")
                ))
                print("로그인이 필요한 상태입니다!")
                manual_login(driver)
            except:
                print("이미 로그인된 상태입니다.")
        else:
            print("쿠키가 없습니다. 수동 로그인을 진행합니다.")
            manual_login(driver)
    except Exception as e:
        print(f"차트 접속 중 오류: {e}")
        manual_login(driver)

def select_timeframe_week(driver: webdriver.Chrome) -> None:
    """주(Week) 타임프레임 선택 - Task2에서 검증된 XPath 사용"""
    try:
        # 먼저 타임프레임 메뉴 열기
        timeframe_button = driver.find_element("xpath", 
            "html/body/div[2]/div/div[3]/div/div/div[3]/div[1]/div/div/div/div/div[4]/div/button")
        timeframe_button.click()
        time.sleep(2)
        
        # Week 타임프레임 선택 (Task2에서 검증된 XPath)
        week_element = driver.find_element("xpath", TIMEFRAME_WEEK_XPATH)
        week_element.click()
        time.sleep(3)
        print("[INFO] 주(Week) 타임프레임이 선택되었습니다.")
        
    except Exception as e:
        print(f"[WARN] 주 타임프레임 선택 실패: {e}")
        print("기본 타임프레임을 사용합니다.")

def export_csv_data(driver: webdriver.Chrome) -> None:
    """CSV 데이터 내보내기 - Task2에서 검증된 XPath 사용"""
    try:
        # 1단계: Export 버튼 클릭 (Task2 검증 XPath)
        export_button = driver.find_element("xpath", EXPORT_BUTTON_XPATH)
        export_button.click()
        time.sleep(2)
        
        # 2단계: Export chart data 메뉴 선택
        export_menu = driver.find_element("xpath", EXPORT_MENU_ITEM_XPATH)
        export_menu.click()
        time.sleep(2)
        
        # 3단계: Bars 옵션 선택 (Task2 검증 XPath)
        bars_option = driver.find_element("xpath", BARS_OPTION_XPATH)
        bars_option.click()
        time.sleep(2)
        
        # 4단계: ISO time 설정
        try:
            iso_time_element = driver.find_element(By.XPATH, "//span[contains(text(), 'ISO time')]")
            iso_time_element.click()
            time.sleep(2)
        except:
            print("[INFO] ISO time 옵션을 찾을 수 없어 기본 설정을 사용합니다.")
        
        # 5단계: Export 확인 버튼 클릭
        export_confirm = driver.find_element("xpath", EXPORT_CONFIRM_XPATH)
        export_confirm.click()
        time.sleep(5)  # 다운로드 대기
        
        print("[INFO] CSV 내보내기가 완료되었습니다.")
        
    except Exception as e:
        raise RuntimeError(f"CSV 내보내기 실패: {e}")

def wait_and_rename_csv() -> str:
    """CSV 파일 다운로드 대기 및 이름 변경"""
    try:
        # 다운로드 완료 대기 (최대 30초)
        for i in range(30):
            csv_files = list(DOWNLOAD_ROOT.glob("*.csv"))
            if csv_files:
                latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)
                
                # 파일명 변경
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                new_name = f"GOOG_Weekly_{timestamp}.csv"
                dest_path = DOWNLOAD_ROOT / new_name
                latest_file.rename(dest_path)
                
                return str(dest_path)
            
            time.sleep(1)
            print(f"다운로드 대기 중... ({i+1}/30)")
        
        raise TimeoutError("CSV 다운로드가 완료되지 않았습니다.")
        
    except Exception as e:
        raise RuntimeError(f"파일 처리 오류: {e}")

# ================================================================
# 메인 실행 함수
# ================================================================

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("Task 1: TradingView GOOG 주(Week) 데이터 다운로드 (수정판)")
    print("=" * 60)
    
    # 드라이버 설정
    driver = setup_driver_with_profile()
    
    try:
        # GOOG 차트로 이동 및 로그인 처리
        print("\n[INFO] GOOG 차트로 이동 중...")
        go_to_goog_chart(driver)
        
        # 주(Week) 타임프레임 선택
        print("[INFO] 주(Week) 타임프레임 선택 중...")
        select_timeframe_week(driver)
        
        # CSV 데이터 내보내기
        print("[INFO] CSV 데이터 내보내기 시작...")
        export_csv_data(driver)
        
        # 다운로드 완료 대기 및 파일명 변경
        print("[INFO] 다운로드 완료 대기 중...")
        saved_file = wait_and_rename_csv()
        
        print(f"\n[SUCCESS] ✅ 다운로드 완료!")
        print(f"파일 위치: {saved_file}")
        
        # 파일 크기 확인
        file_size = Path(saved_file).stat().st_size
        print(f"파일 크기: {file_size:,} bytes")
        
    except Exception as e:
        print(f"\n[ERROR] ❌ 오류 발생: {e}")
        print("브라우저를 수동으로 확인하거나 다시 시도해 주세요.")
        
    finally:
        # 쿠키 저장 및 드라이버 종료
        save_cookies(driver)
        driver.quit()
        print("\n[INFO] 프로그램이 종료되었습니다.")

if __name__ == "__main__":
    main()