import React from "react";
import { User } from "lucide-react";
import iconPng from "@/app/icon.png";

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

/**
 * Renders a subset of markdown into React elements without any library.
 * Handles: **bold**, *italic*, `code`, numbered lists, bullet lists, headings, line breaks.
 */
function renderMarkdown(text: string): React.ReactNode {
  // Split into lines to handle block-level elements
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Heading 1-3
    const h3Match = line.match(/^###\s+(.*)/);
    const h2Match = line.match(/^##\s+(.*)/);
    const h1Match = line.match(/^#\s+(.*)/);
    if (h1Match || h2Match || h3Match) {
      const match = h1Match || h2Match || h3Match;
      const level = h1Match ? 1 : h2Match ? 2 : 3;
      const cls = level === 1
        ? "text-sm font-bold text-slate-800 mt-2 mb-1"
        : level === 2
        ? "text-xs font-bold text-slate-700 mt-2 mb-0.5"
        : "text-xs font-semibold text-slate-700 mt-1";
      elements.push(
        <p key={i} className={cls}>{renderInline(match![1])}</p>
      );
      i++;
      continue;
    }

    // Horizontal rule
    if (/^---+$/.test(line.trim())) {
      elements.push(<hr key={i} className="border-slate-200 my-2" />);
      i++;
      continue;
    }

    // Bullet list item
    if (/^[\-\*]\s+/.test(line)) {
      const listItems: React.ReactNode[] = [];
      while (i < lines.length && /^[\-\*]\s+/.test(lines[i])) {
        listItems.push(
          <li key={i} className="flex gap-1.5 items-start">
            <span className="text-slate-400 shrink-0 mt-0.5">•</span>
            <span>{renderInline(lines[i].replace(/^[\-\*]\s+/, ""))}</span>
          </li>
        );
        i++;
      }
      elements.push(
        <ul key={`ul-${i}`} className="space-y-0.5 my-1">
          {listItems}
        </ul>
      );
      continue;
    }

    // Numbered list item
    if (/^\d+\.\s+/.test(line)) {
      const listItems: React.ReactNode[] = [];
      let num = 1;
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        listItems.push(
          <li key={i} className="flex gap-1.5 items-start">
            <span className="text-slate-500 font-mono text-[11px] shrink-0 mt-0.5 w-4">{num}.</span>
            <span>{renderInline(lines[i].replace(/^\d+\.\s+/, ""))}</span>
          </li>
        );
        i++;
        num++;
      }
      elements.push(
        <ol key={`ol-${i}`} className="space-y-0.5 my-1">
          {listItems}
        </ol>
      );
      continue;
    }

    // Empty line → vertical spacer
    if (line.trim() === "") {
      if (elements.length > 0) {
        elements.push(<div key={i} className="h-1.5" />);
      }
      i++;
      continue;
    }

    // Normal paragraph
    elements.push(
      <p key={i} className="leading-relaxed">
        {renderInline(line)}
      </p>
    );
    i++;
  }

  return <>{elements}</>;
}

/**
 * Renders inline markdown: **bold**, *italic*, `code`, and plain text.
 */
function renderInline(text: string): React.ReactNode {
  // Pattern: **bold**, *italic*, `code`
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={idx} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={idx} className="italic text-slate-700">{part.slice(1, -1)}</em>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={idx} className="bg-slate-100 text-slate-700 rounded px-1 py-0.5 text-[11px] font-mono">
          {part.slice(1, -1)}
        </code>
      );
    }
    return <span key={idx}>{part}</span>;
  });
}


function RuleBadge({ ruleId }: { ruleId: string }) {
  const [ruleData, setRuleData] = React.useState<any>(null);
  const [isHovered, setIsHovered] = React.useState(false);

  React.useEffect(() => {
    import('@/lib/api').then(({ getRule }) => {
      getRule(ruleId)
        .then((data) => {
          if (data && data.description) {
            setRuleData(data);
          }
        })
        .catch(() => {});
    });
  }, [ruleId]);

  return (
    <div 
      className="relative flex items-center"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <span
        className="text-[10px] font-bold bg-slate-100 border border-slate-200 text-slate-700 px-2 py-0.5 rounded-md hover:bg-slate-200 hover:border-slate-300 transition-colors cursor-help"
      >
        {ruleId}
      </span>
      
      {isHovered && ruleData && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 z-50 animate-fade-in shadow-xl">
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden flex flex-col">
            <div className="bg-slate-50 border-b border-slate-100 px-3 py-2">
              <p className="text-xs font-bold text-slate-800 break-words">{ruleData.rule_name || ruleId}</p>
              <p className="text-[9px] font-medium text-slate-400 uppercase tracking-wide mt-0.5">{ruleData.domain || "General"} Domain</p>
            </div>
            <div className="px-3 py-2.5 max-h-48 overflow-y-auto custom-scrollbar">
              <p className="text-[11px] text-slate-600 leading-relaxed whitespace-pre-wrap font-sans">
                {ruleData.description}
              </p>
            </div>
          </div>
          {/* Tooltip Arrow */}
          <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-white border-b border-r border-slate-200 transform rotate-45"></div>
        </div>
      )}
    </div>
  );
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 max-w-[88%] ${isUser ? "ml-auto flex-row-reverse" : "mr-auto"}`}>
      {/* Avatar Icon */}
      <div
        className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-xs font-semibold ${
          isUser
            ? "bg-slate-200 text-slate-700"
            : "bg-navy text-white"
        }`}
        style={!isUser ? { backgroundColor: "#1A365D" } : {}}
      >
        {isUser ? <User className="w-4 h-4" /> : <img src={iconPng.src} className="w-5 h-5 object-contain" alt="RailVera AI" />}
      </div>

      {/* Bubble Body */}
      <div className="space-y-1.5 min-w-0 flex-1">
        <div
          className={`rounded-2xl px-4 py-3 text-sm shadow-sm ${
            isUser
              ? "bg-gradient-to-tr from-slate-700 to-slate-800 text-white rounded-tr-none"
              : "bg-white border border-slate-200 text-slate-800 rounded-tl-none"
          }`}
        >
          {/* Rendered message content */}
          <div className={`font-sans text-sm leading-relaxed ${isUser ? "text-white" : "text-slate-800"}`}>
            {isUser
              ? message.content // user messages are plain text, no need to render
              : renderMarkdown(message.content)
            }
          </div>

          {/* Cited Rules inside Bubble */}
          {!isUser && message.rules_cited && message.rules_cited.length > 0 && (
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap items-center gap-1.5">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider shrink-0 mr-1">
                Applied Rules:
              </span>
              {message.rules_cited.map(rule => (
                <RuleBadge key={rule} ruleId={rule} />
              ))}
            </div>
          )}
        </div>

        {/* Sender label */}
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
