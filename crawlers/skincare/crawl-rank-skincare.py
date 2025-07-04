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


def get_top100_skincare() -> dict:
    chrome_options = Options()
    chrome_options.add_argument('--headless') 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )

    # 올리브영 스킨케어 랭킹 페이지 열기
    url = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010001&pageIdx=1&rowsPerPage=8&t_page=%EB%9E%AD%ED%82%B9&t_click=%ED%8C%90%EB%A7%A4%EB%9E%AD%ED%82%B9_%EC%8A%A4%ED%82%A8%EC%BC%80%EC%96%B4"
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

    # return pd.DataFrame(data)
    return data


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

    # 용량, 주요사양, 성분 추출
    def get_detail_info(soup, title):
        try:
            dl_tags = soup.select("div#artcInfo dl.detail_info_list")
            for dl in dl_tags:
                dt = dl.select_one("dt")
                dd = dl.select_one("dd")
                if dt and dd:
                    dt_text = dt.text.strip()
                    dd_text = dd.text.strip()
                    if title in dt_text:
                        return dd_text
        except Exception as e:
            print(f"상세 정보 파싱 실패 ({title}): {e}")
        return ""

    # 상세스펙 정보 추출
    detail_spec = {}
    spec_titles = ["용량", "주요 사양", "성분"]
    for title in spec_titles:
        detail_spec[title] = get_detail_info(soup, title)

    return {
        "category": category,
        "numOfReviews": total_review,
        "avgReview": review_score,
        "pctOf5": pctOf5,
        "pctOf4": pctOf4,
        "pctOf3": pctOf3,
        "pctOf2": pctOf2,
        "pctOf1": pctOf1,
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


##### 실행 코드 #####
# df = get_top100_skincare()

# with SB(uc=True, test=True) as sb:
#     detail_list = []
#     for goods_no in df['goodsNo']:
#         detail = get_product_detail_info(sb, goods_no)
#         detail_list.append(detail)

# detail_df = pd.DataFrame(detail_list)
# result_df = pd.concat([df.reset_index(drop=True), detail_df.reset_index(drop=True)], axis=1)

# result_df.to_json('skincare_result.json', orient='records', force_ascii=False, indent=2)

