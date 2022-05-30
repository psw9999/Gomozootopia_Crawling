import string
import OpenDartReader
from xml.etree.ElementTree import Element, SubElement, ElementTree, dump
from urllib.request import urlopen
from bs4 import BeautifulSoup
import copy
import re

###############################################################################
# 수정이력
# 2022-02-03 : (단위 : 원), (단위 : 백만원) 크롤링
###############################################################################

api_key = 'a7911a1206c5a0cb3e8566e766e744be51b7fa76'
dart = OpenDartReader(api_key)

def financialStatements() :
    global rcept_numbers, company_codes, Requirements, IPO_data

    for index, rcept_no in enumerate(rcept_numbers) :
        if index == 1:
            break
        sales, profit, unit = 0, 0, 1
        IPO_data[company_codes[index]] = Requirements.copy()
        subDocs = dart.sub_docs(rcept_no, "재무에 관한 사항")
        subDoc = list(subDocs.url)
        report = urlopen(subDoc[0])
        r = report.read()
        xmlsoup = BeautifulSoup(r,'html.parser')
        tables = xmlsoup.find_all("table")
        
        for i in range(len(tables)) :
            summarizeTable = tables[i].find_all("tr")
            for s in summarizeTable :
                temp = s.find_all("td")
            
                if len(temp) < 2 :
                    continue
        
                if "매출액" in temp[0].get_text() :
                    #print(sales)
                    sales = temp[1].get_text().replace(',','').rstrip()
        
                elif "영업이익" in temp[0].get_text() :
                    profit = temp[1].get_text().replace(',','').rstrip()

                if profit != 0 and sales != 0 :
                    for j in range(i-1,-1,-1) :
                        temp2 = tables[j].find_all("td")
                        
                        if 1 <= len(temp2) <= 2 :
                            for t in temp2 :
                                if t.has_attr("align") :
                                    if t.get_text().strip().find("(단위:원)") :
                                        print(t.get_text().strip())
                                        print(i,j)
                                        if "백만원" in t.get_text().strip() :
                                            unit = 1000000
                                        if "천원" in t.get_text().strip() :
                                            unit = 1000
                                        else :
                                            unit = 1
                                        break
                        
                        if unit != 0 :
                            break
                    break

            if profit != 0 and sales != 0 and unit != 0 :
                #print(profit,sales,unit)
                break
        
        if profit[0] == '(' :
            profit = re.sub(r'[^0-9]','',profit)
            profit = int(profit) * -1
        
        IPO_data[company_codes[index]]["profit"] = int(profit) * unit
        IPO_data[company_codes[index]]["sales"] = int(sales) * unit

def stockQuantityStatements() :
    global rcept_numbers, company_codes, Requirements, IPO_data
    
    for index, rcept_no in enumerate(rcept_numbers) :
        financial_company = {}
        subDocs = dart.sub_docs(rcept_no, "모집 또는 매출에 관한 일반사항")
        subDoc = list(subDocs.url)
    
        report = urlopen(subDoc[0])
        r = report.read()
        xmlsoup = BeautifulSoup(r, 'html.parser')
        body = xmlsoup.find("body")
        summarizeTable = body.find_all("tr")

        for s in range(len(summarizeTable)):
            temp = summarizeTable[s].find_all("th")

            if len(temp) < 4:
                continue

            if "배정물량" in temp[1].get_text().replace(" ", ""):
                temp_td = summarizeTable[s + 1].find_all("td")
                if len(temp_td) > 3:
                    company = temp_td[0].get_text().replace("\xa0", "")
                    #print(company)
                    limit = temp_td[2].get_text().replace("\n", "").replace(" ", "")
                    # 다음 td에 청약 최고 한도 서술되어 있음

                    # if re.compile('[가-힣]+').findall(limit) == ['주']:
                    temp_td2 = summarizeTable[s + 2].find_all("td")  # 다음 tr 값에 주) 에 대한 내용이 있음
                    limit2 = ' '.join(temp_td2[1].get_text().split())  # 개행문자, 띄워쓰기 중복 등 제거
                    limit3 = limit2.replace(',', '').replace(' ', '').replace('주~', '~')  # (숫자)주~(숫자)주 를 찾기위해 ,와 공백문자 제거 and 주~ 을 ~로 변환
                    limit4 = re.findall(r'일반|우대|\d{2,3}%|\d{2,10}~\d{2,10}주', limit3)  # (숫자)주~(숫자)주 정규식 찾기
                    limit5 = ''
                    #print(limit4)
                    try:
                        for i in range(len(limit4)):
                            if limit4[i] == '일반':
                                if limit4[i + 1] == '100%':
                                    limit5 = limit4[i + 2]
                                    #print(limit5)
                                elif limit4[i + 1].find("주") == -1:
                                    continue
                                else:
                                    limit5 = limit4[i + 1]
                                    #print(limit5)
                                    break
                            else:
                                continue

                        limit6 = []  # 숫자에 , 찍기
                        for num in limit5.replace('주', '').split('~'):  # 주 를 빼고 ~로 숫자를 나눔
                            limit6.append(format(int(num), ',d'))  # 숫자에 콤마찍음

                        financial_company[company] = [temp_td[1].get_text().replace("\n", "").replace(" ", "").replace("\xa0", ""),
                                                    str(limit6[0]) + '주~' + str(limit6[1]) + '주']

                    except ValueError as e:
                        financial_company[company] = [temp_td[1].get_text().replace("\n", "").replace(" ", "").replace("\xa0", ""),
                                                    temp_td[2].get_text().replace("\n", "").replace(" ", "")]
    
        for s in range(len(summarizeTable)) :
            temp = summarizeTable[s].find_all("th")
            temp2 = summarizeTable[s].find_all("td")
            if len(temp) > 1:
                focus_word_hopeprice = re.sub(r'\s+', '', temp[0].get_text())
                if "희망공모가액" in focus_word_hopeprice:
                    temp_td = summarizeTable[s].find_all("td")
                    if len(temp_td) > 1:
                        hopeprice = temp_td[1].get_text()

            elif len(temp2) > 1:
                focus_word_hopeprice = re.sub(r'\s+', '', temp2[0].get_text())
                if "희망공모가액" in focus_word_hopeprice:
                    temp_td = summarizeTable[s].find_all("td")
                    if len(temp_td) > 1:
                        hopeprice = temp_td[1].get_text()
        
        hopeprice = hopeprice.replace(",", "").replace("원","")
        hope = re.findall(r'\d{1,100}', hopeprice)
    
        IPO_data[company_codes[index]]["ipo_price_low"] = hope[0]
        IPO_data[company_codes[index]]["ipo_price_high"] = hope[1]
    
        IPO_data[company_codes[index]]["stockQuantity"] = financial_company.copy()

def test() :
    global rcept_numbers, company_codes, Requirements, IPO_data

    tempTable = 0
    
    for index, rcept_no in enumerate(rcept_numbers) :
        if index == 1 :
            break
        sales, profit, unit = 0, 0, 1
        IPO_data[company_codes[index]] = Requirements.copy()
        subDocs = dart.sub_docs(rcept_no, "재무에 관한 사항")    
        subDoc = list(subDocs.url)
        report = urlopen(subDoc[0])
        r = report.read()
        xmlsoup = BeautifulSoup(r,'html.parser')
        tables = xmlsoup.find_all(["table","p"])
        
        for i in range(len(tables)) :
            temp = tables[i].find_all("a")
            if len(temp) > 0 :
                if "III.재무에관한사항" in temp[0].get_text().replace(" ", ""):
                    for j in range(i+1, len(tables)) :
                        t = tables[j].find_all("tbody")
                        flag = False
                        if len(t) > 0 and "(단위:" in t[0].get_text().replace(" ", ""):
                            t_row = tables[j+1].find_all("tr")
                            tt_list = []
                            for k in range(len(t_row)):  # 연도(분기) 정보 취득  (조건확인)

                                print(k, "============\n")
                                kkk = 0
                                for abcd in t_row[k].find_all():
                                    kkk += 1
                                    print(str(kkk) + "] ", abcd)

                                if "년" in t_row[k].get_text().replace("연", "년"):
                                    flag = True
                                    for tr in t_row[k].find_all():
                                        tr = tr.get_text().replace(" ", "")
                                        if tr == "":
                                            continue
                                        tt_list.append(re.findall(r'\d{1,4}[년기/.]', tr))
                                    break
                            recent_index = 0
                            if tt_list:  # 최근값이 있는 열(column) Index 취득
                                for k in tt_list:
                                    pass
                            for k in range(len(t_row)):  # 테이블에서 '항목'에 [recent_index]를 조회하여 반환
                                pass

                            print(tt_list)    
                        if flag:
                            break



                            
                                
    
day_list = ["2021-12-06","2021-12-07"]

today = input("날짜를 입력하세요 : ")
IPO_data = {}

# 오늘의 기타법인의 증권신고서(지분증권) 읽어오기
df_test = dart.list(start = today ,end= today, final=False)
s = (df_test.report_nm.str.contains('[기재정정]증권신고서(지분증권)', case = False, regex = False))
df_test = df_test.loc[s, :]
s = (df_test.corp_cls.str.contains('E', case = False, regex = False))
df_test = df_test.loc[s, :]
print(df_test)

Requirements = {'profit' : 0, 'sales' : 0, 'stockQuantity' : 0,'ipo_price_low' : 0, 'ipo_price_high' : 0}

rcept_numbers = list(df_test.rcept_no)
company_codes = list(df_test.corp_code)

# financialStatements()
#stockQuantityStatements()
test()
#print(IPO_data)
