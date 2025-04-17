from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import requests
from bs4 import BeautifulSoup
import re
import os
import logging
from fastapi import Response

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

        serp = requests.get("https://serpapi.com/search.json", params={
            "q": query,
            "hl": "ja",
            "api_key": SERP_API_KEY
        }).json()

        logging.info(f"[STEP 1] SerpAPI response for '{company_name}': {serp}")

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
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
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
    # Dify API送信前にログを出力
    logging.info(f"[DIFY DEBUG] Request URL: {DIFY_API_URL}")
    logging.info(f"[DIFY DEBUG] API_KEY is set: {bool(DIFY_API_KEY)}")
    logging.info(f"[DIFY DEBUG] Payload: {dify_payload}")
    logging.info(f"[DIFY DEBUG] Headers: {headers}")


    try:
        dify_response = requests.post(DIFY_API_URL, headers=headers, json=dify_payload)
        dify_response.raise_for_status()  # ステータスコードが4xx/5xxなら例外にする
        dify_result = dify_response.json()
        predictions = dify_result.get("results", [])
        logging.info(f"[DIFY RAW RESPONSE]: {dify_result}")
    except Exception as e:
        logging.error(f"[DIFY ERROR] 呼び出しに失敗: {str(e)}")
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
