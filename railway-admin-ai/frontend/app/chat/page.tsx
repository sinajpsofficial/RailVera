"use client";
import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { getMe, createCase, getCaseDetails, uploadDocument, runEligibilityCheck, generateReport, getReportDownloadUrl, logout, sendCaseReply } from "@/lib/api";

import DocumentStatusTracker from "@/components/documents/DocumentStatusTracker";
import DocumentDemandNotice from "@/components/chat/DocumentDemandNotice";
import MessageBubble from "@/components/chat/MessageBubble";
import { Award, LogOut, UploadCloud, AlertCircle, FileCheck, CheckSquare, FileText, Send, HelpCircle } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  type: "text" | "demand_notice" | "followup";
  rules_cited?: string[];
}

const CASE_DOMAINS = [
  { value: "Promotion", label: "Promotion Criteria Assessment" },
  { value: "Leave.Earned", label: "Earned Leave Approval" },
  { value: "Leave.Medical", label: "Medical Leave Check" },
  { value: "Increment", label: "Service Increment Validation" },
  { value: "Discipline", label: "Disciplinary Inquiry Audit" },
  { value: "Transfer", label: "Service Transfer Review" },
  { value: "DeptExam", label: "Departmental Examination clearance" },
  { value: "Retirement", label: "Superannuation Settlement & Benefits" },
];

export default function ChatPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  
  // Auth states
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [loadingUser, setLoadingUser] = useState(true);

  // Case states
  const [caseId, setCaseId] = useState<string | null>(null);
  const [selectedDomain, setSelectedDomain] = useState("Promotion");
  const [caseQuery, setCaseQuery] = useState("");
  const [caseCreated, setCaseCreated] = useState(false);
  const [caseStatus, setCaseStatus] = useState("open");

  // Interaction states
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [loadingMessage, setLoadingMessage] = useState(false);
  
  // Document states
  const [submittedDocs, setSubmittedDocs] = useState<string[]>([]);
  const [missingDocs, setMissingDocs] = useState<string[]>([]);
  const [demandNotice, setDemandNotice] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  // Assessment & Report states
  const [checkingEligibility, setCheckingEligibility] = useState(false);
  const [decisionOutcome, setDecisionOutcome] = useState<string | null>(null);
  const [compilingReport, setCompilingReport] = useState(false);
  const [reportId, setReportId] = useState<string | null>(null);

  // Scroll to bottom helper
  const chatEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, demandNotice]);

  // Auth Guard — fail fast if no token exists
  useEffect(() => {
    async function fetchMe() {
      if (typeof window !== "undefined" && !localStorage.getItem("token")) {
        router.push("/");
        return;
      }
      try {
        const user = await getMe();
        setCurrentUser(user);
      } catch (err) {
        if (typeof window !== "undefined") localStorage.removeItem("token");
        router.push("/");
      } finally {
        setLoadingUser(false);
      }
    }
    fetchMe();
  }, [router]);


  // Handle case initialization
  const handleStartCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!caseQuery.trim()) return;

    setLoadingMessage(true);
    try {
      const dbCase = await createCase(selectedDomain, caseQuery.trim());
      setCaseId(dbCase.id);
      setCaseStatus(dbCase.status);
      setSubmittedDocs(dbCase.submitted_documents || []);
      setMissingDocs(dbCase.missing_documents || []);
      setCaseCreated(true);

      // Add user message & assistant reply
      setMessages([
        {
          id: `usr-${Date.now()}`,
          role: "user",
          content: `Initial Case Query [Domain: ${selectedDomain}]: ${caseQuery.trim()}`,
          type: "text"
        },
        {
          id: `ast-${Date.now()}`,
          role: "assistant",
          content: `Case created successfully. Registered Case ID: ${dbCase.id}.\n\nRequired checklist: ${dbCase.required_documents.join(", ")}.\n` +
                   (dbCase.status === "blocked" 
                     ? "⚠ Note: Evaluation is currently BLOCKED pending document submission." 
                     : "Checklist satisfied. We can evaluate eligibility."),
          type: "text"
        }
      ]);

      // Trigger demand notice warning if case is blocked
      if (dbCase.status === "blocked" && dbCase.missing_documents?.length > 0) {
        // Compile static demand text warning locally or let backend trigger it on check
        setDemandNotice(
          `╔══════════════════════════════════════════════════════╗\n` +
          `║         DOCUMENT REQUIREMENT NOTICE                  ║\n` +
          `║         Case: ${selectedDomain} | Employee: ${currentUser?.name || "Member"}     ║\n` +
          `╚══════════════════════════════════════════════════════╝\n\n` +
          `The following documents are missing and required:\n` +
          dbCase.missing_documents.map((d: string) => `  - ${d} * REQUIRED`).join("\n") +
          `\n\nPlease upload the files using the sidebar to proceed.`
        );
      }
    } catch (err: any) {
      alert(`Failed to start case: ${err.message}`);
    } finally {
      setLoadingMessage(false);
    }
  };

  // Handle file upload
  const handleUploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !caseId) return;

    setUploading(true);
    try {
      const doc = await uploadDocument(file, caseId);
      
      // Update local tracking
      const updatedSubmitted = [...submittedDocs];
      if (doc.document_type && !updatedSubmitted.includes(doc.document_type)) {
        updatedSubmitted.push(doc.document_type);
        setSubmittedDocs(updatedSubmitted);
      }
      
      // Re-read case to pull recalculated missing document checklists
      const caseDetails = await getCaseDetails(caseId);
      setCaseStatus(caseDetails.status);
      setMissingDocs(caseDetails.missing_documents || []);
      
      // Add status message to chat
      setMessages(prev => [
        ...prev,
        {
          id: `upload-${Date.now()}`,
          role: "assistant",
          content: `📄 Uploaded file "${doc.original_filename}" processed successfully.\n` +
                   `- Classified as: ${doc.document_type || "Unknown"}\n` +
                   `- Readability check: ${doc.is_readable ? "PASS" : "FAIL"}\n` +
                   `- OCR Quality: ${(doc.ocr_quality_score * 100).toFixed(0)}%\n` +
                   (doc.rejection_reason ? `- Alert: ${doc.rejection_reason}` : ""),
          type: "text"
        }
      ]);

      // Unblock or adjust demand notice state
      if (caseDetails.status !== "blocked") {
        setDemandNotice(null);
      } else {
        setDemandNotice(
          `╔══════════════════════════════════════════════════════╗\n` +
          `║         DOCUMENT REQUIREMENT NOTICE                  ║\n` +
          `║         Case: ${selectedDomain} | Employee: ${currentUser?.name || "Member"}     ║\n` +
          `╚══════════════════════════════════════════════════════╝\n\n` +
          `The following documents are missing and required:\n` +
          caseDetails.missing_documents.map((d: string) => `  - ${d} * REQUIRED`).join("\n") +
          `\n\nPlease upload the files using the sidebar to proceed.`
        );
      }
    } catch (err: any) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = ""; // Reset file selector
    }
  };

  // Run assessment check
  const handleCheckEligibility = async () => {
    if (!caseId) return;

    setCheckingEligibility(true);
    try {
      const res = await runEligibilityCheck(caseId);
      setDecisionOutcome(res.decision);
      
      // Append findings to message list
      let outcomeMsg = `⚖️ **Evaluation Verdict: ${res.decision}**\n` +
                       `Status Details: ${res.eligibility_status}\n` +
                       `Confidence rating: ${res.confidence_level}\n\n`;
                       
      if (res.follow_up_questions?.length > 0) {
        outcomeMsg += `**Required Additional Facts:**\n` +
                      res.follow_up_questions.map((q: string) => `- ${q}`).join("\n");
      } else {
        outcomeMsg += `**Administrative Notes:**\n${res.administrative_notes}`;
      }
      
      setMessages(prev => [
        ...prev,
        {
          id: `check-${Date.now()}`,
          role: "assistant",
          content: outcomeMsg,
          type: res.follow_up_questions?.length > 0 ? "followup" : "text",
          rules_cited: res.supporting_rules?.map((r: any) => r.rule_id) || []
        }
      ]);
      
      // Update local case checks
      const caseDetails = await getCaseDetails(caseId);
      setCaseStatus(caseDetails.status);
    } catch (err: any) {
      alert(`Evaluation failed: ${err.message}`);
    } finally {
      setCheckingEligibility(false);
    }
  };

  // Compile PDF Report
  const handleCompileReport = async () => {
    if (!caseId) return;

    setCompilingReport(true);
    try {
      const rep = await generateReport(caseId);
      setReportId(rep.id);
      
      setMessages(prev => [
        ...prev,
        {
          id: `rep-${Date.now()}`,
          role: "assistant",
          content: `📜 **Official Decision Report PDF compiled successfully!**\n` +
                   `You can now download the signed PDF from the sidebar panel.`,
          type: "text"
        }
      ]);
    } catch (err: any) {
      alert(`Report compilation failed: ${err.message}`);
    } finally {
      setCompilingReport(false);
    }
  };

  // Send subsequent message/replies — parses facts and re-evaluates
  const handleSendMessage = async () => {
    if (!chatInput.trim() || !caseId) return;

    const userMsg = chatInput.trim();
    setChatInput("");
    setLoadingMessage(true);

    // Append user message immediately to UI
    setMessages(prev => [
      ...prev,
      {
        id: `usr-${Date.now()}`,
        role: "user",
        content: userMsg,
        type: "text"
      }
    ]);

    try {
      // Call /api/cases/{case_id}/reply — backend parses facts, merges, re-evaluates
      const res = await sendCaseReply(caseId, userMsg);

      let outcomeMsg = `⚖️ **Re-Evaluation Verdict: ${res.decision}**\n` +
                       `Status: ${res.eligibility_status}\n`;

      if (res.confidence_level && res.confidence_level !== "N/A") {
        outcomeMsg += `Confidence: ${res.confidence_level}\n`;
      }

      outcomeMsg += "\n";

      if (res.follow_up_questions?.length > 0) {
        outcomeMsg += `**Still need more information:**\n` +
                      res.follow_up_questions.map((q: string) => `- ${q}`).join("\n");
      } else if (res.administrative_notes) {
        outcomeMsg += `**Administrative Notes:**\n${res.administrative_notes}`;
      }

      if (res.decision === "Eligible" || res.decision === "Not Eligible") {
        setDecisionOutcome(res.decision);
      }

      setMessages(prev => [
        ...prev,
        {
          id: `ast-${Date.now()}`,
          role: "assistant",
          content: outcomeMsg,
          type: res.follow_up_questions?.length > 0 ? "followup" : "text",
          rules_cited: res.supporting_rules?.map((r: any) => r.rule_id) || []
        }
      ]);

      // Refresh case status
      const caseDetails = await getCaseDetails(caseId);
      setCaseStatus(caseDetails.status);
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: `Failed to process reply: ${err.message}`,
          type: "text"
        }
      ]);
    } finally {
      setLoadingMessage(false);
    }
  };


  const handleLogout = () => {
    logout();
    router.push("/");
  };

  if (loadingUser) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-50 font-sans">
      {/* Header Bar */}
      <header className="flex items-center justify-between bg-gradient-to-r from-slate-950 to-slate-800 text-white px-6 py-4 border-b border-slate-900 shadow-md shrink-0">
        <div className="flex items-center gap-3">
          <Award className="w-6.5 h-6.5 text-amber-400" />
          <div>
            <h1 className="text-sm font-bold tracking-wide uppercase">
              Indian Railways Decision Support AI Portal
            </h1>
            <p className="text-[10px] text-slate-400 mt-0.5">
              Logged in as: {currentUser?.name} ({currentUser?.employee_id}) · {currentUser?.department || "General"}
            </p>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg border border-slate-700 text-xs font-semibold hover:bg-white/5 transition-all text-slate-300"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Logout</span>
        </button>
      </header>

      {/* Main Body */}
      <div className="flex-1 flex overflow-hidden w-full">
        {/* Left Side: Document Panel & Case setup */}
        <aside className="w-96 border-r border-slate-200 bg-white p-5 flex flex-col gap-5 overflow-y-auto shrink-0 shadow-sm">
          {!caseCreated ? (
            /* Start Case Form */
            <form onSubmit={handleStartCase} className="space-y-4">
              <div>
                <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-2">
                  Initiate New Case
                </h2>
                <p className="text-xs text-slate-400">
                  Select a rule domain and outline your administrative question.
                </p>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                  Rule Category Domain
                </label>
                <select
                  value={selectedDomain}
                  onChange={e => setSelectedDomain(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2 px-3 text-xs focus:outline-none focus:ring-2 focus:ring-slate-500/20"
                >
                  {CASE_DOMAINS.map(d => (
                    <option key={d.value} value={d.value}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                  Assessment Request Query
                </label>
                <textarea
                  rows={4}
                  required
                  placeholder="e.g. Please evaluate employee promotion to Senior Driver grade post. Completing 6 years of service and passed exam."
                  value={caseQuery}
                  onChange={e => setCaseQuery(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2 px-3 text-xs focus:outline-none focus:ring-2 focus:ring-slate-500/20 resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={loadingMessage}
                className="w-full py-2.5 bg-gradient-to-tr from-slate-800 to-slate-900 hover:from-slate-700 hover:to-slate-800 text-white rounded-xl text-xs font-semibold shadow-md transition-all disabled:opacity-50"
              >
                {loadingMessage ? "Initializing Case..." : "Start Evaluation"}
              </button>
            </form>
          ) : (
            /* Document Upload & Assessment Panel */
            <div className="space-y-5">
              <div>
                <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-2 py-0.5 rounded uppercase tracking-wide">
                  Active Case File
                </span>
                <h3 className="text-xs font-bold text-slate-700 mt-2 truncate">
                  Domain: {selectedDomain}
                </h3>
                <p className="text-[10px] text-slate-400 font-mono mt-1 select-all">
                  ID: {caseId}
                </p>
              </div>

              <hr className="border-slate-100" />

              {/* Upload Panel */}
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                  Evidence Submissions
                </label>
                <button
                  type="button"
                  onClick={() => fileRef.current?.click()}
                  disabled={uploading}
                  className="w-full flex flex-col items-center justify-center py-5 px-4 border-2 border-dashed border-slate-200 rounded-xl hover:border-slate-400 hover:bg-slate-50 transition-all text-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  <UploadCloud className="w-6 h-6 text-slate-400" />
                  <span className="text-xs font-medium text-slate-600">
                    {uploading ? "Uploading Document..." : "Add Scanned Document"}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    PDF, JPG, PNG (Max 20MB)
                  </span>
                </button>
                <input
                  ref={fileRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={handleUploadFile}
                  className="hidden"
                />
              </div>

              {/* Document Checklists Status Tracker */}
              <DocumentStatusTracker
                submitted={submittedDocs}
                missing={missingDocs}
              />

              <hr className="border-slate-100" />

              {/* Actions Card */}
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
                <p className="text-xs font-bold text-slate-500 uppercase tracking-wide border-b pb-2">
                  Evaluation Controls
                </p>
                
                <button
                  type="button"
                  onClick={handleCheckEligibility}
                  disabled={checkingEligibility || uploading}
                  className="w-full flex items-center justify-center gap-1.5 py-2 bg-navy text-white hover:bg-navy-light rounded-lg text-xs font-semibold shadow-sm transition-all disabled:opacity-40"
                  style={{ backgroundColor: "#1A365D" }}
                >
                  <CheckSquare className="w-4 h-4" />
                  <span>Verify Rules Eligibility</span>
                </button>

                {decisionOutcome && (
                  <button
                    type="button"
                    onClick={handleCompileReport}
                    disabled={compilingReport}
                    className="w-full flex items-center justify-center gap-1.5 py-2 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold shadow-sm transition-all"
                  >
                    <FileCheck className="w-4 h-4 text-emerald-500" />
                    <span>{compilingReport ? "Compiling..." : "Generate PDF Report"}</span>
                  </button>
                )}

                {reportId && (
                  <a
                    href={getReportDownloadUrl(reportId)}
                    download={`decision_report_${caseId}.pdf`}
                    className="w-full flex items-center justify-center gap-1.5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm text-center transition-all animate-bounce mt-2"
                  >
                    <FileText className="w-4 h-4" />
                    <span>Download Official PDF Report</span>
                  </a>
                )}
              </div>
            </div>
          )}
        </aside>

        {/* Right Side: Chat Window */}
        <main className="flex-1 flex flex-col overflow-hidden bg-slate-50">
          {/* Document Demand warning notice box */}
          {demandNotice && (
            <DocumentDemandNotice notice={demandNotice} />
          )}

          {/* Messages Scroll Grid */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto text-slate-400 gap-3">
                <div className="p-4 rounded-3xl bg-white border border-slate-200 shadow-sm text-slate-500">
                  <Award className="w-8 h-8 text-amber-500 mx-auto" />
                </div>
                <h3 className="text-base font-bold text-slate-700 mt-2">
                  Administrative Decision Assistant
                </h3>
                <p className="text-xs leading-relaxed text-slate-400">
                  Welcome to the Railway Administrative Assessment panel. Select a category in the sidebar to initialize a case file, upload employee evidence, and evaluate eligibility based on the official guidelines.
                </p>
              </div>
            )}
            
            {messages.map(msg => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {loadingMessage && (
              <div className="flex items-center gap-1.5 text-slate-400 text-xs pl-12">
                <div className="animate-bounce h-2 w-2 bg-slate-400 rounded-full"></div>
                <div className="animate-bounce h-2 w-2 bg-slate-400 rounded-full [animation-delay:0.2s]"></div>
                <div className="animate-bounce h-2 w-2 bg-slate-400 rounded-full [animation-delay:0.4s]"></div>
                <span className="text-[11px] ml-1">Analyzing rules manual...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Footer Input Bar */}
          <footer className="bg-white border-t border-slate-200 p-4 shrink-0 shadow-inner">
            <div className="flex gap-2 max-w-4xl mx-auto w-full items-center">
              <input
                disabled={!caseCreated || loadingMessage}
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && !e.shiftKey && handleSendMessage()}
                placeholder={
                  caseCreated 
                    ? "Respond with facts or clarify evaluation check..." 
                    : "To start, select a domain and initiate case details..."
                }
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-slate-500/20 disabled:opacity-50"
              />
              <button
                onClick={handleSendMessage}
                disabled={!caseCreated || loadingMessage || !chatInput.trim()}
                className="p-2.5 rounded-xl text-white hover:bg-slate-800 disabled:opacity-50 transition-all shrink-0 shadow-sm"
                style={{ backgroundColor: "#1A365D" }}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}
