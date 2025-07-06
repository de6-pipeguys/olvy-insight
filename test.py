from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = "https://www.oliveyoung.co.kr/store/display/getBrandShopDetail.do?onlBrndCd=A001643"
driver.get(url)

# 첫 페이지 상품 수 확인
time.sleep(2)
first_page_items = driver.find_elements(By.CSS_SELECTOR, 'li[data-goods-idx]')
print(f"✅ 1페이지 상품 수: {len(first_page_items)}")

# 2번 페이지 버튼 클릭 (send_keys 방식)
try:
    page_2_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-page-no="2"]'))
    )
    page_2_btn.send_keys('\n')
    page_2_btn.send_keys('\n')
    print("✅ 2페이지 버튼 엔터 입력 완료")
except Exception as e:
    print(f"❌ 2페이지 버튼 클릭 실패: {e}")

# 페이지 전환 대기
time.sleep(3)

# 두 번째 페이지 상품 수 다시 확인
second_page_items = driver.find_elements(By.CSS_SELECTOR, 'li[data-goods-idx]')
print(f"✅ 2페이지 이후 상품 수: {len(second_page_items)}")

input("👉 엔터를 누르면 브라우저를 닫습니다.")
driver.quit()
