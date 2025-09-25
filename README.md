# 주식 차트 데이터의 자동 크롤링 메크로 개발

💰 상금 정리

    튜토리얼 : 튜토리얼 완료하고 신청 확인되면 2만원 상당(선착순 10팀)
    Task 1: 완료 시 5만원 (선착순 3팀에게 지급)
    Task 2: 완료 시 5만원 (선착순 3팀에게 지급)
    Task 3: 완료 시 10만원 (선착순 3팀에게 지급)
    Task 4: 완료 시 50만원 (선착순 1팀에게 지급)


📝 과제 상세

<br>[튜토리얼]</br>
과제내용 : 
1) 팀 빌딩(인원 제한 없음, 개인 참여 가능)
2) 구글폼 신청, 
3) 튜토리얼 결과 이메일 제출

튜토리얼 결과 제출 : 
Private Information (출제자의 메일 주소이므로 제거하였습니다.)

상금 : 
과제 완료시 오프라인 미팅 후 2만원 상당 쿠폰(편의점/커피) 지급


<br>[Task 1]</br>
구현 내용 : 
1) 트레이딩뷰(TradingView) 접속 
2) 구글(종목코드 GOOG) 종목 선택 
3) 주 데이터를 선택
4) 엑셀로 다운로드하는 매크로 구현 

프로그램 출력물 : 
GOOG 종목에 대한 주 데이터 CSV 파일

상금 : 
과제 완료시 오프라인 미팅 후 5만원 지급(선착순 3팀)


<br>[Task 2]</br>

구현  내용 : 
Task 1을 확장 하여 구글(Google) 년/월/주/일/시/10분 단위(지연로딩) 데이터 다운로드 구현<br></br>
★ 특히, 일, 시, 10분 단위 선택 시 마우스 드래그를 이용한 과거 데이터를 불러오는 기능 구현 필요

프로그램 출력물 : 
GOOG 종목에 대한 년/월/주/일/시/10분  데이터 CSV 파일

상금 :
과제 완료시 오프라인 미팅 후 5만원 지급(선착순 3팀)


<br>[Task 3]</br>

구현 내용 : 
Task 2를 확장하여, 지정한 보조지표를 추가하고, 지정한 30개 종목에 대해 Task 2 반복 수행 구현

프로그램 출력물 : 
지정한 30개 종목에 대한  년/월/주/일/시/10분  데이터 CSV 파일

상금 : 
과제 완료시 오프라인 미팅 후 10만원 지급(선착순 3팀)


<br>[Task 4]</br>

구현 내용: 
Task 3을 확장하여 주기적으로 자동으로 데이터 수집 및 DB 저장까지 실행되는 전자동화 구축 구현  

프로그램 출력물 : 
매일 오전 9시 자동 실행, 3일간 테스트 시 오류 없이 동작 (이상 상황 대응 포함)  및 오류 없는 완전 자동화 시스템

결과물:   
상금 : 과제 완료시 오프라인 미팅 후 50만원 지급(선착순 1팀)

<br>Document Link: https://docs.google.com/forms/d/1Ng_GmgsnWGAL06sjmTDXA6WhAcLn1ahDD9taVHn9Q2o/viewform?pli=1&pli=1&edit_requested=true
<br>Tutorial Video Link: https://www.youtube.com/watch?v=uJn2SArkhvk

### How to Run?
Please Download Requirements in your Terminal:
pip install selenium helium python-dotenv

Create .env file and Setting your Tradingview Account:
userEMAIL = "Your_TrainingView_Account_Email" / userPASSWORD = "Your_TrainingView_Account_Password"
