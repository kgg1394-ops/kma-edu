import urllib.request
import re
import datetime
import json

def get_pubmed_papers(query, limit=3):
    # 키워드별로 검색 (한 섹션당 3개씩)
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query.replace(' ', '+')}&retmax={limit}&sort=date&retmode=json"
    
    try:
        with urllib.request.urlopen(search_url) as response:
            search_data = json.loads(response.read().decode('utf-8'))
            ids = search_data['esearchresult']['idlist']
        
        if not ids:
            return "<p>최근 논문이 없습니다.</p>"

        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(ids)}&retmode=json"
        with urllib.request.urlopen(summary_url) as res:
            summary_data = json.loads(res.read().decode('utf-8'))
            
        papers_html = ""
        for pmid in ids:
            paper_info = summary_data['result'][pmid]
            title = paper_info.get('title', 'No Title')
            pubdate = paper_info.get('pubdate', 'Recent')
            
            papers_html += f"""
            <div style="background: white; margin-bottom: 12px; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db;">
                <span style="color: #7f8c8d; font-size: 0.85em;">📅 {pubdate}</span><br>
                <a href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" target="_blank" style="text-decoration: none; color: #2c3e50; font-weight: bold; font-size: 1em;">{title}</a>
            </div>"""
        return papers_html
    except:
        return "<p>데이터를 가져오는 중 오류가 발생했습니다.</p>"

# 1. 관심 키워드 설정
keywords = {
    "🏥 General GI": "Gastroenterology",
    "📸 Endoscopy": "Endoscopy",
    "🧬 IBD & Inflammation": "Inflammatory Bowel Disease"
}

# 2. 각 키워드별 결과 생성
all_sections_html = ""
for display_name, search_term in keywords.items():
    all_sections_html += f"""
    <h2 style="color: #2c3e50; margin-top: 40px; border-bottom: 2px solid #eee; padding-bottom: 10px;">{display_name}</h2>
    {get_pubmed_papers(search_term)}
    """

# 3. 시간 설정 (KST)
now = datetime.datetime.now() + datetime.timedelta(hours=9)
time_label = now.strftime("%Y-%m-%d %H:%M")

# 4. 전체 HTML 템플릿
html_template = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>GI/Endoscopy Paper Dashboard</title>
</head>
<body style="font-family: 'Apple SD Gothic Neo', sans-serif; background-color: #f4f7f6; padding: 20px; max-width: 800px; margin: auto;">
    <header style="text-align: center; padding: 30px 0;">
        <h1 style="color: #2c3e50; margin-bottom: 5px;">🏥 GI 전문의 최신 지견</h1>
        <p style="color: #95a5a6;">매일 아침 6시, PubMed 실시간 자동 업데이트</p>
        <span style="background: #34495e; color: white; padding: 5px 15px; border-radius: 20px; font-size: 0.8em;">Last Update: {time_label} (KST)</span>
    </header>

    <main>
        {all_sections_html}
    </main>

    <section style="margin-top: 60px; padding: 25px; background: #2c3e50; border-radius: 12px; color: white;">
        <h3 style="margin-top: 0; color: #3498db;">🚀 MedProductive Project</h3>
        <p style="font-size: 0.95em; opacity: 0.9;">
            전공의 업무 자동화 시스템 Vol 1. 제작 중<br>
            AI를 활용한 효율적인 임상 환경을 만듭니다.
        </p>
    </section>

    <footer style="text-align: center; margin-top: 40px; color: #bdc3c7; font-size: 0.8em;">
        <p>This page is automatically maintained by GitHub Actions.</p>
    </footer>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)
