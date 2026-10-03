export interface LegalArticle {
  id: string;
  regulation_name: string;
  regulation_number: string;
  regulation_year: number;
  hierarchy_level: string;
  status: "BERLAKU" | "DICABUT_SEBAGIAN" | "DICABUT_SELURUHNYA" | "MENGUBAH" | "DIUJI_MK";
  chapter?: string | null;
  part?: string | null;
  article_number: string;
  content: string;
  explanation?: string | null;
  effective_date?: string | null;
  notes?: string | null;
}

export interface ClarificationOption {
  label: string;
  description: string;
  legal_implication: string;
}

export interface ClarificationQuestion {
  id: string;
  question: string;
  context_why_needed: string;
  options: ClarificationOption[];
  allow_custom_input: boolean;
}

export interface LegalAssessment {
  case_summary: string;
  issue: string;
  applicable_rules: LegalArticle[];
  application_analysis: string;
  conclusion: string;
  aggravating_factors: string[];
  mitigating_factors: string[];
  procedural_steps: string[];
  legal_disclaimer: string;
}

export interface QueryApiResponse {
  is_clarification_mode: boolean;
  message: string;
  completeness_score: number;
  missing_elements: string[];
  clarification_questions: ClarificationQuestion[];
  assessment: LegalAssessment | null;
  retrieved_articles: LegalArticle[];
}
