#!/usr/bin/env python3
"""
AuraCode Requirements Ambiguity and Non-Technical Dialogue Checker (Gate G1)
Evaluates requirements files, specs, and code for ambiguity markers, unconfirmed assumptions,
and generates structured non-technical clarification questions for non-technical users.
"""
import os
import sys
import json
import re
import glob

AMBIGUITY_PATTERNS = [
    (r"\bTODO\b", "Unresolved TODO item found"),
    (r"\bFIXME\b", "Unresolved FIXME item found"),
    (r"\bTBD\b", "To Be Determined (TBD) marker found"),
    (r"\b(?:maybe|probably|should work|something like|etc\.?)\b", "Vague specification phrasing"),
    (r"\b(?:as expected|normal behavior|standard way)\b", "Underspecified behavior assumption"),
]

NON_TECHNICAL_QUESTION_TEMPLATES = {
    "missing_edge_case": "Quando acontecer um erro imprevisto ou falha de conexão, o sistema deve mostrar uma mensagem amigável ao usuário ou tentar reconectar sozinho? Sobrou alguma dúvida sobre esta escolha?",
    "missing_user_role": "Quem são as pessoas autorizadas a acessar esta funcionalidade (ex: qualquer usuário ou apenas administradores)? Sobrou alguma dúvida sobre como os perfis funcionam?",
    "missing_data_retention": "Por quanto tempo as informações antigas ou relatórios devem ser guardados no sistema antes de serem arquivados? Sobrou alguma dúvida sobre o armazenamento?",
    "unspecified_flow": "Quando o usuário clicar no botão final, para onde ele deve ser redirecionado? Sobrou alguma dúvida sobre esta navegação?"
}

def analyze_workspace(workspace_dir: str, include_json: bool = False) -> dict:
    findings = []
    unclear_requirements = []
    suggested_questions = []

    extensions = ['*.md', '*.txt', '*.rst']
    if include_json:
        extensions.append('*.json')

    doc_files = []
    for ext in extensions:
        doc_files.extend(glob.glob(os.path.join(workspace_dir, '**', ext), recursive=True))

    ignored_dirs = [
        '.git', 'node_modules', 'venv', '__pycache__', '.agents', '.auracode', '_auracode',
        'framework_audit', 'docs/audit', '_reversa_sdd', '_reversa_refactor', '_reversa_bugs',
        '_reversa_docs', '_reversa_forward', 'schemas', 'validation/schemas'
    ]
    doc_files = [f for f in doc_files if not any(x in f.replace('\\', '/') for x in ignored_dirs)]

    for filepath in doc_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                rel_path = os.path.relpath(filepath, workspace_dir)

                for pattern, desc in AMBIGUITY_PATTERNS:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        findings.append({
                            "file": rel_path,
                            "line": line_no,
                            "issue": desc,
                            "snippet": match.group(0)
                        })
                        unclear_requirements.append(f"{rel_path}:{line_no} - {desc}: '{match.group(0)}'")
        except (IOError, UnicodeDecodeError):
            continue

    if len(findings) > 0:
        status = "WARN" if len(findings) < 5 else "FAIL"
    else:
        status = "PASS"

    for key, template in NON_TECHNICAL_QUESTION_TEMPLATES.items():
        suggested_questions.append({
            "category": key,
            "question_pt_br": template
        })

    result = {
        "status": status,
        "ambiguity_score": round(max(0.0, 1.0 - (len(findings) * 0.1)), 2),
        "total_ambiguity_findings": len(findings),
        "unclear_requirements": unclear_requirements,
        "suggested_non_technical_questions": suggested_questions,
        "details": findings
    }
    return result

def main() -> None:
    args = sys.argv[1:]
    include_json = "--include-json" in args
    positional = [a for a in args if not a.startswith("--")]
    target_dir = positional[0] if positional else "."
    res = analyze_workspace(os.path.abspath(target_dir), include_json=include_json)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    if res["status"] == "FAIL":
        sys.exit(1)

if __name__ == "__main__":
    main()
