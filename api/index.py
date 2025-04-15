from fastapi import FastAPI, Request
import requests
from bs4 import BeautifulSoup
import re
import os

app = FastAPI()

DIFY_API_URL = "https://api.dify.ai/v1/workflows/YOUR_WORKFLOW_ID/execute"
DIFY_API_KEY = os.getenv("DIFY_API_KEY")
SERP_API_KEY = os.getenv("SERPAPI_KEY")


@app.post("/")
async def get_info_with_file(
    company_name: str = Form(...),
    phone_number: str = Form(...),
    email: str = Form(...),
    file: UploadFile = File(...)
):
    # SerpAPIでURL取得
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

    # Difyにmultipart/form-dataで送信
    files = {
        "file": (file.filename, await file.read(), file.content_type)
    }

    data = {
        "inputs": {
            "url": url,
            "prefecture": prefecture,
            "info": info
        },
        "response_mode": "blocking",
        "user": "auto"
    }

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}"
    }

    response = requests.post(
        DIFY_API_URL,
        headers=headers,
        data={"inputs": str(data["inputs"]), "response_mode": "blocking", "user": "auto"},
        files=files
    )

    return {"status": "sent to dify", "dify_status_code": response.status_code}
