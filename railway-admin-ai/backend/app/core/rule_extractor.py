"""
rule_extractor.py  — v4 (precise chapter-title mapping, broader paragraph splitting, and expanded field extractors)
"""

import re
from pathlib import Path
from collections import Counter
from typing import List, Dict, Optional


class RuleExtractor:
    """
    Reads rules.md (Indian Railway Establishment Manual, UTF-16 encoded)
    and converts each numbered rule paragraph into a structured dictionary.
    """

    def __init__(self):
        self._counters: Dict[str, int] = {}

    # ── Public entry point ─────────────────────────────────────────────────────

    def extract_rules(self, rules_md_path: str) -> List[Dict]:
        text = self._read_file(rules_md_path)
        sections = self._split_into_sections(text)
        rules = []
        for section_text, chapter_name in sections:
            rule = self._parse_section(section_text, chapter_name)
            if rule:
                rules.append(rule)
        return rules

    # ── File reading ───────────────────────────────────────────────────────────

    def _read_file(self, path: str) -> str:
        raw = Path(path).read_bytes()
        if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
            return raw.decode('utf-16')
        try:
            return raw.decode('utf-8')
        except UnicodeDecodeError:
            return raw.decode('latin-1', errors='ignore')

    # ── Improved section splitter ──────────────────────────────────────────────

    def _split_into_sections(self, text: str) -> List[tuple]:
        """
        Returns (paragraph_text, chapter_name) tuples.
        """
        lines = text.split('\n')

        # Broader paragraph start patterns to capture all rules
        para_pat = re.compile(
            r'^\d{2,4}(?:-[A-Za-z])?[\.\)\-–]?\s+([A-Z]|\(|\d)',
        )
        rule_pat = re.compile(r'^Rule\s+\d+', re.IGNORECASE)

        chapter_pat = re.compile(
            r'^CHAPTER[\s\-–]+([IVXLCDM\d]+)[:\.\.\-–]?\s*(.*)',
            re.IGNORECASE
        )

        sections = []
        current_chapter = "General"
        current_lines: List[str] = []
        pending_chapter_match = None

        for line in lines:
            stripped = line.strip()

            # Awaiting title from next line
            if pending_chapter_match is not None:
                ch_num, inline_title = pending_chapter_match
                if stripped and not chapter_pat.match(stripped):
                    ch_title = stripped if not inline_title else inline_title
                    current_chapter = f"Chapter {ch_num}: {ch_title[:100]}"
                    pending_chapter_match = None
                    continue
                else:
                    current_chapter = f"Chapter {ch_num}" if not inline_title else f"Chapter {ch_num}: {inline_title}"
                    pending_chapter_match = None

            # Detect chapter heading
            ch_match = chapter_pat.match(stripped)
            if ch_match and len(stripped) < 150:
                if current_lines:
                    block = '\n'.join(current_lines).strip()
                    if block:
                        sections.append((block, current_chapter))
                    current_lines = []
                ch_num = ch_match.group(1)
                inline_title = ch_match.group(2).strip()
                if inline_title:
                    current_chapter = f"Chapter {ch_num}: {inline_title[:100]}"
                else:
                    pending_chapter_match = (ch_num, "")
                continue

            # Detect start of a numbered paragraph
            is_chapter = re.match(r'^CHAPTER[\s\-–]+([IVXLCDM\d]+)', stripped, re.IGNORECASE)
            is_para_start = (para_pat.match(stripped) or rule_pat.match(stripped)) and not is_chapter
            
            if is_para_start and current_lines:
                block = '\n'.join(current_lines).strip()
                if block:
                    sections.append((block, current_chapter))
                current_lines = [line]
                continue

            current_lines.append(line)

        # Flush last block
        if current_lines:
            block = '\n'.join(current_lines).strip()
            if block:
                sections.append((block, current_chapter))

        return sections

    # ── Section parsing ────────────────────────────────────────────────────────

    def _parse_section(self, section: str, chapter: str) -> Optional[Dict]:
        if len(section.strip()) < 50:
            return None

        # Rule language substance filter
        rule_signals = [
            "shall", "must", "eligible", "entitl", "prohibit", "disqualif",
            "required", "sanctioned", "payable", "admissible", "granted",
            "not be", "may be", "leave", "penalty", "increment", "pension",
            "allowance", "transfer", "promotion", "retirement", "lien",
            "appoint", "confirmation", "service", "charge sheet", "dismissal"
        ]
        text_lower = section.lower()
        if not any(sig in text_lower for sig in rule_signals):
            return None

        lines = section.strip().split('\n')
        first_line = lines[0].strip()
        body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else section.strip()

        # Rule name
        rule_name = re.sub(r'^\d[\d\.\-–A-Z]*[\.\)\s]+', '', first_line).strip()
        if len(rule_name) < 3:
            rule_name = first_line[:255]

        # Rule number (section reference)
        num_match = re.match(r'^(\d{2,4}[A-Z]?)', first_line)
        section_ref = num_match.group(1) if num_match else None

        domain = self._detect_domain(section, chapter)
        rule_id = self._generate_rule_id(domain)

        return {
            "rule_id": rule_id,
            "rule_name": rule_name[:255],
            "domain": domain,
            "source": "rules.md",
            "chapter": chapter[:100] if chapter else None,
            "section": section_ref,
            "description": (body or section)[:4000],
            "eligibility_conditions": self._extract_conditions(section),
            "required_documents": self._extract_documents(section),
            "disqualifying_conditions": self._extract_disqualifiers(section),
            "exceptions": self._extract_exceptions(section),
            "decision_logic": self._extract_decision_logic(section),
            "authority": self._extract_authority(section),
            "related_rules": [],
            "raw_text": section[:6000],
        }

    # ── Rule ID ────────────────────────────────────────────────────────────────

    def _generate_rule_id(self, domain: str) -> str:
        DOMAIN_PREFIXES = {
            "Promotion": "PROM", "Leave": "LEAVE", "Increment": "INCR",
            "Discipline": "DISC", "Transfer": "TRNF", "DeptExam": "EXAM",
            "Retirement": "RETR", "Pension": "PENS", "Benefits": "BENF",
            "Service": "SRVC", "Attendance": "ATTN", "General": "GEN",
        }
        prefix = DOMAIN_PREFIXES.get(domain, "GEN")
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return f"{prefix}_{self._counters[prefix]:03d}"

    # ── Domain detection ───────────────────────────────────────────────────────

    def _detect_domain(self, text: str, chapter: str) -> str:
        chapter_lower = chapter.lower()
        title_lower = chapter_lower.split(":", 1)[1].strip() if ":" in chapter_lower else chapter_lower

        # Step 1: Explicit chapter number mapping
        num_match = re.match(r'^chapter\s+([ivxlcdm]+|\d+)', chapter_lower)
        if num_match:
            ch_num = num_match.group(1).upper()
            ch_num_map = {
                "I": "Service", "1": "Service",
                "II": "Promotion", "2": "Promotion",
                "III": "Promotion", "3": "Promotion",
                "IV": "Promotion", "4": "Promotion",
                "V": "Service", "5": "Service",
                "VI": "Increment", "6": "Increment",
                "VII": "Benefits", "7": "Benefits",
                "VIII": "Benefits", "8": "Benefits",
                "IX": "Benefits", "9": "Benefits",
                "X": "Service", "10": "Service",
                "XI": "Benefits", "11": "Benefits",
                "XII": "Service", "12": "Service",
                "XIII": "Service", "13": "Service",
                "XIV": "Service", "14": "Service",
                "XV": "Service", "15": "Service",
                "XVI": "Leave", "16": "Leave",
            }
            if ch_num in ch_num_map:
                return ch_num_map[ch_num]

        # Step 2: Explicit chapter title keywords
        if "holiday" in title_lower or "casual leave" in title_lower or "leave rules" in title_lower:
            return "Leave"
        elif "seniority" in title_lower or "promotion" in title_lower:
            return "Promotion"
        elif "increment" in title_lower or "pay, increment" in title_lower or "pay level" in title_lower or "pay scale" in title_lower:
            return "Increment"
        elif "allowance" in title_lower or "dearness" in title_lower or "running allowance" in title_lower:
            return "Benefits"
        elif "advance" in title_lower:
            return "Benefits"
        elif "pension" in title_lower or "provident fund" in title_lower or "gratuity" in title_lower:
            return "Pension"
        elif "discipline" in title_lower or "penalty" in title_lower or "suspension" in title_lower:
            return "Discipline"
        elif "transfer" in title_lower:
            return "Transfer"
        elif "examination" in title_lower or "departmental exam" in title_lower or "qualifying exam" in title_lower:
            return "DeptExam"
        elif "retirement" in title_lower or "superannuation" in title_lower:
            return "Retirement"
        elif "attendance" in title_lower or "absence" in title_lower:
            return "Attendance"
        elif "arrear" in title_lower or "overpayment" in title_lower:
            return "Service"
        elif "change in name" in title_lower or "change in names" in title_lower:
            return "Service"
        elif "absorption" in title_lower or "disabled" in title_lower or "medically decategorised" in title_lower:
            return "Service"
        elif "forwarding of application" in title_lower or "forwarding of applications" in title_lower:
            return "Service"
        elif "temporary service" in title_lower or "temporary services" in title_lower or "temporary railway servant" in title_lower:
            return "Service"
        elif "recruitment" in title_lower or "training" in title_lower or "confirmation" in title_lower or "re-employment" in title_lower:
            return "Service"
        elif "probationer" in title_lower or "probationary" in title_lower:
            return "Service"

        # Step 3: Keyword frequency in full text (fallback)
        KEYWORD_DOMAIN_MAP = {
            "Promotion": ["promotion", "seniority", "selection grade", "zone of consideration", "promoted", "ldce", "gdce", "upgradation"],
            "Leave": ["earned leave", "half pay leave", "medical leave", "leave without pay", "casual leave", "leave account", "leave balance", "leave encashment", "study leave", "maternity leave", "commuted leave"],
            "Increment": ["annual increment", "increment", "efficiency bar", "withholding of increment", "stagnation"],
            "Discipline": ["penalty", "punishment", "suspension", "charge sheet", "dismissed", "removed", "censure", "major penalty", "minor penalty", "disciplinary action", "inquiry officer"],
            "Transfer": ["transferred", "transfer", "posting", "deputation", "relieve", "joining time", "inter-railway transfer"],
            "DeptExam": ["departmental examination", "qualifying examination", "selection test", "written test"],
            "Retirement": ["retirement", "superannuation", "voluntary retirement", "last pay certificate", "no dues"],
            "Pension": ["pension", "gratuity", "commutation", "family pension", "provident fund", "death gratuity"],
            "Benefits": ["allowance", "dearness allowance", "house rent allowance", "travelling allowance", "subsistence allowance", "running allowance", "compensatory allowance"],
            "Service": ["appointment", "probation", "confirmation", "seniority list", "direct recruit", "service conditions", "service record"],
            "Attendance": ["unauthorized absence", "absence", "overstay", "leave without permission"],
        }
        
        combined = title_lower + " " + text.lower()
        best_domain = "General"
        best_score = 0
        for domain, keywords in KEYWORD_DOMAIN_MAP.items():
            score = sum(combined.count(kw) for kw in keywords)
            if score > best_score:
                best_score = score
                best_domain = domain
        return best_domain if best_score >= 2 else "General"

    # Expanded field extractors (government-language enhanced)

    def _extract_conditions(self, text: str) -> List[str]:
        patterns = [
            r"shall\s+(?:be\s+)?(.{10,180}?)[\.;]",
            r"must\s+(.{10,180}?)[\.;]",
            r"eligible\s+(?:for|to|if|when|where|provided|on)\s+(.{10,180}?)[\.;]",
            r"entitled\s+to\s+(.{10,180}?)[\.;]",
            r"admissible\s+(?:to|when|if|subject)\s+(.{10,180}?)[\.;]",
            r"subject\s+to\s+(.{10,180}?)[\.;]",
            r"on\s+completion\s+of\s+(.{10,180}?)[\.;]",
            r"provided\s+(?:that|he|she|the|railway)\s+(.{10,180}?)[\dots]",
            r"(?:sanctioned|granted)\s+(?:if|when|to|for)\s+(.{10,180}?)[\.;]",
            r"will\s+be\s+eligible\s+(?:for|to|if|when|where|provided)\s+(.{10,180}?)[\.;]",
            r"shall\s+be\s+eligible\s+(?:for|to|if|when|where|provided)\s+(.{10,180}?)[\.;]",
            r"should\s+have\s+passed\s+(.{10,180}?)[\.;]",
            r"on\s+satisfactory\s+completion\s+of\s+(.{10,180}?)[\dots]",
            r"subject\s+to\s+the\s+condition\s+that\s+(.{10,180}?)[\.;]",
        ]
        results = []
        for pat in patterns:
            results.extend(m.strip() for m in re.findall(pat, text, re.IGNORECASE))
        seen, unique = set(), []
        for r in results:
            if r not in seen and 10 < len(r) < 200:
                seen.add(r)
                unique.append(r)
        return unique[:10]

    def _extract_documents(self, text: str) -> List[Dict]:
        patterns = [
            r"(?:submit|produce|furnish|attach|provide|submit)\s+(.{5,150}?)[\.;]",
            r"application\s+in\s+(?:Form|format)\s+(.{3,60}?)[\dots\n]",
            r"certificate\s+from\s+(.{5,120}?)[\.;]",
            r"medical\s+certificate\s+(.{5,120}?)[\.;]",
            r"(?:Form|format)\s+([A-Z]{1,5}[\-\d]*)\s+(?:duly|signed|filled)",
            r"on\s+production\s+of\s+(.{5,120}?)[\.;]",
            r"(?:accompanied|supported)\s+by\s+(.{5,120}?)[\.;]",
            r"certificate\s+of\s+(.{5,120}?)[\.;]",
            r"declaration\s+to\s+the\s+effect\s+(.{5,120}?)[\.;]",
            r"deed\s+changing\s+his\s+name",
            r"publication\s+of\s+the\s+change\s+in\s+(.{5,120}?)[\.;]",
            r"surety\s+bond\s+by\s+(.{5,120}?)[\.;]",
            r"service\s+agreement",
            r"written\s+paper\s+and\s+a\s+viva\s+voce",
        ]
        docs = []
        seen = set()
        for pat in patterns:
            for m in re.findall(pat, text, re.IGNORECASE):
                cleaned = m.strip()
                if len(cleaned) > 5 and cleaned not in seen:
                    seen.add(cleaned)
                    docs.append({"document_type": cleaned[:200], "mandatory": True})
        return docs[:10]

    def _extract_disqualifiers(self, text: str) -> List[str]:
        patterns = [
            r"(?:not eligible|disqualified|ineligible|not entitled)\s+(?:if|when|where|for|in case)\s+(.{10,180}?)[\.;]",
            r"shall not be (?:eligible|entitled|granted|admissible)\s+(.{10,180}?)[\.;]",
            r"not\s+be\s+granted\s+if\s+(.{10,180}?)[\.;]",
            r"debarred\s+from\s+(.{10,180}?)[\.;]",
            r"forfeited?\s+(?:if|when|on)\s+(.{10,180}?)[\.;]",
            r"withheld?\s+(?:if|when|on|in)\s+(.{10,180}?)[\.;]",
            r"will not be (?:eligible|entitled|granted|admissible)\s+(.{10,180}?)[\.;]",
            r"no\s+railway\s+servant\s+shall\s+(.{10,180}?)[\.;]",
            r"rendered\s+(?:himself\s+)?ineligible\s+(.{10,180}?)[\.;]",
            r"cannot\s+be\s+(?:promoted|appointed)\s+(.{10,180}?)[\.;]",
            r"failing\s+which\s+(.{10,180}?)[\.;]",
        ]
        results = []
        for pat in patterns:
            results.extend(m.strip() for m in re.findall(pat, text, re.IGNORECASE))
        seen, unique = set(), []
        for r in results:
            if r not in seen and 10 < len(r) < 200:
                seen.add(r)
                unique.append(r)
        return unique[:8]

    def _extract_exceptions(self, text: str) -> List[str]:
        patterns = [
            r"(?:provided that|notwithstanding|except where|save as|save that)\s+(.{10,250}?)[\.;]",
            r"(?:except in|except where|except when)\s+(.{10,200}?)[\.;]",
            r"however[,\s]+(.{10,200}?)[\.;]",
            r"(?:unless|until)\s+(.{10,150}?)[\.;]",
            r"provided\s+further\s+(?:that\s+)?(.{10,250}?)[\.;]",
            r"except\s+with\s+the\s+(.{10,200}?)[\.;]",
            r"may\s+be\s+relaxed\s+(.{10,200}?)[\.;]",
            r"subject\s+to\s+relaxation\s+(.{10,200}?)[\.;]",
        ]
        results = []
        for pat in patterns:
            results.extend(m.strip() for m in re.findall(pat, text, re.IGNORECASE))
        seen, unique = set(), []
        for r in results:
            if r not in seen and 10 < len(r) < 250:
                seen.add(r)
                unique.append(r)
        return unique[:6]

    def _extract_decision_logic(self, text: str) -> str:
        patterns = [
            r"(if\s+.{10,300}?(?:then|shall be|eligible|entitled|admissible|granted).{0,150}?)[\dots]",
            r"(where\s+.{10,200}?(?:shall|may|will)\s+.{10,100}?)[\.;]",
            r"(in\s+case\s+of\s+.{10,200}?(?:shall|eligible|admissible)[^;\.]{0,80})[\.;]",
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()[:500]
        return ""

    def _extract_authority(self, text: str) -> Optional[str]:
        auth_cit = re.findall(r'\((?:Authority\s*[:\-–]?\s*([^)]+))\)', text, re.IGNORECASE)
        if auth_cit:
            return auth_cit[0].strip()
        
        patterns = [
            r"(?:Railway Board|General Manager|DRM|Divisional Railway Manager|"
            r"Chief Personnel Officer|CPO|DPO|Personnel Officer|"
            r"competent authority|sanctioning authority|Head of Department|"
            r"HOD|President|Ministry)\b",
        ]
        matches = []
        for pat in patterns:
            matches.extend(re.findall(pat, text, re.IGNORECASE))
        if matches:
            most_common = Counter(m.strip() for m in matches).most_common(1)
            return most_common[0][0] if most_common else None
        return None

