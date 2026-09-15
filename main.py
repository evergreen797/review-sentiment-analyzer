"""
Review Sentiment & Summary Analyzer — Apify Actor
"""

import asyncio
import json
import re

import requests
from apify import Actor

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"


def parse_reviews(reviews_text: str, max_reviews: int) -> list[str]:
    lines = [line.strip() for line in reviews_text.splitlines()]
    reviews = [line for line in lines if line]
    return reviews[:max_reviews]


def build_prompt(reviews: list[str]) -> str:
    numbered_reviews = "\n".join(f"{i + 1}. {r}" for i, r in enumerate(reviews))

    return f"""Analizza queste {len(reviews)} recensioni di clienti. Per ognuna, determina il sentiment e fino a 3 temi ricorrenti brevi (es. "tempi di consegna", "qualità prodotto").

Poi genera un riassunto complessivo in 2-3 frasi e i 5 temi più ricorrenti in totale.

Rispondi SOLO con un oggetto JSON valido in questo formato esatto, senza testo aggiuntivo prima o dopo:

{{
  "reviews": [
    {{"index": 1, "sentiment": "positivo", "themes": ["tema1", "tema2"]}},
    ...
  ],
  "overall_summary": "riassunto in 2-3 fr

