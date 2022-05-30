# Mysql DB 모듈

2022-01-30, 작성자 : 최현식



### 용도

Mysql Database에 연결하여 상호작용을 하는 모듈입니다.


### 예시

```python
# DB정보를 사용하여 개체를 생성합니다.
mysql = MysqlDB("127.0.0.1", 3306, "database_name", "username", "password")

# 입력된 정보를 통해 DB에 연결합니다.
mysql.connection()
```



### 사전작업

1. 데이터베이스 연결을 생성한 후 연결



## MysqlDB 함수

__init__ (token)

​	최초로 class를 만들때 사용됩니다.

- token : 슬랙BOT이 사용할 Token 정보를 입력합니다.
- return : `null`




__slack_post_message__ (channel, msg)

​	원하는 `#채널` 에 채팅을 보냅니다.

- channel : 채팅을 보낼 채널명을 입력합니다. 이때 `#` 도 포함해야합니다.
- msg : 채팅으로 전달할 내용을 입력합니다.

- return : `null`
- 