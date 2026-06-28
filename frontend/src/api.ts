import type {
  AdhocMatchResponse,
  InterviewPlan,
  InterviewPlanRequest,
  InterviewReport,
  InterviewReportRequest,
  LearningPlan,
  LearningPlanRequest,
} from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE as string) || "/api";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export interface ExtractedDoc {
  filename: string;
  text: string;
  char_count: number;
  method: string; // pdf-text | pdf-ocr | docx | text | image-ocr
}

export async function extractDocText(file: File): Promise<ExtractedDoc> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/documents/extract-text`, {
    method: "POST",
    body: form,
  });
  return handle<ExtractedDoc>(res);
}

export async function adhocMatch(
  cvText: string,
  jobText: string,
): Promise<AdhocMatchResponse> {
  const res = await fetch(`${API_BASE}/match/adhoc`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cv_text: cvText, job_text: jobText }),
  });
  return handle<AdhocMatchResponse>(res);
}

export async function generateLearningPlan(
  payload: LearningPlanRequest,
): Promise<LearningPlan> {
  const res = await fetch(`${API_BASE}/learning-plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle<LearningPlan>(res);
}

export async function startInterview(
  payload: InterviewPlanRequest,
): Promise<InterviewPlan> {
  const res = await fetch(`${API_BASE}/interview/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle<InterviewPlan>(res);
}

export async function getInterviewReport(
  payload: InterviewReportRequest,
): Promise<InterviewReport> {
  const res = await fetch(`${API_BASE}/interview/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle<InterviewReport>(res);
}
