import re
import OpenDartReader
dart_api_key = "a5f0a27ad384e3e1af8ea81c2f0be00a419bfb1e"


class DartCrawling:
    target_report = [['N00', 'DARTAPI_지분estkRs'],
                     ['R00', '증권발행실적보고서'],
                     ['R01', '증권신고서(지분증권)'],
                     ['R02', '[기재정정]증권신고서(지분증권)'],
                     ['R03', '[발행조건확정]증권신고서(지분증권)'],
                     ['R04', '철회신고서']]
    report_name = ""
    price_title = ["모집(매출)가액", "모집가액", "매출가액"]
    def __init__(self, api_key):
        self._dart = OpenDartReader(api_key)

    # 이름에 따른 증권신고서 분류
    def kind_report(self, report_name):
        # 입력 : 보고서명 (str)
        # 출력 : 보고서 분류 코드 (str)
        report_name = re.sub(r'\s+', '', report_name)  # 공백제거
        report_name = re.sub(r'[(](\d{2,}).\d{2,}[)]', '', report_name)  # 보고서 뒤에 붙은 일정제거 ex (2022.03)
        for i in range(0, len(self.target_report)):
            if report_name in self.target_report[i][1]:
                return self.target_report[i][0]
        return "E00"

    # 해당 일자의 원하는 증권신고서만 가져오기
    def list_report(self, date):
        # 입력 : 공시보고서 발행일 (0000-00-00)
        # 출력 : List 0보고서번호, 1보고서명, 2기업고유번호(다트), 3기업이름, 4시장구분(코스피/코스닥/코넥스/기타), 5종목번호(상장코드)
        # reports = self._dart.list(start=date, end=date, final=False)  # 전체보고서 가져오기
        '''
        DART 보고서의 목록을 DataFrame으로 반환
        * corp: 종목코드 (고유번호, 법인명도 가능)
        * start: 조회 시작일 (기본값: 1999-01-01')
        * end: 조회 종료일 (기본값: 당일)
        * kind: 보고서 종류:  A=정기공시, B=주요사항보고, C=발행공시, D=지분공시, E=기타공시,
                                        F=외부감사관련, G=펀드공시, H=자산유동화, I=거래소공시, J=공정위공시
        * kind_detail:  보고서 종류 상세 see https://bit.ly/39vY79t
        * final: 최종보고서 여부 (기본값: True)
        '''
        reports = self._dart.list(start=date, end=date, kind='C', final=False)  # 발행공시 보고서 가져오기
        s = (reports.report_nm.str.contains(self.report_name))  # 원하는 보고서만 가져오기(보고서명 기준)
        reports = reports.loc[s, :]

        list_report = (
            list(reports.rcept_no), list(reports.report_nm), list(reports.corp_code), list(reports.corp_name),
            list(reports.corp_cls), list(reports.stock_code))
        return list_report


od = DartCrawling(dart_api_key)
report_list = od.list_report("2021-10-05")
report_number = report_list[0]
report_name = report_list[1]
dart_code = report_list[2]
company_name = report_list[3]
index_name = report_list[4]
stock_code = report_list[5]

# 전체 보고서 확인 및 필요데이터 데이터베이스에 등록
check_api_list = []
for i in range(0, len(report_number)):
    # 변수 선언
    rnum = report_number[i]
    rname = report_name[i]
    rcode = od.kind_report(rname)
    rdartcode = dart_code[i]
    rcpname = company_name[i]
    rcpindex = index_name[i]
    rstockcode = stock_code[i]
    if rcode != "E00":
        print(rnum, rcpname, rname, rcpindex, rdartcode, rstockcode)
