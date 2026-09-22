import re


SECURITY_RULES = [
    {
        "code": "disk_destruction",
        "title": "Disk üzerinde yıkıcı işlem",
        "pattern": (
            r"\b(?:"
            r"Format-Volume|"
            r"Clear-Disk|"
            r"Initialize-Disk|"
            r"Remove-Partition"
            r")\b"
        ),
        "description": (
            "Disk biçimlendirme, temizleme veya bölüm silme "
            "işlemi tespit edildi."
        ),
    },
    {
        "code": "system_root_delete",
        "title": "Sistem diski üzerinde toplu silme",
        "pattern": (
            r"\bRemove-Item\b"
            r"(?=[\s\S]{0,500}(?:-Recurse|-R\b))"
            r"(?=[\s\S]{0,500}(?:"
            r"C:\\(?:\s|['\"]|$)|"
            r"C:/(?:\s|['\"]|$)|"
            r"\$env:SystemDrive|"
            r"\$env:SystemRoot|"
            r"\$env:windir"
            r"))"
        ),
        "description": (
            "Sistem dizini üzerinde özyinelemeli silme "
            "işlemi tespit edildi."
        ),
    },
    {
        "code": "cmd_recursive_delete",
        "title": "Komut satırıyla toplu silme",
        "pattern": (
            r"\b(?:cmd(?:\.exe)?\s+/c\s+)?"
            r"(?:del|erase|rd|rmdir)\b"
            r"[\s\S]{0,300}"
            r"(?:/s\b|/q\b)"
        ),
        "description": (
            "CMD üzerinden toplu dosya veya klasör silme "
            "işlemi tespit edildi."
        ),
    },
    {
        "code": "shadow_copy_delete",
        "title": "Gölge kopyaları silme",
        "pattern": (
            r"\b(?:"
            r"vssadmin(?:\.exe)?\s+delete\s+shadows|"
            r"wmic(?:\.exe)?\s+shadowcopy\s+delete|"
            r"Remove-WmiObject[\s\S]{0,200}Win32_ShadowCopy"
            r")\b"
        ),
        "description": (
            "Sistem geri yükleme veya gölge kopyalarını "
            "silme işlemi tespit edildi."
        ),
    },
]


def normalize_script(script_content):
    if not isinstance(script_content, str):
        return ""

    return (
        script_content
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .strip()
    )


def remove_powershell_comments(script_content):
    result = []
    index = 0
    length = len(script_content)

    inside_single_quote = False
    inside_double_quote = False
    inside_block_comment = False

    while index < length:
        current = script_content[index]

        next_character = (
            script_content[index + 1]
            if index + 1 < length
            else ""
        )

        if inside_block_comment:
            if current == "#" and next_character == ">":
                inside_block_comment = False
                index += 2
                continue

            index += 1
            continue

        if not inside_single_quote and not inside_double_quote:
            if current == "<" and next_character == "#":
                inside_block_comment = True
                index += 2
                continue

            if current == "#":
                while (
                    index < length
                    and script_content[index] != "\n"
                ):
                    index += 1

                if index < length:
                    result.append("\n")
                    index += 1

                continue

        if current == "'" and not inside_double_quote:
            if inside_single_quote and next_character == "'":
                result.append(current)
                result.append(next_character)
                index += 2
                continue

            inside_single_quote = not inside_single_quote

        elif current == '"' and not inside_single_quote:
            if index > 0 and script_content[index - 1] == "`":
                result.append(current)
                index += 1
                continue

            inside_double_quote = not inside_double_quote

        result.append(current)
        index += 1

    return "".join(result)


def analyze_script(script_content):
    normalized_script = normalize_script(
        script_content
    )

    if not normalized_script:
        return {
            "allowed": False,
            "risk_score": 0,
            "risk_level": "low",
            "security_status": "blocked",
            "summary": "Script içeriği boş olamaz.",
            "findings": [],
        }

    analyzed_script = remove_powershell_comments(
        normalized_script
    )

    findings = []

    for rule in SECURITY_RULES:
        matches = list(
            re.finditer(
                rule["pattern"],
                analyzed_script,
                flags=(
                    re.IGNORECASE
                    | re.MULTILINE
                    | re.DOTALL
                ),
            )
        )

        if not matches:
            continue

        first_match = matches[0].group(0).strip()

        findings.append(
            {
                "code": rule["code"],
                "title": rule["title"],
                "description": rule["description"],
                "risk_level": "critical",
                "score": 100,
                "block": False,
                "match_count": len(matches),
                "matched_content": first_match[:200],
            }
        )

    if findings:
        return {
            "allowed": True,
            "risk_score": 100,
            "risk_level": "critical",
            "security_status": "warning",
            "summary": (
                "Scriptte dikkat gerektiren kritik bir işlem "
                "tespit edildi."
            ),
            "findings": findings,
        }

    return {
        "allowed": True,
        "risk_score": 0,
        "risk_level": "low",
        "security_status": "safe",
        "summary": (
            "Scriptte bilinen kritik bir işlem bulunamadı."
        ),
        "findings": [],
    }


def validate_script_or_raise(script_content):
    analysis = analyze_script(
        script_content
    )

    if not normalize_script(script_content):
        raise ValueError(
            "Script içeriği boş olamaz."
        )

    return analysis