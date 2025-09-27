import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
import time
# helium 라이브러리는 더 이상 사용하지 않음

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
        
        # TradingView 메인 페이지로 이동
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
    
    # 사용자 데이터 디렉토리 설정
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
            
            # 로그인 상태 확인 (특정 이미지 요소가 있는지 확인)
            try:
                wait = WebDriverWait(driver, 5)
                # 먼저 특정 이미지 요소가 있는지 확인
                img_element = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div[2]/div/div/div/div/img')))
                print("특정 이미지 요소 발견! 쿠키로 자동 로그인 성공!")
                
            except:
                print("쿠키 로그인 실패, 수동 로그인 필요")
                # 사용자 수동 로그인
                manual_login(driver)
        else:
            print("저장된 쿠키 없음, 수동 로그인")
            manual_login(driver)
            
        # 기존 차트 크롤링 코드 실행
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
            print("\n\n================================================")
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

            # Lazy load for short timeframes: 마우스 드래그 시뮬레이션
            if is_short:
                try:
                    # 상위 캔버스 요소 찾기 (pane-top-canvas)
                    canvas = driver.find_element(By.CSS_SELECTOR, 'canvas[data-name="pane-top-canvas"]')
                    
                    # 캔버스 크기와 위치 정보 가져오기
                    canvas_size = canvas.size
                    canvas_location = canvas.location
                    
                    # 캔버스 중심 좌표 계산
                    center_x = canvas_size['width'] // 2
                    center_y = canvas_size['height'] // 2
                    
                    print(f"캔버스 중심 좌표: ({center_x}, {center_y})")
                    
                    # JavaScript로 마우스 휠 이벤트 발생
                    print(f"--- 🟢{tf_label}마우스 휠 스크롤 다운 이벤트 (차트 축소)🟢 ---")
                    
                    # deltaY: 양수(+)는 아래로 스크롤 (축소), 음수(-)는 위로 스크롤 (확대)
                    # 한 번에 여러 번 스크롤하는 효과를 주려면 이 코드를 반복문으로 감싸면 됩니다.
                    for i in range(32): # 32번 스크롤하여 확실하게 축소
                        wheel_script = f"""
                        var canvas = arguments[0];
                        var rect = canvas.getBoundingClientRect();
                        
                        // 이벤트 발생 좌표 (캔버스 중심)
                        var clientX = rect.left + {center_x};
                        var clientY = rect.top + {center_y};
                        
                        // 스크롤 강도 (200)
                        var scrollAmount = 200; 
                        
                        console.log('휠 이벤트 발생 시도: (' + clientX + ', ' + clientY + ')');
                        
                        // 실제 사용자처럼 보이도록 휠 이벤트 전에 마우스 포인터를 해당 위치로 옮기는 이벤트를 추가할 수 있습니다.
                        canvas.dispatchEvent(new PointerEvent('pointermove', {{
                            clientX: clientX,
                            clientY: clientY,
                            pointerId: 1,
                            pointerType: 'mouse',
                            bubbles: true,
                            cancelable: true,
                            view: window
                        }}));

                        // WheelEvent에 최대한 많은 속성을 채워넣어 실제 이벤트처럼 시뮬레이션
                        var wheelEvent = new WheelEvent('wheel', {{
                            clientX: clientX,
                            clientY: clientY,
                            screenX: window.screenX + clientX,
                            screenY: window.screenY + clientY,
                            deltaX: 0,
                            deltaY: scrollAmount,  // 양수: 아래로 스크롤
                            deltaZ: 0,
                            deltaMode: 0, // 0: DOM_DELTA_PIXEL (픽셀 단위)
                            bubbles: true,
                            cancelable: true,
                            composed: true, // Shadow DOM 경계를 넘어 이벤트 전파 허용
                            view: window
                        }});
                        
                        canvas.dispatchEvent(wheelEvent);
                        console.log('휠 이벤트 전달 완료');
                        """
                        
                        driver.execute_script(wheel_script, canvas)
                        print(f"✅ {i+1}번째 마우스 휠 아래로 스크롤 완료")
                        time.sleep(0.1) # 각 스크롤 사이에 아주 짧은 딜레이
                    
                    # timeframe에 따라 다른 드래그 횟수 설정 (10m: 256, 1h: 32, D: 8) -> 브라우저 크기에 따른 편차 예상으로 큰 값으로 설정
                    if tf_short == 'D':  # 1 day
                        drag_count = 6
                    elif tf_short == '1h':  # 1 hour
                        drag_count = 30
                    elif tf_short == '10m':  # 10 minutes
                        drag_count = 50
                    else:
                        drag_count = 50  # 기본값
                    
                    print(f"--- 🟢{tf_label} - 드래그 횟수: {drag_count}회🟢 ---")
                    
                    # JavaScript를 사용하여 마우스 드래그 이벤트 시뮬레이션
                    for i in range(drag_count):
                        # 캔버스 x축 왼쪽 시작에서 오른쪽 마지막까지 드래그
                        start_x = 100  # 캔버스 왼쪽 시작
                        start_y = center_y  # y축은 중심 유지
                        end_x = canvas_size['width'] - 100  # 캔버스 오른쪽 마지막
                        end_y = center_y  # y축은 중심 유지
                        
                        # JavaScript로 마우스 드래그 이벤트 발생
                        drag_script = f"""
                        var canvas = arguments[0];
                        var rect = canvas.getBoundingClientRect();
                        
                        console.log('캔버스 위치:', rect);
                        console.log('드래그 시작:', {start_x}, {start_y});
                        console.log('드래그 끝:', {end_x}, {end_y});
                        
                        // 1. 기본 마우스 이벤트
                        var mouseDownEvent = new MouseEvent('mousedown', {{
                            clientX: rect.left + {start_x},
                            clientY: rect.top + {start_y},
                            screenX: rect.left + {start_x},
                            screenY: rect.top + {start_y},
                            button: 0,
                            buttons: 1,
                            bubbles: true,
                            cancelable: true,
                            view: window
                        }});
                        
                        // 2. 포인터 이벤트 (최신 브라우저)
                        var pointerDownEvent = new PointerEvent('pointerdown', {{
                            clientX: rect.left + {start_x},
                            clientY: rect.top + {start_y},
                            screenX: rect.left + {start_x},
                            screenY: rect.top + {start_y},
                            button: 0,
                            buttons: 1,
                            pointerId: 1,
                            pointerType: 'mouse',
                            bubbles: true,
                            cancelable: true,
                            view: window
                        }});
                        
                        // 이벤트 발생
                        canvas.dispatchEvent(mouseDownEvent);
                        canvas.dispatchEvent(pointerDownEvent);
                        
                        // 약간의 지연 후 드래그
                        setTimeout(function() {{
                            // 중간 지점들을 거쳐서 부드럽게 드래그
                            var steps = 10;
                            var stepX = ({end_x} - {start_x}) / steps;
                            var stepY = ({end_y} - {start_y}) / steps;
                            
                            for (var step = 1; step <= steps; step++) {{
                                var currentX = {start_x} + (stepX * step);
                                var currentY = {start_y} + (stepY * step);
                                
                                var mouseMoveEvent = new MouseEvent('mousemove', {{
                                    clientX: rect.left + currentX,
                                    clientY: rect.top + currentY,
                                    screenX: rect.left + currentX,
                                    screenY: rect.top + currentY,
                                    button: 0,
                                    buttons: 1,
                                    bubbles: true,
                                    cancelable: true,
                                    view: window
                                }});
                                
                                var pointerMoveEvent = new PointerEvent('pointermove', {{
                                    clientX: rect.left + currentX,
                                    clientY: rect.top + currentY,
                                    screenX: rect.left + currentX,
                                    screenY: rect.top + currentY,
                                    button: 0,
                                    buttons: 1,
                                    pointerId: 1,
                                    pointerType: 'mouse',
                                    bubbles: true,
                                    cancelable: true,
                                    view: window
                                }});
                                
                                canvas.dispatchEvent(mouseMoveEvent);
                                canvas.dispatchEvent(pointerMoveEvent);
                            }}
                            
                            // 마우스 업 이벤트
                            var mouseUpEvent = new MouseEvent('mouseup', {{
                                clientX: rect.left + {end_x},
                                clientY: rect.top + {end_y},
                                screenX: rect.left + {end_x},
                                screenY: rect.top + {end_y},
                                button: 0,
                                buttons: 0,
                                bubbles: true,
                                cancelable: true,
                                view: window
                            }});
                            
                            var pointerUpEvent = new PointerEvent('pointerup', {{
                                clientX: rect.left + {end_x},
                                clientY: rect.top + {end_y},
                                screenX: rect.left + {end_x},
                                screenY: rect.top + {end_y},
                                button: 0,
                                buttons: 0,
                                pointerId: 1,
                                pointerType: 'mouse',
                                bubbles: true,
                                cancelable: true,
                                view: window
                            }});
                            
                            canvas.dispatchEvent(mouseUpEvent);
                            canvas.dispatchEvent(pointerUpEvent);
                            
                            console.log('드래그 완료');
                        }}, 50);
                        """
                        
                        driver.execute_script(drag_script, canvas)
                        print(f"✅ {i+1}/{drag_count}번째 마우스 드래그 완료")
                        time.sleep(1)  # 각 드래그 사이에 1초 대기
                    
                except Exception as e:
                    print(f"❌ 마우스 스크롤 및 드래그 실패: {e}")

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

            # ISO time 옵션 클릭
            iso_time_element = driver.find_element(By.XPATH, "//span[contains(text(), 'ISO time')]")
            iso_time_element.click()
            time.sleep(2)

            elem = driver.find_element("xpath", "/html/body/div[6]/div[2]/div/div[1]/div/div[3]/div/span/button")
            elem.click()
            time.sleep(5)  # Wait for download

            print(f"{tf_short} 다운로드 완료")
            print("================================================")
            time.sleep(2)
            
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        # 프로그램 종료 전에 쿠키 저장
        save_cookies(driver)
        driver.quit()

if __name__ == "__main__":
    main()