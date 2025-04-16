from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import requests
from bs4 import BeautifulSoup
import re
import os

app = FastAPI()

# Dify Workflow API設定
DIFY_API_URL = "https://api.dify.ai/v1/workflows/YOUR_WORKFLOW_ID/execute"
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

@app.post("/")
async def handle_batch_request(payload: RequestPayload):
    results = []

    for item in payload.items:
        company_name = item.company_name
        phone_number = item.phone_number
        email = item.email

        # Step 1: SerpApiで企業URLを取得
        query = f"{company_name} {phone_number} {email}".strip()
        serp = requests.get("https://serpapi.com/search.json", params={
            "q": query,
            "hl": "ja",
            "api_key": SERP_API_KEY
        }).json()

        url, address_text, snippet_text, info = "", "", "", ""

        if "knowledge_graph" in serp and "website" in serp["knowledge_graph"]:
            url = serp["knowledge_graph"]["website"]
        elif "organic_results" in serp and len(serp["organic_results"]) > 0:
            url = serp["organic_results"][0].get("link", "")

        if "knowledge_graph" in serp:
            address_text = serp["knowledge_graph"].get("address", "")
        if "organic_results" in serp and len(serp["organic_results"]) > 0:
            snippet_text = serp["organic_results"][0].get("snippet", "")
            info = snippet_text

        # Step 2: ホームページから都道府県を取得
        prefecture = ""
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text()
            match = re.search(r"(東京都|北海道|(?:京都|大阪)府|.{2,3}県)", text)
            if match:
                prefecture = match.group(1)
        except:
            for source in [address_text, snippet_text]:
                match = re.search(r"(東京都|北海道|(?:京都|大阪)府|.{2,3}県)", source)
                if match:
                    prefecture = match.group(1)
                    break

        # Step 3: Difyへ送信（業種分類）
        headers = {
            "Authorization": f"Bearer {DIFY_API_KEY}",
            "Content-Type": "application/json"
        }

        dify_payload = {
            "inputs": {
                "info": info,
                "file": payload.industry_texts
            },
            "response_mode": "streaming",
            "user": "company-fetcher"
        }

        try:
            dify_response = requests.post(DIFY_API_URL, headers=headers, json=dify_payload)
            dify_result = dify_response.json()
            predicted_industry = dify_result.get("industry", "")
        except Exception as e:
            predicted_industry = ""

        # 結果を追加
        results.append({
            "company_name": company_name,
            "email": email,
            "url": url,
            "prefecture": prefecture,
            "industry": predicted_industry
        })

    return results
