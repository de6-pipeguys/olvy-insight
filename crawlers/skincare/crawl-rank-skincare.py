from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import datetime


def get_top100_skincare() -> pd.DataFrame:
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # 브라우저 창 없이 실행하려면 주석 해제
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 드라이버 실행
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # 올리브영 스킨케어 랭킹 페이지 열기
    url = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010001&pageIdx=1&rowsPerPage=8&t_page=%EB%9E%AD%ED%82%B9&t_click=%ED%8C%90%EB%A7%A4%EB%9E%AD%ED%82%B9_%EC%8A%A4%ED%82%A8%EC%BC%80%EC%96%B4"
    driver.get(url)

    # 페이지 로딩 대기
    time.sleep(2.5)

    # 랭킹 정보 가져오기
    data = []
    items = driver.find_elements(
        By.CSS_SELECTOR, "div.TabsConts.on ul.cate_prd_list li"
    )
    rank = 1
    # 타임스탬프 생성
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in items:
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
            "바이오힐 보",
            "브링그린",
            "웨이크메이크",
            "컬러그램",
            "필리밀리",
            "아이디얼포맨",
            "라운드어라운드",
            "식물나라",
            "케어플러스",
            "탄탄",
            "딜라이트 프로젝트",
        ]
        is_pb = 1 if brand in pb_brands else 0

        data.append(
            {
                "rank": rank_val,
                "brandName": brand,
                "isPB": is_pb,
                "goodsName": name,
                "finalPrice": price_final,
                "originalPrice": price_original,
                "flagList": flag_str,
                "goodsNo": goods_no,
                "createdAt": collected_at,
            }
        )
        rank += 1

    # 드라이버 종료 (테스트용, 실제 크롤링 작업 후에 종료)
    driver.quit()
    return pd.DataFrame(data)


def get_product_detail_info(goods_no: str) -> dict:
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # 브라우저 창 없이 실행하려면 주석 해제
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 드라이버 실행
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )

    url = f"https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={goods_no}"
    driver.get(url)
    time.sleep(5.5)

    # 총리뷰수
    try:
        review_info = driver.find_element(By.CSS_SELECTOR, "#repReview em").text.strip()
        total_review = int(
            review_info.replace("(", "").replace("건)", "").replace(",", "")
        )
    except Exception as e:
        print(f"총 리뷰수 파싱 실패: {e}")
        total_review = None

    # 리뷰평점
    try:
        review_score = driver.find_element(By.CSS_SELECTOR, "#repReview b").text.strip()
        review_score = float(review_score)
    except Exception as e:
        print(f"리뷰평점 파싱 실패: {e}")
        review_score = None

    # 일시품절 여부
    try:
        btn_area = driver.find_element(By.CSS_SELECTOR, "div.prd_btn_area.new-style.type1")
        soldout_btns = btn_area.find_elements(By.CSS_SELECTOR, "button.btnSoldout")
        is_soldout = False
        for btn in soldout_btns:
            if btn.is_displayed() and "일시품절" in btn.text:
                is_soldout = True
                break
    except Exception as e:
        print(f"일시품절 여부 파싱 실패: {e}")
        is_soldout = False


    # # 리뷰 분포 
    # pctOf5, pctOf4, pctOf3, pctOf2, pctOf1 = None, None, None, None, None
    # try:
    #     # 리뷰 탭 클릭
    #     review_tab = driver.find_element(By.CSS_SELECTOR, "a.goods_reputation[data-attr*='리뷰']")
    #     review_tab.click()
    #     time.sleep(1.5)  # 탭 전환 대기

    #     # 리뷰 분포 추출
    #     percent_elements = driver.find_elements(By.CSS_SELECTOR, "ul.graph_list span.per")
    #     percent_list = [int(el.text.strip().replace("%", "")) for el in percent_elements]
    #     if len(percent_list) == 5:
    #         pctOf5, pctOf4, pctOf3, pctOf2, pctOf1 = percent_list

    # except Exception as e:
    #     print(f"리뷰 분포 파싱 실패: {e}")

    driver.quit()

    return {
        "numOfReviews": total_review,
        "avgReview": review_score,
        "isSoldout": bool(is_soldout),
        # "pctOf5": pctOf5,
        # "pctOf4": pctOf4,
        # "pctOf3": pctOf3,
        # "pctOf2": pctOf2,
        # "pctOf1": pctOf1,
    }

