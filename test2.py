from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import time

url = "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000222773&dispCatNo=9000002&trackingCd=BrandA001643_PROD&t_page=%EB%B8%8C%EB%9E%9C%EB%93%9C%EA%B4%80&t_click=%EC%A0%84%EC%B2%B4%EC%83%81%ED%92%88_%EC%A0%84%EC%B2%B4_%EC%83%81%ED%92%88%EC%83%81%EC%84%B8&t_number=2"

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(url)

time.sleep(3)  # JS 렌더링 대기

# id가 moveBrandShop인 요소에서 텍스트 추출
# 상품 기본 정보 가져오기
try:
    # 브랜드 명
    brand_elem = driver.find_element(By.ID, 'moveBrandShop')
    brand_name = brand_elem.text.strip()
    print("브랜드명 :", brand_name)

    # 제품명
    product_elem = driver.find_element(By.CSS_SELECTOR, 'p.prd_name')
    product_name = product_elem.text.strip()
    print("상품명 :", product_name)

    # 할인가
    discount_elem = driver.find_element(By.CSS_SELECTOR, 'span.price-2 strong')
    discount_price = discount_elem.text.strip()
    print("할인가 :", discount_price)

    # 정가
    origin_elem = driver.find_element(By.CSS_SELECTOR, 'span.price-1 strike')
    origint_price = origin_elem.text.strip()
    print("정가 :", origint_price)

except:
    print(" 가져올 수 없습니다 .")

# 구매정보 가져오기
try:
    buy_info_tab = driver.find_element(By.CSS_SELECTOR, 'a.goods_buyinfo')
    buy_info_tab.click()
except:
    print("구매정보 가져오기 실패")

# 리뷰정보 가져오기

driver.quit()