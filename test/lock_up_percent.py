import OpenDartReader
from urllib.request import urlopen
from bs4 import BeautifulSoup
###############################################################################
# 수정사항
# 1. 현재 비상장 기업만 읽어오도록 함, 실권주도 읽어올 수 있도록 수정
# 2. 표 위에 표시된 (원, 백만원) 단위 읽어서 알려줘야 함.
# 3. 증권신고서가 여러개인 경우 여러번 수행하도록 수정
###############################################################################

api_key = 'a7911a1206c5a0cb3e8566e766e744be51b7fa76'
dart = OpenDartReader(api_key)
# 2022-01-14 : LG 에너지솔루션

# today = input("날짜를 입력하세요 : ")
today = "2022-01-14"
financial_company = {}

# 오늘의 기타법인의 증권신고서(지분증권) 읽어오기
df_test = dart.list(start=today, end=today, final=False)
s = (df_test.report_nm.str.contains('[발행조건확정]증권신고서(지분증권)', case=False, regex=False))
df_test = df_test.loc[s, :]
s = (df_test.corp_cls.str.contains('Y', case=False, regex=False))
df_test = df_test.loc[s, :]
print(df_test)

rcept_no = list(df_test.rcept_no)
xml_text = dart.document(rcept_no[0])
subDocs = dart.sub_docs(rcept_no[0], "증권발행조건확정")
subDoc = list(subDocs.url)

print(subDoc[0])
report = urlopen(subDoc[0])
r = report.read()
xmlsoup = BeautifulSoup(r, 'html.parser')
body = xmlsoup.find("body")
summarizeTable = body.find_all("tr")

for s in range(len(summarizeTable)):
    temp = summarizeTable[s].find_all("td")

    # if len(temp) < 15:
    #     continue

    # print(temp, temp[0].get_text().replace(" ", ""))
    if temp and "확약" in temp[0].get_text().replace(" ", ""):
        temp_td = summarizeTable[s + 5].find_all("td")
        temp_td2 = summarizeTable[s + 4].find_all("td")
        notMustHave = int(temp_td2[14].get_text().replace(',', ''))
        haveSum = int(temp_td[14].get_text().replace(',', ''))
        print((haveSum-notMustHave)/haveSum*100)
        break
