"use client";
import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { getMe, createCase, getCaseDetails, uploadDocument, getDocumentStatus, runEligibilityCheck, generateReport, getReportDownloadUrl, logout, sendCaseReply, getMyCases, getPendingCases, getCaseConversation, reviewCase } from "@/lib/api";

import DocumentStatusTracker from "@/components/documents/DocumentStatusTracker";
import DocumentDemandNotice from "@/components/chat/DocumentDemandNotice";
import MessageBubble from "@/components/chat/MessageBubble";
import { LogOut, UploadCloud, AlertCircle, FileCheck, CheckSquare, FileText, Send, HelpCircle } from "lucide-react";
import iconPng from "@/app/icon.png";

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
  const [progressPercentage, setProgressPercentage] = useState(0);
  const [decisionOutcome, setDecisionOutcome] = useState<string | null>(null);
  const [compilingReport, setCompilingReport] = useState(false);
  const [reportId, setReportId] = useState<string | null>(null);

  // Cases lists & Review states
  const [myCases, setMyCases] = useState<any[]>([]);
  const [pendingCases, setPendingCases] = useState<any[]>([]);
  const [reviewStatus, setReviewStatus] = useState<string>("draft");
  const [reviewNotes, setReviewNotes] = useState<string | null>(null);
  const [reviewNotesInput, setReviewNotesInput] = useState<string>("");
  const [submittingReview, setSubmittingReview] = useState<boolean>(false);

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

  // Refresh user and pending cases queues
  const refreshCaseLists = async () => {
    try {
      const myRes = await getMyCases();
      setMyCases(myRes);
      // Only admins fetch pending reviews queue
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      if (token) {
        // Fetch current user details if not yet fetched to check role
        let role = currentUser?.role;
        if (!role) {
          try {
            const me = await getMe();
            role = me.role;
          } catch {}
        }
        if (role === "admin") {
          const pendRes = await getPendingCases();
          setPendingCases(pendRes);
        }
      }
    } catch (err) {
      console.error("Failed to refresh case lists:", err);
    }
  };

  // Load user's case lists on user load
  useEffect(() => {
    if (currentUser) {
      refreshCaseLists();
    }
  }, [currentUser]);

  // Load a case and its conversation history into the main view
  const handleLoadCase = async (id: string) => {
    setLoadingMessage(true);
    try {
      const details = await getCaseDetails(id);
      setCaseId(details.id);
      setSelectedDomain(details.domain);
      setCaseStatus(details.status);
      setReviewStatus(details.review_status);
      setReviewNotes(details.review_notes);
      setSubmittedDocs(details.submitted_documents || []);
      setMissingDocs(details.missing_documents || []);
      setDecisionOutcome(details.decision);
      setReportId(null); // Reset report since it's a new loaded case
      
      // Get conversation history
      const history = await getCaseConversation(id);
      const formattedHistory: Message[] = history.map((h: any) => ({
        id: h.id,
        role: h.role,
        content: h.message,
        type: h.message_type === "followup" ? "followup" : "text",
        rules_cited: h.rules_cited || []
      }));
      setMessages(formattedHistory);

      if (details.status === "blocked" && details.missing_documents?.length > 0) {
        setDemandNotice(
          `╔══════════════════════════════════════════════════════╗\n` +
          `║         DOCUMENT REQUIREMENT NOTICE                  ║\n` +
          `║         Case: ${details.domain} | Employee ID: ${details.user_id}     ║\n` +
          `╚══════════════════════════════════════════════════════╝\n\n` +
          `The following documents are missing and required:\n` +
          details.missing_documents.map((d: string) => `  - ${d} * REQUIRED`).join("\n") +
          `\n\nPlease upload the files using the sidebar to proceed.`
        );
      } else {
        setDemandNotice(null);
      }
      setCaseCreated(true);
    } catch (err: any) {
      alert(`Failed to load case: ${err.message}`);
    } finally {
      setLoadingMessage(false);
    }
  };

  // Submit human-in-the-loop approval or rejection
  const handleReviewCase = async (action: "approve" | "reject") => {
    if (!caseId) return;
    if (!reviewNotesInput.trim() || reviewNotesInput.trim().length < 10) {
      alert("Please provide at least 10 characters of justification/notes for the review decision.");
      return;
    }
    setSubmittingReview(true);
    try {
      const res = await reviewCase(caseId, action, reviewNotesInput.trim());
      setReviewStatus(res.review_status);
      setReviewNotes(res.review_notes);
      setReviewNotesInput("");

      // Update local case state
      const details = await getCaseDetails(caseId);
      setCaseStatus(details.status);

      // Append official review statement message in conversation UI
      setMessages(prev => [
        ...prev,
        {
          id: `review-${Date.now()}`,
          role: "assistant",
          content: `Case Decision Recorded\n\nThis case has been ${action === "approve" ? "approved" : "rejected"} by Personnel Officer ${currentUser?.name}.\n\nOfficer notes: ${res.review_notes}`,
          type: "text"
        }
      ]);

      await refreshCaseLists();
    } catch (err: any) {
      alert(`Failed to submit review: ${err.message}`);
    } finally {
      setSubmittingReview(false);
    }
  };


  const handleBackToCases = () => {
    setCaseId(null);
    setCaseCreated(false);
    setMessages([]);
    setDemandNotice(null);
    setDecisionOutcome(null);
    setReportId(null);
    setChatInput("");
    refreshCaseLists();
  };


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
          content: caseQuery.trim(),
          type: "text"
        },
        {
          id: `ast-${Date.now()}`,
          role: "assistant",
          content: `Your case has been registered successfully.\n\nCase ID: ${dbCase.id}\nDomain: ${selectedDomain}\n\nRequired documents for this case: ${dbCase.required_documents.join(", ")}.\n` +
                   (dbCase.status === "blocked"
                     ? "Please upload the missing documents using the sidebar so we can proceed with the evaluation."
                     : "All required documents are accounted for. You can run the eligibility evaluation now."),
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
      setReviewStatus(dbCase.review_status || "draft");
      setReviewNotes(dbCase.review_notes || null);
      await refreshCaseLists();
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

      // Add status message to chat
      setMessages(prev => [
        ...prev,
        {
          id: `upload-${Date.now()}`,
          role: "assistant",
          content: `Document received: "${doc.original_filename}"\n\nThe file has been saved and is being processed in the background (OCR and classification). The document checklist in the sidebar will update automatically once processing is complete.` +
                   (doc.rejection_reason ? `\n\nNote: ${doc.rejection_reason}` : ""),
          type: "text"
        }
      ]);

      // Fetch the initial full case (normally pending/processing at this point)
      const caseDetails = await getCaseDetails(caseId);
      setCaseStatus(caseDetails.status);
      setSubmittedDocs(caseDetails.submitted_documents || []);
      setMissingDocs(caseDetails.missing_documents || []);

      // Update demand notice based on refreshed case state
      if (caseDetails.status !== "blocked") {
        setDemandNotice(null);
      } else {
        setDemandNotice(
          `DOCUMENT REQUIREMENT NOTICE\n` +
          `Case: ${selectedDomain} | Employee: ${currentUser?.name || "Member"}\n\n` +
          `The following documents are still required:\n` +
          (caseDetails.missing_documents || []).map((d: string) => `  - ${d}`).join("\n") +
          `\n\nPlease upload the files using the sidebar to continue.`
        );
      }
      setReviewStatus(caseDetails.review_status || "draft");
      setReviewNotes(caseDetails.review_notes || null);
      await refreshCaseLists();

      // Start polling the document status in the background
      const pollDocStatus = async (docId: string, filename: string) => {
        let attempts = 0;
        const maxAttempts = 30; // 45 seconds max
        const interval = 1500; // 1.5 seconds

        const checkStatus = async () => {
          try {
            const statusRes = await getDocumentStatus(docId);
            const status = statusRes.processing_status;

            if (status === "done") {
              // Refresh case details once processing is finished
              const refreshedCase = await getCaseDetails(caseId);
              setCaseStatus(refreshedCase.status);
              setSubmittedDocs(refreshedCase.submitted_documents || []);
              setMissingDocs(refreshedCase.missing_documents || []);

              // Update demand notice based on refreshed case state
              if (refreshedCase.status !== "blocked") {
                setDemandNotice(null);
              } else {
                setDemandNotice(
                  `DOCUMENT REQUIREMENT NOTICE\n` +
                  `Case: ${refreshedCase.domain} | Employee: ${currentUser?.name || "Member"}\n\n` +
                  `The following documents are still required:\n` +
                  (refreshedCase.missing_documents || []).map((d: string) => `  - ${d}`).join("\n") +
                  `\n\nPlease upload the files using the sidebar to continue.`
                );
              }
              setReviewStatus(refreshedCase.review_status || "draft");
              setReviewNotes(refreshedCase.review_notes || null);
              await refreshCaseLists();

              // Add a processing complete message to chat
              const isVerified = statusRes.is_verified;
              const docType = statusRes.document_type;
              
              if (docType === "Unknown" || !isVerified) {
                let warningMsg = `⚠️ Unrecognized document: "${filename}" was processed but could not be verified as any required type.\n\n`;
                if (statusRes.rejection_reason) {
                  warningMsg += `Reason: ${statusRes.rejection_reason}\n\n`;
                }
                warningMsg += `Please ensure the document contains clear text and matches one of the required categories.`;
                
                setMessages(prev => [
                  ...prev,
                  {
                    id: `verify-fail-${Date.now()}`,
                    role: "assistant",
                    content: warningMsg,
                    type: "text"
                  }
                ]);
              } else {
                setMessages(prev => [
                  ...prev,
                  {
                    id: `verify-success-${Date.now()}`,
                    role: "assistant",
                    content: `✅ Document "${filename}" verified successfully as: **${docType}**. Checklist updated!`,
                    type: "text"
                  }
                ]);
              }

            } else if (status === "failed") {
              setMessages(prev => [
                ...prev,
                {
                  id: `verify-error-${Date.now()}`,
                  role: "assistant",
                  content: `❌ Processing failed for document "${filename}". Error: ${statusRes.processing_error || "Unknown processing error"}`,
                  type: "text"
                }
              ]);
            } else {
              // Still pending or processing, schedule next poll
              attempts++;
              if (attempts < maxAttempts) {
                setTimeout(checkStatus, interval);
              } else {
                setMessages(prev => [
                  ...prev,
                  {
                    id: `verify-timeout-${Date.now()}`,
                    role: "assistant",
                    content: `⏳ Processing timed out for document "${filename}". Please try again or refresh the page later.`,
                    type: "text"
                  }
                ]);
              }
            }
          } catch (error) {
            console.error("Error polling document status:", error);
            attempts++;
            if (attempts < maxAttempts) {
              setTimeout(checkStatus, interval);
            }
          }
        };

        setTimeout(checkStatus, interval);
      };

      pollDocStatus(doc.id, file.name);

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
    setProgressPercentage(0);

    // Start simulated progress
    const intervalTime = 100; // ms
    let currentProgress = 0;
    
    const timer = setInterval(() => {
      currentProgress += Math.floor(Math.random() * 8) + 3; // Increments by 3-10%
      if (currentProgress > 95) {
        currentProgress = 95; // cap until response returns
        clearInterval(timer);
      }
      setProgressPercentage(currentProgress);
    }, intervalTime);

    try {
      const res = await runEligibilityCheck(caseId);
      
      // Stop the timer and complete the progress
      clearInterval(timer);
      setProgressPercentage(100);
      
      // Brief delay for the user to see 100% complete
      await new Promise(resolve => setTimeout(resolve, 500));

      setDecisionOutcome(res.decision);
      
      // Append findings to message list
      let outcomeMsg = `Evaluation complete.\n\nVerdict: ${res.decision}\nStatus: ${res.eligibility_status}\nConfidence: ${res.confidence_level}\n\n`;
                       
      if (res.follow_up_questions?.length > 0) {
        outcomeMsg += `To complete this evaluation, I need a few more details from you:\n` +
                      res.follow_up_questions.map((q: string, idx: number) => `${idx + 1}. ${q}`).join("\n");
      } else {
        outcomeMsg += res.administrative_notes;
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
      setReviewStatus(caseDetails.review_status || "draft");
      setReviewNotes(caseDetails.review_notes || null);
      await refreshCaseLists();
    } catch (err: any) {
      clearInterval(timer);
      setProgressPercentage(0);
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
          content: `Your official decision report has been compiled and is ready to download.\n\nUse the button in the sidebar panel to save a signed copy of the PDF.`,
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

      let outcomeMsg = `Re-evaluation complete.\n\nVerdict: ${res.decision}\nStatus: ${res.eligibility_status}\n`;

      if (res.confidence_level && res.confidence_level !== "N/A") {
        outcomeMsg += `Confidence: ${res.confidence_level}\n`;
      }

      outcomeMsg += "\n";

      if (res.follow_up_questions?.length > 0) {
        outcomeMsg += `I still need some more information to make a definitive assessment:\n` +
                      res.follow_up_questions.map((q: string, idx: number) => `${idx + 1}. ${q}`).join("\n");
      } else if (res.administrative_notes) {
        outcomeMsg += res.administrative_notes;
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
      setReviewStatus(caseDetails.review_status || "draft");
      setReviewNotes(caseDetails.review_notes || null);
      await refreshCaseLists();
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
          <img src={iconPng.src} className="w-6.5 h-6.5 object-contain" alt="RailVera Logo" />
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
            <div className="space-y-5 flex flex-col h-full overflow-hidden">
              {/* Start Case Form */}
              <form onSubmit={handleStartCase} className="space-y-4 shrink-0">
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

              <hr className="border-slate-100 shrink-0" />

              {/* Case Lists Area */}
              <div className="flex-1 flex flex-col overflow-hidden min-h-[250px]">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 shrink-0">
                  {currentUser?.role === "admin" ? "Personnel Officer Review Queue" : "My Assessment Case History"}
                </h3>

                {currentUser?.role === "admin" ? (
                  <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                    {pendingCases.length === 0 ? (
                      <div className="p-4 border border-dashed border-slate-200 rounded-xl text-center">
                        <p className="text-[11px] text-slate-400 italic">No cases currently awaiting administrative review.</p>
                      </div>
                    ) : (
                      pendingCases.map(c => (
                        <button
                          key={c.id}
                          onClick={() => handleLoadCase(c.id)}
                          className="w-full text-left p-3 rounded-xl border border-amber-200 bg-amber-50/15 hover:bg-amber-50/30 transition-all flex flex-col gap-1.5 shadow-sm"
                        >
                          <div className="flex justify-between items-center gap-2">
                            <span className="text-xs font-bold text-slate-800 truncate">{c.domain}</span>
                            <span className="text-[9px] font-bold bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded uppercase tracking-wide shrink-0">Review Pending</span>
                          </div>
                          <p className="text-[10px] text-slate-500 line-clamp-1 italic">{c.query_text}</p>
                          <div className="flex justify-between items-center text-[9px] text-slate-400 font-mono mt-1">
                            <span>ID: {c.id.substring(0, 8)}...</span>
                            <span>{new Date(c.created_at).toLocaleDateString()}</span>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                ) : (
                  <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                    {myCases.length === 0 ? (
                      <div className="p-4 border border-dashed border-slate-200 rounded-xl text-center">
                        <p className="text-[11px] text-slate-400 italic">No historical case files found.</p>
                      </div>
                    ) : (
                      myCases.map(c => (
                        <button
                          key={c.id}
                          onClick={() => handleLoadCase(c.id)}
                          className="w-full text-left p-3 rounded-xl border border-slate-200 bg-slate-50/30 hover:bg-slate-50/60 transition-all flex flex-col gap-1.5 shadow-sm"
                        >
                          <div className="flex justify-between items-center gap-2">
                            <span className="text-xs font-bold text-slate-800 truncate">{c.domain}</span>
                            <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wide shrink-0 ${
                              c.review_status === "approved" ? "bg-emerald-100 text-emerald-800" :
                              c.review_status === "rejected" ? "bg-rose-100 text-rose-800" :
                              c.review_status === "pending_review" ? "bg-amber-100 text-amber-800" :
                              "bg-slate-200 text-slate-700"
                            }`}>
                              {c.review_status === "approved" ? "Approved" :
                               c.review_status === "rejected" ? "Rejected" :
                               c.review_status === "pending_review" ? "Pending Approval" :
                               "Draft"}
                            </span>
                          </div>
                          <p className="text-[10px] text-slate-500 line-clamp-1 italic">{c.query_text}</p>
                          <div className="flex justify-between items-center text-[9px] text-slate-400 font-mono mt-1">
                            <span>ID: {c.id.substring(0, 8)}...</span>
                            <span>{new Date(c.created_at).toLocaleDateString()}</span>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Document Upload & Assessment Panel */
            <div className="space-y-5">
              {/* Back button */}
              <button
                onClick={handleBackToCases}
                className="flex items-center gap-1.5 py-1 px-2 border border-slate-200 hover:bg-slate-50 text-slate-500 hover:text-slate-800 rounded-lg text-[10px] font-bold uppercase transition-all shrink-0 shadow-sm"
              >
                <span>← Back to Cases</span>
              </button>

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

                {/* Status Badge */}
                <div className="mt-3">
                  <span className={`text-[10px] font-bold px-2 py-1 rounded-md uppercase tracking-wide border ${
                    reviewStatus === "approved" ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
                    reviewStatus === "rejected" ? "bg-rose-50 text-rose-700 border-rose-200" :
                    reviewStatus === "pending_review" ? "bg-amber-50 text-amber-700 border-amber-200 animate-pulse" :
                    "bg-slate-50 text-slate-600 border-slate-200"
                  }`}>
                    {reviewStatus === "approved" ? "Approved by Officer" :
                     reviewStatus === "rejected" ? "Rejected by Officer" :
                     reviewStatus === "pending_review" ? "Awaiting Review" :
                     "Draft / Evaluating"}
                  </span>
                </div>

                {reviewNotes && (
                  <div className="mt-3 text-[10px] text-slate-600 bg-slate-50 border border-slate-150 p-2.5 rounded-lg">
                    <p className="font-bold text-slate-500 uppercase tracking-wide text-[9px] mb-1">Officer Notes:</p>
                    <p className="italic">"{reviewNotes}"</p>
                  </div>
                )}
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
                  className="w-full flex flex-col items-center justify-center gap-1 py-2 bg-navy text-white hover:bg-navy-light rounded-lg text-xs font-semibold shadow-sm transition-all disabled:opacity-40 relative overflow-hidden"
                  style={{ backgroundColor: "#1A365D" }}
                >
                  {/* Background progress bar */}
                  {checkingEligibility && (
                    <div 
                      className="absolute left-0 top-0 bottom-0 bg-white/15 transition-all duration-300 ease-out pointer-events-none"
                      style={{ width: `${progressPercentage}%` }}
                    />
                  )}
                  <div className="flex items-center gap-1.5 z-10">
                    {checkingEligibility ? (
                      <span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white"></span>
                    ) : (
                      <CheckSquare className="w-4 h-4" />
                    )}
                    <span>
                      {checkingEligibility 
                        ? `Verifying... ${progressPercentage}%` 
                        : "Verify Rules Eligibility"
                      }
                    </span>
                  </div>
                </button>

                {/* Personnel Officer HITL Decision Approval Form */}
                {reviewStatus === "pending_review" && currentUser?.role === "admin" && (
                  <div className="border border-amber-200 bg-amber-50/20 rounded-lg p-3 space-y-2 mt-3">
                    <p className="text-[10px] font-bold text-amber-800 uppercase tracking-wider">
                      Personnel Officer Assessment
                    </p>
                    <p className="text-[9px] text-slate-500 leading-tight">
                      Acknowledge correctness and provide mandatory justification notes to sign.
                    </p>
                    <textarea
                      rows={3}
                      value={reviewNotesInput}
                      onChange={e => setReviewNotesInput(e.target.value)}
                      placeholder="Write review justification (minimum 10 characters)..."
                      className="w-full bg-white border border-slate-200 rounded p-2 text-xs focus:outline-none focus:ring-1 focus:ring-amber-500 resize-none"
                    />
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => handleReviewCase("approve")}
                        disabled={submittingReview}
                        className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-semibold transition-all shadow-sm"
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        onClick={() => handleReviewCase("reject")}
                        disabled={submittingReview}
                        className="flex-1 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded text-[11px] font-semibold transition-all shadow-sm"
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                )}

                {/* Awaiting signature notification for regular employees */}
                {reviewStatus === "pending_review" && currentUser?.role !== "admin" && (
                  <div className="w-full p-3 bg-amber-50 border border-amber-200 text-amber-800 text-center rounded-lg text-xs font-semibold">
                    ⏳ Case Decision Pending review by Personnel Officer.
                  </div>
                )}

                {/* PDF generation restricted to approved cases (Bypassed) */}
                {decisionOutcome && !reportId && (
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
                  <img src={iconPng.src} className="w-8 h-8 object-contain mx-auto" alt="RailVera Logo" />
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
