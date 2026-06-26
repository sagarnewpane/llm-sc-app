"""LLM-powered heritage recommendation service using Groq."""

from __future__ import annotations

import json
import logging
from typing import Any

from groq import Groq

from app.core.config import get_settings
from app.db.supabase_client import get_supabase

logger = logging.getLogger(__name__)

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not configured")
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def _get_metric(family: str, key: str) -> Any | None:
    sb = get_supabase()
    result = (
        sb.table("metrics_current")
        .select("metric_value")
        .eq("metric_family", family)
        .eq("metric_key", key)
        .execute()
    )
    if result.data:
        return result.data[0]["metric_value"]
    return None


def _gather_context() -> dict[str, Any]:
    """Gather compact heritage data for the LLM prompt."""
    sb = get_supabase()
    context: dict[str, Any] = {}

    kpi = _get_metric("overview", "kpi_summary")
    if kpi:
        context["overview"] = {
            "total_reviews": kpi.get("total_reviews"),
            "avg_rating": kpi.get("avg_rating"),
            "sacred_content_pct": kpi.get("sacred_content_pct"),
        }

    sentiment = _get_metric("overview", "sentiment_share")
    if sentiment:
        context["sentiment"] = {
            s["sentiment_class"]: {"count": s["count"], "pct": s["percentage"]}
            for s in sentiment
        }

    aspects_result = sb.table("aspect_metrics").select(
        "display_aspect, mention_count, positive_pct, negative_pct, avg_sentiment_score"
    ).execute()
    context["aspects"] = [
        {
            "name": a["display_aspect"],
            "mentions": a["mention_count"],
            "pos": a["positive_pct"],
            "neg": a["negative_pct"],
            "score": a["avg_sentiment_score"],
        }
        for a in (aspects_result.data or [])
    ]

    health = _get_metric("narratives", "heritage_health_report")
    if health:
        context["health_alerts"] = [
            {"aspect": h["title"].replace("Concern: ", ""), "priority": h["priority"], "negative_pct": h.get("evidence", {}).get("negative_pct", 0)}
            for h in health if h.get("priority") in ("critical", "high")
        ]

    network = _get_metric("intelligence", "network_summary")
    if network:
        context["knowledge_graph"] = {
            "entities": network.get("total_entities"),
            "edges": network.get("total_edges"),
        }

    community = _get_metric("social_computing", "community_structure")
    if community:
        context["communities"] = {
            "count": community.get("community_count"),
            "modularity": round(community.get("modularity", 0), 3),
        }

    dual = _get_metric("intelligence", "dual_emotion_reviews")
    if dual:
        context["dual_emotions"] = {
            "pct": dual.get("pct_of_reviews"),
            "count": dual.get("dual_emotion_review_count"),
        }

    return context


HERITAGE_SYSTEM_PROMPT = """You are a heritage management AI advisor for Pashupatinath Temple, Nepal.
Analyze visitor review data and provide actionable, interpretable recommendations.

Return JSON with this exact structure:
{
  "narrative_summary": "2-3 sentence overview of current state",
  "critical_findings": [
    {
      "finding": "Specific finding title",
      "explanation": "Why this matters (1-2 sentences)",
      "evidence": "Data point from metrics",
      "impact": "Consequence if ignored",
      "urgency": "critical|high|medium"
    }
  ],
  "recommendations": [
    {
      "title": "Action-oriented title",
      "rationale": "Why this helps (1 sentence)",
      "expected_outcome": "Success metric",
      "stakeholders": ["site_management"],
      "effort": "low|medium|high",
      "timeline": "immediate|short_term|long_term"
    }
  ],
  "heritage_considerations": "Cultural/spiritual context"
}
Keep responses concise. Max 3 findings and 3 recommendations."""


def generate_recommendations() -> dict[str, Any]:
    """Generate LLM-powered heritage recommendations using gathered context."""
    context = _gather_context()
    client = _get_client()

    context_str = json.dumps(context, indent=2, default=str)

    user_prompt = f"""Analyze this Pashupatinath Temple heritage data and provide 3 critical findings and 3 actionable recommendations.

DATA:
{context_str}

Be specific, cite actual numbers, and provide recommendations a heritage site manager could act on immediately."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": HERITAGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )

        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        return result

    except Exception as e:
        logger.error(f"LLM recommendation generation failed: {e}")
        return {
            "narrative_summary": f"LLM generation failed: {str(e)}. Falling back to data overview.",
            "critical_findings": [],
            "recommendations": [],
            "heritage_considerations": "",
            "error": str(e),
        }


DRAFT_RESPONSE_SYSTEM_PROMPT = """You are a heritage site communications advisor for Pashupatinath Temple, Nepal.
Your job is to draft a professional, empathetic, and culturally respectful response to a negative visitor review.

Guidelines:
- Acknowledge the visitor's experience with genuine empathy
- Reference specific concerns they raised
- If applicable, explain what measures are being or will be taken
- Maintain a respectful, humble tone — never dismissive or defensive
- Reference the spiritual/cultural significance of the site where appropriate
- Keep the response concise (3-5 sentences)
- Do NOT use overly corporate language — sound human and sincere

Return JSON with this exact structure:
{
  "draft": "The response text",
  "tone": "empathetic|professional|apologetic",
  "key_points_addressed": ["point1", "point2"]
}"""


def draft_review_response(review_id: str, tone: str = "professional") -> dict[str, Any]:
    """Generate an LLM-drafted response to a negative visitor review."""
    sb = get_supabase()
    client = _get_client()

    review_result = (
        sb.table("cleaned_reviews")
        .select("review_id, title_clean, text_clean, rating, sentiment_class, reviewer_name, trip_type, date")
        .eq("review_id", review_id)
        .execute()
    )
    if not review_result.data:
        return {"draft": "", "tone": tone, "error": f"Review {review_id} not found"}

    review = review_result.data[0]

    sentiments_result = (
        sb.table("sentiment_mentions")
        .select("aspect_raw, sentiment_label, evidence")
        .eq("review_id", review_id)
        .execute()
    )
    aspects = sentiments_result.data or []

    entities_result = (
        sb.table("entity_mentions")
        .select("entity:entities!entity_mentions_entity_id_fkey(display_name, entity_type)")
        .eq("review_id", review_id)
        .execute()
    )
    entities = [
        {"name": e["entity"]["display_name"], "type": e["entity"]["entity_type"]}
        for e in (entities_result.data or [])
        if e.get("entity")
    ]

    context = {
        "review_text": review.get("text_clean", ""),
        "rating": review.get("rating"),
        "title": review.get("title_clean"),
        "sentiment": review.get("sentiment_class"),
        "reviewer": review.get("reviewer_name"),
        "trip_type": review.get("trip_type"),
        "aspects": [{"aspect": a["aspect_raw"], "sentiment": a["sentiment_label"], "evidence": a.get("evidence")} for a in aspects],
        "entities": entities,
    }

    user_prompt = f"""Draft a response to this negative visitor review of Pashupatinath Temple.

REVIEW:
Title: {review.get('title_clean', 'Untitled')}
Rating: {review.get('rating', 'N/A')} stars
Visitor type: {review.get('trip_type', 'Unknown')}
Text: {review.get('text_clean', '')}

Aspect sentiments: {json.dumps(context['aspects'], default=str)}
Entities mentioned: {json.dumps(context['entities'], default=str)}

Tone: {tone}

Draft a sincere, professional response addressing their concerns."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": DRAFT_RESPONSE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=800,
            response_format={"type": "json_object"},
        )

        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        result["review_id"] = review_id
        result["reviewer_name"] = review.get("reviewer_name")
        result["original_rating"] = review.get("rating")
        result["original_sentiment"] = review.get("sentiment_class")
        return result

    except Exception as e:
        logger.error(f"LLM draft response failed for review {review_id}: {e}")
        return {"draft": "", "tone": tone, "error": str(e)}


ACTION_PLAN_SYSTEM_PROMPT = """You are a heritage site operations planner for Pashupatinath Temple, Nepal.
Your job is to break down an insight, recommendation, or issue into specific, actionable tasks that site managers can execute.

Each task must be concrete and actionable — not vague. Include realistic assignee roles and timeframes.

Return JSON with this exact structure:
{
  "summary": "1-2 sentence overview of the action plan",
  "action_items": [
    {
      "title": "Short task title",
      "description": "Specific description of what to do",
      "priority": "critical|high|medium|low",
      "assignee": "role or team name (e.g. 'maintenance_team', 'cultural_affairs', 'site_manager')",
      "due_hint": "timeframe hint (e.g. 'within 1 week', 'within 1 month', 'next quarter')",
      "category": "infrastructure|cultural|visitor_experience|safety|communication"
    }
  ]
}"""


def generate_action_plan(
    source_type: str,
    title: str,
    context: str,
    num_tasks: int = 5,
) -> dict[str, Any]:
    """Generate structured action items from an insight, recommendation, or alert."""
    client = _get_client()

    user_prompt = f"""Break down the following heritage management item into {num_tasks} specific, actionable tasks.

SOURCE TYPE: {source_type}
TITLE: {title}
CONTEXT: {context}

Provide {num_tasks} concrete tasks with clear assignees, priorities, and timeframes.
Focus on what a Pashupatinath Temple site manager can realistically do."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": ACTION_PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )

        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        result["source_type"] = source_type
        result["source_title"] = title
        return result

    except Exception as e:
        logger.error(f"LLM action plan generation failed: {e}")
        return {
            "source_type": source_type,
            "source_title": title,
            "action_items": [],
            "summary": "",
            "error": str(e),
        }
