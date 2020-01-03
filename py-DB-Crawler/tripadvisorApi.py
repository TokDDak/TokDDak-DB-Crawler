# 메인

from hotel_general_crawler import HotelGeneralCrawler
from hotel_specific_crawler import HotelSpecificCrawler
from food_general_crawler import FoodGeneralCrawler
from food_specific_crawler import FoodSpecificCrawler
from hotel_median_controller import HotelMedianController
from food_median_controller import FoodMedianController


class TripadvisorApi:
    def runAllFunction(self):
        """
        {"france_paris" : 187147, "cityId" : 1},
        {"usa_newyork" : 60763, "cityId" : 2},
        {"japan_tokyo" : 298184, "cityId" : 3},
        {"taiwan_taipei" : 293913, "cityId" : 4},
        {"vietnam_danang" : 298085, "cityId" : 5},
        {"philippines_cebu" : 294261, "cityId" : 6}
        ((187147, 1), (60763, 2), (298184, 3), (293913, 4), (298085, 5), (294261, 6),)
        """

        ALL_CITY_LOCATION_ID = (
            (187147, 1),
            (60763, 2),
            (298184, 3),
            (293913, 4),
            (298085, 5),
            (294261, 6),
        )
        LOCATION_ID_5 = ALL_CITY_LOCATION_ID[4]

        hotel_general_crawler = HotelGeneralCrawler()
        for offset in range(0, 60, 30):
            for location_id in ALL_CITY_LOCATION_ID:
                print(location_id)
                print("offset: ", offset)
                hotel_info_list = hotel_general_crawler.hotelInformationGetter(
                    location_id, offset
                )
                hotel_general_crawler.sqlController(hotel_info_list)

        hotel_specific_crawler = HotelSpecificCrawler()
        for offset in range(90, 150, 30):
            for location_id in LOCATION_ID_5:
                print(location_id)
                print("offset: ", offset)
                hotel_info_list = hotel_specific_crawler.hotelInformationGetter(
                    location_id, offset
                )
                hotel_specific_crawler.sqlController(hotel_info_list)

        food_general_crawler = FoodGeneralCrawler()
        for offset in range(0, 150, 30):
            for location_id in ALL_CITY_LOCATION_ID:
                print(location_id)
                print("offset: ", offset)
                restaurant_info_list = food_general_crawler.foodInformationGetter(
                    location_id, offset
                )
                food_general_crawler.sqlController(restaurant_info_list)

        food_specific_crawler = FoodSpecificCrawler()
        for offset in range(0, 120, 30):
            for location_id in ALL_CITY_LOCATION_ID:
                print(location_id)
                print("offset: ", offset)
                restaurant_info_list = food_specific_crawler.foodInformationGetter(
                    location_id, offset
                )
                food_specific_crawler.sqlController(restaurant_info_list)

        hotel_median_controller = HotelMedianController()
        hotel_median_controller.hotelMedianController()

        food_median_controller = FoodMedianController()
        food_median_controller.foodMedianController()


tripadvisor_api = TripadvisorApi()
tripadvisor_api.runAllFunction()
