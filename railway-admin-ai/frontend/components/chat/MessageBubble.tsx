import React from "react";
import { User, ShieldAlert, Award } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  type: "text" | "demand_notice" | "followup";
  rules_cited?: string[];
}

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 max-w-[85%] ${isUser ? "ml-auto flex-row-reverse" : "mr-auto"}`}>
      {/* Avatar Icon */}
      <div
        className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-xs font-semibold ${
          isUser
            ? "bg-slate-200 text-slate-700"
            : "bg-navy text-white"
        }`}
        style={!isUser ? { backgroundColor: "#1A365D" } : {}}
      >
        {isUser ? <User className="w-4 h-4" /> : <Award className="w-4 h-4 text-amber-400" />}
      </div>

      {/* Bubble Body */}
      <div className="space-y-1.5">
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
            isUser
              ? "bg-gradient-to-tr from-slate-700 to-slate-800 text-white rounded-tr-none"
              : "bg-white border border-slate-200 text-slate-800 rounded-tl-none"
          }`}
        >
          <div className="whitespace-pre-wrap font-sans">
            {message.content}
          </div>

          {/* Renders Cited Rules inside Bubble */}
          {!isUser && message.rules_cited && message.rules_cited.length > 0 && (
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap items-center gap-1.5">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider shrink-0 mr-1">
                Applied Authority:
              </span>
              {message.rules_cited.map(rule => (
                <span
                  key={rule}
                  className="text-[10px] font-bold bg-slate-100 border border-slate-200 text-navy-dark px-2 py-0.5 rounded-md hover:bg-navy/5 transition-colors"
                >
                  {rule}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Sender and Time metadata */}
        <div
          className={`text-[10px] text-slate-400 px-1 font-medium ${
            isUser ? "text-right" : "text-left"
          }`}
        >
          {isUser ? "Employee" : "Personnel AI Officer"}
        </div>
      </div>
    </div>
  );
}
