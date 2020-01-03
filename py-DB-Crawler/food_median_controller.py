# 식당 중앙값 넣기

import requests
import json
import http.client
import numpy as np
import pymysql
import configparser

class FoodMedianController():
    # outlier 제거하는 메소드
    def reject_outliers(self, data, m=2):
        return data[abs(data - np.mean(data)) < m * np.std(data)]


    def foodMedianController(self):
        
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
        sql_select_food = "select * from Food"
        sql_select_median = "select * from Median"
        sql_insert_median_data = "INSERT INTO Median (cityId, category, cost, urlFood) VALUES(%s, %s, %s, %s)"
        sql_update_median_data = "UPDATE Median SET cost = %s, urlFood = %s WHERE cityId = %s AND category = %s"
        
        # 테이블에 들어갈 url
        URL_PARIS = "https://www.tripadvisor.co.kr/Restaurants-g187147-Paris_Ile_de_France.html"
        URL_NEWYORK = "https://www.tripadvisor.co.kr/Restaurants-g60763-New_York_City_New_York.html"
        URL_TOKYO = "https://www.tripadvisor.co.kr/Restaurants-g298184-Tokyo_Tokyo_Prefecture_Kanto-Hotels.html"
        URL_TAIPEI = "https://www.tripadvisor.co.kr/Restaurants-g293913-Taipei.html"
        URL_DANANG = "https://www.tripadvisor.co.kr/Restaurants-g298085-Da_Nang.html"
        URL_CEBU = "https://www.tripadvisor.co.kr/Restaurants-g294261-Cebu_Island_Visayas.html"
        URLS = (URL_PARIS, URL_NEWYORK, URL_TOKYO, URL_TAIPEI, URL_DANANG, URL_CEBU)
        
        # 테이블에 들어갈 음식점 호칭
        RESTAURANT_NAMING = ("간편식", "일반음식점", "고급음식점")
        
        # Food 테이블의 내용을 가져오기 + 출력
        curs.execute(sql_select_food) 
        food_data = curs.fetchall() 
        #print("@@@food_data", food_data)
        
        # 트립어드바이져 API를 이용해서 가져온 정보가 Food 테이블에 들어있는 정보와 겹치는지 확인 후 아닌 것은 추가 맞는 것은 업데이트
        cities = [[], [], [], [], [], []]

        for food_info in food_data:
            if food_info[4] == 1:
                cities[0].append(food_info)
            elif food_info[4] == 2:
                cities[1].append(food_info)
            elif food_info[4] == 3:
                cities[2].append(food_info)
            elif food_info[4] == 4:
                cities[3].append(food_info)
            elif food_info[4] == 5:
                if food_info[3] > 10000:
                    continue
                cities[4].append(food_info)
            else:
                cities[5].append(food_info)
        
        for city in cities:
            temp_list = [[], [], []]
            for restaurant in city:
                if restaurant[2] == "1":
                    temp_list[0].append(restaurant[3])
                elif restaurant[2] =="2":
                    temp_list[1].append(restaurant[3])
                else:
                    temp_list[2].append(restaurant[3])
            city[:] = temp_list[:]
            
        median = []    
        np_cities = np.array(cities)
        for idx, np_city in enumerate(np_cities):
            inner_median = []
            for np_grade in np_city:
                inner_median.append(int(round(np.mean(self.reject_outliers(np.array(np_grade))))))
            #inner_median.append(idx + 1)
            median.append(inner_median)
        print(median)
            
        # Median 테이블의 내용을 가져오기
        curs.execute(sql_select_median) 
        median_data = curs.fetchall() 
        print("median_data", len(median_data))

        final_median_list = []
        if len(median_data) == 24: # 테이블 비었을 경우 -> insert
            for city_idx, one_city in enumerate(median):
                for idx, one_data in enumerate(one_city):
                    temp_list = []
                    temp_list.append(city_idx+1)
                    temp_list.append(RESTAURANT_NAMING[idx])
                    temp_list.append(one_data)
                    temp_list.append(URLS[city_idx])
                    final_median_list.append(temp_list)  
            print("final_median_list", final_median_list)
            curs.executemany(sql_insert_median_data, final_median_list)
        else: # 테이블 이미 차있는 경우 -> update
            print("median_data", median_data)
            for city_idx, one_city in enumerate(median):
                for idx, one_data in enumerate(one_city):
                    temp_list = []
                    temp_list.append(one_data)
                    temp_list.append(URLS[city_idx])
                    temp_list.append(city_idx+1)
                    temp_list.append(RESTAURANT_NAMING[idx])
                    final_median_list.append(temp_list) 
            curs.executemany(sql_update_median_data, final_median_list)

        conn.commit() # RDS에 반영하기
