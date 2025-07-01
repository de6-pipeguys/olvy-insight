import pandas as pd

# AWS S3
import boto3
import io

# BeautifulSoup
import requests
from bs4 import BeautifulSoup

# selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

headers_info = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.oliveyoung.co.kr/store/main/main.do'
    }

# 1. 스킨케어 랭킹 페이지 크롤링 (랭킹, 제품명)
def get_ranking_skincare(headers) -> pd.DataFrame:
    base_url = "https://www.oliveyoung.co.kr/store/main/getBestList.do"
    params = {
        "dispCatNo": "900000100100001",
        "fltDispCatNo": "10000010001",
        "pageIdx": "1",
        "rowsPerPage": "8",
        "t_page": "%EB%9E%AD%ED%82%B9",
        "t_click": "%ED%8C%90%EB%A7%A4%EB%9E%AD%ED%82%B9_%EC%8A%A4%ED%82%B8%EC%BC%80%EC%96%B4"
    }

    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        product_items = soup.select('div.TabsConts.on ul.cate_prd_list li')

        if not product_items:
            print("경고: 페이지에서 제품 항목을 찾을 수 없습니다. 선택 항목이나 페이지 내용을 확인하세요.")
            print("HTML content head for debugging:")
            print(str(soup)[:1000])
            return None

        ranking_data = []

        for item in product_items:
            product_info = {}
            # 랭킹
            rank_element = item.select_one('.thumb_flag')
            product_info['랭킹'] = rank_element.text.strip() if rank_element else 'N/A'
            # 제품명
            name_element = item.select_one('.tx_name')
            product_info['제품명'] = name_element.text.strip() if name_element else 'N/A'
            # 제품코드와 카테고리코드 추출
            a_tag = item.select_one('a[data-ref-goodsno][data-ref-dispcatno]')
            product_info['제품코드'] = a_tag['data-ref-goodsno'] if a_tag and a_tag.has_attr('data-ref-goodsno') else 'N/A'
            product_info['카테고리코드'] = a_tag['data-ref-dispcatno'] if a_tag and a_tag.has_attr('data-ref-dispcatno') else 'N/A'
            ranking_data.append(product_info)

        # 리스트를 DataFrame으로 변환해서 반환
        return pd.DataFrame(ranking_data)

    # 네트워크 요청 실패
    except requests.exceptions.RequestException as e:
        print(f"웹 페이지 요청 실패: {e}")
        return None
    # 위에서 잡지 못한 모든 종류의 예외
    except Exception as e:
        print(f"데이터 파싱 오류: {e}")
        return None


# 2. get_ranking_skincare 함수에서 반환한 DataFrame 인자로 받음
# 상세페이지 URL 리스트를 반환
# 생성된 리스트 갯수 로그찍기(상세 페이지 url 13개 생성했습니다)
def to_product_page(df) -> list:
    base_url = "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo="
    # 제품코드 컬럼이 있는 경우만 처리
    if "제품코드" not in df.columns:
        print("DataFrame에 '제품코드' 컬럼이 없습니다.")
        return []
    # 각 제품코드에 대해 url 생성
    url_list = [base_url + str(code) for code in df["제품코드"] if code != "N/A"]
    return url_list


# 3. to_product_page에서 생성한 url을 갖고 상세정보 페이지 크롤링
def extract_product(product_url, headers) -> pd.DataFrame:
    try:
        response = requests.get(product_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 제품명
        product_name = soup.find("p", class_="prd_name")
        product_name = product_name.get_text(strip=True) if product_name else "N/A"

        # 제조사
        manufacturer = soup.find("a", class_="pd_arrow_link")
        manufacturer = manufacturer.get_text(strip=True) if manufacturer else "N/A"

        # 판매가격
        price_tag = soup.find("span", class_="price-2")
        price_tag = price_tag.find("strong").get_text(strip=True) if price_tag else "N/A"

        # 리뷰 정보
        review_info = soup.find("p", id="repReview")
        review_count = review_info.find("em").get_text(strip=True) if review_info and review_info.find("em") else "N/A"
        review_score = review_info.find("b").get_text(strip=True) if review_info and review_info.find("b") else "N/A"

        # 딕셔너리로 정리
        product_dict = {
            "제품명": product_name,
            "제조사": manufacturer,
            "판매가격": price_tag,
            "리뷰수": review_count,
            "평점": review_score,
            "상세페이지": product_url
        }

        # DataFrame으로 변환해서 반환
        return pd.DataFrame([product_dict])

    except requests.exceptions.RequestException as e:
        print(f"웹 페이지 요청 실패: {e}")
        return None
    except Exception as e:
        print(f"데이터 파싱 오류: {e}")
        return None
    

# 4. 상세 정보 크롤링
# 기능 추가 예정 : s3에 적재되어있는 제품인지 확인하고 이미 적재되어 있다면 크롤링하지 않음
def extract_product_detail(product_url) -> pd.DataFrame:
    from urllib.parse import urlparse, parse_qs

    # User-Agent 설정
    chrome_options = Options()
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options) as driver:
        driver.get(product_url)
        time.sleep(3)  # 첫 페이지 로딩 대기

        # 구매정보 탭 클릭
        try:
            buyinfo_tab = driver.find_element(By.CSS_SELECTOR, 'a.goods_buyinfo')
            buyinfo_tab.click()
            # AJAX 로딩 대기: detail_info_list가 나올 때까지 최대 5초 대기
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div#artcInfo dl.detail_info_list'))
            )
        except Exception as e:
            print("구매정보 탭 클릭 또는 로딩 실패:", e)
            return None

        # 구매정보 영역 파싱
        try:
            artc_info = driver.find_element(By.ID, 'artcInfo')
            dls = artc_info.find_elements(By.CSS_SELECTOR, 'dl.detail_info_list')

            capacity = "N/A"
            spec = "N/A"
            ingredient = "N/A"

            for dl in dls:
                dt_tags = dl.find_elements(By.TAG_NAME, 'dt')
                dd_tags = dl.find_elements(By.TAG_NAME, 'dd')
                if not dt_tags or not dd_tags:
                    continue
                dt_text = dt_tags[0].text.strip()
                dd_text = dd_tags[0].text.strip()
                if "용량" in dt_text or "중량" in dt_text:
                    capacity = dd_text
                elif "주요 사양" in dt_text:
                    spec = dd_text
                elif "화장품법에 따라 기재해야 하는 모든 성분" in dt_text:
                    ingredient = dd_text

            parsed = urlparse(product_url)
            goods_no = parse_qs(parsed.query).get('goodsNo', ['N/A'])[0]

            detail_dict = {
                "goodsNo": goods_no,
                "용량": capacity,
                "제품 주요 사양": spec,
                "성분": ingredient
            }
            # DataFrame으로 변환해서 반환
            return pd.DataFrame([detail_dict])

        except Exception as e:
            print("구매정보 영역 파싱 실패:", e)
            return None


# 5-1. DataFrame을 CSV로 S3에 저장
def upload_df_to_s3_csv(df, bucket, key, aws_access_key_id, aws_secret_access_key, region):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    s3 = boto3.client('s3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name=region)
    s3.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue())


# 5-2. DataFrame을 Parquet으로 S3에 저장
def upload_df_to_s3_parquet(df, bucket, key, aws_access_key_id, aws_secret_access_key, region):
    parquet_buffer = io.BytesIO()
    df.to_parquet(parquet_buffer, index=False)
    s3 = boto3.client('s3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name=region)
    s3.put_object(Bucket=bucket, Key=key, Body=parquet_buffer.getvalue())


