import os, requests, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from datetime import datetime
import subprocess

NARA_API_KEY = os.environ['NARA_API_KEY']
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
GOOGLE_CX = os.environ['GOOGLE_CX']
NAVER_CLIENT_ID = os.environ['NAVER_CLIENT_ID']
NAVER_CLIENT_SECRET = os.environ['NAVER_CLIENT_SECRET']
GMAIL_PASSWORD = os.environ['GMAIL_PASSWORD']
GMAIL_USER = 'yejin9024@gmail.com'
RECIPIENTS = ['lyejin@incross.com']

def setup_font():
    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'fonts-nanum'], capture_output=True)
    font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    bold_path = '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'
    pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
    pdfmetrics.registerFont(TTFont('NanumGothicBold', bold_path))
    return 'NanumGothic', 'NanumGothicBold'

def get_nara_bids():
    results = []
    keywords = ['커머스', '쇼핑몰', '이커머스', '온라인', '운영대행']
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
                        'link': 'https://www.g2b.go.kr'
                    })
        except Exception as e:
            print(f'나라장터 오류: {e}')
    return results[:10]

def get_google_bids():
    results = []
    queries = ['커머스 운영대행 입찰공고', '쇼핑몰 운영대행 RFP 2026','커머스 운영대행','쇼핑몰 운영대행']
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
    keywords = ['이커머스', '커머스 운영대행', '온라인쇼핑몰', '쿠팡', '네이버쇼핑', '카카오커머스','톡딜','백화점','커머스','쇼핑','온라인 쇼핑','쇼핑','T딜','티딜']
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

def create_pdf(nara_bids, google_bids, news, font, font_bold):
    today = datetime.now().strftime('%Y%m%d')
    filename = f'commerce_daily_{today}.pdf'
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    y = height - 40

    # 색상 정의
    BLUE = (0.13, 0.29, 0.58)
    LIGHT_BLUE = (0.23, 0.47, 0.85)
    GRAY = (0.45, 0.45, 0.45)
    LIGHT_GRAY = (0.95, 0.95, 0.97)
    WHITE = (1, 1, 1)
    ACCENT = (0.06, 0.63, 0.55)

    def new_page():
        nonlocal y
        c.showPage()
        # 페이지 상단 얇은 파란 줄
        c.setFillColorRGB(*BLUE)
        c.rect(0, height-8, width, 8, fill=1, stroke=0)
        y = height - 35

    def check_space(needed=40):
        if y < needed:
            new_page()

    # ── 헤더 배경 ──
    c.setFillColorRGB(*BLUE)
    c.rect(0, height-90, width, 90, fill=1, stroke=0)

    # 헤더 텍스트
    c.setFillColorRGB(*WHITE)
    c.setFont(font_bold, 20)
    c.drawString(40, height-45, '커머스 데일리 브리핑')
    c.setFont(font, 11)
    c.drawString(40, height-68, f'INCROSS Commerce Intelligence  |  {datetime.now().strftime("%Y년 %m월 %d일 %A")}')

    # 작은 accent 바
    c.setFillColorRGB(*ACCENT)
    c.rect(0, height-90, width, 4, fill=1, stroke=0)

    y = height - 110

    def section_header(icon, title, color=BLUE):
        nonlocal y
        check_space(50)
        y -= 10
        # 섹션 배경 박스
        c.setFillColorRGB(*LIGHT_GRAY)
        c.roundRect(30, y-8, width-60, 28, 4, fill=1, stroke=0)
        # 왼쪽 accent 바
        c.setFillColorRGB(*color)
        c.rect(30, y-8, 5, 28, fill=1, stroke=0)
        # 텍스트
        c.setFillColorRGB(*color)
        c.setFont(font_bold, 12)
        c.drawString(45, y+6, f'{icon}  {title}')
        y -= 25

    def draw_item(title, sub=None, link=None):
        nonlocal y
        check_space(50)
        y -= 4
        # 아이템 제목
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.setFont(font_bold, 10)
        c.drawString(48, y, f'• {str(title)[:62]}')
        y -= 15
        if sub:
            check_space(20)
            c.setFillColorRGB(*GRAY)
            c.setFont(font, 9)
            c.drawString(58, y, str(sub)[:70])
            y -= 13
        if link:
            check_space(20)
            c.setFillColorRGB(*LIGHT_BLUE)
            c.setFont(font, 8)
            short_link = str(link)[:70]
            c.drawString(58, y, f'↗ {short_link}')
            if link:
                c.linkURL(link, (58, y-2, 500, y+9), relative=0)
            y -= 14
        # 구분선
        c.setStrokeColorRGB(0.9, 0.9, 0.9)
        c.setLineWidth(0.3)
        c.line(48, y, width-40, y)
        y -= 4

    def no_result():
        nonlocal y
        c.setFillColorRGB(*GRAY)
        c.setFont(font, 9)
        c.drawString(48, y, '• 오늘은 해당 공고가 없습니다.')
        y -= 18

    # ── 섹션 1: 나라장터 ──
    section_header('📋', '나라장터 공공입찰 공고', BLUE)
    if nara_bids:
        for bid in nara_bids:
            draw_item(bid['title'], f'기관: {bid["org"]}  |  마감: {bid["deadline"]}', bid['link'])
    else:
        no_result()

    # ── 섹션 2: 사기업 입찰 ──
    section_header('🔍', '사기업 입찰공고', (0.18, 0.45, 0.22))
    if google_bids:
        for bid in google_bids:
            draw_item(bid['title'], bid['snippet'], bid['link'])
    else:
        no_result()

    # ── 섹션 3: 뉴스 ──
    section_header('📰', '커머스 주요 뉴스', (0.55, 0.18, 0.18))
    if news:
        for item in news:
            draw_item(item['title'], item['description'], item['link'])
    else:
        no_result()

    # ── 하단 푸터 ──
    c.setFillColorRGB(*BLUE)
    c.rect(0, 0, width, 28, fill=1, stroke=0)
    c.setFillColorRGB(*WHITE)
    c.setFont(font, 8)
    c.drawString(40, 10, f'INCROSS Commerce Daily  |  자동 생성된 브리핑입니다  |  {datetime.now().strftime("%Y.%m.%d")}')

    c.save()
    return filename

def send_email(pdf_file):
    today = datetime.now().strftime('%Y.%m.%d')
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = ', '.join(RECIPIENTS)
    msg['Subject'] = f'[커머스 데일리] {today} 입찰공고 & 주요소식'

    body = f'''안녕하세요! 😊

오늘의 커머스 데일리 브리핑을 보내드립니다.

📋 나라장터 공공입찰 공고
🔍 사기업 입찰공고
📰 커머스 주요 뉴스

첨부된 PDF 파일을 확인해주세요!

---
INCROSS Commerce Daily | {today}
'''
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    with open(pdf_file, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{pdf_file}"')
        msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        for recipient in RECIPIENTS:
            msg.replace_header('To', recipient)
            server.send_message(msg)
            print(f'발송 완료: {recipient}')

if __name__ == '__main__':
    print('폰트 설치 중...')
    font, font_bold = setup_font()
    print('수집 시작...')
    nara = get_nara_bids()
    google = get_google_bids()
    news = get_naver_news()
    print(f'나라장터:{len(nara)} 구글:{len(google)} 뉴스:{len(news)}')
    pdf = create_pdf(nara, google, news, font, font_bold)
    print(f'PDF 생성: {pdf}')
    send_email(pdf)
