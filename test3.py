from seleniumbase import SB
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time


def get_brand(brand_code) -> pd.DataFrame:
    url = f"https://www.oliveyoung.co.kr/store/display/getBrandShopDetail.do?onlBrndCd={brand_code}"
    data = []
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with SB(uc=True, test=True, headless=True) as sb:
        sb.uc_open_with_reconnect(url, reconnect_time=20)
        time.sleep(2)

        page = 1
        while True:
            if page > 1:
                try:
                    # 페이지네이션 버튼 클릭 (페이지가 없으면 break)
                    sb.click(f"div.pageing a[data-page-no='{page}']")
                    time.sleep(2)  # ajax 로딩 대기
                except Exception as e:
                    print(f"{page}페이지 버튼 클릭 실패 또는 더 이상 페이지 없음: {e}")
                    break

            html = sb.driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # 브랜드명 추출
            try:
                brand = soup.select_one("h2.title-detail-brand").text.strip()
            except Exception:
                brand = "바이오힐 보"

            # 상품 목록 추출
            items = soup.select("ul.prod-list.goodsProd > li")
            if not items:
                print(f"{page}페이지에 상품이 없습니다.")
                break

            for item in items:
                is_pb = 1
                # 상품명
                try:
                    name = item.select_one("span.prod-name.double-line").text.strip()
                except Exception:
                    name = ""
                # 할인가
                try:
                    price_final = item.select_one("strong.total").text.strip().replace("원", "").replace(",", "").replace("~", "")
                except Exception:
                    price_final = ""
                # 정가
                try:
                    price_original = item.select_one("span.origin").text.strip().replace("원", "").replace(",", "")
                except Exception:
                    price_original = ""
                # 특가 정보
                try:
                    flag_spans = item.select("div.flags span.flag")
                    flag_list = [span.text.strip() for span in flag_spans if span.text.strip()]
                    flag_str = ",".join(flag_list) if flag_list else ""
                except Exception:
                    flag_str = ""
                # 품절여부
                try:
                    soldout_flag = item.select_one("span.status_flag.soldout")
                    is_soldout = bool(soldout_flag)
                except Exception:
                    is_soldout = False
                # 주소
                try:
                    link = item.select_one("a")["href"]
                except Exception:
                    link = ""
                data.append({
                    "brandName": brand,
                    "isPB": is_pb,
                    "goodsName": name,
                    "salePrice": price_final,
                    "originalPrice": price_original,
                    "flagList": flag_str,
                    "isSoldout": is_soldout,
                    "createdAt": collected_at,
                    "link": link
                })
            # 다음 페이지로
            page += 1

    return pd.DataFrame(data)

data = get_brand("A001643")
