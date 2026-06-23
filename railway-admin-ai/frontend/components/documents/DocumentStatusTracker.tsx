import React from "react";
import { CheckCircle2, AlertCircle, FileText } from "lucide-react";

interface Props {
  submitted: string[];
  missing: string[];
}

export default function DocumentStatusTracker({ submitted, missing }: Props) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
      <div className="flex items-center justify-between border-b border-slate-200 pb-2">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">
          Document Checklist
        </span>
        <span className="text-xs text-slate-400">
          {submitted.length} submitted
        </span>
      </div>

      <div className="space-y-2">
        {submitted.map(doc => (
          <div
            key={doc}
            className="flex items-center gap-2.5 text-sm text-emerald-800 bg-emerald-50/70 border border-emerald-100 rounded-lg px-3 py-2.5"
          >
            <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
            <span className="font-medium truncate">{doc}</span>
            <span className="text-[10px] bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded ml-auto shrink-0">
              Verified
            </span>
          </div>
        ))}

        {missing.map(doc => (
          <div
            key={doc}
            className="flex items-center gap-2.5 text-sm text-rose-800 bg-rose-50/70 border border-rose-100 rounded-lg px-3 py-2.5"
          >
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 animate-pulse" />
            <span className="font-medium truncate">{doc}</span>
            <span className="text-[10px] bg-rose-100 text-rose-800 font-semibold px-2 py-0.5 rounded ml-auto shrink-0">
              Required
            </span>
          </div>
        ))}

        {submitted.length === 0 && missing.length === 0 && (
          <div className="flex flex-col items-center justify-center py-6 text-center text-slate-400">
            <FileText className="w-8 h-8 stroke-[1.5] mb-2 text-slate-300" />
            <p className="text-xs">No documents required yet.</p>
            <p className="text-[10px] text-slate-400 mt-1">Start a case to see document demands.</p>
          </div>
        )}
      </div>
    </div>
  );
}
