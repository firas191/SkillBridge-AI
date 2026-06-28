# SkillBridge AI — Structured Output Examples

Every module emits validated, structured JSON (Pydantic schemas). Abbreviated, realistic
examples below (from the "AI & Automation Engineer Intern" case).

## 1. Explainable match (`/match/adhoc` → `MatchResult`)

The core deliverable: skills, scores, **evidence**, and recommendations.

```json
{
  "overall_score": 70.0,
  "verdict": "moderate_fit",
  "required_coverage": 0.75,
  "preferred_coverage": 1.0,
  "matched_skills": [
    {
      "requirement": "Large Language Models",
      "canonical_id": "llm",
      "importance": "required",
      "status": "matched",
      "score": 1.0,
      "candidate_skill": "Large Language Models",
      "candidate_evidence": "Deployed a local LLM (TinyLlama) via Flask, cutting drafting time 70%.",
      "rationale": "Candidate demonstrates 'Large Language Models'. Evidence: ..."
    },
    {
      "requirement": "OpenAI API",
      "importance": "required",
      "status": "matched",
      "rationale": "Satisfies 'OpenAI API' via the accepted alternative 'LangChain'."
    }
  ],
  "missing_skills": [
    { "requirement": "Workflow Automation", "importance": "preferred", "status": "missing",
      "rationale": "No evidence of 'Workflow Automation' in the candidate profile." }
  ],
  "gaps": [
    { "skill": "n8n", "importance": "required", "severity": "high",
      "recommendation": "Build foundational proficiency in n8n." }
  ],
  "extra_skills": ["Computer Vision", "MLOps", "PyTorch"],
  "summary": "Ben Khalifa Mohamed Firas is a moderate fit (70/100) for AI & Automation Engineer Intern ..."
}
```

## 2. Learning plan (`/learning-plan` → `LearningPlan`, abbreviated)

```json
{
  "total_weeks": 4, "weekly_hours": 8,
  "leverage_strengths": ["Your LangChain knowledge accelerates learning Workflow Automation."],
  "priority_order": ["Workflow Automation", "KPI Tracking"],
  "modules": [{
    "skill": "Workflow Automation", "estimated_hours": 10,
    "concepts": ["Triggers", "Integration patterns", "Error handling"],
    "practice_project": "Build an n8n workflow: webhook → LLM summary → Slack.",
    "resources": [{ "title": "n8n Docs", "url": "https://docs.n8n.io", "type": "docs" }]
  }],
  "weekly_missions": [{ "week": 1, "theme": "Automation foundations",
    "tasks": ["Install n8n", "Build a webhook workflow"], "deliverable": "First working workflow" }]
}
```

## 3. Interview debrief (`/interview/report` → `InterviewReport`, abbreviated)

```json
{
  "overall_score": 76, "verdict": "Interview-ready",
  "assessments": [{
    "question": "Walk me through deploying a local LLM with Flask.",
    "score": 5, "feedback": "Specific and metric-backed; nothing missing.",
    "strong_answer_points": ["Architecture", "Trade-offs", "Measured outcome"]
  }],
  "strengths": ["Hands-on LLM experience"],
  "improvements": ["Use STAR structure for behavioural answers"],
  "next_steps": ["Practise 3 behavioural stories"]
}
```

## 4. Recruiter brief (`/hr/recommendation` → `HRRecommendation`, abbreviated)

```json
{
  "decision": "interview_with_focus",
  "decision_label": "Interview — with focus areas",
  "headline": "Promising candidate, strong in core AI, focus on automation application.",
  "salary_benchmark": { "role": "ai engineer", "seniority": "intern",
    "currency": "USD", "min": 42000, "median": 58000, "max": 78000 },
  "skill_demand": [{ "skill": "Large Language Models", "demand": "very_high" }],
  "market_outlook": "Demand: very high; trend: surging; competition: very_high.",
  "interview_focus": ["Probe Workflow Automation aptitude"],
  "risks": ["Strong theoretical AI without practical automation application"],
  "fairness_notes": ["Treat the automation gap as learnable for an intern role."],
  "tool_calls": [{ "tool": "salary_benchmark", "summary": "ai engineer (intern): USD 42,000–78,000", "source": "bundled market dataset" }],
  "disclaimer": "Decision support only — a human recruiter makes the final call."
}
```

## 5. Career Twin (`/twin/{id}` → `CareerTwin`, abbreviated)

```json
{
  "name": "Ben Khalifa Mohamed Firas",
  "aggregate": { "roles_explored": 2, "best_fit_role": "ML Engineer", "best_fit_score": 82.0,
    "avg_match_score": 76.0, "interviews_taken": 1, "avg_interview_score": 76.0,
    "recurring_gaps": ["n8n"], "top_skills": ["Large Language Models", "LangChain", "Python"] },
  "briefing": { "headline": "Your path is clearly toward AI & Automation Engineering.",
    "momentum": "Building strong momentum.", "recommended_direction": "Lean into applied LLM/agent roles.",
    "next_missions": ["Explore learning resources for n8n", "Apply to 3 AI roles this week"] },
  "activities": [{ "kind": "match", "title": "AI & Automation Engineer Intern", "score": 82.0 }]
}
```
