// Mirrors the backend response schemas (subset used by the UI).

export interface SkillEvidence {
  name: string;
  canonical_id: string | null;
  canonical_name: string | null;
  category: string | null;
  evidence: string | null;
  proficiency: string | null;
  years_experience: number | null;
  confidence: number;
  match_method: string;
  match_score: number;
}

export interface CandidateProfile {
  name: string;
  headline: string | null;
  summary: string | null;
  total_years_experience: number | null;
  skills: SkillEvidence[];
  education: string[];
  certifications: string[];
}

export interface JobRequirement {
  name: string;
  canonical_id: string | null;
  canonical_name: string | null;
  importance: string;
  weight: number;
  min_years: number | null;
}

export interface JobProfile {
  title: string;
  company: string | null;
  seniority: string | null;
  summary: string | null;
  requirements: JobRequirement[];
  responsibilities: string[];
}

export type MatchStatus = "matched" | "partial" | "missing";
export type Verdict = "strong_fit" | "moderate_fit" | "weak_fit";

export interface SkillMatch {
  requirement: string;
  canonical_id: string | null;
  importance: string;
  weight: number;
  status: MatchStatus;
  score: number;
  candidate_skill: string | null;
  candidate_evidence: string | null;
  candidate_proficiency: string | null;
  candidate_years: number | null;
  required_min_years: number | null;
  rationale: string;
}

export interface Gap {
  skill: string;
  importance: string;
  severity: "high" | "medium" | "low";
  reason: string;
  recommendation: string;
}

export interface MatchResult {
  overall_score: number;
  verdict: Verdict;
  required_coverage: number;
  preferred_coverage: number;
  matched_skills: SkillMatch[];
  missing_skills: SkillMatch[];
  extra_skills: string[];
  gaps: Gap[];
  summary: string;
  candidate_name: string | null;
  job_title: string | null;
}

export interface AdhocMatchResponse {
  candidate: CandidateProfile;
  job: JobProfile;
  result: MatchResult;
}

// ---- Learning Coach ----
export interface LearningResource {
  title: string;
  url: string | null;
  type: "docs" | "course" | "video" | "article" | "practice" | "tool";
}

export interface SkillModule {
  skill: string;
  canonical_id: string | null;
  importance: string;
  why_it_matters: string;
  concepts: string[];
  steps: string[];
  practice_project: string;
  estimated_hours: number;
  resources: LearningResource[];
}

export interface WeeklyMission {
  week: number;
  theme: string;
  focus_skills: string[];
  tasks: string[];
  deliverable: string;
}

export interface LearningPlan {
  candidate_name: string;
  job_title: string;
  overview: string;
  total_weeks: number;
  weekly_hours: number;
  leverage_strengths: string[];
  priority_order: string[];
  modules: SkillModule[];
  weekly_missions: WeeklyMission[];
  closing_note: string;
}

export interface LearningPlanRequest {
  candidate_name: string;
  job_title: string;
  gaps: { skill: string; importance: string; severity: string }[];
  strengths: string[];
  weekly_hours: number;
}

// ---- Interview Simulator ----
export interface InterviewQuestion {
  id: number;
  question: string;
  focus: string;
  type: string;
  what_good_looks_like: string;
}

export interface InterviewPlan {
  intro: string;
  questions: InterviewQuestion[];
}

export interface InterviewPlanRequest {
  candidate_name: string;
  job_title: string;
  summary?: string;
  strengths: string[];
  gaps: string[];
  num_questions: number;
}

export interface TranscriptTurn {
  question: string;
  focus: string;
  what_good_looks_like: string;
  answer: string;
}

export interface InterviewReportRequest {
  candidate_name: string;
  job_title: string;
  transcript: TranscriptTurn[];
}

export interface AnswerAssessment {
  question: string;
  score: number;
  feedback: string;
  strong_answer_points: string[];
}

export interface InterviewReport {
  candidate_name: string;
  job_title: string;
  overall_score: number;
  verdict: string;
  summary: string;
  assessments: AnswerAssessment[];
  strengths: string[];
  improvements: string[];
  next_steps: string[];
}

// ---- HR Agent ----
export interface SalaryBenchmark {
  role: string;
  seniority: string;
  currency: string;
  min: number;
  median: number;
  max: number;
  source: string;
  matched: boolean;
}

export interface SkillDemandItem {
  skill: string;
  demand: string;
}

export interface ToolInvocation {
  tool: string;
  summary: string;
  source: string;
}

export interface HRRequest {
  candidate_name: string;
  job_title: string;
  region?: string;
  seniority?: string;
  strengths: string[];
  gaps: string[];
  overall_score: number;
  verdict?: string;
  summary?: string;
}

export interface HRRecommendation {
  candidate_name: string;
  job_title: string;
  decision: string;
  decision_label: string;
  headline: string;
  rationale: string;
  salary_benchmark?: SalaryBenchmark | null;
  skill_demand: SkillDemandItem[];
  market_outlook: string;
  interview_focus: string[];
  risks: string[];
  fairness_notes: string[];
  tool_calls: ToolInvocation[];
  disclaimer: string;
}

// ---- Career Twin ----
export interface TwinActivity {
  id: string;
  kind: string;
  title: string;
  score?: number | null;
  verdict?: string | null;
  detail: Record<string, unknown>;
  created_at: string;
}

export interface TwinAggregate {
  roles_explored: number;
  best_fit_role?: string | null;
  best_fit_score?: number | null;
  avg_match_score?: number | null;
  interviews_taken: number;
  avg_interview_score?: number | null;
  learning_plans: number;
  recurring_gaps: string[];
  top_skills: string[];
}

export interface TwinBriefing {
  headline: string;
  narrative: string;
  momentum: string;
  recommended_direction: string;
  next_missions: string[];
}

export interface CareerTwin {
  id: string;
  name: string;
  profile: CandidateProfile;
  aggregate: TwinAggregate;
  activities: TwinActivity[];
  briefing: TwinBriefing;
  updated_at: string;
}

export interface TwinSaveRequest {
  candidate_name: string;
  profile: CandidateProfile;
  kind: string;
  title: string;
  score?: number | null;
  verdict?: string | null;
  detail: Record<string, unknown>;
}
