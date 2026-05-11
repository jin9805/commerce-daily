import os, requests, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'fonts-nanum'], capture_output=True)
    font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
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
                        'deadline': item.get('bidClseDt', ''),
                        'link': f'https://www.g2b.go.kr'
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
            for item in data.get('items', [])[:5]:
                results.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('link', '')
                })
        except Exception as e:
            print(f'구글 오류: {e}')
    return results[:10]

def get_naver_news():
    results = []
    keywords = ['이커머스', '커머스 운영대행', '온라인쇼핑몰', '쿠팡', '네이버쇼핑', '카카오커머스', '쇼핑몰','T딜','네이트 온딜','커머스','온라인','백화점','톡딜']
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
            for item in data.get('items', [])[:4]:
                title = item.get('title', '').replace('<b>', '').replace('</b>', '')
                desc = item.get('description', '').replace('<b>', '').replace('</b>', '')
                link = item.get('link', '')
                results.append({'title': title, 'description': desc, 'link': link})
        except Exception as e:
            print(f'네이버 오류: {e}')
    return results[:25]

def create_pdf(nara_bids, google_bids, news, font_name):
    today = datetime.now().strftime('%Y%m%d')
    filename = f'commerce_daily_{today}.pdf'
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    y = height - 50

    def write(text, size=10, gap=16, color=(0,0,0)):
        nonlocal y
        if y < 80:
            c.showPage()
            y = height - 50
        c.setFillColorRGB(*color)
        c.setFont(font_name, size)
        c.drawString(40, y, str(text)[:65])
        y -= gap

    def write_link(text, url, size=9, gap=14):
        nonlocal y
        if y < 80:
            c.showPage()
            y = height - 50
        c.setFillColorRGB(0.1, 0.4, 0.8)
        c.setFont(font_name, size)
        c.drawString(40, y, str(url)[:80])
        if url:
            c.linkURL(url, (40, y-2, 500, y+size), relative=0)
        y -= gap

    def section_title(text):
        nonlocal y
        y -= 5
        c.setFillColorRGB(0.1, 0.3, 0.7)
        c.setFont(font_name, 13)
        c.drawString(40, y, text)
        y -= 20

    # 제목
    c.setFillColorRGB(0.1, 0.3, 0.7)
    c.setFont(font_name, 17)
    c.drawString(40, y, f'커머스 데일리 브리핑 - {datetime.now().strftime("%Y.%m.%d")}')
    y -= 35

    # 나라장터
    section_title('📋 나라장터 공공입찰 공고')
    for bid in nara_bids:
        write(f'• {bid["title"]}', size=10)
        write(f'  기관: {bid["org"]} | 마감: {bid["deadline"]}', size=9, gap=12, color=(0.4,0.4,0.4))
        write_link('  → 나라장터 바로가기', bid["link"])
    if not nara_bids:
        write('• 해당 공고 없음')

    # 구글 사기업
    section_title('🔍 사기업 입찰공고')
    for bid in google_bids:
        write(f'• {bid["title"]}', size=10)
        write(f'  {bid["snippet"]}', size=9, gap=12, color=(0.4,0.4,0.4))
        write_link(f'  → {bid["link"]}', bid["link"])
    if not google_bids:
        write('• 해당 공고 없음')

    # 뉴스
    section_title('📰 커머스 주요 뉴스')
    for item in news:
        write(f'• {item["title"]}', size=10)
        write(f'  {item["description"]}', size=9, gap=12, color=(0.4,0.4,0.4))
        write_link(f'  → {item["link"]}', item["link"])
    if not news:
        write('• 뉴스 없음')

    c.save()
    return filename

def send_email(pdf_file):
    today = datetime.now().strftime('%Y.%m.%d')
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = f'[커머스 데일리] {today} 입찰공고 & 주요소식'
    msg.attach(MIMEText('안녕하세요! 오늘의 커머스 데일리 브리핑입니다.\n첨부파일에서 입찰공고와 뉴스를 확인하세요! 😊', 'plain', 'utf-8'))
    with open(pdf_file, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{pdf_file}"')
        msg.attach(part)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)
    print('메일 발송 완료!')

if __name__ == '__main__':
    print('폰트 설치 중...')
    font_name = setup_font()
    print('수집 시작...')
    nara = get_nara_bids()
    google = get_google_bids()
    news = get_naver_news()
    print(f'나라장터:{len(nara)} 구글:{len(google)} 뉴스:{len(news)}')
    pdf = create_pdf(nara, google, news, font_name)
    print(f'PDF 생성: {pdf}')
    send_email(pdf)
