import requests
import json
import re
from io import BytesIO
from zipfile import ZipFile
from xml.etree.ElementTree import parse
from urllib.request import urlopen


def if_null(target_object):
    if target_object == '-':
        return None
    else:
        return target_object


def str_to_int(number):
    if number == '-':
        return None
    return int(number.replace(",", ""))


def str_to_date(string_date):
    # 날짜를 2021-12-23 형식으로 변경합니다.
    string_date = str(string_date)
    if string_date == '-':
        return None
    str_list = string_date.split(' ')

    date = []
    date.append(re.sub(r'[^0-9]', '', str_list[0]))  # year
    date.append(re.sub(r'[^0-9]', '', str_list[1]))  # month
    date.append(re.sub(r'[^0-9]', '', str_list[2]))  # day
    date = '-'.join(date)
    return date


class DartApi():
    dart_api_url = "https://opendart.fss.or.kr/api/"
    __api_key = ""
    __dict_data = {}
    __corpCode_xmlTree = "noData"

    def __init__(self, api_key):
        self.__api_key = api_key
        # 기업이름 및 고유코드가 담겨있는 xml 파일 다운로드  # 추후에 수정필요. 절대경로기반
        url_corpCode = 'https://opendart.fss.or.kr/api/corpCode.xml'
        params_url_corpCode = {'crtfc_key': self.__api_key}
        res_corpCode = requests.get(url_corpCode, params_url_corpCode)
        with ZipFile(BytesIO(res_corpCode.content)) as zipfile:
            zipfile.extractall('c:\\openDART')
        # xml 파일 초기화 (분석)
        self.__corpCode_xmlTree = parse('c:\\openDART\corpCode.xml')

    def get_corpcode(self, corp_name):
        corpCode_root = self.__corpCode_xmlTree.getroot()
        corpCode_list = self.__corpCode_root.findall('list')
        corp_code = ''
        for l in corpCode_list:
            if l.findtext('corp_name') == corp_name:
                corp_code = l.findtext('corp_code')
        return corp_code

    def get_ipo_data(self, dart_code, target_date):
        # 대상일 기준 최근 1년간의 지분증권 데이터를 가져온다.
        url_fdpp = "https://opendart.fss.or.kr/api/estkRs.json?crtfc_key={}&corp_code={}&bgn_de={}&end_de={}".format(
            self.__api_key,
            dart_code,
            # str(target_date),
            # str(target_date))
            str(int(target_date) - 10000),
            str(int(target_date)))

        # get 요청
        resp = urlopen(url_fdpp)
        resp_json = resp.read().decode()
        resp_dict = json.loads(resp_json)

        # 정상 반환 확인

        if resp_dict["status"] != "000":
            print(resp_dict["status"])
            return "no data targetDate... dart_api module"

        dict_data = {}
        # 일반사항 데이터
        target_key = resp_dict["group"][0]["list"][0]
        dict_data["ipo_schedule"] = {
            "ipo_refund_date": str_to_date(target_key["pymd"]),  # 납입기일 (환불예상일)
            "ipo_start_date": str_to_date(target_key["sbd"]),  # 청약기일 (청약시작일) - 실권주의 경우 구주주 청약일
            "ipo_start_date_ann": str_to_date(target_key["sband"]),  # 청약공고일
            "배정공고일": str_to_date(target_key["asand"]),
            "배정기준일": str_to_date(target_key["asstd"])
        }
        dict_data["ex"] = {
            "stock_type": if_null(target_key["exstk"]),
            "price": if_null(target_key["exprc"]),
            "date": if_null(target_key["expd"])
        }
        # 증권의종류 데이터
        target_key = resp_dict["group"][1]["list"][0]
        dict_data["par_value"] = str_to_int(target_key["fv"])  # 액면가
        dict_data["ipo_price_low"] = str_to_int(target_key["slprc"].replace(",", ""))  # 공모가 하단 밴드
        dict_data["number_of_ipo_shares"] = str_to_int(target_key["stkcnt"])  # 총 공모 주식수
        dict_data["ipo_total_price"] = str_to_int(target_key["slta"])  # 총 공모 금액
        # 인수인정보 데이터
        target_key = resp_dict["group"][2]["list"][0]
        dict_data["대표주간사"] = target_key["actnmn"]
        dict_data["증권의종류"] = target_key["stksen"]
        # 자금의 사용목적 데이터 (여기값을 다 더하면 총 공모액 규모 나옴)
        target_key = resp_dict["group"][3]["list"][0]
        dict_data["purpose_of_funds"] = target_key["se"]  # 자금의 사용목적
        # 매출인에 관한사항 데이터
        target_key = resp_dict["group"][4]["list"][0]
        # 일반청약자 환매 청구권 데이터
        target_key = resp_dict["group"][5]["list"][0]
        dict_data["put_back_option"] = {
            "who": if_null(target_key["exavivr"]),
            "price": str_to_int(target_key["exprc"]),
            "deadline": if_null(target_key["expd"]),
            "reason": if_null(target_key["grtrs"])
        }

        return dict_data


if __name__ == "__main__":
    dart = DartApi("a5f0a27ad384e3e1af8ea81c2f0be00a419bfb1e")
    ddata = dart.get_ipo_data("00990819", "20210101")
    print(json.dumps(ddata, ensure_ascii=False, indent=2))

    while True:
        target_dartcode, target_date = input("DART종목번호 yyyymmdd 입력").split()
        ddata = dart.get_ipo_data(target_dartcode, target_date)
        print(json.dumps(ddata, ensure_ascii=False, indent=2))
        # 자이언트스텝 01264438 20211101
        # 대한전선  00113207 20220505


'''
        # 일반사항 데이터
        target_key = resp_dict["group"][0]["list"][0]
        dict_data["보고서번호"] = target_key["rcept_no"]
        dict_data["기업명"] = target_key["corp_name"]
        dict_data["기업번호"] = target_key["corp_code"]
        dict_data["시장구분"] = target_key["corp_cls"]
        dict_data["수요예측일"] = str_to_date(target_key["sbd"])
        dict_data["납입일(환불일)"] = str_to_date(target_key["pymd"])
        dict_data["공모청약일"] = str_to_date(target_key["sband"])
        # 증권의종류 데이터
        target_key = resp_dict["group"][1]["list"][0]
        dict_data["액면가"] = str_to_int(target_key["fv"])
        dict_data["수요예측밴드_하단"] = str_to_int(target_key["slprc"].replace(",", ""))
        dict_data["공모주식수"] = str_to_int(target_key["stkcnt"])
        # 인수인정보 데이터
        target_key = resp_dict["group"][2]["list"][0]
        dict_data["대표주간사"] = target_key["actnmn"]
        # 자금의 사용목적 데이터 (여기값을 다 더하면 총 공모액 규모 나옴)
        target_key = resp_dict["group"][3]["list"][0]
        # 매출인에 관한사항 데이터
        target_key = resp_dict["group"][4]["list"][0]
        # 일반청약자 환매 청구권 데이터
        target_key = resp_dict["group"][5]["list"][0]
        dict_data["환매청구권_가능자"] = target_key["exavivr"]
        dict_data["환매청구권_기준가격"] = target_key["exprc"]
        dict_data["환매청구권_행사기간"] = target_key["expd"]
'''
