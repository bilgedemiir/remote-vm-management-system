import os
import re

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError(
        "OPENROUTER_API_KEY bulunamadı. .env dosyasını kontrol et."
    )


client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
)


SYSTEM_PROMPT = """
Sen uzman bir Windows sistem yöneticisisin.

Kullanıcının isteğine uygun, doğrudan çalıştırılabilir PowerShell
scripti üret.

Kesin kurallar:

1. Yalnızca PowerShell kodu döndür.
2. Koddan önce veya sonra açıklama yazma.
3. Başlık yazma.
4. Markdown kullanma.
5. Kod bloğu işaretleri kullanma.
6. "İşte script", "Aşağıdaki kod" gibi ifadeler yazma.
7. Açıklama amaçlı PowerShell yorum satırı yazma.
8. Kullanıcının isteğini tekrar etme.
9. Kod dışında hiçbir metin üretme.
10. Çıktı doğrudan PowerShell üzerinde çalıştırılabilir olmalıdır.

İstek belirsizse açıklama istemek yerine güvenli ve en makul
PowerShell kodunu üret.
""".strip()


ROLLBACK_SYSTEM_PROMPT = """
Sen uzman bir Windows sistem yöneticisisin.

Verilen PowerShell scriptinin yaptığı işlemi mümkün olduğunca güvenli
şekilde geri alacak bir PowerShell rollback scripti üret.

Kesin kurallar:

1. Yalnızca PowerShell kodu döndür.
2. Koddan önce veya sonra açıklama yazma.
3. Markdown kullanma.
4. Kod bloğu işaretleri kullanma.
5. Yorum satırı yazma.
6. Orijinal scripti tekrar etme.
7. Geri alınması mümkün olmayan bir işlem varsa yalnızca:
   throw "Bu işlem güvenli şekilde geri alınamaz."
   kodunu döndür.
8. Silinen dosya veya veriyi tahmin ederek yeniden oluşturma.
9. Rollback işlemi mevcut sisteme ek zarar vermemelidir.
10. Çıktı doğrudan PowerShell üzerinde çalıştırılabilir olmalıdır.
""".strip()


def clean_powershell_output(model_output: str) -> str:
    if not model_output:
        raise ValueError("Model boş cevap döndürdü.")

    cleaned_output = model_output.strip()

    code_block_match = re.search(
        r"```(?:powershell|ps1|pwsh)?\s*([\s\S]*?)```",
        cleaned_output,
        flags=re.IGNORECASE,
    )

    if code_block_match:
        cleaned_output = code_block_match.group(1).strip()

    cleaned_output = re.sub(
        r"^\s*```(?:powershell|ps1|pwsh)?\s*",
        "",
        cleaned_output,
        flags=re.IGNORECASE,
    )

    cleaned_output = re.sub(
        r"\s*```\s*$",
        "",
        cleaned_output,
    )

    unwanted_prefixes = [
        r"işte(?: istediğiniz)?(?: powershell)?(?: scripti| kodu)?\s*:",
        r"aşağıdaki(?: powershell)?(?: scripti| kodu)?\s*:",
        r"here(?: is|'s)(?: the)?(?: powershell)?(?: script| code)?\s*:",
        r"powershell(?: script| code)?\s*:",
    ]

    for prefix_pattern in unwanted_prefixes:
        cleaned_output = re.sub(
            rf"^\s*{prefix_pattern}\s*",
            "",
            cleaned_output,
            count=1,
            flags=re.IGNORECASE,
        )

    cleaned_output = cleaned_output.strip()

    if not cleaned_output:
        raise ValueError(
            "Model geçerli bir PowerShell scripti döndürmedi."
        )

    return cleaned_output


def generate_powershell(user_request: str) -> str:
    if not user_request or not user_request.strip():
        raise ValueError("Kullanıcı isteği boş olamaz.")

    response = client.chat.completions.create(
        model="openrouter/free",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_request.strip(),
            },
        ],
    )

    model_output = response.choices[0].message.content

    return clean_powershell_output(model_output)


def generate_rollback_powershell(
    original_script: str
) -> str:
    if (
        not original_script
        or not original_script.strip()
    ):
        raise ValueError(
            "Orijinal script boş olamaz."
        )

    user_prompt = f"""
Aşağıdaki PowerShell scriptinin yaptığı işlemi geri alacak
güvenli bir rollback scripti üret.

ORİJİNAL SCRIPT:{original_script.strip()}
""".strip()

    response = client.chat.completions.create(
        model="openrouter/free",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": ROLLBACK_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    model_output = (
        response.choices[0].message.content
    )

    return clean_powershell_output(
        model_output
    )