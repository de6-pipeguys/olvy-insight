import time
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from seleniumbase import SB

# 공통 드라이버
def get_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
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


# 상품 리스트 수집
def get_product_list():
    # 클렌징 카테고리 url
    base_url = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010011&pageIdx=1&rowsPerPage=8"
    
    driver = get_driver()
    driver.get(base_url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.TabsConts.on ul.cate_prd_list li'))
    )
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    items = soup.select('div.TabsConts.on ul.cate_prd_list li')
    driver.quit()
    return items


# 기본 정보 추출
def extract_rank_info(item, rank_num):
    
    pbBrand = {'바이힐보', '브링그린', '웨이크메이크', '컬러그램', '필리밀리', '아이디얼포맨',
        '라운드어라운드', '식물나라', '케어플러스', '탄탄', '딜라이트 프로젝트'}
    
    rank_tag = item.select('span.thumb_flag.best')
    rank = int(rank_tag[0].text.strip()) if rank_tag else rank_num + 1
    is_special = False if rank_tag else True

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
    isSoldout = 1 if soldout_tag else 0

    link_tag = item.select_one('a.prd_thumb')
    goodsUrl = link_tag['href'] if link_tag else None


    return {
        'rank': rank, 'brandName': brandName, 'isPb': isPb, 'goodsName': goodsName,
        'salePrice': salePrice, 'originalPrice': originalPrice,
        'flagList': flagList, 'isSoldout': isSoldout, 'goodsUrl': goodsUrl
    }


# 상세정보 추출: SB로 탭 진입 및 리뷰/구매정보 수집
def extract_detail_info(goods_url, sb):
    detail_data = {
        'totalComment': None, 'numOfReviews': None, 'avgReview': None,
        'pctOf5': 0, 'pctOf4': 0, 'pctOf3': 0, 'pctOf2': 0, 'pctOf1': 0,
        'capacity': "N/A", 'detail': "N/A", 'ingredient': "N/A"
    }

    try:
        sb.uc_open_with_reconnect(goods_url, reconnect_time=60)

        # 리뷰 탭 클릭 및 정보 수집
        try:
            sb.click("li#reviewInfo a.goods_reputation")
            sb.sleep(1.5)  
            html = sb.driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            detail_data['totalComment'] = soup.select_one('p.img_face > em').get_text(strip=True) if soup.select_one('p.img_face > em') else "0"
            detail_data['numOfReviews'] = soup.select_one('p.total > em').get_text(strip=True) if soup.select_one('p.total > em') else "0"

            avg_tag = soup.select_one('p.num > strong')
            detail_data['avgReview'] = float(avg_tag.get_text(strip=True)) if avg_tag else 0.0

            for i, li in enumerate(soup.select('ul.graph_list > li > span.per')):
                detail_data[f'pctOf{5 - i}'] = int(li.text.replace('%', '').strip())
        except Exception as e:
            print(f"[리뷰 탭 오류] {goods_url} - {e}")

        # 구매정보 탭 클릭 및 파싱
        try:
            sb.click("a.goods_buyinfo")
            sb.sleep(1.5)
            sb.wait_for_element("dl.detail_info_list", timeout=10)

            dl_elements = sb.driver.find_elements(By.CSS_SELECTOR, "dl.detail_info_list")
            for dl in dl_elements:
                try:
                    dt = dl.find_element(By.CSS_SELECTOR, "dt").text.strip()
                    dd = dl.find_element(By.CSS_SELECTOR, "dd").text.strip()
                    if "용량" in dt or "중량" in dt:
                        detail_data['capacity'] = dd
                    elif "주요 사양" in dt:
                        detail_data['detail'] = dd
                    elif "모든 성분" in dt:
                        detail_data['ingredient'] = dd
                except:
                    continue

        except Exception as e:
            print(f"[구매정보 탭 오류] {goods_url} - {e}")

    except Exception as e:
        print(f"[상세 진입 실패] {goods_url} - {e}")

    return detail_data

# 전체 실행
def main():
    items = get_product_list()
    print(f"✅ 총 {len(items)}개 상품 수집됨")

    basic_list = []
    rank_num = 0
    for item in items:  # 테스트시 범위 지정
        basic = extract_rank_info(item, rank_num)
        rank_num = basic.get('rank', rank_num + 1)
        basic_list.append(basic)

    result = []
    with SB(uc=True, test=False) as sb:
        for basic in basic_list:
            print(f"[{basic['rank']}위] {basic['goodsName']} 상세정보 수집 중...")
            detail = extract_detail_info(basic['goodsUrl'], sb)
            basic.update(detail)
            del basic["goodsUrl"]
            result.append(basic)

    df = pd.DataFrame(result)
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    df['createdAt'] = now_str
    df['updatedAt'] = now_str
    df.to_csv(f"crawl_suncare_{now_str}.csv", index=False)
    print("✅ 전체 저장 완료!")
    return df

# 실행
if __name__ == "__main__":
    df = main()
    
