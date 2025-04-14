from fastapi import FastAPI, Request
import requests
from bs4 import BeautifulSoup
import re
import os
api_key = os.getenv("SERPAPI_KEY")

app = FastAPI()

@app.post("/")
async def get_info(data: Request):
    body = await data.json()
    company_name = body["company_name"]
    phone_number = body["phone_number"]
    email = body["email"]

    # SerpAPIでURL取得
    api_key = "YOUR_SERPAPI_KEY"
    query = f"{company_name} {phone_number} {email}".strip()
    serp = requests.get("https://serpapi.com/search.json", params={
        "q": query, "hl": "ja", "api_key": api_key
    }).json()

    url = ""
    if "knowledge_graph" in serp and "website" in serp["knowledge_graph"]:
        url = serp["knowledge_graph"]["website"]
    elif "organic_results" in serp and len(serp["organic_results"]) > 0:
        url = serp["organic_results"][0].get("link", "")

    # URLから都道府県・業種抽出
    prefecture, industry = "", ""
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text()
        match = re.search(r"(東京都|北海道|(?:京都|大阪)府|.{2,3}県)", text)
        if match:
            prefecture = match.group(1)

        keywords = ["IT", "製造", "小売", "不動産", "建設", "医療", "教育", "物流", "サービス"]
        found = [kw for kw in keywords if kw in text]
        industry = found[0] if found else ""
    except:
        pass

    return {
        "url": url,
        "prefecture": prefecture,
        "industry": industry
    }
