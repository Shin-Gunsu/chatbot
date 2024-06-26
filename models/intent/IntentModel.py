import tensorflow.compat.v1 as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras import preprocessing

import sys
import os
file_path = os.path.dirname(__file__)  # 현재 파일의 절대 경로를 가져옵니다.
sys.path.append(file_path+'../../')
from config.GlobalParams import MAX_SEQ_LEN
# 의도 분류 모델 모듈
class IntentModel:
    def __init__(self, model_name, proprocess):

        # 의도 클래스 별 레이블
        self.labels = {0: "졸업요건", 1: "질의응답", 2: "과제", 3:"과목추천",4:"학식",5:"셔틀"}

        # 의도 분류 모델 불러오기
        self.model = load_model(model_name)

        # 챗봇 Preprocess 객체
        self.p = proprocess


    # 의도 클래스 예측
    def predict_class(self, query):
        # 형태소 분석
        pos = self.p.pos(query)

        # 문장내 키워드 추출(불용어 제거)
        keywords = self.p.get_keywords(pos, without_tag=True)
        sequences = [self.p.get_wordidx_sequence(keywords)]

        # 단어 시퀀스 벡터 크기


        file_path = os.path.dirname(__file__)  # 현재 파일의 절대 경로를 가져옵니다.
        sys.path.append(file_path+'../../')
        from config.GlobalParams import MAX_SEQ_LEN

        # 패딩처리
        padded_seqs = preprocessing.sequence.pad_sequences(sequences, maxlen=MAX_SEQ_LEN, padding='post')
        predict = self.model.predict(padded_seqs)
        predict_class = tf.math.argmax(predict, axis=1)
        print(predict)
        return predict_class.numpy()[0]