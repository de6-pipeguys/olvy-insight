from django.db.models.expressions import result
from seleniumbase import SB
from bs4 import BeautifulSoup
from time import sleep
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

url = "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000222773&dispCatNo=9000002&trackingCd=BrandA001643_PROD&t_page=%EB%B8%8C%EB%9E%9C%EB%93%9C%EA%B4%80&t_click=%EC%A0%84%EC%B2%B4%EC%83%81%ED%92%88_%EC%A0%84%EC%B2%B4_%EC%83%81%ED%92%88%EC%83%81%EC%84%B8&t_number=2"

product_data = []

with SB(uc=True, test=True) as sb:
    sb.uc_open_with_reconnect(url, reconnect_time=60)

    html = sb.driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    try:
        # 브랜드 명
        brand_name = sb.get_text("#moveBrandShop")
        print("브랜드명 :", brand_name)

        # 제품명
        product_name = sb.get_text("p.prd_name")
        print("상품명 :", product_name)

        # 할인가
        discount_price = sb.get_text("span.price-2 strong")
        print("할인가 :", discount_price)

        # 정가
        if sb.is_element_present("span.price-1 strike"):
            origin_price = sb.get_text("span.price-1 strike")
            print("정가:", origin_price)
        else:
            origin_price = discount_price
            print("정가 -> 할인가 대체:", origin_price)

        # 세일플래그
        flags = []
        span_elements = sb.find_elements("css selector", "p#icon_area span")
        for span in span_elements:
            flags.append(span.text.strip())

        print("상품 플래그 리스트:", flags)

    except Exception as e:
        print("기본 정보 수집 실패:", e)

    # 구매정보 클릭
    try:
        sb.click("a.goods_buyinfo")
        sleep(2)
        print("구매정보 탭 클릭 완료")

        # 전체 <dl> 리스트 가져오기
        dl_elements = sb.find_elements("css selector", "dl.detail_info_list")

        # 가져올 인덱스 (1, 2, 7번째 → 파이썬 기준: 0, 1, 6)
        target_indices = [1, 2, 7]
        target_fields = ['capacity', 'detail', 'ingredients']  # 원하는 이름으로 바꾸세요

        result = {}

        for idx, field in zip(target_indices, target_fields):
            try:
                dd = dl_elements[idx].find_element("css selector", "dd").text.strip()
                result[field] = dd
            except Exception as e:
                result[field] = None  # 값이 없을 경우 None 처리

        print(result)
    except Exception as e:
        print("구매정보 탭 클릭 실패:", e)

    # 리뷰정보 클릭 및 수집
    try:
        sb.click("a.goods_reputation")
        sleep(2)
        print("리뷰 정보 탭 클릭 완료")
        # 리뷰정리
        totalComment = sb.get_text("div.grade_img em")
        # 리뷰갯수
        numOfReviews = sb.get_text("div.star_area em")
        # 리뷰 평점
        avgReview = sb.get_text("div.star_area strong")
        # 리뷰 점수 퍼센트
        percent_elements = sb.find_elements("css selector", "ul.graph_list span.per")
        percent_list = [el.text.strip() for el in percent_elements]
        pctOf5 = percent_list[0]
        pctOf4 = percent_list[1]
        pctOf3 = percent_list[2]
        pctOf2 = percent_list[3]
        pctOf1 = percent_list[4]
    except Exception as e:
        print("리뷰 정보 탭 클릭 완료:", e)

    # 리뷰 정보
    polls = sb.find_elements("css selector", "dl.poll_type2.type3")
    review_detail = []
    for poll in polls:
        try:
            # 설문 제목 (예: 피부타입)
            title = poll.find_element("css selector", "span").text.strip()
            # 하위 항목들 (li)
            li_tags = poll.find_elements("css selector", "ul.list > li")
            for li in li_tags:
                label = li.find_element("css selector", "span.txt").text.strip()
                percent = li.find_element("css selector", "em.per").text.strip()
                review_detail.append({
                    "type": title,
                    "value": label,
                    "gauge": percent
                })
        except Exception as e:
            print("오류:", e)
    # 저장
    product_info = {
        "brand": brand_name,  # 브랜드명
        "product": product_name,  # 상품이름
        "discountPrice": discount_price,  # 할인가
        "originPrice": origin_price,  # 정가
        "isPB": 1,  # Pb여부
        "flag": flags, # 혜택
        "totalcoment" : totalComment,
        "numOfReviews" : numOfReviews,
        "avgReview" : avgReview,
        "pctOf5" : pctOf5,
        "pctOf4" : pctOf4,
        "pctOf3" : pctOf3,
        "pctOf2" : pctOf2,
        "pctOf1" : pctOf1,
        "capacity" : result['capacity'],
        "detail" : result['detail'],
        "ingredients" : result['ingredients'],
        "review_detail" : review_detail
    }
    product_data.append(product_info)
# 결과 출력
from pprint import pprint
pprint(product_data)
