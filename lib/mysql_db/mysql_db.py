import pymysql


class MysqlDB():
    __host = "127.0.0.1"
    __port = 3306
    __database = ""
    __username = ""
    __password = ""
    '''
    __host = "34.135.81.32"
    __port = 3306
    __database = "stockServer"
    __username = "admin"
    __password = "P@ssVV0rd"
    '''
    __cursor = -1
    __conn = -1

    def sethost(self, host):
        self.__host = host

    def setport(self, port):
        self.__port = port

    def setedatabase(self, db):
        self.__database = db

    def setusername(self, username):
        self.__username = username

    def setpassword(self, password):
        self.__password = password

    def __init__(self, host, port, db_name, db_username, db_userpw):
        self.__host = host
        self.__port = port
        self.__database = db_name
        self.__username = db_username
        self.__password = db_userpw
        print("make mysql object.")

    def connection(self):
        self.__conn = pymysql.connect(host=self.__host,
                               user=self.__username,
                               passwd=self.__password,
                               db=self.__database,
                               port=self.__port,
                               use_unicode=True,
                               charset='utf8')
        self.__cursor = self.__conn.cursor()

    def disconnection(self):
        self.__conn.close()

    def query(self, *args):
        if len(args) == 1:  # 단순 쿼리문
            try:
                if self.__cursor == -1:
                    raise "please make connection first"
                self.__cursor.execute(args[0])
                result = self.__cursor.fetchall()
                self.__conn.commit()
                return result
            except Exception as e:
                self.__conn.rollback()
                raise e
        elif len(args) == 2:  # 인자값을 추가로 넘길 때
            try:
                if self.__cursor == -1:
                    raise "please make connection first"
                self.__cursor.execute(args[0], args[1])
                result = self.__cursor.fetchall()
                self.__conn.commit()
                return result
            except Exception as e:
                self.__conn.rollback()
                raise e
        else:
            raise "no argument"

    def query_select(self, query):
        # deprecated. use this.query
        try:
            if self.__cursor == -1:
                raise "please make connection first"
            self.__cursor.execute(query)
            result = self.__cursor.fetchall()
            self.__conn.commit()
            return result
        except Exception as e:
            self.__conn.rollback()
            raise e

    def query_insert(self, query, values):
        # deprecated. use this.query
        try:
            if self.__cursor == -1:
                raise "please make connection first"
            self.__cursor.execute(query, values)
            result = self.__cursor.fetchall()
            self.__conn.commit()
            return result
        except Exception as e:
            self.__conn.rollback()
            raise e


if __name__ == "__main__":
    print("=======================[ DB객체 초기화 ]=========================")
    mysql = MysqlDB("34.135.81.32", 3306, "stockServer", "admin", "P@ssVV0rd")
    mysql.connection()
    mysql.query("SET collation_connection = 'utf8mb4_general_ci';")

    '''
    # hello = mysql.query(""
    #                     "SELECT ipo_index, stock_name, stock_kinds, dart_code, regist_date"
    #                     " FROM ipo"
    #                     " WHERE stock_name ='래몽래인' AND dart_code=1234567890"
    #                     " ORDER BY regist_date DESC"
    #                     " LIMIT 100;")
    target_dart_code = "1234567890"
    hello = mysql.query("SELECT ipo_index, stock_name, dart_code, stock_code \
                        FROM ( \
                            SELECT * \
                            FROM ipo \
                            ORDER BY ipo_index DESC \
                            LIMIT 100 \
                        ) AS ddd \
                        WHERE dart_code = %s \
                        ", target_dart_code)
    print(type(hello))
    print("전체 데이터 :", hello)
    print("첫번째 데이터 :", hello[0])  # 첫번째 데이터 출력  # 조회결과가 없을경우. IndexError: tuple index out of range
    print("첫번째 요소 :", hello[0][0])  # 첫번째 데이터의 첫번째 요소 출력
    '''
    '''
    print("=======================[ select 테스트 ]=========================")
    # result = mysql.query_select("select * from ipo")
    result = mysql.query("select * from ipo")
    print(result)

    print("=======================[ insert 데이터 생성 ]=========================")
    data = (
        "종목명입니다",
        123456,
        1234567890,
        "코스모스",
        "2222-01-01",
        "1000-10-10",
        "1000-10-20",
        "1000-10-30",
        "1000-11-03",
        12.34,
        1200.5,
        10000,
        8000,
        9000,
        "안녕하세요",
        "일반공모자",
        9500,
        "1000-12-31",
        "2022-01-30"
    )
    print(data)

    print("=======================[ insert 테스트 ]=========================")
    result = mysql.query(""
                                "INSERT INTO ipo ("
                                "stock_name, stock_code, dart_code, stock_exchange, ipo_forecast_date, ipo_start_date, ipo_end_date, ipo_refund_date, ipo_debut_date, lock_up_percent, ipo_institutional_acceptance_rate, ipo_price, ipo_price_low, ipo_price_high, underwriter, regist_date"
                                ")"
                                "VALUES ("
                                "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s ,%s ,%s, %s"
                                ")"
                                "", data)
    print(result)
    '''

    '''
    print("=======================[ insert 데이터 생성 ]=========================")
    data = (
        "종목명입니다",
        123456,
        1234567890,
        "코스모스",
        "2222-01-01",
        "1000-10-10",
        "1000-10-20",
        "1000-10-30",
        "1000-11-03",
        12.34,
        1200.5,
        10000,
        8000,
        9000,
        "안녕하세요",
        "일반공모자",
        9500,
        "1000-12-31",
        "2022-01-30"
    )
    print(data)
    
    print("=======================[ insert 테스트 ]=========================")
    result = mysql.query(""
        "INSERT INTO ipo ("
        "stock_name, stock_code, dart_code, stock_exchange, ipo_forecast_date, ipo_start_date, ipo_end_date, ipo_refund_date, ipo_debut_date, lock_up_percent, ipo_institutional_acceptance_rate, ipo_price, ipo_price_low, ipo_price_high, underwriter, regist_date"
        ")"
        "VALUES ("
        "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s ,%s ,%s, %s"
        ")"
        "", data)
    print(result)
    
    mysql.query("SET @ipo_index = 23, @ipo_debut_date = '2021-01-10'; UPDATE ipo SET ipo_debut_date = DATE_FORMAT(@ipo_debut_date, '%Y-%m-%d'), update_date = NOW() WHERE ipo_index = @ipo_index;")
    '''
    # mysql.query("UPDATE ipo SET ipo_debut_date = DATE_FORMAT('2021-01-15', '%Y-%m-%d'), update_date = NOW() WHERE ipo_index = 23;")



    target_report = [['N00', 'DARTAPI_지분estkRs'],
                     ['R00', '증권발행실적보고서'],
                     ['R01', '증권신고서(지분증권)'],
                     ['R02', '[기재정정]증권신고서(지분증권)'],
                     ['R03', '[발행조건확정]증권신고서(지분증권)']]
    #mysql.query("SET @ipo_index = 23, @ipo_debut_date = '2021-01-10'")
    # 크롤링 데이터 업로드 테스트 로직.
    test_case = 'NEW_INDEX'
    if test_case == 'R00':
        print("증권발행실적보고서")
        data = (23, '2021-01-19')
        mysql.query("SET @ipo_index = %s, @ipo_debut_date = %s", data)
        mysql.query("UPDATE ipo SET ipo_debut_date = DATE_FORMAT(@ipo_debut_date, '%Y-%m-%d'), update_date = NOW() WHERE ipo_index = @ipo_index")
    elif test_case == 'R01' or test_case == 'R02':
        print("증권신고서 1.일반값")
        data = (23, '001235', 1111111111, 22222222, 10001, 20002, 50000)
        mysql.query("set @ipo_index = %s, @sector_code = %s, @profits = %s, @sales = %s, @ipo_price_low = %s, @ipo_price_high = %s, @ipo_min_deposit = %s;", data)
        mysql.query("update ipo \
                    set sector = @sector_code, profits = @profits, sales = @sales, ipo_price_low = @ipo_price_low, ipo_price_high = @ipo_price_high, ipo_min_deposit = @ipo_min_deposit, update_date = NOW() \
                    where ipo_index = @ipo_index;")
        print("증권신고서 2.주간사")
        data = (23, '신한금융투자', 3333, 2222, 1111, 14)
        mysql.query("set @ipo_index = %s, @under_name = %s, @ind_total_max = %s, @ind_total_min = %s, @ind_can_max = %s, @ind_can_min = %s;", data)
        mysql.query("insert into ipo_underwriter \
	                    (ipo_index, under_name, ind_total_max, ind_total_min, ind_can_max, ind_can_min, update_date) \
	                    values (@ipo_index, @under_name, @ind_total_max, @ind_total_min, @ind_can_max, @ind_can_min, now()) \
                    on duplicate key \
	                    update ind_total_max = @ind_total_max, ind_total_min = @ind_total_min, ind_can_max = @ind_can_max, ind_can_min = @ind_can_min, update_date = NOW();")
    elif test_case == 'R03':
        print("발행조건확정 증권신고서")
        data = (23, 72.34, 2345.21, 39900)
        mysql.query("set @ipo_index = %s, @lock_up_percent = %s, @ipo_institutional_acceptance_rate = %s, @ipo_price = %s", data)
        mysql.query("update ipo \
                    set lock_up_percent = @lock_up_percent, ipo_institutional_acceptance_rate = @ipo_institutional_acceptance_rate, ipo_price = @ipo_price, update_date = NOW() \
                    where ipo_index = @ipo_index")
    elif test_case == 'N00':
        print("DART API 지분증권")
        data = (23, '코스닥', '2021-02-01', '2021-02-02', '2021-02-03', '2021-02-04', None, None, None, 999999)
        mysql.query("set @ipo_index = %s, @stock_exchange = %s, @ipo_forecast_date = %s, @ipo_start_date = %s, @ipo_end_date = %s, @ipo_refund_date = %s, @put_back_option_who = %s, @put_back_option_price = %s, @put_back_option_deadline = %s, @number_of_ipo_shares = %s;", data)
        mysql.query("update ipo \
                    set stock_exchange = @stock_exchange, ipo_forecast_date = @ipo_forecast_date, ipo_start_date = @ipo_start_date, ipo_end_date = @ipo_end_date, ipo_refund_date = @ipo_refund_date, put_back_option_who = @put_back_option_who, put_back_option_price = @put_back_option_price, put_back_option_deadline = @put_back_option_deadline, number_of_ipo_shares = @number_of_ipo_shares, update_date = NOW() \
                    where ipo_index = @ipo_index")
    elif test_case == 'NEW_INDEX':
        print("신규 IpoIndex 등록 또는 기존번호 검색")
        data = ("TestCase", '123456')
        mysql.query("SET @stock_name = %s, @dart_code = %s", data)
        mysql.query("INSERT INTO ipo (stock_name, dart_code, regist_date) \
                    SELECT @stock_name, @dart_code, now() \
                    from dual \
                    WHERE NOT EXISTS ( \
                        SELECT * FROM ipo \
                        WHERE \
                            dart_code = @dart_code AND \
                            regist_date > DATE_FORMAT(DATE_ADD(NOW(), INTERVAL -6 MONTH), '%Y-%m-%d'));")
        result = mysql.query("SELECT ipo_index \
                    FROM ipo \
                    WHERE \
                        dart_code = @dart_code AND \
                        regist_date > DATE_FORMAT(DATE_ADD(NOW(), INTERVAL -6 MONTH), '%Y-%m-%d');")
        print("ipoIndex :", result[0][0])
    else:
        print("올바른 보고서 번호를 선택해주세요.")

