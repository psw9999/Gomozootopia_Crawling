import requests
import datetime
from bs4 import BeautifulSoup
# 원본소스 : https://aspdotnet.tistory.com/2495
# API 출처 : https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15012690


class HolidayCheck:
    __apikey = ""  # 일반 인증키(Encoding)
    __today = datetime.datetime.now()
    __holiday = []

    def __init__(self, apikey):
        self.__apikey = apikey
        self.set_holiday_list()

    def print_whichday(self, year, month, day):
        r = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        aday = datetime.date(year, month, day)
        bday = aday.weekday()
        return r[bday]

    def get_request_query(self, url, operation, params, serviceKey):
        import urllib.parse as urlparse
        params = urlparse.urlencode(params)
        request_query = url + '/' + operation + '?' + params + '&' + 'serviceKey' + '=' + serviceKey
        return request_query

    def is_it(self, target_date):
        # True: 공휴일, False: 영업일
        if isinstance(target_date, datetime.datetime):
            target_date = target_date.strftime("%Y-%m-%d")
        if isinstance(target_date, str):
            tl = len(target_date)
            if tl != 10:
                target_date = datetime.datetime.strptime(target_date, "%Y%m%d")
            elif tl == 10:
                target_date = datetime.datetime.strptime(target_date, "%Y-%m-%d")
            else:
                return False
        else:
            return False

        # 토요일 일요일은 쉬는날 반환
        target_date = target_date.date()
        if 5 <= target_date.weekday() <= 6:
            return True
        for hdate, hname in self.__holiday:
            # print(hdate, hname, " ===== ", target_date)
            if hdate.date() == target_date:
                return True
        return False

    def print_holiday_list(self):
        print(self.__holiday)

    def set_holiday_list(self):
        for year in range(self.__today.year - 1, self.__today.year + 2):  # 작년도, 금년도, 내년도 휴일만 가져옴.
            for month in range(1, 13):
                # 요청 인자 선언
                if month < 10:
                    month = '0' + str(month)
                else:
                    month = str(month)

                url = 'http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService'
                operation = 'getRestDeInfo'
                params = {'solYear': year, 'solMonth': month}

                # 공휴일 정보 조회 (API 요청)
                request_query = self.get_request_query(url, operation, params, self.__apikey)
                get_data = requests.get(request_query)

                # 분석
                if get_data.ok:
                    soup = BeautifulSoup(get_data.content, 'html.parser')
                    item = soup.findAll('item')
                    # print(item)
                    for i in item:
                        day = int(i.locdate.string[-2:])
                        # weekname = self.print_whichday(int(year), int(month), day)
                        holiday_date = datetime.datetime.strptime(i.locdate.string, '%Y%m%d')
                        self.__holiday.append([holiday_date, i.datename.string])


if __name__ == "__main__":
    holiday = HolidayCheck(
        "fF5OJkqdLH%2BOGt4%2F3F0FtaLc%2B4GsfqE%2BNxyg6iTAAl3NeK8jTGT26iCHraMiKTY%2FfXyHfox2azdPtitSo4SoXw%3D%3D")

    print(holiday.print_holiday_list())

    print(holiday.is_it(datetime.datetime.now()))
    print("2022-01-22", holiday.is_it("2022-01-22"))
    print("20220101(신정)", holiday.is_it("20220101"))  # 신정
    print("20220301(삼일절)", holiday.is_it("20220301"))  # 삼일절
    print("20220302(평일)", holiday.is_it("20220302"))  # 평일

    print("2021-12-11(토요일)", holiday.is_it("2021-12-11"))  # 토요일
    ipo_end_date = datetime.datetime.strptime("2021-12-10", "%Y-%m-%d") + datetime.timedelta(days=1)
    print("2021-12-11(토요일,date형식)", holiday.is_it(ipo_end_date))  # 12월 10일 + 1

    while True:
        ddddd = input()  # 1) 2022-01-22,  2) 20220122,  3) datetime
        print(holiday.is_it(ddddd))
