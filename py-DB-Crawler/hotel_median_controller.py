# 호텔 중앙값 넣기

import requests
import json
import http.client
import numpy as np
import pymysql
import configparser


class HotelMedianController:
    # outlier 제거하는 메소드
    def reject_outliers(self, data, m=2):
        return data[abs(data - np.mean(data)) < m * np.std(data)]

    def hotelMedianController(self):
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
        sql_select_hotel = "select * from Hotel"
        sql_select_median = "select * from Median"
        sql_insert_median_data = "INSERT INTO Median (cityId, category, cost, urlHotel) VALUES(%s, %s, %s, %s)"
        sql_update_median_data = "UPDATE Median SET cost = %s, urlHotel = %s WHERE cityId = %s AND category = %s"

        # 테이블에 들어갈 url
        URL_PARIS = (
            "https://www.tripadvisor.co.kr/Hotels-g187147-Paris_Ile_de_France.html"
        )
        URL_NEWYORK = (
            "https://www.tripadvisor.co.kr/Hotels-g60763-New_York_City_New_York.html"
        )
        URL_TOKYO = "https://www.tripadvisor.co.kr/Hotels-g298184-Tokyo_Tokyo_Prefecture_Kanto-Hotels.html"
        URL_TAIPEI = "https://www.tripadvisor.co.kr/Hotels-g293913-Taipei.html"
        URL_DANANG = "https://www.tripadvisor.co.kr/Hotels-g298085-Da_Nang.html"
        URL_CEBU = "https://www.tripadvisor.co.kr/Hotels-g294261-Cebu_Island_Visayas-Hotels.html"
        URLS = [URL_PARIS, URL_NEWYORK, URL_TOKYO, URL_TAIPEI, URL_DANANG, URL_CEBU]

        # 테이블에 들어갈 음식점 호칭
        HOTEL_NAMING = ["저가호텔", "일반호텔", "고급호텔", "최고급호텔"]  # 1성과 2성 모두 저가호텔로하기

        # Hotel 테이블의 내용을 가져오기 + 출력
        curs.execute(sql_select_hotel)
        hotel_data = curs.fetchall()
        # print("@@@hotel_data", hotel_data)

        # 트립어드바이져 API를 이용해서 가져온 정보가 Food 테이블에 들어있는 정보와 겹치는지 확인 후 아닌 것은 추가 맞는 것은 업데이트
        cities = [[], [], [], [], [], []]

        for hotel_info in hotel_data:
            if hotel_info[5] == 1:
                cities[0].append(hotel_info)
            elif hotel_info[5] == 2:
                cities[1].append(hotel_info)
            elif hotel_info[5] == 3:
                cities[2].append(hotel_info)
            elif hotel_info[5] == 4:
                cities[3].append(hotel_info)
            elif hotel_info[5] == 5:
                cities[4].append(hotel_info)
            else:
                cities[5].append(hotel_info)

        for city in cities:
            temp_list = [[], [], [], [], []]
            for hotel in city:
                if hotel[3] == "0":
                    continue
                elif hotel[3] == "1":
                    temp_list[0].append(hotel[4])
                elif hotel[3] == "2":
                    temp_list[1].append(hotel[4])
                elif hotel[3] == "3":
                    temp_list[2].append(hotel[4])
                elif hotel[3] == "4":
                    temp_list[3].append(hotel[4])
                else:
                    temp_list[4].append(hotel[4])
            city[:] = temp_list[:]
        # print("cities", cities) # 각 도시별, 등급별 가격이 모임

        median = []
        np_cities = np.array(cities)
        for city_idx, np_city in enumerate(np_cities):
            inner_median = []
            for grade_idx, np_grade in enumerate(np_city):
                inner_median.append(
                    int(round(np.mean(self.reject_outliers(np.array(np_grade)))))
                )
            median.append(inner_median)
        print("median", median)

        # Refactor: 1성과 2성의 평균으로 저가호텔가격을 만들기 (1성이 초저가 였는데 2성과 평균을 내고 초저가 가격은 없엔다))
        hotel_median_infos = []
        for city in median:
            hotel_median_list = [int((city[0] + city[1]) / 2), *city[2:]]
            hotel_median_infos.append(hotel_median_list)

        # Median 테이블의 내용을 가져오기
        curs.execute(sql_select_median)
        median_data = curs.fetchall()
        print("median_data", len(median_data))

        final_median_list = []
        print("len(median_data)", len(median_data))
        if len(median_data) == 0:  # 테이블 비었을 경우 -> insert
            for city_idx, one_city in enumerate(hotel_median_infos):
                for idx, one_data in enumerate(one_city):
                    temp_list = []
                    temp_list.append(city_idx + 1)
                    temp_list.append(HOTEL_NAMING[idx])
                    temp_list.append(one_data)
                    temp_list.append(URLS[city_idx])
                    final_median_list.append(temp_list)
            print("final_median_list", final_median_list)
            curs.executemany(sql_insert_median_data, final_median_list)
        else:  # 테이블 이미 차있는 경우 -> update
            print("median_data", median_data)
            for city_idx, one_city in enumerate(hotel_median_infos):
                for idx, one_data in enumerate(one_city):
                    temp_list = []
                    temp_list.append(one_data)
                    temp_list.append(URLS[city_idx])
                    temp_list.append(city_idx + 1)
                    temp_list.append(HOTEL_NAMING[idx])
                    final_median_list.append(temp_list)
            print("final_median_list", final_median_list)
            curs.execute("SET SQL_SAFE_UPDATES = 0")
            curs.executemany(sql_update_median_data, final_median_list)

        conn.commit()  # RDS에 반영하기
