import threading
import json
from openai import OpenAI
import sys
import os
file_path = os.path.dirname(__file__) 

# from config.DatabaseConfig import *
# from utils.Database import Database
from utils.BotServer import BotServer
from utils.Preprocess import Preprocess
from models.intent.IntentModel import IntentModel
from models.ner.NerModel import NerModel
from utils.FindAnswer import FindAnswer
from utils.FindIntent import FindIntent
from utils.Preprocess import Preprocess
from utils.GetAnswer_assistant import GetAnswer_assistant
from utils.Scrap import Scrap
from utils.LoginMakeCookie import LoginMakeCookie
from config.GlobalParams import gptapi_key


# 전처리 객체 생성
p = Preprocess(word2index_dic=file_path + '/train_tools/dict/chatbot_dict.bin',
               userdic=file_path + '/utils/user_dict.txt')

# 의도 파악 모델
intent = IntentModel(model_name=file_path + '/models/intent/intent_model.h5', proprocess=p)
print('의도 분류 모델 호출')
# 개체명 인식 모델
ner = NerModel(model_name=file_path + '/models/ner/ner_model.h5', proprocess=p)
print('개체명 인식 모델 호출')

#chat에서 받은 데이터 
def send_chat_data(conn,recv_json_data):
    query = recv_json_data['query']
    # 의도 파악
    intent_model = FindIntent(intent)
    intent_predict = intent_model.classification(query)
    
    if intent_predict[0] == 1:
        # QnA
        ner_predicts = ner.predict(query)
        ner_list = []
        for keyword, tag in ner_predicts:
            if tag != 0 and tag != 1:
                print(keyword, tag)
                ner_list.append(keyword)
        #ASSISTANT 모델
        assistant_model = GetAnswer_assistant(OpenAI(api_key=gptapi_key))
        assistant_model.create_thread()
        answer = assistant_model.ask(query)
        print(answer)
        send_json_data_str = {
            "Answer" : answer,
            "Intent": intent_predict[1],
            "Ner": ner_list
        }
        assistant_model.end_QnA()
        message = json.dumps(send_json_data_str)
        conn.send(message.encode())
        print(send_json_data_str)
    elif intent_predict[0] == 2:
        #과제 가져오기
        '''
        hwscrap = Scrap()
        r = hwscrap.scrapHW(host_response)
        send_string = ""
        for i in r:
            send_string = send_string + i + '\n'
        send_json_data_str = {
            "Answer" : send_string,
        }
        message = json.dumps(send_json_data_str)
        conn.send(message.encode())
        '''
        menuscrap = Scrap()
        r = menuscrap.scrapMenu()
        send_string = ""
        for i in r:
            for j in i:
                send_string = send_string + i + '\n'
        send_json_data_str = {
            "Answer" : send_string,
        }
        message = json.dumps(send_json_data_str)
        conn.send(message.encode()) 
    elif intent_predict[0] == 4:
        #학식 가져오기
        menuscrap = Scrap()
        r = menuscrap.scrapMenu()
        send_string = ""
        for i in r:
            for j in i:
                send_string = send_string + j + '\n'
        send_json_data_str = {
            "Answer" : send_string,
        }
        message = json.dumps(send_json_data_str)
        conn.send(message.encode())
    elif intent_predict[0] == 0:
        #수강이력 가져오기(일단 졸업요건 레이블 사용)
        studentnumscrap = Scrap()
        r = studentnumscrap.scrapStudentNumber(host_response)

        start_year = ''.join(filter(str.isdigit, r))[:4]
        coursehistoryscrap = Scrap()
        chlist = coursehistoryscrap.scrapCourseHistory(user_id, int(start_year)) #수강이력 리스트(포맷: 과목명(분반))
        '''
        send_string = ""
        for i in chlist:
            send_string = send_string + i + '\n'
        send_json_data_str = {
            "Answer" : send_string,
        }
        message = json.dumps(send_json_data_str)
        conn.send(message.encode()) 
        '''
        
    else :
        #졸업요건, 과목추천 의도 보냄
        send_json_data_str = {
            "Intent": intent_predict[1],
        }
        message = json.dumps(send_json_data_str)
        conn.send(message.encode())

host_response = None
user_id = ""
def to_client(conn, addr):
    global host_response
    global user_id
    #로그인 POST 요청 응답
    
    try:
        # db.connect()  # 디비 연결

        # 데이터 수신
        read = conn.recv(2048)  # 수신 데이터가 있을 때 까지 블로킹
        print('===========================')
        print('Connection from: %s' % str(addr))

        if read is None or not read:
            # 클라이언트 연결이 끊어지거나, 오류가 있는 경우
            print('클라이언트 연결 끊어짐')
            exit(0)


        # json 데이터로 변환
        recv_json_data = json.loads(read.decode())
        print("데이터 수신 : ", recv_json_data)
        if "id" in recv_json_data:
            if "pw" in recv_json_data:
                        user_id = recv_json_data['id']
                        user_pw = recv_json_data['pw']
                        lmc = LoginMakeCookie(user_id, user_pw)
                        host_response = lmc.makeCookie() #쿠키 생성 및 HOST 응답 저장

                        if (lmc.isLogin()):
                            send_json_data_str = {
                                "LoginState": True,
                                "StudentNumber": "",
                                "Department": "",
                                "Email": "",
                            }
                        else:
                            send_json_data_str = {
                                "LoginState": False
                            }
                        

                        message = json.dumps(send_json_data_str)
                        conn.send(message.encode())
                        print(user_id)
                        print(user_pw)
        else:
            
            send_chat_data(conn,recv_json_data)
 
   

    except Exception as ex:
        print(ex)



if __name__ == '__main__':

    port = 5050
    listen = 100

    # 봇 서버 동작
    bot = BotServer(port, listen)
    bot.create_sock()
    print("bot start")

    while True:
        conn, addr = bot.ready_for_client()

        client = threading.Thread(target=to_client, args=(
            conn,
            addr,

        ))
        client.start()
