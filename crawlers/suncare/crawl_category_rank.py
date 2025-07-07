from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import datetime
from seleniumbase import SB
from bs4 import BeautifulSoup
import json

# 카테고리별 URL 
CATEGORY_URLS = {
    "skincare": "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010001&pageIdx=1&rowsPerPage=8",
    "cleansing": "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010010&pageIdx=1&rowsPerPage=8",
    "suncare": "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010011&pageIdx=1&rowsPerPage=8",
    "manscare": "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010007&pageIdx=1&rowsPerPage=8",
    "food": "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000020005&pageIdx=1&rowsPerPage=8"
}

# 범용 카테고리 크롤링 함수
def get_category_top100(category_name: str) -> list:
    url = CATEGORY_URLS.get(category_name)
    if not url:
        raise ValueError(f"카테고리 '{category_name}'에 해당하는 URL이 없습니다.")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless') 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )

    # 올리브영 선케어 랭킹 페이지 열기
    url = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010011&pageIdx=1&rowsPerPage=8"
    driver.get(url)

    # 페이지 로딩 대기
    time.sleep(2.5)

    data = []
    items = driver.find_elements(
        By.CSS_SELECTOR, "div.TabsConts.on ul.cate_prd_list li"
    )
    rank = 1
    
    # 타임스탬프 생성
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in items:
        try:
            # 순위 (.thumb_flag 요소가 없는 경우 대비)
            try:
                rank_tag = item.find_element(By.CSS_SELECTOR, ".thumb_flag")
                if rank_tag.text.strip().isdigit():
                    rank_val = int(rank_tag.text.strip())
                    rank = rank_val
                else:
                    rank_val = rank
            except Exception:
                rank_val = rank

            try:
                # 브랜드
                brand = item.find_element(By.CSS_SELECTOR, ".tx_brand").text.strip()
                # 제품명
                name = item.find_element(By.CSS_SELECTOR, ".tx_name").text.strip()
                # 제품 코드 (goodsNo)
                try:
                    a_tag = item.find_element(By.CSS_SELECTOR, "a[data-ref-goodsno]")
                    goods_no = a_tag.get_attribute("data-ref-goodsno")
                except Exception:
                    goods_no = ""
                # 정가 (null 허용)
                try:
                    price_original = item.find_element(
                        By.CSS_SELECTOR, ".prd_price .tx_org .tx_num"
                    ).text.strip()
                except Exception:
                    price_original = ""
                # 구매가격
                try:
                    price_final = item.find_element(
                        By.CSS_SELECTOR, ".prd_price .tx_cur .tx_num"
                    ).text.strip()
                except Exception as e:
                    print(f"구매가격 정보 파싱 실패: {e}")
                    price_final = ""
                # 기타 프로모션 정보(null 허용)
                try:
                    flag_spans = item.find_elements(By.CSS_SELECTOR, ".prd_flag .icon_flag")
                    flag_list = [
                        span.text.strip() for span in flag_spans if span.text.strip()
                    ]
                    flag_str = ",".join(flag_list) if flag_list else ""
                except Exception:
                    flag_str = ""
            except Exception as e:
                print(f"제품 정보 파싱 실패: {e}")
                continue

            # 올리브영 PB 브랜드 여부 확인
            pb_brands = [
                "바이오힐 보", "브링그린", "웨이크메이크", "컬러그램", "필리밀리",
                "아이디얼포맨", "라운드어라운드", "식물나라", "케어플러스", "탄탄", "딜라이트 프로젝트",
            ]
            is_pb = 1 if brand in pb_brands else 0

            # 일시품절 여부 확인
            try:
                soldout_flag = item.find_element(By.CSS_SELECTOR, "span.status_flag.soldout")
                is_soldout = soldout_flag.is_displayed()
            except Exception:
                is_soldout = False

            data.append(
                {
                    "rank": rank_val,
                    "brandName": brand,
                    "isPB": is_pb,
                    "goodsName": name,
                    "salePrice": price_final,
                    "originalPrice": price_original,
                    "flagList": flag_str,
                    "goodsNo": goods_no,
                    "createdAt": collected_at,
                    "isSoldout": bool(is_soldout)
                }
            )
            rank += 1

        except Exception as e:
            print(f"제품 정보 파싱 실패: {e}")
            continue

    driver.quit()

    return data


