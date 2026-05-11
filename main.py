import os, requests, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
import subprocess

NARA_API_KEY = os.environ['NARA_API_KEY']
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
GOOGLE_CX = os.environ['GOOGLE_CX']
NAVER_CLIENT_ID = os.environ['NAVER_CLIENT_ID']
NAVER_CLIENT_SECRET = os.environ['NAVER_CLIENT_SECRET']
GMAIL_PASSWORD = os.environ['GMAIL_PASSWORD']
GMAIL_USER = 'yejin9024@gmail.com'

def setup_font():
    subprocess.run(['apt-get', 'install', '-y', 'fonts-nanum'], capture_output=True)
    font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
    return 'NanumGothic'

def get_nara_bids():
    results = []
    keywords = ['커머스', '쇼핑몰운영', '이커머스', '온라인몰', '운영대행']
    for keyword in keywords:
        try:
            url = 'http://apis.data.go.kr/1230000/BidPublicInfoService04/getBidPblancListInfoServc'
            params = {
                'serviceKey': NARA_API_KEY,
                'pageNo': '1',
                'numOfRows': '5',
                'inqryDiv': '1',
                'bidNtceNm': keyword,
                'type': 'json'
            }
            res = requests.get(url, params=params, timeout=10)
            data = res.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if items:
                for item in items[:3]:
                    results.append({
                        'title': item.get('bidNtceNm', ''),
                        'org': item.get('ntceInsttNm', ''),
                        'deadline': item.get('bidClseDt', '')
                    })
        except Exception as e:
            print(f'나라장터 오류: {e}')
    return results[:10]

def get_google_bids():
    results = []
    queries = ['커머스 운영대행 입찰공고', '쇼핑몰 운영대행 RFP 2026']
    for query in queries:
        try:
            url = 'https://www.googleapis.com/customsearch/v1'
            params = {
                'key': GOOGLE_API_KEY,
                'cx': GOOGLE_CX,
                'q': query,
                'num': 5,
                'dateRestrict': 'd7'
            }
            res = requests.get(url, params=params, timeout=10)
            data = res.json()
            for item in data.get('items', [])[:3]:
                results.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', '')
                })
        except Exception as e:
            print(f'구글 오류: {e}')
    return results[:8]

def get_naver_news():
    results = []
    keywords = ['이커머스', '커머스 운영대행', '온라인쇼핑몰']
    headers = {
        'X-Naver-Client-Id': NAVER_CLIENT_ID,
        'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
    }
    for keyword in keywords:
        try:
            url = 'https://openapi.naver.com/v1/search/news.json'
            params = {'query': keyword, 'display': 5, 'sort': 'date'}
            res = requests.get(url, headers=headers, params=params, timeout=10)
            data = res.json()
            for item in data.get('items', [])[:3]:
                title = item.get('title', '').replace('<b>', '').replace('</b>', '')
                desc = item.get('description', '').replace('<b>', '').replace('</b>', '')
                results.append({'title': title, 'description': desc})
        except Exception as e:
            print(f'네이버 오류: {e}')
    return results[:10]

def create_pdf(nara_bids, google_bids, news, font_name):
    today = datetime.now().strftime('%Y%m%d')
    filename = f'commerce_daily_{today}.pdf'
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    y = height - 50

    def write(text, size=10, gap=16, bold=False):
        nonlocal y
        if y < 60:
            c.showPage()
            y = height - 50
        c.setFont(font_name, size)
        c.drawString(40, y, text[:60])
        y -= gap

    c.setFont(font_name, 16)
    c.drawString(40, y, f'커머스 데일리 브리핑 - {datetime.now().strftime("%Y.%m.%d")}')
    y -= 30

    c.setFont(font_name, 13)
    c.drawString(40, y, '📋 나라장터 공공입찰 공고')
