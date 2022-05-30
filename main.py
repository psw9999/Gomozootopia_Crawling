from multiprocessing import cpu_count
import OpenDartReader
from xml.etree.ElementTree import Element, SubElement, ElementTree, dump
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
import re
import datetime
import pandas as pd
import json
import traceback
from lib.slack import slack
from lib.mysql_db import mysql_db
from lib.dart_api import dart_api
from lib.holiday_check import holiday_check


class notIpoError(Exception):
    pass


def line_info(return_type=None):
    import inspect

    # line number 여기를 호출한 곳의 라인위치(라인번호)를 리턴한다.
    cf = inspect.currentframe()
    linenumber = cf.f_back.f_lineno

    # Call to Function name 여기를 호출한 곳의 함수이름(function name(def))를 리턴한다.
    func_name = cf.f_back.f_code.co_name

    # file name 여기를 호출한 파일 이름을 리턴한다.
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    filename = module.__file__
    get_filename = filename.split('/')[-1]

    if return_type == 'filename':
        result_info = f'{get_filename}'
    elif return_type == 'function' or return_type == 'func_name' or return_type == 'f_name':
        result_info = f'{func_name}'
    elif return_type == 'lineinfo' or return_type == 'linenum' or return_type == 'lineno':
        result_info = f'{linenumber}'
    elif return_type == 'info' or return_type is None:
        result_info = f'[{func_name}:{linenumber}]'
    elif return_type == 'info_all' or return_type is None:
        result_info = f'{get_filename}({func_name}.{linenumber})'
    else:
        result_info = f'{get_filename}({func_name}.{linenumber})'
    return result_info


def crawling_date(date_string):
    ddate = re.findall('[\d]+', re.sub(r'\s+', '', date_string))
    year, month, day = [], [], []
    startDay, endDay = None, None
    li = len(ddate)
    if li == 6:  # 그대로 쓰면됨    yyyy-mm-dd ~ yyyy-mm-dd
        year.append(ddate[0])
        month.append(ddate[1])
        day.append(ddate[2])

        year.append(ddate[3])
        month.append(ddate[4])
        day.append(ddate[5])
    elif li == 5:  # 년이 없는거  yyyy-mm-dd ~ mm-dd
        year.append(ddate[0])
        month.append(ddate[1])
        day.append(ddate[2])

        year.append(ddate[0])
        month.append(ddate[3])
        day.append(ddate[4])
    elif li == 4:  # 년, 월이 없는거  yyyy-mm-dd ~ dd
        year.append(ddate[0])
        month.append(ddate[1])
        day.append(ddate[2])

        year.append(ddate[0])
        month.append(ddate[1])
        day.append(ddate[3])
    else:  # 예상범위 밖
        raise Exception("[crawling_date] 지원하지않는 날짜형식입니다.")
    
    # date to str
    startDay = datetime.datetime.strptime(
        str(year[0]) + "-" + str(month[0])+ "-" + str(day[0]), "%Y-%m-%d")
    
    endDay = datetime.datetime.strptime(
        str(year[1]) + "-" + str(month[1]) + "-" + str(day[1]), "%Y-%m-%d")
    
    startDay = startDay.strftime("%Y-%m-%d")
    endDay = endDay.strftime("%Y-%m-%d")

    return startDay, endDay


class DartCrawling:
    target_report = [['N00', 'DARTAPI_지분estkRs'],
                     ['R00', '증권발행실적보고서'],
                     ['R01', '증권신고서(지분증권)'],
                     ['R02', '[기재정정]증권신고서(지분증권)'],
                     ['R03', '[발행조건확정]증권신고서(지분증권)'],
                     ['R04', '철회신고서']]
    report_name = ""
    price_title = ["모집(매출)가액", "모집가액", "매출가액"]
    underwriter_title = ["증권", "투자", "금융"]
    # 22.05.05 : 증권사 크롤링하던 에러 수정 (회사이름에 해당 단어가 들어가면 문서 포함 안시킴.)
    # underwriter = ["증권", "투자", "금융"]
    underwriter = ["케이비증권", "유안타증권", "KB금융", "상상인증권", "한양증권", "리딩투자증권", "BNK투자증권", "아이비케이투자증권", "다올투자증권", "미래에셋증권", "삼성증권",
                   "한국투자증권", "NH투자증권", "교보증권", "하이투자증권", "현대차증권", "키움증권", "이베스트투자증권",
                   "SK증권", "대신증권", "메리츠증권", "한화투자증권", "하나금융투자", "토스증권", "NH선물", "신한금융투자", "DB금융투자", "유진증권", "메리츠증권",
                   "카카오페이증권", "NH투자증권", "부국증권", "신영증권", "케이프투자증권", "한국증권금융", "한국포스증권", "우리종합금융", "신한은행"]

    def __init__(self, api_key):
        self._dart = OpenDartReader(api_key)

    # 보고서코드가 의미하는 보고서가 무엇인지 반환
    def report_type(self, report_key):
        # 입력 : 원하는 보고서 KEY 값
        # 출력 : 해당 KEY값에 해당하는 보고서명 String
        for i in range(0, len(self.target_report)):
            if report_key in self.target_report[i][0]:
                return self.target_report[i][1]
        return "E00"

    # 해당 일자의 원하는 증권신고서만 가져오기
    def list_report(self, date):
        # 입력 : 공시보고서 발행일 (0000-00-00)
        # 출력 : List 0보고서번호, 1보고서명, 2기업고유번호(다트), 3기업이름, 4시장구분(코스피/코스닥/코넥스/기타), 5종목번호(상장코드)
        reports = self._dart.list(start=date, end=date, kind='C', final=False)  # 발행공시 보고서 가져오기
        s = (reports.report_nm.str.contains(self.report_name))  # 원하는 보고서만 가져오기(보고서명 기준)
        reports = reports.loc[s, :]

        # 22.05.05 : 증권사 크롤링하던 에러 수정
        reports = reports[reports['corp_name'].str.contains('|'.join(self.underwriter)) == False]

        list_report = (
            list(reports.rcept_no), list(reports.report_nm), list(reports.corp_code), list(reports.corp_name),
            list(reports.corp_cls), list(reports.stock_code))
        return list_report

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

    # 보고서 내에 원하는 메뉴의 HTML BODY값을 RETURN
    def document_body(self, report_number, menu_name):
        # 입력 : 보고서번호, 조회할메뉴이름(DART 좌측 메뉴들..)
        # 출력 : 해당메뉴 html page의 body값
        subDocs = self._dart.sub_docs(report_number, menu_name)
        subDoc = list(subDocs.url)

        # print(subDoc[0])  # 주소 출력
        report = urlopen(subDoc[0])
        r = report.read()
        xmlsoup = BeautifulSoup(r, 'html.parser')
        body = xmlsoup.find("body")
        return body

    # 해당 종목에 업종코드를 반환
    def get_sector(self, company_code):
        # 입력 : 조회를 원하는 종목번호 (compnay_code는 dart에서 관리하는code, 주식시장에 종목코드 모두 사용가능)
        # 출력 : 해당 종목에 업종코드 (5자리 숫자)
        info = self._dart.company(company_code)['induty_code']
        industry_code = info
        # if len(info) != 5:
        #     for _ in range(5 - len(info)):
        #         industry_code += '0'

        return industry_code

    # 각 보고서별 로직을 실행시키고 결과값을 반환
    # 2022-05-21 : 인자값 변경 (index -> 회사이름)
    #def report_to_dict(self, report_code, report_number, company_index):
    def report_to_dict(self, report_code, report_number, company_name):
        # 입력 : 보고서 분류 코드 (str), 보고서 번호 (str), 시장구분 (str)
        # 출력 : dict (필수값(type): 보고서코드(str data) 및 해당 데이터들)
        if report_code in "E00":
            pass
            # raise Exception('E00: 지정된 형식과 일치하는 보고서가 아닙니다. ' + report_code)
        # print("타입: ", report_code, "보고서번호: ", report_number)
        if report_code in "R00":
            return self.__r00_logic(report_number)
        elif report_code in "R01":
            return self.__r01_logic(report_number, company_name)
        elif report_code in "R02":
            return self.__r02_logic(report_number, company_name)
        elif report_code in "R03":
            return self.__r03_logic(report_number)
        elif report_code in "R04":
            return self.__r04_logic(report_number)
        else:
            pass
        # if company_index == 'E':  # 법인구분 : Y(유가), K(코스닥), N(코넥스), E(기타)

    # 각 보고서별 로직
    # 입력 : 보고서 번호 (str)
    # 출력 : dict
    def __r00_logic(self, report_number):
        dict = {}
        html_body = self.document_body(report_number, "발행개요")
        html_body2 = self.document_body(report_number, "증권교부일 등")
        html_body3 = self.document_body(report_number, "청약 및 배정에 관한 사항")

        # 증권사의 가타파생결합사채 예외 처리
        summarizeTable = str(html_body3)
        ban_list = ["기타파생결합사채", "주가연계증권", "주식워런트증권"]
        for ban in ban_list:
            if ban in summarizeTable:
                raise notIpoError

        summarizeTable = str(html_body)
        kind = ""
        if "기업공개" in summarizeTable:
            kind = "공모주"
        elif "실권주" in summarizeTable:
            kind = "실권주"
        else:  # 기타 사채의 경우 해당 조건문에서 확인한다.
            kind = "기타"
            raise notIpoError

        # 2022-05-04
        # 페이지에 p 태그 데이터를 가져온다.
        summarizeTable = str(html_body2.find_all("p"))
        summarizeTable = re.sub(r'\s+', '', summarizeTable)
        st = summarizeTable.split("상장")

        # '상장' 단어 이후 제일 처음 나온 날짜를 가져온다.
        port_regex = re.findall(
            "(\d{4})[- /.년]*([1-9]|0[1-9]|1[012])[- /.월]*([1-9]|0[1-9]|[12][0-9]|3[01])[- /.일]",
            st[1])
        d = datetime.datetime.strptime(str(port_regex[0]), "('%Y', '%m', '%d')")

        # # 페이지에 p 태그 데이터를 가져온다.
        # summarizeTable = str(html_body2.find_all("p"))
        #
        # # 가장 마지막에 있는 날짜 정보를 상장일로 사용한다.
        # port_regex = re.findall(
        #     "(\d{4})[- /.년]*([1-9]|0[1-9]|1[012])[- /.월]*([1-9]|0[1-9]|[12][0-9]|3[01])[- /.일]",
        #     summarizeTable)
        # end_point = port_regex.pop()
        # d = datetime.datetime.strptime(str(end_point), "('%Y', '%m', '%d')")

        # dict 출력
        dict = {"ipo_debut_date": d.strftime("%Y-%m-%d"), "kind": kind}
        return dict

    def __r01_logic(self, report_number, company_name):  # 증권신고서(지분증권) - 최초
        return self.__r02_logic(report_number, company_name)

    def __r02_logic(self, report_number, company_name):  # [기재정정]증권신고서(지분증권) - 정정
        profit, sales, unit = -1, -1, -1
        html_body = self.document_body(report_number, "모집 또는 매출에 관한 일반사항")
        summarizeTable = html_body.find_all("tr")
        html_table = html_body.find_all("table")
        tables_2 = html_body.find_all(["table", "p"])

        html_body2 = self.document_body(report_number, "재무에 관한 사항")
        tables = html_body2.find_all(["table", "p"])
        # 2022.04.28 - Default 값 0 -> -1로 수정
        # dict = {'profit': 0, 'sales': 0, 'stockQuantity': 0, 'ipo_price_low': 0, 'ipo_price_high': 0, 'kind': 'none'}
        dict = {'profit': -1, 'sales': -1, 'stockQuantity': -1, 'ipo_price_low': -1, 'ipo_price_high': -1,
                'kind': 'none'}
        financial_company = {}

        # 공모주 / 실권주 판단 - 스팩(기업인수목적), 리츠 같은거는 이름으로..?
        kind = '기타'
        for s in html_table:
            s_text = s.get_text()
            if "실권주" in s_text:
                kind = "실권주"
                break
            elif "주주우선공모" in s_text:
                kind = "기타"
                raise notIpoError
            elif "일반공모" in s_text:
                kind = "공모주"
                break
        
        # 영업이익, 매출액 크롤링 플래그
        fin_flag = False
        iiii_flag = False
        iii_flag = False
        iii_index = 0
        iiii_index = 0
        recent_column_flag = False
        tt_list = []
        
        # 2022-05-21 : 스팩이 회사명에 포함된 경우 매출액, 영업이익 크롤링에서 제외
        if "스팩" not in company_name :
            # 영업이익, 매출액 크롤링
            for i in range(len(tables)):
                # 2022.04.16 : 1. 요약재무정보 ~ 2. 연결재무제표 내의 데이터만 수집
                # if not iii_flag:  # 재무에 관한사항을 찾기
                if (not iii_flag) or (not iiii_flag):
                    temp = tables[i].find_all("a")

                    # 22.04.03 : 111. 재무에관한사항으로 쓴 놈들이 있어서 수정
                    # if len(temp) > 0 and "III. 재무에관한사항" in temp[0].get_text().replace(" ", ""):

                    # 2022.04.16 : 1. 요약재무정보 ~ 2. 연결재무제표 내의 데이터만 수집
                    # if len(temp) > 0 and "재무에관한사항" in temp[0].get_text().replace(" ", ""):
                    if len(temp) > 0 and "요약재무정보" in temp[0].get_text().replace(" ", ""):
                        for j in range(i + 1, len(tables)):
                            t = tables[j].find_all(["tbody", "p"])
                            temp_unit = ""
                            if len(t) == 0 and "(단위:" in tables[j].get_text().replace(" ", "").replace("\xa0", "").replace("[", "("):
                                temp_str1 = tables[j].get_text().replace(" ", "").replace("\xa0", "").replace("&nbsp;","")
                                try:
                                    start = temp_str1.index(":")
                                    #temp_unit = temp_str1[start + 1:-1].replace(")", "").replace("\n", "")
                                    temp_unit = re.sub(r'\s+', '',temp_str1[start + 1:-1]).replace(")", "")
                                    iii_flag = True
                                    iii_index = j
                                    break
                                except ValueError:
                                    print("금액의 단위를 찾을 수 없습니다!")

                            # 22.05.26 : 매출액, 영업이익 단위 크롤링 변경
                            #elif len(t) > 0 and "(단위:" in t[0].get_text().replace(" ", "").replace("\xa0", "").replace("[","("):
                            elif len(t) > 0 :
                                for z in range(len(t)) :
                                    if "(단위:" in t[z].get_text().replace(" ", "").replace("\xa0", "").replace("[","("):
                                        temp_str2 = t[z].get_text().replace(" ", "").replace("\xa0", "").replace("&nbsp;","")
                                        try:
                                            start = temp_str2.index(":")
                                            #temp_unit = temp_str2[start + 1:-1].replace(")", "").replace("\n", "").replace(" ","")
                                            temp_unit = re.sub(r'\s+', '',temp_str2[start + 1:-1]).replace(")", "")
                                            iii_flag = True
                                            iii_index = j
                                            break
                                        except ValueError:
                                            print("금액의 단위를 찾을 수 없습니다!")
                                if iii_flag :
                                    break
                                    
                        if temp_unit == "원":
                            unit = 1
                        elif temp_unit == "십원":
                            unit = 10
                        elif temp_unit == "백원":
                            unit = 100
                        elif temp_unit == "천원":
                            unit = 1000
                        elif temp_unit == "만원":
                            unit = 10000
                        elif temp_unit == "십만원":
                            unit = 100000
                        elif temp_unit == "백만원":
                            unit = 1000000
                        elif temp_unit == "천만원":
                            unit = 10000000
                        elif temp_unit == "억원":
                            unit = 100000000
                        else :
                            print("영업이익, 매출액 크롤링에 실패했습니다. (단위 크롤링 실패)")
                            break
                        # print(temp_unit, unit)

                    elif len(temp) > 0 and "연결재무제표" in temp[0].get_text().replace(" ", ""):
                        iiii_index = i
                        iiii_flag = True

                else:  # iii 아래에 있는 테이블데이터 순차적으로 확인
                    recent_index = -1
                    # 2022.04.16 : 1. 요약재무정보 ~ 2. 연결재무제표 내의 데이터만 수집
                    # for j in range(iii_index, len(tables)):
                    for j in range(iii_index, iiii_index):
                        t_row = tables[j].find_all("tr")

                        if not recent_column_flag:
                            for k in range(len(t_row)):
                                recent_list = re.findall(r'\d{1,4}[연년기/.]', t_row[k].get_text().replace(" ", ""))
                                if recent_list:
                                    recent_column_flag = True
                                    for tr in t_row[k].find_all(['th', 'td']):  # 'tr'
                                        tr = tr.get_text().replace(" ", "")
                                        if tr == "":
                                            continue
                                        tt_list.append(re.findall(r'\d{1,4}[연년기/.]', tr))
                                    break

                            # tt_list 중, 최근값이 있는 열(column)확인하여 recent_index 반환
                            now_index = -1
                            if tt_list:
                                maxV = 0
                                if tt_list[0] != []:
                                    tt_list.insert(0, [])
                                # print(tt_list)
                                for kk in tt_list:
                                    now_index += 1
                                    for k in kk:
                                        nm = int(re.findall(r'\d{1,4}', k)[0])
                                        if maxV < nm:
                                            maxV = nm
                                            recent_index = now_index
                                # print(str(recent_index) + "] 최대값:", maxV)

                        if recent_column_flag:
                            # 테이블에서 '항목'에 [recent_index]를 조회하여 반환
                            # print(recent_index)
                            for k in range(len(t_row)):
                                tword = t_row[k].get_text().replace(" ", "")
                                # 22.04.03 : 항목이 "매출"로만 쓰인 경우 때문에 추가함.
                                ttword = ''.join(re.findall("[가-힣+]", tword))
                                # 매출액 or 영업수익 크롤링
                                if "매출액" in tword or "영업수익" in tword or ttword == "매출":
                                    ddt = t_row[k].find_all("td")
                                    # sales = ddt[recent_index].get_text().replace(",", "").replace("\xa0", "").replace(" ", "").replace("\n", "")

                                    sales = re.sub('&nbsp;|,|\xa0|\n| ', '', ddt[recent_index].get_text())
                                    # if "(" in sales or ")" in sales:
                                    #     sales = int(sales.replace("(", "").replace(")", "")) * -1 * unit
                                    # else:
                                        # sales = int(sales) * unit
                                    sales = int(sales) * unit
                                    # print(sales)

                                # 영업이익 크롤링
                                if "당기순이익" in tword or "당(분)기순이익" in tword :
                                    ddt = t_row[k].find_all("td")
                                    # profit = ddt[recent_index].get_text().replace(",", "").replace(" ", "").replace("\xa0","").replace("\n", "")
                                    profit = re.sub('&nbsp;|,|\xa0|\n', '', ddt[recent_index].get_text())
                                    
                                    # 22.04.03 : 음수표현을 다르게 하는 놈들때문에 수정
                                    # if "(" in profit or ")" in profit:
                                    #     profit = int(profit.replace("(", "").replace(")", "")) * -1 * unit
                                    profit_sign = re.findall("\D", profit)
                                    if profit_sign:
                                        profit = int(''.join(re.findall("\d", profit))) * -1 * unit
                                    else:
                                        profit = int(profit) * unit
                                    # print(profit)
                                
                                # 영업이익 크롤링
                                if "당기순손실" in tword:
                                    ddt = t_row[k].find_all("td")
                                    #profit = ddt[recent_index].get_text().replace(",", "").replace(" ", "").replace("\xa0","").replace("\n", "")
                                    profit=re.sub('&nbsp;|,|\xa0|\n', '', ddt[recent_index].get_text())
                                    # 22.04.03 : 음수표현을 다르게 하는 놈들때문에 수정
                                    # if "(" in profit or ")" in profit:
                                    #     profit = int(profit.replace("(", "").replace(")", "")) * -1 * unit
                                    profit_sign = re.findall("\D", profit)
                                    if profit_sign:
                                        profit = int(''.join(re.findall("\d", profit))) * unit
                                    else:
                                        profit = int(profit) * unit * -1
                                    # print(profit)

                                if sales != -1 and profit != -1:
                                    fin_flag = True
                                    break

                        if recent_column_flag and fin_flag:
                            break

                if recent_column_flag and fin_flag:
                    break
                
        # 2022.05.21 : 실권주 주간사 크롤링 추가 
        if kind == "실권주" :
            underwriterFlag = False
            for i in range(len(tables_2)):
                temp = tables_2[i].find_all("a")
                if len(temp) > 0 and "인수등에관한사항" in temp[0].get_text().replace(" ", ""):
                    for j in range(i+1, len(tables_2)) :
                        t_row = tables_2[j].find_all("tr")
                        for k in range(len(t_row)):
                            tr = t_row[k].find_all(['th', 'td'])
                            if len(tr) < 2 :
                                continue
                            underwriter1 = re.sub('&nbsp;|,|\xa0|\n| ', '', tr[0].get_text())
                            underwriter2 = re.sub('&nbsp;|,|\xa0|\n| ', '', tr[1].get_text())
                            #if "주관회사" in tr[0].get_text().replace(" ","") :
                            for s in self.underwriter_title :
                                if s in underwriter1 :
                                    financial_company[underwriter1] = ["0","0","0","0"]
                                    underwriterFlag = True
                                    break
                                if s in underwriter2 :
                                    financial_company[underwriter2] = ["0","0","0","0"]
                                    underwriterFlag = True
                                    break
                        if underwriterFlag == True :
                            break
                if underwriterFlag == True :
                    break           
                
        else :
            # 증권사별 배정 물량 (모집 또는 매출에 관한 일반사항)
            for s in range(len(summarizeTable)):  # summarizeTable = find_all("tr")  # todo p 도 봐야함. title에잇네.
                temp = summarizeTable[s].find_all(["th","td"])  # todo 엔켐은 td로 되어있어서 검색이 잘안됨.
                if len(temp) < 4:
                    continue
                if "배정물량" in temp[1].get_text().replace(" ", ""):
                    # 22-05-26 : 증권사 로직 수정
                    temp_td = summarizeTable[s + 1].find_all(["td"])
                    if len(temp_td) > 3:
                        # print("증권사 배정수량:", summarizeTable[s + 1].get_text())

                        # 주간사 구분하는 로직. (일반청약자일때 예외처리.)
                        stock_companies = ["금융", "투자", "증권", "(주)"]
                        company_flag = False
                        company = temp_td[0].get_text().replace("\xa0", "").replace(" ", "").replace("\n", "")
                        for stock_company in stock_companies:
                            if stock_company in company:
                                company_flag = True
                        if company_flag == False:
                            # 주간사명을 확인할 수 없는 경우, 타이틀에 있는지 확인.
                            company = "확인 필요"
                            company_title = summarizeTable[s - 1].get_text()
                            for ud_name in self.underwriter:
                                if ud_name in company_title:
                                    company = ud_name
                                    break

                        #일반청약자 배정물량
                        limit = list(map(int, re.findall("[\d,]+", temp_td[1].get_text().replace(',','') )))
                        # print(" 일반청약자 배정물량>>>>:", limit)
                        limit6 = [limit[0], limit[1], -1, -1]
                        financial_company[company] = limit6
                        # -----------------------------------------------------------------------------------------------------------------------------------------------------------

        # 상단,하단 밴드 (모집 또는 매출에 관한 일반사항)
        hopeprice = ""
        ipo_price_low = -1
        ipo_price_high = -1
        spec_stock_flag = False
        if kind != "실권주":  # 공모주, 기타
            for s in range(len(summarizeTable)):
                temp = summarizeTable[s].find_all(["td", "th"])
                if len(temp) > 1:
                    focus_word_hopeprice = re.sub(r'\s+', '', temp[0].get_text())
                    if "희망공모가액" in focus_word_hopeprice or "공모희망가액" in focus_word_hopeprice:
                        temp = summarizeTable[s].find_all("td")
                        if len(temp) > 1:
                            hopeprice = temp[1].get_text()
            if isinstance(hopeprice, str):
                hopeprice = hopeprice.replace(",", "").replace("원", "")
            #print(hopeprice)
            hope = re.findall(r'\d{1,100}', hopeprice)

            if len(hope) == 1:  # 스팩주 등 공모가격이 밴드형태가 아닌 경우
                ipo_price_low = 0
                ipo_price_high = int(hope[0])
            else:  # 일반 공모주의 상하단 밴드
                ipo_price_low = int(hope[0])
                ipo_price_high = int(hope[1])
        else:  # 실권주 모집매출가액(공모가)
            forfeited_price_flag = False
            forfeited_price = -1
            for s in range(len(summarizeTable)):  # summarizeTable = body.find_all("tr")
                temp = summarizeTable[s]
                temp_text = temp.get_text().replace(" ", "")
                # if temp and "모집(매출)가액" in temp_text or "모집가액" in temp_text or "매출가액" in temp_text:
                for pt in self.price_title:
                    if pt in temp_text:
                        temp_div = temp.find_all(["td", "th"])
                        for td_i in range(len(temp_div)):
                            temp_div_td_text = temp_div[td_i].get_text().replace(" ", "")
                            # 2022.04.28 수정
                            # if temp_div and "모집(매출)가액" in temp_div_td_text or "모집가액" in temp_div_td_text or "매출가액" in temp_div_td_text:
                            if pt in temp_div_td_text:
                                temp_next = summarizeTable[s + 1].find_all(["td", "th"])
                                forfeited_price = temp_next[td_i].get_text()
                                forfeited_price_flag = True
                                break
                if forfeited_price_flag:
                    break
            if isinstance(forfeited_price, str):
                forfeited_price = int(forfeited_price.replace(",", "").replace("원", ""))
            ipo_price_low = 0
            ipo_price_high = forfeited_price

        # 수요예측 일시
        ipo_forecast_start = None  # null로 지정. 날짜Type아니면 DB에서 오류발생함.
        ipo_forecast_end = None
        unclaimed_ipo_start_day = None
        unclaimed_ipo_end_day = None
        if kind != "실권주":  # 공모주, 기타
            try:
                for s in range(len(summarizeTable)):
                    temp = summarizeTable[s].find_all(["td", "th"])
                    if len(temp) > 1:
                        focus_word_forecast = re.sub(r'\s+', '', temp[0].get_text())
                        if "수요예측일시" in focus_word_forecast or "수요예측일" in focus_word_forecast:
                            # print(" 수요예측틀: ", focus_word_forecast)

                            forecast_date = re.sub(r'\s+', '', temp[1].get_text())
                            # print(" 수요예측 대상판정:", forecast_date)
                            if "국내" in forecast_date:
                                forecast_date = re.sub(r'\s+', '', temp[2].get_text())
                            elif "해외" in forecast_date:
                                temp_f = summarizeTable[s + 1].find_all(["td", "th"])
                                forecast_date = re.sub(r'\s+', '', temp_f[1].get_text())
                            # print(" 수요예측 대상최종:", forecast_date)

                            ipo_forecast_start, ipo_forecast_end = crawling_date(forecast_date)
                            # print(" 수요예측결과: ", ipo_forecast_start, ipo_forecast_end)
                            break
                        
            except Exception as e:
                print("수요예측 오류발생")
                print(str(report_number), traceback.format_exc())
                
        # 실권주 수요예측일은 진행 X, 청약기일은 수집
        else:  
            try:
                for s in range(len(summarizeTable)):
                    temp = summarizeTable[s].find_all(["td", "th"])
                    if len(temp) > 1:
                        ipo_word = re.sub(r'\s+', '', temp[1].get_text())
                        if "일반공모청약" == ipo_word :
                            ipo_date = re.sub(r'\s+', '', temp[0].get_text())
                            unclaimed_ipo_start_day, unclaimed_ipo_end_day = crawling_date(ipo_date)
                            print("실권주공모일: ", unclaimed_ipo_start_day, unclaimed_ipo_end_day)
                            break
            except Exception as e :
                print("청약기일 수집 오류발생")
                print(str(report_number), traceback.format_exc())
                
        dict["kind"] = kind
        dict["ipo_price_low"] = ipo_price_low
        dict["ipo_price_high"] = ipo_price_high
        dict["profit"] = profit
        dict["sales"] = sales
        dict["stockQuantity"] = financial_company.copy()
        dict["ipo_forecast_start"] = ipo_forecast_start
        dict["ipo_forecast_end"] = ipo_forecast_end
        dict["unclaimed_ipo_start_day"] = unclaimed_ipo_start_day
        dict["unclaimed_ipo_end_day"] = unclaimed_ipo_end_day
        return dict

    def __r03_logic(self, report_number):  # [발행조건확정]증권신고서(지분증권)
        html_body = self.document_body(report_number, "증권발행조건확정")
        summarizeTable = html_body.find_all("tr")

        ipo_price = -1
        acceptance_rate = -1.0
        lock_up_percent = -1
        kind = "기타"
        rate_flag = False
        lock_up_flag = False
        kind_flag = False
        for s in range(len(summarizeTable)):
            temp = summarizeTable[s].find_all(["th", "td"])

            if len(temp) > 3:
                focus_word_arate = re.sub(r'\s+', '', temp[0].get_text())
                focus_word_price = re.sub(r'\s+', '', temp[3].get_text())
                # 2022.04.28
                # if "모집(매출)" in focus_word_price:
                if focus_word_price in self.price_title:
                    temp_td = summarizeTable[s + 1].find_all("td")
                    if len(temp_td) > 3:
                        ipo_price = re.sub(r'[^0-9]', '', temp_td[3].get_text())
                elif not rate_flag and "경쟁률" in focus_word_arate:
                    temp_td = summarizeTable[s].find_all("td")
                    acceptance_rate = float(
                        (temp_td[7].get_text().replace(',', '').split(":")[0]))  # 경쟁률 ':'기준 왼쪽값만 가져옴
                    rate_flag = True

            if not lock_up_flag:
                if temp and "미확약" in temp[0].get_text().replace(" ", ""):
                    temp_td = summarizeTable[s].find_all("td")
                    # temp_td = re.findall("/d",temp_td)
                    temp_td2 = summarizeTable[s + 1].find_all("td")
                    # temp_td2 = re.findall("/d",temp_td2)
                    notMustHaves = []
                    haveSums = []
                    for i in range(len(temp_td) - 1):
                        nMHtemp = re.sub(r'[^0-9]', '', temp_td[i + 1].get_text())
                        if nMHtemp != '':
                            notMustHaves.append(int(nMHtemp))
                        hStemp = re.sub(r'[^0-9]', '', temp_td2[i + 1].get_text())
                        if hStemp != '':
                            haveSums.append(int(hStemp))

                    notMustHave = max(notMustHaves)
                    haveSum = max(haveSums)

                    lock_up_percent = (haveSum - notMustHave) / haveSum * 100  # (전체 - 미확약자 = 확약자) / 전체 * 100
                    lock_up_percent = round(lock_up_percent, 2)  # 소수점 반올림 둘째자리까지만 반환
                    lock_up_flag = True
                else:
                    '''
                    tables = html_body.find_all(["table", "p"])
                    for i in range(len(tables)):
                        if "의무보유확약신청내역" in tables[i].get_text().replace(" ", ""):
                            table = tables[i + 1].find_all("td")
                            for j in range(len(table)):
                                if "수량대비비율" in table[j].get_text().replace(" ", ""):
                                    lock_up_percent = float(table[j + 2].get_text().replace("%", ""))
                                    lock_up_flag = True
                                    break
                            if lock_up_flag:
                                break
                    '''
                    tables = html_body.find_all(["table"])
                    for table in tables:
                        table_temps = table.find_all("td")
                        for table_i in range(len(table_temps)):
                            if "수량대비비율" in table_temps[table_i].get_text().replace(" ", ""):
                                lock_up_percent = float(table_temps[table_i + 2].get_text().replace("%", ""))
                                lock_up_flag = True
                                break

            if not kind_flag:  # 공모주(일반공모) / 실권주(주주배정후 실권주 일반공모) 구분
                tr_text = re.sub(r'\s+', '', summarizeTable[s].get_text())
                if "실권주" in tr_text:
                    kind = "실권주"
                    kind_flag = True
                elif "주주우선공모" in tr_text:
                    kind = "기타"
                    kind_flag = True
                elif "일반공모" in tr_text:
                    kind = "공모주"
                    kind_flag = True

        dict = {"ipo_price": ipo_price,
                "ipo_institutional_acceptance_rate": acceptance_rate,
                "lock_up_percent": lock_up_percent,
                "kind": kind}
        return dict

    def __r04_logic(self, report_number):  # 철회신고서
        global target_date

        html_body = self.document_body(report_number, "철회신고서")
        summarizeTable = html_body.find_all("tr")

        ipo_cancel_bool = 'Y'
        ipo_cancel_date = target_date
        ipo_cancel_reason = ''
        for index, s in enumerate(summarizeTable):
            print("r04=>", s.get_text())
            if "철회신고서제출사유" in re.sub(r'\s+', '', s.get_text()):
                temp = summarizeTable[index + 1].find_all("td")
                ipo_cancel_reason = re.sub(r'([<](([/][A-z]*)|([A-z]))[>])', '', temp[0].get_text())  # html tag 제외
                break

        dict = {"ipo_cancel_bool": ipo_cancel_bool,
                "ipo_cancel_date": ipo_cancel_date,
                "ipo_cancel_reason": ipo_cancel_reason}
        return dict
    


def upload_dict(cd):
    global db, target_date
    # 최근에 등록된 녀석이 있는경우 그 ipo_index를 기준으로 데이터를 업데이트 한다. 없을 경우 신규 insert.
    # TODO ipo 조회시 종료일 기준으로 판단 할 것.
    data = (cd["rcpname"], cd["rdartcode"], target_date)
    db.query("SET @stock_name = %s, @dart_code = %s, @target_date = %s", data)
    db.query("INSERT INTO ipo (stock_name, dart_code, regist_date) \
                SELECT @stock_name, @dart_code, now() \
                from dual \
                WHERE NOT EXISTS ( \
                    SELECT * FROM ipo \
                    WHERE \
                        dart_code = @dart_code AND \
                        regist_date >= DATE_FORMAT(DATE_ADD(@target_date, INTERVAL -6 MONTH), '%Y-%m-%d'));")
    result = db.query("SELECT ipo_index \
                FROM ipo \
                WHERE \
                    dart_code = @dart_code AND \
                    regist_date >= DATE_FORMAT(DATE_ADD(@target_date, INTERVAL -6 MONTH), '%Y-%m-%d');")
    print(cd["rcpname"], "ipoIndex(DB넘버링) :", result[0][0])

    ipo_index = None
    if result:  # 기존 데이터가 DB에 있는지 확인.
        ipo_index = result[0][0]
    else:
        pass

    # udpate 쿼리문에는 반드시 `update_date` 도 넣을것.
    report_type = cd["rcode"]
    if report_type in "N00":  # DART API 지분증권
        data = (ipo_index,
                cd["rstockcode"],
                cd["rcpindex"],
                cd["induty_code"],
                cd["apidata"]["ipo_schedule"]["ipo_start_date"],
                cd["apidata"]["ipo_schedule"]["ipo_end_date"],
                cd["apidata"]["ipo_schedule"]["ipo_refund_date"],
                cd["apidata"]["put_back_option"]["who"],
                cd["apidata"]["put_back_option"]["price"],
                cd["apidata"]["put_back_option"]["deadline"],
                cd["apidata"]["ipo_price_low"],
                cd["apidata"]["par_value"],
                cd["apidata"]["purpose_of_funds"])
        db.query(
            "set @ipo_index = %s,"
            "@stock_code = %s,"
            "@stock_exchange = %s,"
            "@induty_code = %s,"
            "@ipo_start_date = %s,"
            "@ipo_end_date = %s,"
            "@ipo_refund_date = %s,"
            "@put_back_option_who = %s,"
            "@put_back_option_price = %s,"
            "@put_back_option_deadline = %s,"
            "@number_of_ipo_shares = %s,"
            "@par_value = %s,"
            "@purpose_of_funds = %s;",
            data)
        if cd["kind"] == "실권주":
            db.query("update ipo set "
                     "stock_code = @stock_code,"
                     "sector = @induty_code,"
                     "stock_exchange = @stock_exchange,"
                     "ex_start_date = @ipo_start_date,"
                     "ex_end_date = @ipo_end_date,"
                     "ipo_refund_date = @ipo_refund_date,"
                     "put_back_option_who = @put_back_option_who,"
                     "put_back_option_price = @put_back_option_price,"
                     "put_back_option_deadline = @put_back_option_deadline,"
                     "number_of_ipo_shares = @number_of_ipo_shares,"
                     "par_value = @par_value,"
                     "purpose_of_funds = @purpose_of_funds,"
                     "update_date = NOW()"
                     "where ipo_index = @ipo_index")
        else:
            db.query("update ipo set "
                     "stock_code = @stock_code,"
                     "sector = @induty_code,"
                     "stock_exchange = @stock_exchange,"
                     "ipo_start_date = @ipo_start_date,"
                     "ipo_end_date = @ipo_end_date,"
                     "ipo_refund_date = @ipo_refund_date,"
                     "put_back_option_who = @put_back_option_who,"
                     "put_back_option_price = @put_back_option_price,"
                     "put_back_option_deadline = @put_back_option_deadline,"
                     "number_of_ipo_shares = @number_of_ipo_shares,"
                     "par_value = @par_value,"
                     "purpose_of_funds = @purpose_of_funds,"
                     "update_date = NOW()"
                     "where ipo_index = @ipo_index")
    elif report_type in "R00":  # 증권발행실적보고서
        data = (ipo_index,
                cd["ipo_debut_date"])
        db.query("SET @ipo_index = %s,"
                 "@ipo_debut_date = %s",
                 data)
        db.query("UPDATE ipo SET "
                 "ipo_debut_date = DATE_FORMAT(@ipo_debut_date, '%Y-%m-%d'),"
                 "update_date = NOW()"
                 "WHERE ipo_index = @ipo_index")
    elif report_type in "R01" or report_type in "R02":  # 증권신고서(지분증권)
        data = (ipo_index,
                cd["kind"],
                cd["profit"],
                cd["sales"],
                cd["ipo_price_low"],
                cd["ipo_price_high"],
                cd["ipo_forecast_start"],
                cd["ipo_forecast_end"],
                cd["unclaimed_ipo_start_day"],
                cd["unclaimed_ipo_end_day"])
        db.query(
            "set @ipo_index = %s,"
            "@kind = %s,"
            "@profits = %s,"
            "@sales = %s,"
            "@ipo_price_low = %s,"
            "@ipo_price_high = %s,"
            "@ipo_forecast_start = %s,"
            "@ipo_forecast_end = %s,"
            "@unclaimed_ipo_start_date = %s,"
            "@unclaimed_ipo_end_date = %s;",
            data)
        db.query("update ipo set "
                 "stock_kinds = @kind,"
                 "profits = @profits,"
                 "sales = @sales,"
                 "ipo_price_low = @ipo_price_low,"
                 "ipo_price_high = @ipo_price_high,"
                 "ipo_forecast_start = @ipo_forecast_start,"
                 "ipo_forecast_end = @ipo_forecast_end,"
                 "ipo_start_date = @unclaimed_ipo_start_date,"
                 "ipo_end_date = @unclaimed_ipo_end_date,"
                 "update_date = NOW() "
                 "where ipo_index = @ipo_index;")
        for uname, uvalue in cd["stockQuantity"].items():
            data = (ipo_index,
                    uname,
                    uvalue[1],
                    uvalue[0],
                    uvalue[3],
                    uvalue[2])
            db.query(
                "set @ipo_index = %s,"
                "@under_name = %s,"
                "@ind_total_max = %s,"
                "@ind_total_min = %s,"
                "@ind_can_max = %s,"
                "@ind_can_min = %s;",
                data)
            db.query("insert into ipo_underwriter "
                     "(ipo_index, under_name, ind_total_max, ind_total_min, ind_can_max, ind_can_min, update_date) "
                     "values (@ipo_index, @under_name, @ind_total_max, @ind_total_min, @ind_can_max, @ind_can_min, now()) "
                     "on duplicate key "
                     "update "
                     "ind_total_max = @ind_total_max,"
                     "ind_total_min = @ind_total_min,"
                     "ind_can_max = @ind_can_max,"
                     "ind_can_min = @ind_can_min,"
                     "update_date = NOW();")
    elif report_type in "R03":  # [발행조건확정]증권신고서(지분증권)
        # todo. 여기에 최소증거금도 추가
        data = (ipo_index,
                cd["lock_up_percent"],
                cd["ipo_institutional_acceptance_rate"],
                cd["ipo_price"])
        db.query("set @ipo_index = %s,"
                 "@lock_up_percent = %s,"
                 "@ipo_institutional_acceptance_rate = %s,"
                 "@ipo_price = %s",
                 data)
        db.query("update ipo set "
                 "lock_up_percent = @lock_up_percent,"
                 "ipo_institutional_acceptance_rate = @ipo_institutional_acceptance_rate,"
                 "ipo_price = @ipo_price,"
                 "update_date = NOW() "
                 "where ipo_index = @ipo_index")
    elif report_type in "R04":  # 철회신고서
        data = (ipo_index,
                cd["ipo_cancel_bool"],
                cd["ipo_cancel_date"],
                cd["ipo_cancel_reason"],
                cd["ipo_cancel_date"])
        db.query("set @ipo_cancel_bool = %s,"
                 "@ipo_cancel_date = %s,"
                 "@ipo_cancel_reason = %s,"
                 "@terminate_date = %s",
                 data)
        db.query("update ipo set "
                 "ipo_cancel_bool = @ipo_cancel_bool,"
                 "ipo_cancel_date = @ipo_cancel_date,"
                 "ipo_cancel_reason = @ipo_cancel_reason,"
                 "terminate_date = @terminate_date,"
                 "update_date = NOW() "
                 "where ipo_index = @ipo_index")
    else:
        print("해당보고서 형식은 데이터베이스 로직에서 지원하지 않습니다.")
        pass


#######################################################################################################################
#
# 메인문 https://kin.naver.com/qna/detail.nhn?d1id=1&dirId=10402&docId=378158321#answer1
#
#######################################################################################################################
if __name__ == "__main__":
    # 객체 생성 및 초기값 설정
    print(datetime.datetime.now(), "공휴일(holiday_check) 확인 모듈 초기화", flush=True)
    holiday = holiday_check.HolidayCheck(
        "fF5OJkqdLH%2BOGt4%2F3F0FtaLc%2B4GsfqE%2BNxyg6iTAAl3NeK8jTGT26iCHraMiKTY%2FfXyHfox2azdPtitSo4SoXw%3D%3D")
    print(datetime.datetime.now(), "슬랙(slack) 모듈 초기화", flush=True)
    sl = slack.SlackBot("xoxb-3040674388865-3013432400759-NKjLH4nlL1CzMwDil9SYUpvh")
    print(datetime.datetime.now(), "다트(dart) 모듈 초기화", flush=True)
    dart = DartCrawling("a5f0a27ad384e3e1af8ea81c2f0be00a419bfb1e")
    dart_native = dart_api.DartApi("a5f0a27ad384e3e1af8ea81c2f0be00a419bfb1e")
    print(datetime.datetime.now(), "데이터베이스(mysql_db) 모듈 초기화", flush=True)
    # db = mysql_db.MysqlDB("34.135.81.32", 3306, "stockServer", "admin", "P@ssVV0rd")
    db = mysql_db.MysqlDB("34.135.81.32", 3306, "stockServer", "everywhere", "everypw")
    db.connection()
    db.query("SET collation_connection = 'utf8mb4_general_ci';")

    sl.slack_post_message('#crawling', '크롤링 로직 가동이 시작되었습니다.')
    sl.slack_post_message('#test', '크롤링 로직 가동이 시작되었습니다.')

    while True:
        target_date = input("\n\n보고서 탐색일을 입력해주세요 :")
        # target_date = "2021-10-05"
        # target_date = "2021-12-17"
        # target_date = "2021-12-22"  # 대한전선 증권신고서 - datetime.datetime.now()
        # target_date = "2022-01-19"  # 대한전선 증권신고서 - datetime.datetime.now()
        # target_date = "2021-11-30"  # 래몽래인 증권신고서 - datetime.datetime.now()
        # target_date = "2021-12-23"  # 래몽래인 - datetime.datetime.now()
        # target_date = "2022-01-21"  # LG에너지솔루션 - datetime.datetime.now()
        print("크롤링 기준일자 : " + target_date)
        if holiday.is_it(target_date):
            yyyy, mm, dd = target_date.split('-')
            print("휴무일 입니다." + holiday.print_whichday(int(yyyy), int(mm), int(dd)))
        else:
            sl.slack_post_message("#crawling", "[기준일] " + str(target_date))
            sl.slack_post_message("#test", "[기준일] " + str(target_date))

            # 금일 보고서 목록 확인
            report_list = dart.list_report(target_date)
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
                crawling_dict = {}
                rcode = dart.kind_report(report_name[i])
                rnum = report_number[i]
                rdartcode = dart_code[i]
                rcpname = company_name[i]
                rcpindex = index_name[i]
                rstockcode = stock_code[i]

                # DART 크롤링 진행하여 dict 반환
                try:
                    # 2022.05.21 : 인자값 index -> 회사이름으로 변경
                    #crawling_dict = dart.report_to_dict(rcode, rnum, rcpindex)
                    crawling_dict = dart.report_to_dict(rcode, rnum, rcpname)
                    if type(crawling_dict) == type(None):
                        raise IndexError
                    else:
                        crawling_dict["rcode"] = rcode
                        crawling_dict["rcpindex"] = rcpindex
                        crawling_dict["rcpname"] = rcpname
                        crawling_dict["rstockcode"] = rstockcode
                        crawling_dict["rdartcode"] = rdartcode
                        sl.slack_post_message("#test", "[" + str(datetime.datetime.now()) + "] " + str(crawling_dict))

                        print("\033[36m \033[40m - " + rcode + dart.report_type(
                            rcode) + " - " + rcpname + " https://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + rnum + "\033[0m")
                        print("```\n", json.dumps(crawling_dict, ensure_ascii=False, indent=2), "\n```")
                except IndexError:
                    if rcode != "E00":
                        sl.slack_post_message("#crawling", "*[ERROR]*[" + line_info("info") + "][크롤링] ```" +
                                              "관련 데이터 없음 (조회중 형식문제 발생 예상)" + "[" + str(rcode) + "/" +
                                              str(rdartcode) + "/ " + str(rcpname) + "/ " + str(report_name[i]))

                        print("\033[36m \033[40m - " + rcode + dart.report_type(
                            rcode) + " - " + rcpname + " https://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + rnum + "\033[0m")
                        print(str(rcpname), traceback.format_exc())
                    continue
                except notIpoError:
                    # print("__r00_logic: 공모주(기업공개)가 아니므로 종료합니다. 추후 실권주 처리 구현 필요. " + str(rcpname))
                    continue
                except Exception as e:
                    sl.slack_post_message("#crawling", "*[ERROR]*[" + line_info("info") + "][크롤링] ```" +
                                          str(e) + "[" + str(rcode) + "] " + str(rcpname) + "(" + str(
                        rstockcode) + ")(" + str(
                        rdartcode) + ")```")

                    print("\033[36m \033[40m - " + rcode + dart.report_type(
                        rcode) + " - " + rcpname + " https://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + rnum + "\033[0m")
                    print(str(rcpname), traceback.format_exc())
                    continue

                # 비상장주식의 실권주 및 손상값(kind 없음) 건너뛰기
                if "kind" not in crawling_dict.keys():
                    print("손상된 값(kind 없음)을 건너뜁니다.", crawling_dict["rcpname"])
                    continue
                if crawling_dict["kind"] == "기타" or \
                        (crawling_dict["rcpindex"] == 'E' or crawling_dict["rcpindex"] == '기타') or \
                        (crawling_dict["rcpindex"] == 'N' or crawling_dict["rcpindex"] == '코넥스') and \
                        crawling_dict["kind"] == "실권주":
                    print("비상장주식 실권주 또는 주주우선배정 처리를 건너뜁니다.(코넥스,기타)", crawling_dict["rcpname"])
                    continue  # 비상장주식의 실권주 건너뛰기

                # API(지분증권)로 체크할 리스트에 추가
                check_dict = {"rcpindex": rcpindex, "rcpname": rcpname, "rstockcode": rstockcode,
                              "rdartcode": rdartcode, "kind": crawling_dict["kind"]}
                check_api_list.append(check_dict)

                # 데이터베이스 업로드
                if type(crawling_dict) == type(None):
                    pass
                else:
                    try:
                        upload_dict(crawling_dict)
                    except Exception as e:
                        sl.slack_post_message("#crawling", "*[ERROR]*[" + line_info("info") + "][데이터베이스] ```" +
                                              str(e) + "[" + str(rcode) + "] " + str(rcpname) + "(" + str(
                            rstockcode) + ")(" + str(
                            rdartcode) + "```")
                        print(str(rcpname), traceback.format_exc())

            # 정상적으로 크롤링된 종목들의 추가정보를 DART API에서 불러옴. (모든 타이밍에 조회하여 최신자료로 갱신진행)
            print("===================================[DART_API_N00]===================================")
            for api_dict in check_api_list:
                # 비상장주식의 실권주 및 손상값(kind 없음) 건너뛰기
                try:
                    if "kind" not in api_dict.keys():
                        print("손상된 값을 건너뜁니다.", api_dict["rcpname"], api_dict)
                        continue
                    if api_dict["kind"] == "기타" or \
                            (api_dict["rcpindex"] == 'E' or api_dict["rcpindex"] == '기타') or \
                            (api_dict["rcpindex"] == 'N' or api_dict["rcpindex"] == '코넥스') and \
                            api_dict["kind"] == "실권주":
                        print("비상장주식 실권주 또는 주주우선배정 처리를 건너뜁니다.(코넥스,기타)", api_dict["rcpname"])
                        continue
                except Exception as e:
                    sl.slack_post_message("#crawling", "*[ERROR]*[" + line_info("info") + "][DART_API 조건문] ```" +
                                          str(e) + "[" + str(api_dict["rcode"]) + "] " + str(
                        api_dict["rcpname"]) + "(" + str(api_dict["rstockcode"]) + ")(" + str(
                        api_dict["rdartcode"]) + "```")
                    print(str(api_dict["rcpname"]), traceback.format_exc())
                    continue

                # DART API 지분 데이터 조회
                try:
                    print("\033[37m \033[40m - DART_API: " + api_dict["rcpname"] + "\033[0m")
                    api_dict["rcode"] = 'N00'
                    ddata = dart_native.get_ipo_data(api_dict["rdartcode"], target_date.replace("-", ""))
                    api_dict["apidata"] = ddata
                    api_dict["induty_code"] = dart.get_sector(api_dict["rdartcode"])

                    if api_dict["rcpindex"] == 'K':
                        api_dict["rcpindex"] = "코스닥"
                    elif api_dict["rcpindex"] == 'Y':
                        api_dict["rcpindex"] = "코스피"
                    elif api_dict["rcpindex"] == 'N':
                        api_dict["rcpindex"] = "코넥스"
                    elif api_dict["rcpindex"] == 'E':
                        api_dict["rcpindex"] = "기타"

                    ipo_end_date = datetime.datetime.strptime(api_dict["apidata"]["ipo_schedule"]["ipo_start_date"],
                                                              "%Y-%m-%d") + datetime.timedelta(days=1)
                    while holiday.is_it(ipo_end_date) or ipo_end_date.weekday() >= 5:
                        ipo_end_date = ipo_end_date + datetime.timedelta(days=1)
                    api_dict["apidata"]["ipo_schedule"]["ipo_end_date"] = ipo_end_date.strftime("%Y-%m-%d")

                    print("```\n", json.dumps(api_dict, ensure_ascii=False, indent=2), "\n```")
                except Exception as e:
                    sl.slack_post_message("#crawling", "*[ERROR]*[" + line_info("info") + "][DART_API] ```" +
                                          str(e) + "[" + str(api_dict["rcode"]) + "] " + str(
                        api_dict["rcpname"]) + "(" + str(api_dict["rstockcode"]) + ")(" + str(
                        api_dict["rdartcode"]) + "```")
                    print(str(api_dict["rcpname"]), traceback.format_exc())

                # 데이터베이스 업로드
                try:
                    upload_dict(api_dict)
                except Exception as e:
                    sl.slack_post_message("#crawling",
                                          "*[ERROR]*[" + line_info("info") + "][데이터베이스 - DART지분증권API] ```" +
                                          str(e) + "[" + str(api_dict["rcode"]) + "] " + str(
                                              api_dict["rcpname"]) + "(" + str(api_dict["rstockcode"]) + ")(" + str(
                                              api_dict["rdartcode"]) + "```")
                    print(str(api_dict["rcpname"]), traceback.format_exc())
