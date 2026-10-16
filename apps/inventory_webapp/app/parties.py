"""Parse client / architect / MEP from drawing title-block text.

Kept local to the webapp so API/Docker do not depend on PYTHONPATH for
``riser_extract`` when enriching project cards from PDFs.
"""

from __future__ import annotations

import re


def parse_parties(full_text: str) -> dict[str, str | None]:
    lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]
    upper_lines = [ln.upper() for ln in lines]

    def after_label(label: str) -> str | None:
        for i, u in enumerate(upper_lines):
            if u == label or u.startswith(label + " ") or u.startswith(label + ":"):
                if ":" in lines[i]:
                    rest = lines[i].split(":", 1)[1].strip(" :-")
                    if rest and len(rest) > 1:
                        return rest
                for j in range(i + 1, min(i + 4, len(lines))):
                    cand = lines[j].strip(" :-")
                    if not cand:
                        continue
                    if cand.upper() in {
                        "ARCHITECT",
                        "CLIENT",
                        "ENGINEER",
                        "MEP",
                        "DRAWN",
                        "CHECKED",
                        "REV",
                        "SCALE",
                        "DATE",
                        "TITLE",
                        "PROJECT",
                        "DISCLAIMER",
                    }:
                        continue
                    if cand.upper().startswith(
                        ("ARCHITECT", "CLIENT", "SCALE", "DATE", "DRAWING", "REV")
                    ):
                        continue
                    return cand
        return None

    client = after_label("CLIENT")
    architect = None
    if re.search(
        r"([\w.-]+@curioarchitects\.co\.uk|www\.curioarchitects\.co\.uk)",
        full_text,
        re.I,
    ):
        architect = "Curio Architects"
    if not architect:
        architect = after_label("ARCHITECT")
        if architect and "@" in architect:
            domain = architect.split("@", 1)[1].split("/", 1)[0]
            host = domain.split(".")[0]
            if "curio" in host.lower():
                architect = "Curio Architects"
            else:
                architect = host.replace("-", " ").title()
    if architect and client and architect.upper().rstrip(".") == client.upper().rstrip("."):
        architect = None
        if re.search(r"curioarchitects", full_text, re.I):
            architect = "Curio Architects"

    mep = None
    mep_address = None
    mep_web = None
    if re.search(r"\bSeneca\s+Group\s+Ltd\b", full_text, re.I):
        mep = "Seneca Group Ltd"
    if not mep:
        m = re.search(
            r"\b(Seneca\s+(?:Engineering\s+)?(?:Group\s+)?Ltd)\b", full_text, re.I
        )
        if m:
            mep = re.sub(r"\s+", " ", m.group(1)).strip()
    addr = re.search(
        r"(4th\s+Floor,\s+Silverstream\s+House,[^\n]+Fitzrovia[^\n]*)",
        full_text,
        re.I,
    )
    if addr:
        mep_address = re.sub(r"\s+", " ", addr.group(1)).strip(" ,")
    web = re.search(r"(www\.senecagrp\.com)", full_text, re.I)
    if web:
        mep_web = web.group(1).lower()

    if client:
        client = re.sub(r"\s+", " ", client).strip()
        if client.isupper() and len(client) < 40:
            client = client.title().replace("Ltd", "Ltd")

    return {
        "client": client,
        "architect": architect,
        "mep": mep,
        "mep_address": mep_address,
        "mep_web": mep_web,
    }
