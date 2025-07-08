from seleniumbase import SB
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time


def get_brand(brand_name, brand_code) -> pd.DataFrame:
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
                brand = brand_name

            # 상품 목록 추출
            items = soup.select("ul.prod-list.goodsProd > li")
            if not items:
                print(f"{page}페이지에 상품이 없습니다.")
                break

            for item in items:
                is_pb = 1
                try:
                    name = item.select_one("span.prod-name.double-line").text.strip()
                except Exception:
                    name = ""
                try:
                    a_tag = item.select_one("a[data-ref-goodsno]")
                    goods_no = a_tag["data-ref-goodsno"] if a_tag else ""
                except Exception:
                    goods_no = ""
                try:
                    price_final = item.select_one("strong.total").text.strip().replace("원", "").replace(",", "").replace("~", "")
                except Exception:
                    price_final = ""
                try:
                    price_original = item.select_one("span.origin").text.strip().replace("원", "").replace(",", "")
                except Exception:
                    price_original = ""
                try:
                    flag_spans = item.select("div.flags span.flag")
                    flag_list = [span.text.strip() for span in flag_spans if span.text.strip()]
                    flag_str = ",".join(flag_list) if flag_list else ""
                except Exception:
                    flag_str = ""
                try:
                    soldout_flag = item.select_one("span.status_flag.soldout")
                    is_soldout = bool(soldout_flag)
                except Exception:
                    is_soldout = False

                data.append({
                    "brandName": brand,
                    "isPB": is_pb,
                    "goodsName": name,
                    "goodsNo": goods_no,
                    "salePrice": price_final,
                    "originalPrice": price_original,
                    "flagList": flag_str,
                    "isSoldout": is_soldout,
                    "createdAt": collected_at
                })
            # 다음 페이지로
            page += 1

    return pd.DataFrame(data)



##### 실행 코드 #####
# PB_BRAND_CODE_DICT = {
#     "바이오힐 보": "A000897",
#     "브링그린": "A002253",
#     "웨이크메이크": "A001240",
#     "컬러그램": "A002712",
#     "필리밀리": "A002502",
#     "아이디얼포맨": "A001643",
#     "라운드어라운드": "A001306",
#     "식물나라": "A000036",
#     "케어플러스": "A003339",
#     "탄탄": "A015673",
#     "딜라이트 프로젝트": "A003361",
# }

# for brand_name, brand_code in PB_BRAND_CODE_DICT.items():
#     df = get_brand(brand_name, brand_code)

    # with SB(uc=True, test=True) as sb:
    #     detail_list = []
    #     for goods_no in df['goodsNo']:
    #         detail = get_product_detail_info(sb, goods_no)
    #         detail_list.append(detail)

#     detail_df = pd.DataFrame(detail_list)
#     result_df = pd.concat([df.reset_index(drop=True), detail_df.reset_index(drop=True)], axis=1)

#     result_df.to_json('skincare_result.json', orient='records', force_ascii=False, indent=2)