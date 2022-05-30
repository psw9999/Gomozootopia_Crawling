import OpenDartReader
from urllib.request import urlopen
from bs4 import BeautifulSoup
###############################################################################
# 실권주 공모가(모집매출가액), R01, R02
# 2022-04-03
###############################################################################

api_key = 'a7911a1206c5a0cb3e8566e766e744be51b7fa76'
dart = OpenDartReader(api_key)
# 2022-01-14 : LG 에너지솔루션
# 2022-01-19 : 대한전선 실권주

# today = input("날짜를 입력하세요 : ")
today = "2022-01-19"
financial_company = {}

# 오늘의 기타법인의 증권신고서(지분증권) 읽어오기
df_test = dart.list(start=today, end=today, final=False)
s = (df_test.report_nm.str.contains('[기재정정]증권신고서(지분증권)', case=False, regex=False))
df_test = df_test.loc[s, :]
s = (df_test.corp_cls.str.contains('Y', case=False, regex=False))
df_test = df_test.loc[s, :]
print(df_test)

rcept_no = list(df_test.rcept_no)
xml_text = dart.document(rcept_no[0])
subDocs = dart.sub_docs(rcept_no[0], "모집 또는 매출에 관한 일반사항")
subDoc = list(subDocs.url)

print(subDoc[0])
report = urlopen(subDoc[0])
r = report.read()
xmlsoup = BeautifulSoup(r, 'html.parser')
body = xmlsoup.find("body")
summarizeTable = body.find_all("tr")




forfeited_price_flag = False
forfeited_price = -1
for s in range(len(summarizeTable)):  # summarizeTable = body.find_all("tr")
    temp = summarizeTable[s]

    if temp and "모집(매출)가액" in temp.get_text().replace(" ", ""):
        temp_div = temp.find_all(["td", "th"])
        for td_i in range(len(temp_div)):
            if temp_div and "모집(매출)가액" in temp_div[td_i].get_text().replace(" ", ""):
                temp_next = summarizeTable[s+1].find_all(["td", "th"])
                forfeited_price = int(temp_next[td_i].get_text().replace(',', ''))
                forfeited_price_flag = True
                break

    if forfeited_price_flag:
        break

print("실권주 공모가:", forfeited_price)
