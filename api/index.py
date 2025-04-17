from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import requests
from bs4 import BeautifulSoup
import re
import os
import logging
from fastapi import Response
import json

# ログの設定
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Dify Workflow API設定
DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"
DIFY_API_KEY = os.getenv("DIFY_API_KEY")

# SerpApi APIキー
SERP_API_KEY = os.getenv("SERPAPI_KEY")

class CompanyItem(BaseModel):
    company_name: str
    phone_number: str
    email: str

class RequestPayload(BaseModel):
    items: List[CompanyItem]
    industry_texts: str

# エラーログを残さない
@app.get("/")
def root():
    return {"message": "POSTリクエストでデータを送信してください。"}
@app.get("/favicon.ico")
def favicon():
    return Response(content="", media_type="image/x-icon")

@app.post("/")
async def handle_batch_request(payload: RequestPayload):
    enriched_items = []

    for item in payload.items:
        company_name = item.company_name
        phone_number = item.phone_number
        email = item.email

        # Step 1: SerpApiで企業URLを取得
        query = f"{company_name} {phone_number} {email}".strip()

        # serp = requests.get("https://serpapi.com/search.json", params={
        #     "q": query,
        #     "hl": "ja",
        #     "api_key": SERP_API_KEY
        # }).json()

        serp = {'search_metadata': {'id': '6800581e72e8d4c18bfad34e', 'status': 'Success', 'json_endpoint': 'https://serpapi.com/searches/7d9b5aa4df6c9fbc/6800581e72e8d4c18bfad34e.json', 'created_at': '2025-04-17 01:23:42 UTC', 'processed_at': '2025-04-17 01:23:42 UTC', 'google_url': 'https://www.google.com/search?q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&oq=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&hl=ja&sourceid=chrome&ie=UTF-8', 'raw_html_file': 'https://serpapi.com/searches/7d9b5aa4df6c9fbc/6800581e72e8d4c18bfad34e.html', 'total_time_taken': 6.29}, 'search_parameters': {'engine': 'google', 'q': '有限会社川越屋硝子店 03-3391-1309 s.sibata522+1@gmail.com', 'google_domain': 'google.com', 'hl': 'ja', 'device': 'desktop'}, 'search_information': {'query_displayed': '有限会社川越屋硝子店 03-3391-1309 s.sibata522+1@gmail.com', 'total_results': 2, 'time_taken_displayed': 0.23, 'organic_results_state': 'Results for exact spelling'}, 'inline_images': [{'source': 'http://kawagoeya-glassten.com/company.html', 'thumbnail': 'https://serpapi.com/searches/6800581e72e8d4c18bfad34e/images/659aac014e31bd88045c2a827d09a75f2eb3dcbfcea335838e823aacae1602e2.jpeg', 'original': 'http://kawagoeya-glassten.com/images/company_p.gif', 'title': '会社概要＞有限会社・川越屋硝子店', 'source_name': '杉並区でガラス屋さん80年「川越屋硝子店」'}, {'source': 'https://www.travelbook.co.jp/t-601/topic-102911/', 'thumbnail': 'https://serpapi.com/searches/6800581e72e8d4c18bfad34e/images/659aac014e31bd885423592b670ca041a232af3b57e17e416a5ce9c5ba1e1da0.jpeg', 'original': 'https://d1d37e9z843vy6.cloudfront.net/jp/images/4747955/d5d957a2.png', 'title': '有限会社川越屋硝子店ってどんな業者？口コミ・料金・評判を徹底 ...', 'source_name': 'www.travelbook.co.jp'}, {'source': 'http://kawagoeya-glassten.com/form.html', 'thumbnail': 'https://serpapi.com/searches/6800581e72e8d4c18bfad34e/images/659aac014e31bd88f7d2914154114def349ed314b7bc15db034a093c1dfe8695.jpeg', 'original': 'http://kawagoeya-glassten.com/images/meisi.gif', 'title': 'お問い合わせはこちらから＞川越屋硝子店', 'source_name': '杉並区でガラス屋さん80年「川越屋硝子店」'}, {'source': 'http://kawagoeya-glassten.com/form.html', 'thumbnail': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTw6s761VIVJhKjoeRXYuolo1ZTiKyhOG5KNF95PF62qseVeKji5oOLHno&s', 'original': 'http://kawagoeya-glassten.com/images/shop2.jpg', 'title': 'お問い合わせはこちらから＞川越屋硝子店', 'source_name': '杉並区でガラス屋さん80年「川越屋硝子店」'}, {'source': 'http://kawagoeya-glassten.com/repair.html', 'thumbnail': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRkz56gHc0UNvDppauozCt8EFnk_shsgmokE1s4urEum8JP8XipyedVVw4&s', 'original': 'http://kawagoeya-glassten.com/images/ware_glass.gif', 'title': 'ガラス修理・交換は安くて安心の川越屋硝子店へ', 'source_name': '杉並区でガラス屋さん80年「川越屋硝子店」'}, {'source': 'https://www.ekiten.jp/shop_6057330/', 'thumbnail': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTEesYjUrg-Li-gfWsQGsbLKeztojVIpfdTwTZeYjjpDIu1yXQYYi2hJ1Y&s', 'original': 'https://image.ekiten.jp/shop/6057330/616703_20130725144838.jpg', 'title': '川越屋硝子店（杉並区） | エキテン', 'source_name': 'エキテン'}, {'source': 'http://kawagoeya-glassten.com/dannetu.html', 'thumbnail': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTGX0hQSCA7liGznLSTQ-dpm4m6-HtM4MhO_gQbnOrGH6I9KUeuXVqczSU&s', 'original': 'http://kawagoeya-glassten.com/images/ecohouse.gif', 'title': '断熱・結露ガラスなら安くて安心の川越屋硝子店へ', 'source_name': '杉並区でガラス屋さん80年「川越屋硝子店」'}, {'source': 'https://www.kawagoeya.com/?page_id=16', 'thumbnail': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSjp8Xk3qPXJ3v22M_ppgqIhvgoVoMOivOnjpY8eDNK2hz8LrRASa1z3CA&s', 'original': 'https://www.kawagoeya.com/wp/wp-content/themes/kawagoeya/img/history/history-img01_sp.jpg', 'title': '川越屋の歩み - 株式会社川越屋 ｜ 落花生・豆菓子を丹精込めて ...', 'source_name': '川越屋'}, {'source': 'http://kawagoeya-glassten.com/jisseki.html', 'thumbnail': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTaVppzh3aEP1IbSQPXxJuLrfDYxJNef6U-iAJfmfIj-JAu-HKTcxEPGks&s', 'original': 'http://kawagoeya-glassten.com/images/green_room.jpg', 'title': 'ガラス工事例・施工実績＞川越屋硝子店', 'source_name': '杉並区でガラス屋さん80年「川越屋硝子店」'}], 'ai_overview': {'page_token': 'oAXwCnicvZXbcuo2FEBf-x2dES8ngC9c7Mx4TiVb2IZAUAIJ5IUxxggbjMEGDLydf-lX9WuOLBMuSdNOO51qGHTZF23tvdj8-H3hL-d__PLrbLNZJfflcpqmJRpFdOGV3CgsO8lh6Zan0SKJ3dn32UILnMJhp8kFN9GEgudrzQaFzoM8sOrHsNqJusquGHikwO200dhJvIC53QdJeVRmX3MgG2xTSkqBU_INxzUnZFqtk5IkiErpseyETAH-u4Fudk8Ek_NGv5E26WlhZofUxvTWPOQ7ErOpce2SnnxR6EN1JBmQ3ErYYCfzs34F2tmBC22dDIZXjvBVXNfBX99mf7yXK2P41TC5DdMJKErzozRXzz01K3snutzbhVCxEjhDpP_RE2rBICTdqAGJ_VHGIqBPHcvcsIfp5Qll1RLK45hNYjlOstrpPVWIGsIqaY_f8PDg94gnylHL21rTmeWnNXLHqXCTMxbJNRZDUxkeoTpBRlp6KCHxzIRNApw_hReNfa3_Kh3PV2nlkw33hAXNLPIs2HYPNuGEr7sUmo_NPjzXiEL8XlKc539u80zmtjqCuN3iQinT5qTRvD6kDQ-nHLN7Kxa7FKU8jMx7BcJWHpSNyCv3rl_Iw-92bElgBbXbUG8QaNowOD0DQRu_68zYZEI9i44Vykiz7Ey5rc8kTM1g0cAI8XWawwFPD8NsY98ywRD5Mpvn0fjiHP0JBHi7m-rr6Gm1fSWK100Px_lxHyznZs97hyAKx_-gObj_EyasdfTPmLRuMOluT5h8bB0nTEJ2NbJPreMTJs9Z69BZ67AumPjwgskiO-CYVBgmT7x1GFnruGCC4d9j0rxgQi-Y4C8xMd8xCeg-zTFJMW9j7c-Y_Fetg9Pi5dNtH9kG9FM_accPh9BCsUnHqrFueVhwq0NhGRW38G40DTf3qziidyN_co-k5uYwKaw1gGtA1YGiAqwClX0EgCsA6UCFANcBZGsMcBWgOlANgBWAakCB_EQECuI6IhdVATS4ORNBoNa_CXJRllWxKMqC-o3h6I-djVOVJCAh8TcaOv4i-_MshIs40gSnUh8pxmo6axq7l-DoWW_dR9tr7PrPj32h48YP1hqKejzQu-J0Hso1nwzGfnvubgbWdp_WvHmnXWwEaRrqSk-a-9JxcLTkoy9adWuF6pPXFu2PqioevTwtGtti53k77nWULX0x9oOw_SKjiRJJS_uNEB5PogXVujKUHPdVsQth7Go6_4kUEtcZeclOc92qKqtORZookqMISiGkm8NKq4g_Aa7-V98', 'serpapi_link': 'https://serpapi.com/search.json?engine=google_ai_overview&page_token=oAXwCnicvZXbcuo2FEBf-x2dES8ngC9c7Mx4TiVb2IZAUAIJ5IUxxggbjMEGDLydf-lX9WuOLBMuSdNOO51qGHTZF23tvdj8-H3hL-d__PLrbLNZJfflcpqmJRpFdOGV3CgsO8lh6Zan0SKJ3dn32UILnMJhp8kFN9GEgudrzQaFzoM8sOrHsNqJusquGHikwO200dhJvIC53QdJeVRmX3MgG2xTSkqBU_INxzUnZFqtk5IkiErpseyETAH-u4Fudk8Ek_NGv5E26WlhZofUxvTWPOQ7ErOpce2SnnxR6EN1JBmQ3ErYYCfzs34F2tmBC22dDIZXjvBVXNfBX99mf7yXK2P41TC5DdMJKErzozRXzz01K3snutzbhVCxEjhDpP_RE2rBICTdqAGJ_VHGIqBPHcvcsIfp5Qll1RLK45hNYjlOstrpPVWIGsIqaY_f8PDg94gnylHL21rTmeWnNXLHqXCTMxbJNRZDUxkeoTpBRlp6KCHxzIRNApw_hReNfa3_Kh3PV2nlkw33hAXNLPIs2HYPNuGEr7sUmo_NPjzXiEL8XlKc539u80zmtjqCuN3iQinT5qTRvD6kDQ-nHLN7Kxa7FKU8jMx7BcJWHpSNyCv3rl_Iw-92bElgBbXbUG8QaNowOD0DQRu_68zYZEI9i44Vykiz7Ey5rc8kTM1g0cAI8XWawwFPD8NsY98ywRD5Mpvn0fjiHP0JBHi7m-rr6Gm1fSWK100Px_lxHyznZs97hyAKx_-gObj_EyasdfTPmLRuMOluT5h8bB0nTEJ2NbJPreMTJs9Z69BZ67AumPjwgskiO-CYVBgmT7x1GFnruGCC4d9j0rxgQi-Y4C8xMd8xCeg-zTFJMW9j7c-Y_Fetg9Pi5dNtH9kG9FM_accPh9BCsUnHqrFueVhwq0NhGRW38G40DTf3qziidyN_co-k5uYwKaw1gGtA1YGiAqwClX0EgCsA6UCFANcBZGsMcBWgOlANgBWAakCB_EQECuI6IhdVATS4ORNBoNa_CXJRllWxKMqC-o3h6I-djVOVJCAh8TcaOv4i-_MshIs40gSnUh8pxmo6axq7l-DoWW_dR9tr7PrPj32h48YP1hqKejzQu-J0Hso1nwzGfnvubgbWdp_WvHmnXWwEaRrqSk-a-9JxcLTkoy9adWuF6pPXFu2PqioevTwtGtti53k77nWULX0x9oOw_SKjiRJJS_uNEB5PogXVujKUHPdVsQth7Go6_4kUEtcZeclOc92qKqtORZookqMISiGkm8NKq4g_Aa7-V98'}, 'organic_results': [{'position': 1, 'title': '杉並区でガラス屋さん80年「川越屋硝子店」', 'link': 'http://kawagoeya-glassten.com/index.html', 'redirect_link': 'https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=http://kawagoeya-glassten.com/index.html&ved=2ahUKEwi9-cyH9N2MAxU8M1kFHfL_KA8QFnoECB0QAQ', 'displayed_link': 'http://kawagoeya-glassten.com', 'favicon': 'https://serpapi.com/searches/6800581e72e8d4c18bfad34e/images/6b167b18cdfcdf436ba5305c45a0801da12556f8d9df2d1e41f3b6d6c9263252.png', 'snippet': '窓ガラスの修理交換は、東京都杉並区阿佐谷南(阿佐ヶ谷)の地元のガラス専門店「川越屋硝子店」へおまかせください。 窓や什器のガラス修理交換,古くなった手鏡, ...', 'snippet_highlighted_words': ['川越屋硝子店'], 'missing': ['s.', 'sibata522+', 'gmail.'], 'source': 'kawagoeya-glassten.com'}, {'position': 2, 'title': '＜会社概要＞有限会社・川越屋硝子店', 'link': 'http://kawagoeya-glassten.com/company.html', 'redirect_link': 'https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=http://kawagoeya-glassten.com/company.html&ved=2ahUKEwi9-cyH9N2MAxU8M1kFHfL_KA8QFnoECBoQAQ', 'displayed_link': 'http://kawagoeya-glassten.com › company', 'favicon': 'https://serpapi.com/searches/6800581e72e8d4c18bfad34e/images/6b167b18cdfcdf436ba5305c45a0801d47ab790c73cab54750c47bd66881c61a.png', 'snippet': 'ガラス施工一級技能士の店 窓とガラス修理は東京・杉並区阿佐谷南(阿佐ヶ谷)で創業80年のガラス専門店・川越屋硝子店へどうぞおまかせください。', 'snippet_highlighted_words': ['川越屋硝子店'], 'missing': ['s.', 'sibata522+', 'gmail.'], 'source': 'kawagoeya-glassten.com'}], 'top_stories_link': 'https://www.google.com/search?sca_esv=cc5939a42d82a808&hl=ja&q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1@gmail.com&udm=2&source=univ&fir=sY9WOrT2Kh54XM%252CNWfRpIHRHHt4aM%252C_%253BRXY5ortIDmPI_M%252CfWAaIQgdEWV_OM%252C_%253BpQ3iTRRsh-zVwM%252CpSBJ52E_pUgpsM%252C_%253BqzoXfin2zglauM%252CpSBJ52E_pUgpsM%252C_%253BAsMOAStPArUkOM%252CS26WXulBT956rM%252C_%253BUq04co2LEvH0pM%252CAqzBG-3-uECXCM%252C_%253BLr5IULKevTBoQM%252CcTWDv_2CC38FdM%252C_%253B9YWaTk6Um0G7HM%252CEbgfmawQp0IEcM%252C_%253BycAwSlOJJb6OvM%252CKAF1LgXKV-4OCM%252C_&usg=AI4_-kQoj1obajsEHe-hKxkN9T7o3M3EXA&sa=X&ved=2ahUKEwi9-cyH9N2MAxU8M1kFHfL_KA8Q7Al6BAgOEAY', 'top_stories_serpapi_link': 'https://serpapi.com/search.json?device=desktop&engine=google&google_domain=google.com&hl=ja&q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com', 'dmca_messages': {'title': '除外した結果についての注意', 'messages': [{'content': '最も的確な検索結果を表示するために、上の 2 件と似たページは除外されています。検索結果をすべて表示するには、ここから再検索してください。', 'highlighted_words': [{'link': 'https://www.google.com/search?q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&sca_esv=cc5939a42d82a808&hl=ja&filter=0', 'text': 'ここから再検索してください'}]}]}, 'pagination': {'current': 1, 'next': 'https://www.google.com/search?q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&oq=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&hl=ja&start=10&sourceid=chrome&ie=UTF-8', 'other_pages': {'2': 'https://www.google.com/search?q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&oq=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&hl=ja&start=10&sourceid=chrome&ie=UTF-8', '3': 'https://www.google.com/search?q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&oq=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&hl=ja&start=20&sourceid=chrome&ie=UTF-8', '4': 'https://www.google.com/search?q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&oq=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&hl=ja&start=30&sourceid=chrome&ie=UTF-8', '5': 'https://www.google.com/search?q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&oq=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&hl=ja&start=40&sourceid=chrome&ie=UTF-8'}}, 'serpapi_pagination': {'current': 1, 'next_link': 'https://serpapi.com/search.json?device=desktop&engine=google&google_domain=google.com&hl=ja&q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&start=10', 'next': 'https://serpapi.com/search.json?device=desktop&engine=google&google_domain=google.com&hl=ja&q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&start=10', 'other_pages': {'2': 'https://serpapi.com/search.json?device=desktop&engine=google&google_domain=google.com&hl=ja&q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&start=10', '3': 'https://serpapi.com/search.json?device=desktop&engine=google&google_domain=google.com&hl=ja&q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&start=20', '4': 'https://serpapi.com/search.json?device=desktop&engine=google&google_domain=google.com&hl=ja&q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&start=30', '5': 'https://serpapi.com/search.json?device=desktop&engine=google&google_domain=google.com&hl=ja&q=%E6%9C%89%E9%99%90%E4%BC%9A%E7%A4%BE%E5%B7%9D%E8%B6%8A%E5%B1%8B%E7%A1%9D%E5%AD%90%E5%BA%97+03-3391-1309+s.sibata522%2B1%40gmail.com&start=40'}}}

        url, address_text, snippet_text, info = "", "", "", ""

        if "knowledge_graph" in serp and "website" in serp["knowledge_graph"]:
            url = serp["knowledge_graph"]["website"]
        elif "organic_results" in serp and len(serp["organic_results"]) > 0:
            url = serp["organic_results"][0].get("link", "")

        if "knowledge_graph" in serp:
            address_text = serp["knowledge_graph"].get("address", "") # 所在地も追加
        if "organic_results" in serp and len(serp["organic_results"]) > 0:
            snippet_text = serp["organic_results"][0].get("snippet", "")
            info = snippet_text

        logging.info(f"[STEP 1] URL: {url}, Address: {address_text}, Snippet: {snippet_text}")

        # Step 2: ホームページから都道府県を取得
        prefecture = ""
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=7)
            soup = BeautifulSoup(res.text, "html.parser") # これを出力してaddress取得できないか確認。
            text = soup.get_text()
            match = re.search(r"(東京都|北海道|(?:京都|大阪)府|.{2,3}県)", text)
            if match:
                prefecture = match.group(1)
        except Exception as e:
            logging.warning(f"[STEP 2] Failed to fetch from URL: {url}, trying fallback. Error: {e}")
            for source in [address_text, snippet_text]:
                match = re.search(r"(東京都|北海道|(?:京都|大阪)府|.{2,3}県)", source)
                if match:
                    prefecture = match.group(1)
                    break

        logging.info(f"[STEP 2] Extracted prefecture for '{company_name}': {prefecture}")

        enriched_items.append({
            "company_name": company_name,
            "email": email,
            "url": url,
            "prefecture": prefecture,
            "info": info
        })

    logging.info(f"[STEP 3] Enriched Items: {enriched_items}")


    # Step 3: Difyへ一括送信
    dify_payload = {
        "inputs": {
            "industry_texts": payload.industry_texts,
            "info_list": json.dumps([
                {"company_name": item["company_name"], "info": item["info"]}
                for item in enriched_items
            ], ensure_ascii=False)
        },
        "response_mode": "blocking",
        "user": "company-fetcher"
    }

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        dify_response = requests.post(DIFY_API_URL, headers=headers, json=dify_payload)
        dify_response.raise_for_status()
    
        dify_result = dify_response.json()
        logging.info(f"[DIFY RAW RESPONSE]: {json.dumps(dify_result, ensure_ascii=False)}")
    
        # "data" → "outputs" → "results" を取得（文字列として）
        results_str = dify_result.get("data", {}).get("outputs", {}).get("results", "[]")
    
        # JSON文字列をリストに変換
        predictions = json.loads(results_str)
        logging.info(f"[DIFY PARSED PREDICTIONS]: {predictions}")
    
    except Exception as e:
        logging.error(f"[DIFY ERROR] 呼び出し or 結果のパースに失敗: {e}")
        predictions = []

    # Step 4: 結果を統合
    results = []
    for item in enriched_items:
        matched = next((p["industry"] for p in predictions if p["company_name"] == item["company_name"]), "")
        results.append({
            "company_name": item["company_name"],
            "email": item["email"],
            "url": item["url"],
            "prefecture": item["prefecture"],
            "industry": matched
        })

    return results
