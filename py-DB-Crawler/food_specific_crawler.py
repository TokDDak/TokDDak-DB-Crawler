# 식당 3 등급만 넣기.

import requests
import json
import http.client
import numpy as np
import pymysql
import configparser


class FoodSpecificCrawler:
    def moneySpecificTrimmer(self, input_string):
        """
        Food Price data would look like "$20 - $40".
        This method change the one to 30.
        This element will be inserted in cost column.
        """
        temp_list = input_string.replace(",", "").split(" - ")
        if len(temp_list) == 1:
            return int(temp_list[0][1:])
        mean = (int)((int(temp_list[0][1:]) + int(temp_list[1][1:])) / 2)

        return mean

    def priceLevelTrimmer(self, input_price_level):
        """
        Price level data would look like $$ - $$$.
        This method change the one to 2.
        $ -> 1
        $$ - $$$ -> 2
        $$$$ -> 3
        This element will be inserted in grade column.
        """
        if input_price_level == None:
            return None

        if input_price_level.count("$") == 1:
            return 1
        elif input_price_level.count("$") == 5:
            return 2
        else:
            return 3

    def dataOverlapChecker(self, base_data, checking_info):
        """
        겹치는 데이터가 있는지 여부를 확인하는 메서드
        """

        if (checking_info[0],) in base_data:
            return True
        return False

    def foodInformationGetter(self, input_data, offset):
        """
        Get food data and extract information.
        """

        # 파라미터 변수 정리
        location_id = input_data[0]
        cityId = input_data[1]

        # config 변수 정리
        config = configparser.ConfigParser()
        config.read("config.ini")

        rapid_api_key = config["API"]["tripadvisorapi"]

        # rapidapi 연결하기
        conn = http.client.HTTPSConnection("tripadvisor1.p.rapidapi.com")

        headers = {
            "x-rapidapi-host": "tripadvisor1.p.rapidapi.com",
            "x-rapidapi-key": rapid_api_key,
        }
        # 호텔 리퀘스트 만들기 (함수의 파라미터로 들어오는 location_id를 이용하여 국가 선택 + 옵션설정을 원하면 rapidAPI홈페이지에서 설정하기)

        conn.request(
            "GET",
            "/restaurants/list?lunit=km&limit=30&prices_restaurants=10953&currency=USD&offset="
            + str(offset)
            + "&lang=en_US&location_id="
            + str(location_id),
            headers=headers,
        )

        # prices_restaurants=10953%252C10954&  -> 1과 3단계만 넣기. 지금은 3단계만 넣는 것으로 되어있음. 그리고 저 주석이 맞는지 모르겠음.

        res = conn.getresponse()

        # response 읽기
        data = res.read()

        # response를 dictionary로 만들기
        dict_data = json.loads(data)
        # print(dict_data) # 확인 출력문

        # 딕셔너리 다듬기
        dict_data_data = dict_data.get("data")

        # price_list = [] # 호텔의 가격을 담아둘 리스트 (우선은 안쓰고 추후에 가운데 값 구할 때 사용?)
        foods_data = []  # 테이블에 들어갈 호텔들의 정보를 담아두는 리스트 (이름, 클래스, 가격, 카테고리?)
        for one_data in dict_data_data:
            try:
                food_data = []
                if one_data.get("name") == None:
                    continue
                food_data.append(one_data.get("name"))
                food_data.append(
                    self.priceLevelTrimmer(one_data.get("price_level"))
                )  # grade

                if -1 == one_data.get("price", -1):  # cost가 없으면 그 데이터는 넣지 않는다.
                    continue
                elif 1 == int(
                    self.moneySpecificTrimmer(one_data.get("price"))
                ):  # cost가 1이면 안넣기
                    continue
                else:
                    food_data.append(
                        int(self.moneySpecificTrimmer(one_data.get("price")))
                    )  # 넣기

                food_data.append(cityId)  # cityId
                foods_data.append(food_data)
            except AttributeError as e:
                continue
        return foods_data

    def sqlController(self, food_info_list):

        """
        SQL문을 컨트롤 하는 메서드
        """

        # config 변수 정리
        config = configparser.ConfigParser()
        config.read("config.ini")

        db_host = config["DATABASE"]["db_host"]
        db_user = config["DATABASE"]["db_user"]
        db_password = config["DATABASE"]["db_password"]
        db_name = config["DATABASE"]["db_name"]

        # 스키마와 연결
        conn = pymysql.connect(
            host=db_host, user=db_user, password=db_password, db=db_name, charset="utf8"
        )
        # 커서 생성
        curs = conn.cursor()

        # SQL문들
        sql = "select name from Food"
        sql_insert_foods_information = (
            "INSERT INTO Food (name, grade, cost, CityId) VALUES(%s, %s, %s, %s)"
        )
        sql_delete = "DELETE FROM Food"
        sql_update_price = "UPDATE Food SET cost = %s WHERE name = %s"

        # Food 테이블의 내용을 가져오기 + 출력
        curs.execute(sql)
        food_data = curs.fetchall()
        # print("food_data", food_data)

        # 트립어드바이져 API를 이용해서 가져온 정보가 Food 테이블에 들어있는 정보와 겹치는지 확인 후 아닌 것은 추가 맞는 것은 업데이트
        new_food_data = []
        overlapped_food_cost_data = []
        for info in food_info_list:
            if not self.dataOverlapChecker(food_data, info):  # 겹치는 호텔정보가 아닐 경우
                print("info", info)
                new_food_data.append(info)
            else:  # 겹치는 food의 경우 -> cost만 업데이트 한다
                overlapped_food_cost_data.append((info[3], info[0]))
        print("overlapped_food_cost_data", overlapped_food_cost_data)
        print("new_food_data", new_food_data)
        curs.executemany(sql_insert_foods_information, new_food_data)
        curs.executemany(sql_update_price, overlapped_food_cost_data)

        conn.commit()  # RDS에 반영하기
