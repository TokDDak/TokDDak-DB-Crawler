"""
HotelGeneralCrawler : TripAdvisor API를 이용해서 원하는 정보를 가져와 가공하여 DB에 저장하는 클래스
"""

import configparser
import json
import http.client
import numpy as np
import requests
import pymysql

class HotelGeneralCrawler():

    def moneyGeneralTrimmer(self, input_string):
        
        '''
        Hotel Price data would look like "$263 - $505".
        This method change the one to 263. (get minimum price)
        '''
        
        temp_list = input_string.split(" - ")
        return (temp_list[0])[1:].replace(",", "")

    def dataOverlapChecker(self, base_data, checking_info):
        '''
        겹치는 데이터가 있는지 여부를 확인하는 메서드
        '''
        
        if (checking_info[0],) in base_data:
            return True
        return False


    def hotelInformationGetter(self, input_data, offset):
        
        '''
        Get hotel data and extract information.
        '''
        
        # 파라미터 정리
        location_id = input_data[0]
        cityId = input_data[1]
        
        # config 변수 정리
        config = configparser.ConfigParser()
        config.read('config.ini')

        rapid_api_key = config['API']['tripadvisorapi']
        
        # rapidapi 연결하기
        conn = http.client.HTTPSConnection("tripadvisor1.p.rapidapi.com")
        headers = {
            'x-rapidapi-host': "tripadvisor1.p.rapidapi.com",
            'x-rapidapi-key': rapid_api_key
            }
        
        # 호텔 리퀘스트 만들기 (함수의 파라미터로 들어오는 location_id를 이용하여 국가 선택 + 옵션설정을 원하면 rapidAPI홈페이지에서 설정하기)
        api_url = ("/hotels/list?offset="
                            +str(offset)
                            +"&currency=USD&child_rm_ages=7%252C10&limit=30&checkin=2020-01-08&order=asc&lang=en_US&sort=recommended&nights=1&location_id="
                            + str(location_id)
                            +"&adults=1&rooms=1")
        
        # &hotel_class=5 -> 5등급만 뽑기
        
        conn.request("GET", api_url, headers=headers)
        res = conn.getresponse()
        
        # response 읽기
        data = res.read()

        # response를 dictionary로 만들기
        dict_data = json.loads(data)
        #print(dict_data) # 확인 출력문
        
        # 딕셔너리 다듬기
        dict_data_data = dict_data.get('data')

        hotels_data = [] # 테이블에 들어갈 호텔들의 정보를 담아두는 리스트 (이름, 클래스, 가격, 카테고리?)
        for one_data in dict_data_data:
            try:
                hotel_data = []
                hotel_data.append(one_data.get("name"))
                sub_category = one_data.get("subcategory_type")
                sub_categorys = ["hotel", "small_hotel", "hostel", "guest_house", "villa"]
                if not sub_category in sub_categorys:
                    continue
                else:
                    hotel_data.append(sub_category)                
                hotel_data.append(int(float(one_data.get("hotel_class"))))
                hotel_data.append(int(self.moneyGeneralTrimmer(one_data.get("price"))))
                hotel_data.append(cityId) # cityId
                hotels_data.append(hotel_data)
            except AttributeError as e:
                continue

        return hotels_data

    def sqlController(self, hotel_info_list):
        
        '''
        SQL문을 컨트롤 하는 메서드
        '''
        
        # config 변수 정리
        config = configparser.ConfigParser()
        config.read('config.ini')

        db_host = config['DATABASE']['db_host']
        db_user = config['DATABASE']['db_user']
        db_password = config['DATABASE']['db_password']
        db_name = config['DATABASE']['db_name']
        
        # 스키마와 연결
        conn = pymysql.connect(host=db_host, 
                                user=db_user, 
                                password=db_password,
                                db=db_name,
                                charset='utf8')
        # 커서 생성
        curs = conn.cursor()
        
        # SQL문들
        sql = "select name from Hotel"
        sql_insert_hotel_information = "INSERT INTO City (continent, country, name) VALUES('Europe', 'France', 'Paris')"
        sql_insert_hotels_information = "INSERT INTO Hotel (name, category, subCategory, cost, CityId) VALUES(%s, %s, %s, %s, %s)"
        sql_delete = "DELETE FROM Hotel"
        sql_update_price = "UPDATE Hotel SET cost = %s WHERE name = %s"
        
        # 호텔 테이블의 내용을 가져오기 + 출력
        curs.execute(sql) 
        hotel_data = curs.fetchall() 
        #print("hotel_data", hotel_data) # 지금까지 DB에 있는 호텔 데이터
        
        # 트립어드바이져 API를 이용해서 가져온 정보가 호텔 테이블에 들어있는 정보와 겹치는지 확인 후 아닌 것은 추가 맞는 것은 업데이트
        new_hotel_data = []
        overlapped_hotel_cost_data = []
        
        for info in hotel_info_list:
            if not self.dataOverlapChecker(hotel_data, info): # 겹치는 호텔정보가 아닐 경우
                print("info", info)
                new_hotel_data.append(info)
            else: # 겹치는 호텔의 경우 -> cost만 업데이트 한다
                overlapped_hotel_cost_data.append((info[3], info[0]))
        print("overlapped_hotel_cost_data", overlapped_hotel_cost_data)
        print("new_hotel_data", new_hotel_data)
        curs.executemany(sql_insert_hotels_information, new_hotel_data)
        curs.executemany(sql_update_price, overlapped_hotel_cost_data)
        
        #curs.execute(sql_delete) # 테이블 삭제
        #data = curs.fetchall() # 가져오기 (select에서 사용)
        #print(data)
        
        conn.commit() # RDS에 반영하기
        