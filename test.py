from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import time

# 상품 상세 주소 리스트화

def crawl_product_info() :
    url = "https://www.oliveyoung.co.kr/store/display/getBrandShopDetail.do?onlBrndCd=A001643&t_page=%EC%83%81%ED%92%88%EC%83%81%EC%84%B8&t_click=%EB%B8%8C%EB%9E%9C%EB%93%9C%EA%B4%80_%EC%83%81%EB%8B%A8&t_brand_name=%EC%95%84%EC%9D%B4%EB%94%94%EC%96%BC%ED%8F%AC%EB%A7%A8"

    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    time.sleep(2)  # JS 렌더링 대기

    # totCnt span 추출
    totcnt = driver.find_element(By.ID, 'totCnt')
    totcnt = totcnt.text.strip()
    print("총 상품 수:", totcnt)

    # 주소 추출
    li_elements = driver.find_elements(By.CSS_SELECTOR, 'li[data-goods-idx]')
    try:
        li = driver.find_element(By.CSS_SELECTOR, 'li[data-goods-idx]')

        # 링크
        product_link = li.find_elements(By.CSS_SELECTOR, 'a')
        product_link = product_link[0].get_attribute('href') if product_link else 'N/A'

        print("✅ 주소 :", product_link)

    except:
        print("❌ 상품 정보 추출 실패")

    driver.quit()
    # 제품 상세 페이지 주소 리스트화
    parsed = urlparse(product_link)
    query = parse_qs(parsed.query)
    url_list = []
    for i in range(1, int(totcnt) + 1):
        query['t_number'] = [str(i)]
        new_query = urlencode(query, doseq=True)
        new_url = urlunparse(parsed._replace(query=new_query))
        url_list.append(new_url)
    return url_list

def crawl_product_detail(list) :
    return

url_list = crawl_product_info()
