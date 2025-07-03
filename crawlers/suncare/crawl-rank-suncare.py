import pandas as pd
from bs4 import BeautifulSoup
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Selenium 드라이버 설정 
def get_driver():
    options = Options()
    # 옵션 설정 (headless 제거 권장, 필요시 주석 해제)
    # options.add_argument("--headless")  
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)

    # 셀레니움 탐지 우회 설정
    stealth(driver,
        languages=["ko-KR", "ko"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        run_on_insecure_origins=False
    )
    return driver

# 선케어 카테고리 url
base_url = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010011&pageIdx=1&rowsPerPage=8&t_page=%EB%9E%AD%ED%82%B9&t_click=%ED%8C%90%EB%A7%A4%EB%9E%AD%ED%82%B9_%EC%84%A0%EC%BC%80%EC%96%B4"

def extract_product_info(base_url, limit=100):
    pbBrand = {'바이힐보', '브링그린', '웨이크메이크', '컬러그램', '필리밀리', '아이디얼포맨', 
        '라운드어라운드', '식물나라', '케어플러스', '탄탄', '딜라이트 프로젝트'}
    
    driver = get_driver()
    driver.get(base_url)

    # 상품 목록 로딩 대기
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.TabsConts.on ul.cate_prd_list li'))
        )
    except Exception as e:
        print("상품 목록 로딩 실패. HTML 일부 출력")
        print(driver.page_source[:500])
        driver.quit()
        raise e

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    items = soup.select('div.TabsConts.on ul.cate_prd_list li')

    result_list = []
    rank_num = 0

    for item in items[:limit]:
        try:
            # 기본 정보 추출
            rank_tag = item.select('span.thumb_flag.best')
            if rank_tag:
                rank = int(rank_tag[0].text.strip())
            else:
                rank_num += 1
                rank = rank_num
            is_special = not bool(rank_tag)

            brandName = item.select_one('span.tx_brand').text.strip()
            isPb = 1 if brandName in pbBrand else 0
            goodsName = item.select_one('p.tx_name').text.strip()
            salePrice = item.select_one('p.prd_price > span.tx_cur > span.tx_num').text.strip()
            org_tag = item.select('p.prd_price > span.tx_org > span.tx_num')
            originalPrice = org_tag[0].text.strip() if org_tag else salePrice

            flag_tags = item.select('p.prd_flag > span.icon_flag')
            flagList = [tag.text.strip() for tag in flag_tags] if flag_tags else []
            if is_special:
                flagList.append('오특')

            soldout_tag = item.select_one('span.status_flag.soldout')
            isSoldout = 1 if soldout_tag and "품절" in soldout_tag.text.strip() else 0

            data = {
                'rank': rank,
                'brandName': brandName,
                'isPb': isPb,
                'goodsName': goodsName,
                'salePrice': salePrice,
                'originalPrice': originalPrice,
                'flagList': flagList,
                'isSoldout': isSoldout
            }
            
            result_list.append(data)

        except Exception as e:
            print(f"[기본/상세 정보 수집 실패] {e}")
            continue
    
    # 데이터 프레임 & 저장
    df = pd.DataFrame(result_list)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df['createdAt'] = now_str
    df['updatedAt'] = now_str

    # CSV 저장
    file_name = f"crawler_suncare_{now_str[:10]}.csv"
    df.to_csv(file_name, index=False, encoding='utf-8-sig')
    print(f"전체 상품 정보 수집 및 저장 완료! → {file_name}")

    driver.quit()

    return df

# 3개만 테스트 저장
extract_product_info(base_url, limit=3)
