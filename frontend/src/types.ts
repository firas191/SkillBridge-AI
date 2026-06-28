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
