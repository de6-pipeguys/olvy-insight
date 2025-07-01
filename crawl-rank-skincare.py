import requests
from bs4 import BeautifulSoup
import re # 정규표현식은 판매가격에서 '원', 쉼표 제거에 계속 사용

def crawl_oliveyoung_ranking_simplified():
    base_url = "https://www.oliveyoung.co.kr/store/main/getBestList.do"
    params = {
        "dispCatNo": "900000100100001",  # 스킨케어 카테고리
        "fltDispCatNo": "10000010001",
        "pageIdx": "1",
        "rowsPerPage": "8",
        "t_page": "%EB%9E%AD%ED%82%B9",
        "t_click": "%ED%8C%90%EB%A7%A4%EB%9E%AD%ED%82%B9_%EC%8A%A4%ED%82%B8%EC%BC%80%EC%96%B4"
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.oliveyoung.co.kr/store/main/main.do'
    }

    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        soup = BeautifulSoup(response.text, 'html.parser')

        # 상품 아이템 리스트 선택자: div.TabsConts.on 안에 있는 ul.cate_prd_list의 li 태그들
        product_items = soup.select('div.TabsConts.on ul.cate_prd_list li')

        if not product_items:
            print("Warning: No product items found on the page. Check selector or page content.")
            print("HTML content head for debugging:")
            print(str(soup)[:1000]) # HTML 내용 일부 출력하여 디버깅에 도움
            return

        ranking_data = []

        for item in product_items:
            product_info = {}

            # 랭킹
            rank_element = item.select_one('.thumb_flag')
            product_info['랭킹'] = rank_element.text.strip() if rank_element else 'N/A'

            # 제품명 (tx_name)
            name_element = item.select_one('.tx_name')
            product_info['제품명'] = name_element.text.strip() if name_element else 'N/A'

            ranking_data.append(product_info)
            # 각 상품 정보 출력 구분선은 제거 (필요하면 다시 추가 가능)

        return ranking_data

    except requests.exceptions.RequestException as e:
        print(f"웹 페이지 요청 실패: {e}")
        return None
    except Exception as e:
        print(f"데이터 파싱 오류: {e}")
        return None

if __name__ == "__main__":
    print("올리브영 스킨케어 랭킹 정보 크롤링 시작 (상세페이지 제외)...")
    crawled_data = crawl_oliveyoung_ranking_simplified()
    
    if crawled_data:
        print("\n--- 크롤링 결과 ---")
        for item in crawled_data:
            print(f"랭킹: {item.get('랭킹')}")
            print(f"제품명: {item.get('제품명')}")
            print("=" * 40)

    else:
        print("크롤링된 데이터가 없습니다.")