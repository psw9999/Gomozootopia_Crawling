import OpenDartReader


class DartCrawling:
    def __init__(self, api_key):
        self._dart = OpenDartReader(api_key)

    # 해당 종목에 업종코드를 반환
    def get_sector(self, company_code):
        # 입력 : 조회를 원하는 종목번호 (compnay_code는 dart에서 관리하는code, 주식시장에 종목코드 모두 사용가능)
        # 출력 : 해당 종목에 업종코드 (5자리 숫자)
        # info = self._dart.company(company_code)[0]['induty_code']
        info = self._dart.company(company_code)['induty_code']
        industry_code = info
        if len(info) != 5:
            for _ in range(5 - len(info)):
                industry_code += '0'

        return industry_code


######################################### MAIN ###################################################
dart = DartCrawling("a5f0a27ad384e3e1af8ea81c2f0be00a419bfb1e")
print("삼성전자 업종코드", dart.get_sector('005930'))
