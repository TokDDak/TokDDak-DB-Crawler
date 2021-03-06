# TokDDak 프로젝트에 사용되는 Hotel, Food, Activity table record를 채우기 위한 코드들이 있는 레포지토리.

#### 버전 1.0  


### config  
- config.ini에서 RDS 정보와 API key를 가져온다.    


### 메서드 기능  
- hotelInformationGetter와 restaurantInformationGetter가 주요 기능을 수행하는 메소드 :    
- 각각 API에서 JSON형식으로 정보를 가져오고 원하는 필드만 뽑아서 리스트로 만드는 기능.    

- sqlController : 위에서 생성된 리스트와 sql문을 pymysql 모듈을 이용하여 실행한다.

- moneyTrimmer, priceLevelTrimmer : hotelInformationGetter와 restaurantInformationGetter 메서드에서 사용하는 메서드로서 API에서 받은 데이터를 원하는 포맷으로 바꾸어주는 기능을 수행하는 메소드.

- dataOverlapChecker : 이미 RDS에 들어있는 데이터인지 아닌지 판단하는 메소드.

- hotelMedianController, foodMedianController : 한 나라의 같은 등급의 호텔과 식당 대표 금액을 구하는 메소드.

- reject_outliers : 위의 대표 금액을 구하는 메소드에서 사용하는 극단치 값을 제거하는 메소드.


### 사용 모듈  
- pymysql (https://github.com/PyMySQL/PyMySQL)


### 추후 추가 예정 기능
[x] price값이 없는 식당은 RDS에 추가하지 않도록 만든다.  
[x] 1과 3등급에 해당되는 식당 데이터를 더 가져오도록 만든다.  
[x] 금액이 1인 식당은 추가하지 않는다. (그런데 파리에서 몇 개 추가되는 것이 있음) 
[ ] 자동으로 DB에 업데이트하는 기능은 추후 추가 예정. (스케쥴러)    



****
## 추가 제작

- activity_db.ipynb : activity 더미 엑셀 파일을 db에 넣기위한 프로그램


### DB 넣는 순서.
- city들을 넣어준다.
- hotel과 food를 각각 테이블에 해당 프로그램을 사용하여 넣어준다.
- hotel과 food의 대표값을 median 테이블에 해당 프로그램을 사용하여 넣어준다.
- activity를 activity 테이블에 해당 프로그램을 사용하여 넣어준다.
