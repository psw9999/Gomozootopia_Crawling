# 공모주 알리미 데이터수집서버
이하 데이터 수집서버의 크롤링 관련 내용
- DART API를 통한 기본 정보 수집
- DART 보고서 크롤링을 통한 관련 정보 수집

파이썬 Dict 출력 예시 : https://www.notion.so/45d5e59a8df64af984d7fe0c09154613
<br/>
파이썬 to 데이터베이스 쿼리 예시 : https://www.notion.so/DB-Query-3ffed5f6b0354293b58aad9486be6f14

<br/>
<br/>

## 할일

### 쿼리문 작성

크롤링 후 데이터베이스에 올릴 쿼리문 작성

1. ipo 테이블에서
   - stock_name(회사명)과 stock_kinds(공모주/실권주 구분)을 통해
   - ipo_index 값을 가져온다.
   - 이 때, regist_date 순으로 정렬하여 가장 최근에 등록된 값을 가져온다.
     - 단, 가장 최근에 등록된 값이 1년 이후인 경우 무시한다. (없는 것으로 취급하여 새로 등록)
2. 조회된 ipo_index를 기준으로 한다.
   - 해당 값을 기준으로 update를 진행한다.
   - 조회된값이 없을경우 insert를 진행할 수 없다. 
     - 사유 : DART API를 통해 조회된 값을 가장먼저 등록하므로 ipo_index가 반드시 존재해야한다. 또한 `ipo_underwriter` , `ipo_financials` , `ipo_comment` 등은 ipo_index를 forigen key로 사용하므로, 해당 값 없이는 등록을 할 수 없다.





### DB 관련

ipo_financials 데이터베이스 추가 (상장시점 기준의 데이터를 보관하는 데이터베이스)

ipo_comment 데이터베이스 추가 (각 종목별 히스토리 보관 / 표출은 최신코멘트)
