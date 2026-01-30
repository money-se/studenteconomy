import os, re, html
from pathlib import Path

ROOT = Path(".")  # kör i repo-roten

def strip_html(text: str) -> str:
    # Ta bort script/style
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I|re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I|re.S)
    # Ta bort tags
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    # Normalisera whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_tag_content(html_text: str, tag: str) -> str:
    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", html_text, flags=re.I|re.S)
    return m.group(1).strip() if m else ""

def get_meta_description(html_text: str) -> str:
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']\s*/?>', html_text, flags=re.I|re.S)
    if not m:
        m = re.search(r'<meta\s+content=["\'](.*?)["\']\s+name=["\']description["\']\s*/?>', html_text, flags=re.I|re.S)
    return m.group(1).strip() if m else ""

def has_relaterat_block(html_text: str) -> bool:
    # enkel heuristik: rubrik "Relaterat" eller "Relaterat sparande"
    return bool(re.search(r">Relaterat<|>Relaterat\s", html_text, flags=re.I))

def has_h1(html_text: str) -> bool:
    return bool(re.search(r"<h1\b", html_text, flags=re.I))

def word_count(html_text: str) -> int:
    text = strip_html(html_text)
    # räkna ord (sv/eng): split på whitespace
    return 0 if not text else len(text.split())

pages = []

# Hitta alla index.html under repo (inkl root index.html)
for path in ROOT.rglob("index.html"):
    # hoppa över node_modules om någon gång skulle finnas
    if "node_modules" in path.parts:
        continue
    rel = path.as_posix()
    try:
        html_text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        pages.append((rel, "ERROR_READ", 0, "", "", False, False, False))
        continue

    title = get_tag_content(html_text, "title")
    desc = get_meta_description(html_text)
    wc = word_count(html_text)
    h1 = has_h1(html_text)
    relaterat = has_relaterat_block(html_text)

    # “OK” tröskel – du kan justera:
    status = "OK" if wc >= 180 else "TUNN"

    pages.append((rel, status, wc, title, desc, bool(title), bool(desc), h1, relaterat))

# Sortera: tunnast först
pages.sort(key=lambda x: (x[1] != "TUNN", x[2]))

print("AUDIT: StudentEkonomi")
print("Legend: OK >=180 ord, TUNN <180 ord\n")

# Summering
total = len(pages)
tunn = sum(1 for p in pages if p[1] == "TUNN")
ok_ = total - tunn
print(f"Totalt: {total} | OK: {ok_} | TUNN: {tunn}\n")

# Tabell
print("FILE\tSTATUS\tWORDS\tTITLE?\tDESC?\tH1?\tRELATERAT?")
for rel, status, wc, title, desc, has_title, has_desc, has_h1_flag, has_rel in pages:
    print(f"{rel}\t{status}\t{wc}\t{int(has_title)}\t{int(has_desc)}\t{int(has_h1_flag)}\t{int(has_rel)}")

# Extra: lista problem som faktiskt skadar SEO
print("\nKRITISKT (saknar title/desc/h1):")
crit = [p for p in pages if (p[5] is False or p[6] is False or p[7] is False)]
if not crit:
    print("Inga kritiska hittades.")
else:
    for rel, status, wc, title, desc, has_title, has_desc, has_h1_flag, has_rel in crit:
        print(f"- {rel} | {status} | {wc} ord | title:{has_title} desc:{has_desc} h1:{has_h1_flag}")

print("\nREKOMMENDERAT (tunn + saknar Relaterat):")
rec = [p for p in pages if p[1] == "TUNN" and p[8] is False]
if not rec:
    print("Inga.")
else:
    for rel, status, wc, *_rest in rec:
        print(f"- {rel} | {wc} ord")
