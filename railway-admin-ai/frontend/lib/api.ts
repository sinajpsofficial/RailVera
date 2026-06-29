const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// Helper to get auth header
export function getAuthHeaders(): Record<string, string> {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      return {
        "Authorization": `Bearer ${token}`
      };
    }
  }
  return {};
}

// ── Auth API ───────────────────────────────────────────────────────────

export async function login(email: string, password: string) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000); // 15s timeout
  try {
    const res = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      signal: controller.signal,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Authentication failed");
    }
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    return data;
  } finally {
    clearTimeout(timeout);
  }
}

export async function register(payload: any) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000); // 15s timeout
  try {
    const res = await fetch(`${API_URL}/api/auth/register`, {
      method: "POST",
      signal: controller.signal,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed");
    }
    return await res.json();
  } finally {
    clearTimeout(timeout);
  }
}


export function logout() {
  localStorage.removeItem("token");
}

export async function getMe() {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000); // 5s timeout
  try {
    const res = await fetch(`${API_URL}/api/auth/me`, {
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      }
    });
    if (!res.ok) throw new Error("Unauthorized");
    return await res.json();
  } finally {
    clearTimeout(timeout);
  }
}


// ── Cases API ──────────────────────────────────────────────────────────

export async function createCase(domain: string, query_text: string) {
  const res = await fetch(`${API_URL}/api/cases/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({ domain, query_text })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create case");
  }
  return await res.json();
}

export async function getCaseDetails(caseId: string) {
  const res = await fetch(`${API_URL}/api/cases/${caseId}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error("Failed to fetch case details");
  return await res.json();
}

/**
 * Sends a free-text reply on a case.
 * The backend parses facts from the message, merges them into case.extracted_facts,
 * and re-evaluates eligibility — returning a fresh EligibilityCheckResponse.
 */
export async function sendCaseReply(caseId: string, message: string) {
  const res = await fetch(`${API_URL}/api/cases/${caseId}/reply`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({ message })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Reply failed");
  }
  return await res.json();
}



// ── Document API ───────────────────────────────────────────────────────

export async function uploadDocument(file: File, caseId: string) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("case_id", caseId);

  const res = await fetch(`${API_URL}/api/documents/upload`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Document upload failed");
  }
  return await res.json();
}

// ── Eligibility API ────────────────────────────────────────────────────

export async function runEligibilityCheck(caseId: string) {
  const res = await fetch(`${API_URL}/api/eligibility/check`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({ case_id: caseId })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Eligibility check failed");
  }
  return await res.json();
}

// ── Reports API ────────────────────────────────────────────────────────

export async function generateReport(caseId: string) {
  const res = await fetch(`${API_URL}/api/reports/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({ case_id: caseId })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate report");
  }
  return await res.json();
}

export function getReportDownloadUrl(reportId: string) {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  return `${API_URL}/api/reports/${reportId}/download${token ? `?token=${token}` : ""}`;
}

export async function getMyCases() {
  const res = await fetch(`${API_URL}/api/cases/me`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error("Failed to fetch user cases");
  return await res.json();
}

export async function getPendingCases() {
  const res = await fetch(`${API_URL}/api/cases/pending`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error("Failed to fetch pending cases");
  return await res.json();
}

export async function getCaseConversation(caseId: string) {
  const res = await fetch(`${API_URL}/api/cases/${caseId}/conversation`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error("Failed to fetch case conversation");
  return await res.json();
}

export async function reviewCase(caseId: string, action: "approve" | "reject", notes: string) {
  const res = await fetch(`${API_URL}/api/cases/${caseId}/review`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({ action, notes })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to submit review");
  }
  return await res.json();
}

// ── Rules API ──────────────────────────────────────────────────────────

export async function getRule(ruleId: string) {
  const res = await fetch(`${API_URL}/api/rules/${ruleId}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error("Failed to fetch rule");
  return await res.json();
}
