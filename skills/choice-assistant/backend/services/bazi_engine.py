"""English text

English text HTML English text BaziEngineEnglish text 3379-3440
English textEnglish textEnglish textEnglish textEnglish text
English text bazi-skill English textEnglish text

API
  parse(text)        -> {year, month, day, gender, place, hour, calendar, missing}
  year_pillar(y,m,d) -> English textEnglish text 'English text'
  analyze(text)      -> {complete, info, missing?/pillars?, wuxing?, element?, audit?}
"""

import re
from typing import Any, Dict, List, Optional

# 10 English text
STEMS: List[str] = ["English text", "English text", "English text", "English text", "English text", "English text", "English text", "English text", "English text", "English text"]

# 12 English text
BRANCHES: List[str] = ["English text", "English text", "English text", "English text", "English text", "English text", "English text", "English text", "English text", "English text", "English text", "English text"]

# 12 English textbranch / English text / English text
HOUR_BRANCHES: List[Dict[str, Any]] = [
    {"branch": "English text", "range": "23:00-01:00", "keys": ["English text", "English text", "English text"]},
    {"branch": "English text", "range": "01:00-03:00", "keys": ["English text", "English text"]},
    {"branch": "English text", "range": "03:00-05:00", "keys": ["English text", "English text", "English text"]},
    {"branch": "English text", "range": "05:00-07:00", "keys": ["English text", "English text", "English text"]},
    {"branch": "English text", "range": "07:00-09:00", "keys": ["English text", "English text", "English text"]},
    {"branch": "English text", "range": "09:00-11:00", "keys": ["English text", "English text", "English text"]},
    {"branch": "English text", "range": "11:00-13:00", "keys": ["English text", "English text", "English text"]},
    {"branch": "English text", "range": "13:00-15:00", "keys": ["English text", "English text", "English text"]},
    {"branch": "English text", "range": "15:00-17:00", "keys": ["English text", "English text", "English text"]},
    {"branch": "English text", "range": "17:00-19:00", "keys": ["English text", "English text", "English text"]},
    {"branch": "English text", "range": "19:00-21:00", "keys": ["English text", "English text", "English text"]},
    {"branch": "English text", "range": "21:00-23:00", "keys": ["English text", "English text", "English text"]},
]

# English textEnglish text=English textEnglish text=English textEnglish text=English textEnglish text=English textEnglish text=English text
BRANCH_WUXING: Dict[str, str] = {
    "English text": "English text", "English text": "English text",
    "English text": "English text", "English text": "English text",
    "English text": "English text", "English text": "English text",
    "English text": "English text", "English text": "English text",
    "English text": "English text", "English text": "English text", "English text": "English text", "English text": "English text",
}

# English textEnglish text=English textEnglish text=English textEnglish text=English textEnglish text=English textEnglish text=English text
STEM_WUXING: Dict[str, str] = {
    "English text": "English text", "English text": "English text",
    "English text": "English text", "English text": "English text",
    "English text": "English text", "English text": "English text",
    "English text": "English text", "English text": "English text",
    "English text": "English text", "English text": "English text",
}

# English textEnglish textEnglish text-English text-English textEnglish text English text/English text/English text English text - / . English text
_BIRTHDAY_RE = re.compile(
    r"(19\d{2}|20\d{2})\s*(?:English text|[-/.])\s*(\d{1,2})\s*(?:English text|[-/.])\s*(\d{1,2})\s*(?:English text|English text)?"
)
# English text
_YEAR_ONLY_RE = re.compile(r"(19\d{2}|20\d{2})")
# English textEnglish textEnglish text
_GENDER_MALE_RE = re.compile(r"(^|\s)(English text|English text|English text|English text)(\s|$)")
_GENDER_FEMALE_RE = re.compile(r"(^|\s)(English text|English text|English text|English text)(\s|$)")
# English textEnglish text + 2-12 English textEnglish text/English text/English text/English text
_PLACE_RE = re.compile(r"(?:English text|English text|English text|English text)\s*([\u4e00-\u9fa5]{2,12}(?:English text|English text|English text|English text)?)")
# English text2-8 English text + English text/English text/English text/English text
_PLACE_FALLBACK_RE = re.compile(r"[\u4e00-\u9fa5]{2,8}(?:English text|English text|English text|English text)")
# English textEnglish text JS English text
_PUNCT_RE = re.compile(r"[]")


def parse(text: str) -> Dict[str, Any]:
    """English text

    English text
      year/month/day: int English text None
      gender: 'English text' / 'English text' / ''
      place: strEnglish text
      hour: English text dict English text None
      calendar: 'English text' / 'English text' / ''
      missing: English textEnglish text
    """
    q = _PUNCT_RE.sub(" ", str(text or ""))

    birthday = _BIRTHDAY_RE.search(q)
    year = None
    month = None
    day = None
    if birthday:
        year = int(birthday.group(1))
        month = int(birthday.group(2))
        day = int(birthday.group(3))
    else:
        year_only = _YEAR_ONLY_RE.search(q)
        if year_only:
            year = int(year_only.group(1))

    if _GENDER_MALE_RE.search(q):
        gender = "English text"
    elif _GENDER_FEMALE_RE.search(q):
        gender = "English text"
    else:
        gender = ""

    place_match = _PLACE_RE.search(q)
    place = place_match.group(1) if place_match else ""
    if not place:
        # English textEnglish text "XEnglish text/XEnglish text/XEnglish text/XEnglish text" English text
        all_places = _PLACE_FALLBACK_RE.findall(q)
        if all_places:
            place = all_places[-1]

    hour = next(
        (h for h in HOUR_BRANCHES if any(k in q for k in h["keys"])),
        None,
    )

    if "English text" in q or "English text" in q:
        calendar = "English text"
    elif "English text" in q or "English text" in q:
        calendar = "English text"
    else:
        calendar = ""

    missing: List[str] = []
    if not birthday:
        missing.append("English text")
    if not hour:
        missing.append("English text")
    if not gender:
        missing.append("English text")
    if not place:
        missing.append("English text")

    return {
        "year": year,
        "month": month,
        "day": day,
        "gender": gender,
        "place": place,
        "hour": hour,
        "calendar": calendar,
        "missing": missing,
    }


def year_pillar(year: Optional[int], month: Optional[int], day: Optional[int]) -> str:
    """English textEnglish text+English text+English text

    English textmonth<2 English text month==2 English text day<4English text
    year English text None English text 'English text'
    """
    if not year:
        return "English text"
    adjusted_year = year
    if month is not None and day is not None and (month < 2 or (month == 2 and day < 4)):
        adjusted_year = year - 1
    stem_idx = ((adjusted_year - 4) % 10 + 10) % 10
    branch_idx = ((adjusted_year - 4) % 12 + 12) % 12
    return STEMS[stem_idx] + BRANCHES[branch_idx] + "English text"


def analyze(text: str) -> Dict[str, Any]:
    """English text

    English text → {complete: false, info, missing}
    English text   → {complete: true, info, pillars, wuxing, element, audit}

    English text + English text + English textEnglish text/English text/English text bazi-skill English text
    """
    info = parse(text)
    if info["missing"]:
        return {"complete": False, "info": info, "missing": info["missing"]}

    yp = year_pillar(info["year"], info["month"], info["day"])
    # year_pillar English text "English text"English text"English text"English text 2 English text
    branch = yp.replace("English text", "")[1]
    base_element = BRANCH_WUXING.get(branch, "English text")
    hour_branch = info["hour"]["branch"]
    hour_range = info["hour"]["range"]

    return {
        "complete": True,
        "info": info,
        "pillars": {
            "year": yp,
            "month": "English text",
            "day": "English text",
            "hour": f"{hour_branch}English text{hour_range}English text",
        },
        "wuxing": (
            f"English text{base_element}English text{hour_branch}"
            f"English textEnglish textEnglish text"
        ),
        "element": f"English text{base_element}English textEnglish text",
        "audit": (
            "English textEnglish text"
            "English textEnglish textEnglish text bazi-skill English text"
        ),
    }


if __name__ == "__main__":
    # English text 1English text1990 English text
    text1 = "English text 1990English text6English text15English text English text English text English text"
    r1 = analyze(text1)
    print("case1English text:", r1)
    assert r1["complete"] is True
    assert r1["info"]["gender"] == "English text"
    assert r1["info"]["year"] == 1990
    assert r1["info"]["month"] == 6
    assert r1["info"]["day"] == 15
    assert r1["info"]["place"] == "English text"
    assert r1["info"]["calendar"] == "English text"
    assert r1["info"]["hour"]["branch"] == "English text"
    assert r1["pillars"]["year"] == "English text", f"English text English textEnglish text {r1['pillars']['year']}"
    assert r1["pillars"]["hour"] == "English text11:00-13:00English text"
    assert "English text" in r1["wuxing"]
    assert "bazi-skill" in r1["audit"]

    # English text 2English text1990English text1English text15English text → 1989 English text
    text2 = "English text 1990English text1English text15English text English text English text English text"
    r2 = analyze(text2)
    print("case2English text:", r2["pillars"]["year"])
    assert r2["pillars"]["year"] == "English text", f"English text English textEnglish text {r2['pillars']['year']}"

    # English text 3English text1990English text2English text4English text → English text
    text3 = "English text 1990English text2English text4English text English text English text English text"
    r3 = analyze(text3)
    print("case3English text:", r3["pillars"]["year"])
    assert r3["pillars"]["year"] == "English text"

    # English text 4English text
    text4 = "English text"
    r4 = analyze(text4)
    print("case4English text:", r4)
    assert r4["complete"] is False
    assert "English text" in r4["missing"]
    assert "English text" in r4["missing"]
    assert "English text" in r4["missing"]
    assert "English text" in r4["missing"]

    # English text 5year_pillar English text
    assert year_pillar(None, None, None) == "English text"
    assert year_pillar(1984, 6, 15) == "English text"  # 1984 English text
    assert year_pillar(2024, 6, 15) == "English text"  # 2024 English text

    # English text 6English text + English text + English text"English text"
    text6 = "English text 1995English text8English text8English text English text English text English text"
    r6 = analyze(text6)
    print("case6English text/English text/English text:", r6["info"]["gender"], r6["info"]["calendar"], r6["info"]["hour"]["branch"])
    assert r6["info"]["gender"] == "English text"
    assert r6["info"]["calendar"] == "English text"
    assert r6["info"]["hour"]["branch"] == "English text"  # "English text" English text

    print("\nEnglish text")
