import json
import httpx
from typing import Dict, Any, List
from app.core.config import settings

# Structured diagnosis template for fallback
def generate_deterministic_ai_fallback(metrics: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    rev_change_pct = metrics["revenue"]["change_percent"]
    margin_change = metrics["margin"]["change_pp"]
    high_risk_count = metrics["customers"]["high_risk"]
    prop_margin = metrics["margin"]["proposed"]
    prop_rev = metrics["revenue"]["proposed"]
    curr_rev = metrics["revenue"]["current"]
    
    # 1. Diagnoses
    diagnoses = []
    if rev_change_pct < -2.0:
        diagnoses.append(
            f"Revenue Leakage: The proposed model reduces total revenue by {abs(rev_change_pct):.1f}% "
            f"(${abs(metrics['revenue']['change']):,.2f} less than current pricing of ${curr_rev:,.2f})."
        )
    elif rev_change_pct > 2.0:
        diagnoses.append(
            f"Revenue Expansion: The proposed model increases revenue by {rev_change_pct:.1f}% "
            f"(extra ${metrics['revenue']['change']:,.2f})."
        )
    else:
        diagnoses.append("Revenue Neutral: The pricing adjustment yields less than 2% change in overall revenue.")

    if margin_change < -1.0:
        diagnoses.append(
            f"Margin Compression: Gross margins deteriorate by {abs(margin_change):.1f} percentage points, "
            f"landing at {prop_margin:.1f}%. The cost of compute is not being absorbed efficiently."
        )
    elif margin_change > 1.0:
        diagnoses.append(
            f"Margin Optimization: Gross margin improves to {prop_margin:.1f}% (+{margin_change:.1f}pp). "
            f"Better coverage of underlying server infrastructure cost."
        )
        
    if metrics["customers"]["bill_increases"] > 300:
        diagnoses.append(
            f"Broad Overage Exposure: Over {metrics['customers']['bill_increases']} customers are exceeding "
            f"included units, pointing to an overage-heavy billing dynamic."
        )

    # 2. Risks
    risks = []
    if high_risk_count > 0:
        risks.append(
            f"Bill Shock: {high_risk_count} customers will experience >25% bill increases. "
            f"This represents a churn risk, particularly in the Growth and Startup segments."
        )
    if prop_margin < 40.0:
        risks.append(
            f"Negative Margin Risk: Proposed margin is low ({prop_margin:.1f}%). "
            f"Extreme usage spikes could cause specific customers to become unprofitable."
        )
    
    # Check for revenue concentration in top users
    risks.append(
        "Heavy User Dependency: The top 5% of customers drive a significant portion of revenue. "
        "Any contract churn among high-tier users would heavily impact the monthly run rate."
    )

    # 3. Recommendations
    recommendation_options = []
    for idx, cand in enumerate(candidates):
        cand_rev = cand["revenue"]["proposed"]
        cand_margin = cand["margin"]["proposed"]
        cand_risk = cand["customers"]["high_risk"]
        
        # Craft explanation
        if idx == 0:
            explanation = (
                f"This option lowers the barrier to entry with a base of ${cand['base_price']}. "
                f"Maintains a high overage fee, preserving revenue from enterprise users while protecting startups."
            )
        elif idx == 1:
            explanation = (
                f"Recommended. Increasing included tasks to {cand['included_units']} absorbs regular users "
                f"within the subscription. Decreasing overage slightly reduces bill shock by {abs(cand_risk - high_risk_count)} customers."
            )
        else:
            explanation = (
                f"Premium offering. A higher base of ${cand['base_price']} targets high-utilization growth accounts, "
                f"boosting gross margin to {cand_margin:.1f}%."
            )
            
        recommendation_options.append({
            "option_name": f"Option {chr(65+idx)}: {cand['name']}",
            "base_price": float(cand["base_price"]),
            "included_units": int(cand["included_units"]),
            "overage_price": float(cand["overage_price"]),
            "revenue": float(cand_rev),
            "margin": float(cand_margin),
            "high_risk_customers": int(cand_risk),
            "explanation": explanation
        })

    summary = (
        f"The proposed pricing change results in a gross revenue of ${prop_rev:,.2f} with a gross margin of {prop_margin:.1f}%. "
        f"The primary driver of the revenue change is the modified overage rate. We recommend implementing Option B "
        f"to balance margin protection and customer bill stability."
    )

    return {
        "diagnosis": diagnoses,
        "risks": risks,
        "recommendations": recommendation_options,
        "summary": summary
    }

async def analyze_simulation_with_ai(metrics: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calls Gemini or OpenAI, or falls back to a deterministic analysis.
    """
    # 1. Prepare structured data
    analysis_payload = {
        "simulation_metrics": {
            "revenue": metrics["revenue"],
            "margin": metrics["margin"],
            "customers": metrics["customers"],
            "health_score": metrics["health_score"]
        },
        "candidates": [
            {
                "base_price": c["base_price"],
                "included_units": c["included_units"],
                "overage_price": c["overage_price"],
                "revenue": c["revenue"]["proposed"],
                "margin": c["margin"]["proposed"],
                "high_risk_customers": c["customers"]["high_risk"]
            }
            for c in candidates
        ]
    }

    # 2. Check for real keys
    if not settings.GEMINI_API_KEY and not settings.OPENAI_API_KEY:
        # Return deterministic analysis immediately (Demo Mode fallback)
        return generate_deterministic_ai_fallback(metrics, candidates)

    prompt = f"""
    You are the "AI Pricing Doctor", a pricing strategist for Flexprice Revenue Twin.
    Analyze this monetization simulation payload:
    {json.dumps(analysis_payload, indent=2)}

    Identify:
    1. Margin leakage (infrastructure cost vs revenue).
    2. Customer bill shock risks (high-risk bill changes).
    3. Heavy user dependency.
    
    Evaluate the candidate models and rank/recommend them based on the simulation numbers.
    Do NOT invent numerical results; use the exact candidate revenue, margin, and risk stats.

    Return your output in raw JSON format matching this schema:
    {{
        "diagnosis": ["list of structural pricing problems"],
        "risks": ["list of financial or churn risks"],
        "recommendations": [
            {{
                "option_name": "Option A / B / C",
                "base_price": 49.00,
                "included_units": 100,
                "overage_price": 0.75,
                "revenue": 52000.00,
                "margin": 54.2,
                "high_risk_customers": 12,
                "explanation": "Tradeoff detail of this candidate model based on the simulated metrics"
            }}
        ],
        "summary": "High-level strategic interpretation of the results."
    }}
    Do NOT wrap the JSON in Markdown code block tags. Return only the raw JSON.
    """

    try:
        if settings.GEMINI_API_KEY:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    result = resp.json()
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(text)

        elif settings.OPENAI_API_KEY:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": settings.LLM_MODEL or "gpt-4o-mini",
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "You are a professional pricing intelligence doctor. Return JSON only."},
                    {"role": "user", "content": prompt}
                ]
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    result = resp.json()
                    text = result["choices"][0]["message"]["content"]
                    return json.loads(text)

    except Exception as e:
        print(f"AI Service API Call failed: {e}. Falling back to deterministic analysis.")
        
    return generate_deterministic_ai_fallback(metrics, candidates)
