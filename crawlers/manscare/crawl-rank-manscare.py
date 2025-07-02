from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep

browser = webdriver.Chrome()

url = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010007&pageIdx=1&rowsPerPage=8&t_page=%EB%9E%AD%ED%82%B9&t_click=%ED%8C%90%EB%A7%A4%EB%9E%AD%ED%82%B9_%EB%A7%A8%EC%A6%88%EC%BC%80%EC%96%B4"
browser.get(url)
sleep(5)

soup = BeautifulSoup(browser.page_source, "html.parser")
itemList = soup.select('.TabsConts.on > ul > li')

dataSave = []
rank_num = 0  # 초기 rank 값

for i, item in enumerate(itemList):
    print(f"\n▶ {i + 1}번째 아이템 처리 중...")

    # 순위 rank ('오특'제품은 계산으로 저장)
    rank_tag = item.select('span.thumb_flag.best')
    if rank_tag:
        rank = int(rank_tag[0].text.strip())
        is_special = False
    else:
        rank = rank_num + 1
        is_special = True
    rank_num = rank

    # 브랜드명 brandName
    brandName = item.select('span.tx_brand')[0].text.strip()
    # PB여부 isPb
    isPb = 1 if brandName == '딜라이트 프로젝트' else 0
    # 상품명 goodsName
    goodsName = item.select('p.tx_name')[0].text.strip()
    # 할인가 salePrice
    salePrice = item.select('p.prd_price > span.tx_cur > span.tx_num')[0].text.strip()
    # 정가 originalPrice (없으면 salePrice값 저장)
    org_tag = item.select('p.prd_price > span.tx_org > span.tx_num')
    originalPrice = org_tag[0].text.strip() if org_tag else salePrice
    # 기타 혜택 flagList(리스트형태, '오특'제품은 추가)
    flag_tags = item.select('p.prd_flag > span.icon_flag')
    flagList = [tag.text.strip() for tag in flag_tags] if flag_tags else []
    if is_special:
        flagList.append('오특')

    data = {
        'rank': rank,
        'brandName': brandName,
        'isPb': isPb,
        'goodsName': goodsName,
        'salePrice': salePrice,
        'originalPrice': originalPrice,
        'flagList': flagList
    }

    ##상세페이지 수집
    link_tag = item.select_one('a.prd_thumb')
    # 상세페이지 주소 goodsUrl
    goodsUrl = link_tag['href'] if link_tag and 'href' in link_tag.attrs else ''

    if goodsUrl:
        browser.get(goodsUrl)
        sleep(3)

        try:
            review_btn = browser.find_element(By.CSS_SELECTOR, 'li#reviewInfo a.goods_reputation')
            review_btn.click()
            sleep(2)

            detail_soup = BeautifulSoup(browser.page_source, "html.parser")

            # ▶ 필수 리뷰 정보
            # 총 코멘트 totalComment
            totalComment = detail_soup.select_one('p.img_face > em').text.strip()
            # 총 리뷰 수 numOfReviews
            numOfReviews = detail_soup.select_one('p.total > em').text.strip()

            # 5~1점 (%) 분포
            li_tags = detail_soup.select('ul.graph_list > li > span.per')
            pctOf5 = int(li_tags[0].get_text(strip=True).replace('%', ''))  # 컬럼명: pctOf5
            pctOf4 = int(li_tags[1].get_text(strip=True).replace('%', ''))  # 컬럼명: pctOf4
            pctOf3 = int(li_tags[2].get_text(strip=True).replace('%', ''))  # 컬럼명: pctOf3
            pctOf2 = int(li_tags[3].get_text(strip=True).replace('%', ''))  # 컬럼명: pctOf2
            pctOf1 = int(li_tags[4].get_text(strip=True).replace('%', ''))  # 컬럼명: pctOf1

            # 포장상태
            packing_data = {'pakingGood': 0, 'pakingMiddle': 0,
                            'pakingBad': 0}  # 컬럼명들: pakingGood, pakingMiddle, pakingBad
            # 유통기한
            exp_data = {'expLong': 0, 'expMiddle': 0, 'expShort': 0}  # 컬럼명들: expLong, expMiddle, expShort
            # 맛
            taste_data = {'tasteGood': 0, 'tasteMiddle': 0, 'tasteBad': 0}  # 컬럼명들: tasteGood, tasteMiddle, tasteBad

            review_list = detail_soup.select('div.poll_all.clrfix > .poll_type2.type3')
            if len(review_list) >= 3:
                categories = [
                    ('paking', ['Good', 'Middle', 'Bad']),
                    ('exp', ['Long', 'Middle', 'Short']),
                    ('taste', ['Good', 'Middle', 'Bad'])
                ]

                for idx, (prefix, suffixes) in enumerate(categories):
                    item_list = review_list[idx].select('dd li')
                    for i, suffix in enumerate(suffixes):
                        key = f"{prefix}{suffix}"  # 각 컬럼명 구성 예: 'pakingGood' 등
                        try:
                            value = int(item_list[i].select_one('em').get_text(strip=True).replace('%', ''))
                        except:
                            value = 0
                        if prefix == 'paking':
                            packing_data[key] = value
                        elif prefix == 'exp':
                            exp_data[key] = value
                        elif prefix == 'taste':
                            taste_data[key] = value
            else:
                print("→ 상세 리뷰 항목 없음 (packing/exp/taste)")

            # ▶ 상세정보 저장
            data.update({
                'totalComment': totalComment,
                'numOfReviews': numOfReviews,
                'pctOf5': pctOf5,
                'pctOf4': pctOf4,
                'pctOf3': pctOf3,
                'pctOf2': pctOf2,
                'pctOf1': pctOf1,
                **packing_data,
                **exp_data,
                **taste_data
            })

            print(f"✓ 리뷰 데이터 수집 완료: {goodsName}")

        except Exception as e:
            print(f"[오류] 리뷰 탭 클릭 또는 파싱 실패: {e}")
            data.update({
                'pakingGood': 0, 'pakingMiddle': 0, 'pakingBad': 0,
                'expLong': 0, 'expMiddle': 0, 'expShort': 0,
                'tasteGood': 0, 'tasteMiddle': 0, 'tasteBad': 0
            })

    dataSave.append(data)

# ▶ DataFrame 생성
raw_health = pd.DataFrame(dataSave)

# ▶ 브라우저 종료
browser.quit()