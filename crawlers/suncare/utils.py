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

def get_product_detail_info(sb, goods_no: str) -> dict:
    url = f"https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={goods_no}"
    sb.uc_open_with_reconnect(url, reconnect_time=5)
    time.sleep(1)
    html = sb.driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 카테고리 추출
    try:
        category = soup.select_one("a.cate_y#midCatNm").text.strip()
    except Exception:
        category = ""

    # 총리뷰수
    try:
        review_info = soup.select_one("#repReview em")
        total_review = int(review_info.text.strip().replace("(", "").replace("건)", "").replace(",", ""))
    except Exception as e:
        print(f"총 리뷰수 파싱 실패: {e}")
        total_review = 0

    # 리뷰평점
    try:
        review_score = soup.select_one("#repReview b")
        review_score = float(review_score.text.strip())
    except Exception as e:
        print(f"리뷰평점 파싱 실패: {e}")
        review_score = None

    # 리뷰 분포 기본값
    pctOf5 = pctOf4 = pctOf3 = pctOf2 = pctOf1 = None
    review_detail = ""

    # 리뷰가 1건 이상 있을 때만 리뷰탭 클릭 및 분포 수집
    if total_review > 0:
        try:
            sb.click("a.goods_reputation")
            WebDriverWait(sb.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.graph_list span.per"))
            )
            percent_elements = sb.find_elements("css selector", "ul.graph_list span.per")
            percent_list = [el.text.strip() for el in percent_elements]
            if len(percent_list) == 5:
                pctOf5 = percent_list[0]
                pctOf4 = percent_list[1]
                pctOf3 = percent_list[2]
                pctOf2 = percent_list[3]
                pctOf1 = percent_list[4]

            # reviewDetail 정보
            review_detail = []
            polls = sb.find_elements("css selector", "dl.poll_type2.type3")
            for poll in polls:
                try:
                    title = poll.find_element("css selector", "span").text.strip()
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
                    print(f"리뷰 설문 수집 오류: {e}")
            review_detail = json.dumps(review_detail, ensure_ascii=False)

        except Exception as e:
            print("리뷰 정보 없음:", e)

    # === 상세스펙(구매정보) 추출 ===
    # 구매정보 탭 클릭
    try:
        sb.click("a.goods_buyinfo")
        time.sleep(1)  # ajax 로딩 대기
        html = sb.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
    except Exception as e:
        print("구매정보 탭 클릭 실패:", e)

    # === 한글 키 → 영어 키 매핑 ===
    title_map = {
        "용량": "capacity",
        "주요 사양": "detail",
        "모든 성분": "ingredient"
    }

    # 기본값 세팅
    detail_spec = {
        "capacity": "",
        "detail": "",
        "ingredient": ""
    }

    try:
        dl_tags = soup.select("div#artcInfo dl.detail_info_list")
        for dl in dl_tags:
            dt = dl.select_one("dt")
            dd = dl.select_one("dd")
            if dt and dd:
                dt_text = dt.text.strip()
                dd_text = dd.text.strip()

                for kr_title, en_key in title_map.items():
                    if kr_title in dt_text:
                        detail_spec[en_key] = dd_text
    except Exception as e:
        print(f"[상세 스펙 파싱 오류]: {e}")

    return {
        "category": category,
        "numOfReviews": total_review,
        "avgReview": review_score,
        "pctOf5": pctOf5,
        "pctOf4": pctOf4,
        "pctOf3": pctOf3,
        "pctOf2": pctOf2,
        "pctOf1": pctOf1,
        "reviewDetail": review_detail,
        **detail_spec,
    }


def get_product_reviews(sb, goods_no: str, max_pages: int = 0) -> list:
    url = f"https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={goods_no}"
    sb.uc_open_with_reconnect(url, reconnect_time=5)
    time.sleep(1)
    html = sb.driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 총리뷰수 확인
    try:
        review_info = soup.select_one("#repReview em")
        total_review = int(review_info.text.strip().replace("(", "").replace("건)", "").replace(",", ""))
    except Exception:
        total_review = 0

    review_list = []
    if total_review > 0:
        try:
            if sb.is_element_visible("a.goods_reputation"):
                sb.click("a.goods_reputation")
                WebDriverWait(sb.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.inner_list li"))
                )

                page_num = 1
                while True:
                    html = sb.driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    review_items = soup.select("ul.inner_list > li")
                    for review in review_items:
                        try:
                            user = review.select_one("p.info_user a.id").text.strip()
                        except Exception:
                            user = ""
                        try:
                            date = review.select_one("div.score_area span.date").text.strip()
                        except Exception:
                            date = ""
                        try:
                            point_text = review.select_one("div.score_area span.point").text
                            import re
                            m = re.search(r"(\d+)점만점에\s*(\d+)점", point_text)
                            star = m.group(2) if m else ""
                        except Exception:
                            star = ""
                        poll_titles = []
                        poll_values = []
                        try:
                            polls = review.select("div.poll_sample dl.poll_type1")
                            for poll in polls:
                                dt = poll.select_one("dt span")
                                dd = poll.select_one("dd span.txt")
                                poll_titles.append(dt.text.strip() if dt else "")
                                poll_values.append(dd.text.strip() if dd else "")
                        except Exception:
                            pass
                        try:
                            content = review.select_one("div.txt_inner").text.strip()
                        except Exception:
                            content = ""

                        review_dict = {
                            "goodsNo": goods_no,
                            "userId": user,
                            "reviewDate": date,
                            "star": star,
                            "reviewText": content,
                        }
                        for idx, (title, value) in enumerate(zip(poll_titles, poll_values), 1):
                            review_dict[f"criteria{idx}"] = title
                            review_dict[f"criteria{idx}_value"] = value

                        review_list.append(review_dict)

                    # 페이지네이션 처리
                    pageing = soup.select_one("div.pageing")
                    if not pageing:
                        break

                    # 다음 페이지 버튼 찾기
                    next_page = None
                    for a in pageing.select("a[data-page-no]"):
                        if a.text.strip() == str(page_num + 1):
                            next_page = a
                            break

                    # max_pages 지정 시 제한
                    if max_pages and page_num >= max_pages:
                        break

                    if next_page:
                        # Selenium에서 해당 페이지 버튼 클릭
                        try:
                            sb.click(f'div.pageing a[data-page-no="{page_num + 1}"]')
                            WebDriverWait(sb.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.inner_list li"))
                            )
                            page_num += 1
                            time.sleep(0.7)
                        except Exception as e:
                            print(f"{page_num+1}페이지 이동 실패:", e)
                            break
                    else:
                        break
        except Exception as e:
            print("리뷰 정보 파싱 실패:", e)

    return review_list
