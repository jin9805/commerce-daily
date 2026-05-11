import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

# 환경변수에서 API 키 가져오기
NARA_API_KEY = os.environ['NARA_API_KEY']
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
GOOGLE_CX = os.environ['GOOGLE_CX']
NAVER_CLIENT_ID = os.environ['NAVER_CLIENT_ID']
NAVER_CLIENT_SECRET = os.environ['NAVER_CLIENT_SECRET']
GMAIL_PASSWORD = os.environ['GMAIL_PASSWORD']
GMAIL_USER = 'yejin9024@gmail.com'

def get_nara_bids():
    """나라장터 입찰공고 가져오기"""
    keywords = ['커머스', '쇼핑몰운영', '이커머스', '온라인몰', '운영대행']
    results = []
    for keyword in keywords:
        url = 'http://apis.data.go.kr/1230000/BidPublicInfoService04/getBidPblancListInfoServc'
        params = {
            'serviceKey': NARA_API_KEY,
            'pageNo': '1',
            'numOfRows': '5',
            'inqryDiv': '1',
            'bidNtceNm': keyword,
            'type': 'json'
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            data = res.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if items:
                for item in items[:3]:
                    results.append({
                        'title': item.get('bidNtceNm', ''),
                        'org': item.get('ntceInsttNm', ''),
                        'date': item.get('bidNtceDt', ''),
                        'deadline': item.get('bidClseDt', '')
                    })
        except:
            pass
    return results[:10]

def get_google_bids():
    """구글 검색으로 사기업 입찰공고 가져오기"""
    queries = ['커머스 운영대행 입찰공고', '쇼핑몰 운영대행 RFP 2026']
    results = []
    for query in queries:
        url = 'https://www.googleapis.com/customsearch/v1'
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CX,
            'q': query,
            'num': 5,
            'dateRestrict': 'd7'
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            data = res.json()
            items = data.get('items', [])
            for item in items[:3]:
                results.append({
                    'title': ite
