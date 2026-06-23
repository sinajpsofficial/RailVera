import React from "react";
import { AlertOctagon } from "lucide-react";

interface Props {
  notice: string;
}

export default function DocumentDemandNotice({ notice }: Props) {
  return (
    <div className="mx-6 mt-4 border border-rose-200 rounded-xl bg-rose-50/60 p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-3 text-rose-700">
        <AlertOctagon className="w-5 h-5 shrink-0" />
        <span className="font-bold text-sm tracking-wide uppercase">
          Document Requirement Notice — Case Evaluation Blocked
        </span>
      </div>
      <pre className="text-[11px] text-rose-900 whitespace-pre-wrap font-mono bg-white/80 border border-rose-100 rounded-lg p-3 leading-relaxed overflow-x-auto shadow-inner">
        {notice}
      </pre>
    </div>
  );
}
