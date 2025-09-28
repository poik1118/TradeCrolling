# tradingview_macro_Task3.py
# -*- coding: utf-8 -*-
"""
Task 3: TradingView 크롤링 매크로 (확장판)
- venv + Python 3.11.9 가정
- Selenium + webdriver-manager + python-dotenv 사용 (환경변수 선택)
- 동작 요약:
  1) TradingView 로그인(쿠키 재사용) 후 차트 페이지 접속
  2) 지정된 보조지표를 추가
  3) 지정한 여러 종목(최대 30개까지) × 여러 시간프레임(연/월/주/일/시/10분)을 반복
  4) 각 조합에 대해 CSV 다운로드
  5) 일/시/10분에서는 확대해 둔 차트를 마우스 휠/드래그로 과거 데이터까지 지연 로딩

주의
- TradingView UI는 수시로 바뀌므로, 버튼/메뉴의 XPath가 달라질 수 있습니다.
  아래 스크립트는 팀원의 Task2 코드의 XPath를 최대한 유지하되, 몇 가지 유연한 선택자를
  함께 시도합니다. 환경에 따라 소폭 수정이 필요할 수 있습니다.
- 사이트 약관을 준수하세요. 빈번한 자동화/스크래핑은 계정 제한 위험이 있습니다.
"""
from __future__ import annotations
import os
import time
import json
from pathlib import Path
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.action_chains import ActionChains


# -----------------------------
# 전역 설정
# -----------------------------
COOKIES_FILE = "tradingview_cookies.json"
# 기본 다운로드 루트 (필요시 절대경로로 바꾸세요)
DOWNLOAD_ROOT = Path(os.environ.get("TV_DOWNLOAD_ROOT", "./downloads")).resolve()
# 크롬 사용자 프로필 디렉토리(로그인/쿠키 유지)
USER_PROFILE_DIR = Path(os.environ.get("TV_CHROME_PROFILE", "./chrome_profile")).resolve()

# 시간프레임 목록 (short, human_label, url_interval, requires_lazyload)
TIMEFRAMES = [
    ('12M', '12 months', '12M',   False),  # 연
    ('M',   '1 month',   '1M',    False),  # 월
    ('W',   '1 week',    '1W',    False),  # 주
    ('D',   '1 day',     '1D',    True),   # 일
    ('1h',  '1 hour',    '60',    True),   # 60분
    ('10m', '10 minutes','10',    True),   # 10분
]


# 지표 추가시 검색에 사용할 키워드들 (예: 'Relative Strength Index', 'MACD' 등)
INDICATORS = [s.strip() for s in os.environ.get("TV_INDICATORS", "Relative Strength Index, MACD").split(",")]

# 종목 리스트 (최대 30개). 환경변수 TV_TICKERS 또는 tickers.txt(한 줄 한 종목)로도 입력 가능
DEFAULT_TICKERS = ["GOOG"]


# -----------------------------
# 유틸
# -----------------------------
def read_tickers() -> List[str]:
    # 1) 환경변수
    env_val = os.environ.get("TV_TICKERS", "").strip()
    if env_val:
        return [s.strip() for s in env_val.split(",") if s.strip()][:30]

    # 2) tickers.txt
    if Path("tickers.txt").exists():
        lines = [ln.strip() for ln in Path("tickers.txt").read_text(encoding="utf-8").splitlines()]
        lines = [x for x in lines if x and not x.startswith("#")]
        if lines:
            return lines[:30]

    # 3) 기본값
    return DEFAULT_TICKERS


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def setup_driver(download_dir: Path) -> webdriver.Chrome:
    ensure_dir(USER_PROFILE_DIR)
    ensure_dir(download_dir)

    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={str(USER_PROFILE_DIR)}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    prefs = {
        "download.default_directory": str(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.set_window_size(1600, 1000)
    return driver


def save_cookies(driver: webdriver.Chrome) -> None:
    try:
        cookies = driver.get_cookies()
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False)
        print("[INFO] 쿠키 저장 완료")
    except Exception as e:
        print(f"[WARN] 쿠키 저장 실패: {e}")


def load_cookies(driver: webdriver.Chrome) -> bool:
    if not Path(COOKIES_FILE).exists():
        return False

    try:
        # 메인 먼저 열기
        driver.get("https://www.tradingview.com/")
        time.sleep(3)
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            for cookie in json.load(f):
                try:
                    driver.add_cookie(cookie)
                except Exception:
                    pass
        print("[INFO] 쿠키 로드 완료")
        return True
    except Exception as e:
        print(f"[WARN] 쿠키 로드 실패: {e}")
        return False


def manual_login(driver: webdriver.Chrome) -> None:
    print("[ACTION] 브라우저에서 TradingView에 로그인하세요.")
    input("로그인 후 Enter를 누르면 진행합니다... ")
    save_cookies(driver)

def go_chart(driver: webdriver.Chrome, symbol: str, interval: str | None = None) -> None:
    base = f"https://www.tradingview.com/chart/?symbol={symbol}"
    url = base if interval is None else f"{base}&interval={interval}"
    driver.get(url)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'canvas[data-name="pane-top-canvas"]'))
    )



def lazy_load_short_tf(driver: webdriver.Chrome, tf_short: str, tf_label: str) -> None:
    """일/시/10분 프레임에서 과거 데이터 로딩(휠 스크롤+좌->우 드래그)"""
    try:
        canvas = driver.find_element(By.CSS_SELECTOR, 'canvas[data-name="pane-top-canvas"]')
    except NoSuchElementException:
        print("[WARN] 캔버스를 찾지 못했습니다.")
        return

    size = canvas.size
    center_x = size["width"] // 2
    center_y = size["height"] // 2

    # 축소(스크롤 다운) 반복
    for i in range(30):
        wheel_script = f"""
        var canvas = arguments[0];
        var rect = canvas.getBoundingClientRect();
        var clientX = rect.left + {center_x};
        var clientY = rect.top  + {center_y};

        canvas.dispatchEvent(new PointerEvent('pointermove', {{
            clientX: clientX, clientY: clientY, pointerId: 1, pointerType: 'mouse', bubbles: true
        }}));
        var e = new WheelEvent('wheel', {{
            clientX: clientX, clientY: clientY, deltaX: 0, deltaY: 200, deltaMode: 0, bubbles: true
        }});
        canvas.dispatchEvent(e);
        """
        driver.execute_script(wheel_script, canvas)
        time.sleep(0.05)

    # 프레임별 드래그 횟수
    drag_count = 6 if tf_short == "D" else (30 if tf_short == "1h" else 50)
    for i in range(drag_count):
        start_x, end_x = 100, size["width"] - 100
        drag_script = f"""
        var canvas = arguments[0];
        var rect = canvas.getBoundingClientRect();

        var down = new MouseEvent('mousedown', {{
            clientX: rect.left + {start_x}, clientY: rect.top + {center_y},
            button: 0, buttons: 1, bubbles: true
        }});
        canvas.dispatchEvent(down);

        var steps = 10;
        var stepX = ({end_x} - {start_x}) / steps;
        for (var s = 1; s <= steps; s++) {{
            var move = new MouseEvent('mousemove', {{
                clientX: rect.left + {start_x} + stepX*s,
                clientY: rect.top + {center_y},
                button: 0, buttons: 1, bubbles: true
            }});
            canvas.dispatchEvent(move);
        }}

        var up = new MouseEvent('mouseup', {{
            clientX: rect.left + {end_x}, clientY: rect.top + {center_y},
            button: 0, buttons: 0, bubbles: true
        }});
        canvas.dispatchEvent(up);
        """
        driver.execute_script(drag_script, canvas)
        time.sleep(0.7)


def add_indicator(driver: webdriver.Chrome, keyword: str) -> None:
    """지표 패널에서 keyword로 검색 후 첫 결과 추가 (안정화+재시도)"""
    for attempt in range(2):
        if not open_indicators_dialog(driver):
            print(f"[WARN] Indicators dialog open failed ({keyword}) try={attempt}")
            continue

        typed = False
        search_candidates = [
            "//div[@role='dialog']//input[@type='text']",
            "//div[@role='dialog']//input[@placeholder or @aria-label]",
            "//input[contains(@placeholder,'Search') or contains(@placeholder,'검색')]",
        ]
        for xp in search_candidates:
            try:
                elems = WebDriverWait(driver, 4).until(EC.presence_of_all_elements_located((By.XPATH, xp)))
                for el in elems:
                    if el.is_displayed():
                        el.clear()
                        el.send_keys(keyword)
                        time.sleep(1.0)
                        typed = True
                        break
                if typed: break
            except Exception:
                continue
        if not typed:
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                for ch in keyword: body.send_keys(ch); time.sleep(0.02)
                time.sleep(1.0)
                typed = True
            except Exception:
                pass
        if not typed:
            print(f"[WARN] 검색어 입력 실패 ({keyword}) try={attempt}")
            try: driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except Exception: pass
            ensure_dialog_closed(driver, 4); focus_chart_canvas(driver)
            continue

        clicked = False
        exact_xp = f"(//div[@role='dialog']//span[normalize-space()='{keyword}'])[1]"
        generic_xps = [
            "(//div[@role='dialog']//div[@role='button' or @role='option']//span[normalize-space()])[1]",
            "(//div[@role='dialog']//div[@role='button' or @role='option'])[1]",
        ]
        try:
            el = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, exact_xp)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            try: el.click()
            except Exception: driver.execute_script("arguments[0].click();", el)
            clicked = True
        except Exception:
            for xp in generic_xps:
                try:
                    el = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, xp)))
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    try: el.click()
                    except Exception: driver.execute_script("arguments[0].click();", el)
                    clicked = True
                    break
                except Exception:
                    continue
            if not clicked:
                try:
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ENTER)
                    time.sleep(0.6)
                    clicked = True
                except Exception:
                    pass

        # 닫고 포커스 복구
        try:
            close_btn = driver.find_element(By.XPATH, "//div[@role='dialog']//button[contains(@aria-label,'Close') or contains(.,'닫기')]")
            driver.execute_script("arguments[0].click();", close_btn)
        except Exception:
            try: driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except Exception: pass
        ensure_dialog_closed(driver, 4); focus_chart_canvas(driver)

        if clicked:
            print(f"[INFO] 지표 추가 완료: {keyword}")
            return
        else:
            print(f"[WARN] 결과 클릭 실패 ({keyword}) try={attempt}")
    print(f"[WARN] 지표 추가 실패: {keyword}")



def export_csv(driver: webdriver.Chrome) -> None:
    """현재 차트에서 CSV 내보내기"""

    # 1) 내보내기 메뉴 열기 (Task2의 XPath 먼저 시도)
    export_btn_candidates = [
        "/html/body/div[2]/div/div[3]/div/div/div[3]/div[1]/div/div/div/div/div[14]/div/div/div/button",
        # 대체: 'Export chart data' 툴팁/라벨 탐색
        "//button[contains(@aria-label,'Export') or .//span[contains(.,'Export')]]",
        "//button[.//span[contains(.,'데이터 내보내기') or contains(.,'내보내기')]]",
    ]
    opened = False
    for xp in export_btn_candidates:
        try:
            WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.XPATH, xp))).click()
            time.sleep(0.8)
            opened = True
            break
        except Exception:
            continue
    if not opened:
        raise RuntimeError("내보내기 버튼을 찾지 못했습니다. XPath를 확인하세요.")

    # 2) 'Export chart data' 항목 클릭 (Task2 XPath + 대체)
    item_candidates = [
        "/html/body/div[6]/div[2]/span/div[1]/div/div/div[4]",
        "//div[@role='menuitem' or @data-name='menu-item']//div[contains(.,'Export')]",
        "//div[contains(.,'데이터 내보내기')]",
    ]
    clicked = False
    for xp in item_candidates:
        try:
            WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.XPATH, xp))).click()
            time.sleep(0.8)
            clicked = True
            break
        except Exception:
            continue
    if not clicked:
        raise RuntimeError("Export 메뉴 항목을 찾지 못했습니다. XPath를 확인하세요.")

    # 3) 옵션 패널에서 'Bars' (OHLCV) 선택 및 ISO time 선택
    try:
        # 'Bars' 탭
        bars_candidates = [
            "/html/body/div[6]/div[2]/div/div[1]/div/div[2]/div/div[3]/span/span[1]",
            "//span[contains(.,'Bars') or contains(.,'바')]",
        ]
        for xp in bars_candidates:
            try:
                WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.XPATH, xp))).click()
                time.sleep(0.5)
                break
            except Exception:
                continue

        # ISO time 체크
        iso_candidates = [
            "//span[contains(text(), 'ISO time')]",
            "//label[.//span[contains(.,'ISO')]]",
        ]
        for xp in iso_candidates:
            try:
                WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.XPATH, xp))).click()
                time.sleep(0.5)
                break
            except Exception:
                continue

        # Export 버튼
        export_confirm_candidates = [
            "/html/body/div[6]/div[2]/div/div[1]/div/div[3]/div/span/button",
            "//button[.//span[contains(.,'Export')] or contains(.,'내보내기')]",
        ]
        for xp in export_confirm_candidates:
            try:
                WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.XPATH, xp))).click()
                time.sleep(0.5)
                break
            except Exception:
                continue
    except Exception as e:
        raise RuntimeError(f"Export 옵션 설정 실패: {e}")


def wait_for_download(download_dir: Path, timeout: int = 60) -> Path:
    """다운로드 완료까지 대기(.crdownload 소멸) 후 최신 파일 경로 반환"""
    end = time.time() + timeout
    last_size = -1
    target: Path|None = None

    while time.time() < end:
        csvs = sorted(download_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        partials = list(download_dir.glob("*.crdownload"))
        # 다운로드가 막 시작하면 .crdownload가 생기고, 끝나면 사라짐
        if csvs and not partials:
            newest = csvs[0]
            # 파일 크기가 안정될 때까지 한 번 더 확인
            size = newest.stat().st_size
            if size == last_size:
                target = newest
                break
            last_size = size
        time.sleep(1)

    if not target:
        raise TimeoutException("CSV 다운로드가 완료되지 않았습니다.")
    return target


def run_for_symbol(driver: webdriver.Chrome, symbol: str, out_root: Path) -> None:
    print(f"\n===== SYMBOL: {symbol} =====")

    # 1) 먼저 기본 차트 열고(무간격) 보조지표를 '한 번' 추가
    #    (동일 레이아웃/심볼에서는 인디케이터가 유지되는 경우가 많음)
    go_chart(driver, symbol, interval=None)
    for kw in INDICATORS:
        add_indicator(driver, kw)

    # 2) 각 시간프레임을 URL 파라미터로 직접 진입 → 드래그 로딩(필요 시) → CSV 내보내기
    for tf_short, tf_label, url_interval, requires_lazy in TIMEFRAMES:
        print(f"\n-- Timeframe: {tf_short} ({tf_label}) --")

        # 메뉴 클릭 대신 URL 파라미터로 안정적으로 진입
        go_chart(driver, symbol, interval=url_interval)
        time.sleep(2)

        # 일/시/10분 등 지연 로딩이 필요한 프레임에서 과거 데이터 끌어오기
        if requires_lazy:
            lazy_load_short_tf(driver, tf_short, tf_label)

        # CSV 내보내기
        export_csv(driver)

        # 저장 경로 구성 및 파일 이동/이름 변경
        tf_dir = out_root / symbol / tf_short
        ensure_dir(tf_dir)
        latest = wait_for_download(out_root)
        ts = time.strftime("%Y%m%d_%H%M%S")
        dest = tf_dir / f"{symbol}_{tf_short}_{ts}.csv"
        latest.replace(dest)
        print(f"[OK] Saved: {dest}")


def main():
    tickers = read_tickers()
    if not tickers:
        print("[ERROR] 종목 리스트가 비었습니다.")
        return

    ensure_dir(DOWNLOAD_ROOT)
    driver = setup_driver(DOWNLOAD_ROOT)

    try:
        # 쿠키 로그인 시도
        if not load_cookies(driver):
            manual_login(driver)

        # 로그인 확인용으로 GOOG 차트 한번 열기
        go_chart(driver, "GOOG")

        for sym in tickers:
            run_for_symbol(driver, sym, DOWNLOAD_ROOT)

        print("\n[ALL DONE] 모든 심볼 처리 완료.")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        save_cookies(driver)
        driver.quit()

def ensure_dialog_closed(driver, timeout=4):
    import time
    end = time.time() + timeout
    while time.time() < end:
        try:
            driver.find_element(By.XPATH, "//div[@role='dialog']")
            time.sleep(0.1)
        except Exception:
            return True
    return False

def focus_chart_canvas(driver):
    try:
        canvas = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'canvas[data-name="pane-top-canvas"]'))
        )
        ActionChains(driver).move_to_element_with_offset(canvas, 5, 5).click().perform()
        time.sleep(0.2)
        return True
    except Exception:
        return False

def open_indicators_dialog(driver, retries=2):
    ensure_dialog_closed(driver, timeout=4)
    for attempt in range(retries):
        focus_chart_canvas(driver)
        candidates = [
            "//*[@data-name='indicator-dialog' or @data-name='indicator-button' or @data-name='open-indicators-dialog']",
            "//button[contains(@aria-label,'Indicators') or contains(@aria-label,'Strategies')]",
            "//button[.//span[normalize-space()='Indicators' or contains(.,'지표') or contains(.,'전략')]]",
            "(//div[contains(@class,'toolbar') or contains(@id,'header')]//button[.//span[contains(.,'Indicators') or contains(.,'지표')]])[1]",
        ]
        for xp in candidates:
            try:
                el = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, xp)))
                try: el.click()
                except Exception: driver.execute_script("arguments[0].click();", el)
                WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']")))
                try:
                    tech_tab = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@role='dialog']//div[.//span[contains(.,'Technicals') or contains(.,'기술적')]]"))
                    )
                    driver.execute_script("arguments[0].click();", tech_tab)
                except Exception:
                    pass
                return True
            except Exception:
                continue
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys("/")
            WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']")))
            return True
        except Exception:
            time.sleep(0.5)
    return False



if __name__ == "__main__":
    main()
