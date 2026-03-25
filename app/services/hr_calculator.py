"""
台灣勞動法結構化計算引擎

解決問題：LLM 數值計算不穩定（資遣費算錯 26 倍等），
將常見 HR 計算以程式精確執行，結果注入 prompt 作為驗證基準。
"""

import re
from datetime import date
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class CalcResult:
    """計算結果"""
    calc_type: str          # severance / overtime / annual_leave / hourly_wage
    formula: str            # 公式說明
    steps: List[str]        # 計算步驟
    result: str             # 最終結果（文字）
    result_value: float     # 最終數值
    legal_basis: str        # 法條依據


# ── 數值擷取工具 ──

_SALARY_RE = re.compile(
    r"(?:月薪|薪資|薪水|月平均工資|平均工資|底薪|基本薪資|月工資)\s*(?:為|是|約|：|:)?\s*"
    r"(\d[\d,]*)\s*(?:元|塊)?",
    re.UNICODE,
)

_YEARS_RE = re.compile(
    r"(?:年資|工作|任職|服務)\s*(?:為|是|約|：|:|\s)*?"
    r"(\d+)\s*年\s*(?:又|零|餘)?\s*(?:(\d+)\s*(?:個月|月))?",
    re.UNICODE,
)

_DATE_RE = re.compile(
    r"(?:到職日|入職日|到職|入職|報到日?|就職)\s*(?:為|是|：|:)?\s*"
    r"(\d{4})\s*[年/\-]\s*(\d{1,2})\s*[月/\-]\s*(\d{1,2})\s*日?",
    re.UNICODE,
)

_OVERTIME_HOURS_RE = re.compile(
    r"加班\s*(\d+(?:\.\d+)?)\s*(?:小時|時|hrs?|hours?)",
    re.UNICODE | re.IGNORECASE,
)


def _parse_money(text: str) -> Optional[int]:
    m = _SALARY_RE.search(text)
    if m:
        return int(m.group(1).replace(",", ""))
    # 嘗試更寬鬆的匹配
    loose = re.search(r"(\d[\d,]{3,})\s*(?:元|塊)", text)
    if loose:
        return int(loose.group(1).replace(",", ""))
    return None


def _parse_years(text: str) -> Optional[float]:
    m = _YEARS_RE.search(text)
    if m:
        years = int(m.group(1))
        months = int(m.group(2)) if m.group(2) else 0
        return years + months / 12.0
    return None


def _parse_start_date(text: str) -> Optional[date]:
    m = _DATE_RE.search(text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def _years_between(start: date, end: date) -> float:
    """精確計算年資（含月份小數）"""
    delta_days = (end - start).days
    return round(delta_days / 365.25, 4)


# ── 資遣費計算（勞基法第17條 / 勞退條例第12條）──

def calc_severance(question: str, ref_date: Optional[date] = None) -> Optional[CalcResult]:
    """
    資遣費 = 年資(年) × 0.5 × 月平均工資
    （勞工退休金條例第12條，新制）
    上限：6 個月月均工資
    """
    salary = _parse_money(question)
    if salary is None:
        return None

    today = ref_date or date.today()
    years = _parse_years(question)
    start_date = _parse_start_date(question)

    if years is None and start_date is not None:
        years = _years_between(start_date, today)

    if years is None:
        return None

    # 新制資遣費：每滿 1 年 → 0.5 個月，上限 6 個月
    half_months = years * 0.5
    half_months_capped = min(half_months, 6.0)
    severance = round(salary * half_months_capped)

    steps = [
        f"月平均工資 = {salary:,} 元",
        f"年資 = {years:.2f} 年" + (f"（到職日 {start_date} 至 {today}）" if start_date else ""),
        f"資遣費基數 = {years:.2f} × 0.5 = {half_months:.2f} 個月" +
        ("（超過上限 6 個月，取 6）" if half_months > 6 else ""),
        f"資遣費 = {salary:,} × {half_months_capped:.2f} = {severance:,} 元",
    ]

    return CalcResult(
        calc_type="severance",
        formula="資遣費 = 年資(年) × 0.5 × 月平均工資（上限 6 個月）",
        steps=steps,
        result=f"{severance:,} 元",
        result_value=severance,
        legal_basis="《勞工退休金條例》第12條（新制資遣費）",
    )


# ── 加班費計算（勞基法第24條）──

def calc_overtime(question: str) -> Optional[CalcResult]:
    """
    平日加班費：
      前 2h: 時薪 × 4/3 (≈1.34)
      第 3h 起: 時薪 × 5/3 (≈1.67)
    """
    salary = _parse_money(question)
    m = _OVERTIME_HOURS_RE.search(question)
    if salary is None or m is None:
        return None

    hours = float(m.group(1))
    hourly = salary / 30 / 8

    is_rest_day = "休息日" in question or "假日" in question

    steps = [
        f"月薪 = {salary:,} 元",
        f"時薪 = {salary:,} / 30 / 8 = {hourly:.2f} 元",
    ]

    if is_rest_day:
        # 休息日
        first2 = min(hours, 2) * hourly * (4 / 3)
        next6 = max(0, min(hours, 8) - 2) * hourly * (5 / 3)
        after8 = max(0, hours - 8) * hourly * (8 / 3)
        total = round(first2 + next6 + after8)
        steps.append(f"休息日加班 {hours} 小時：")
        if hours > 0:
            steps.append(f"  前 2h：{min(hours, 2):.1f} × {hourly:.2f} × 4/3 = {first2:.0f}")
        if hours > 2:
            steps.append(f"  第 3~8h：{max(0, min(hours, 8) - 2):.1f} × {hourly:.2f} × 5/3 = {next6:.0f}")
        if hours > 8:
            steps.append(f"  第 9h 起：{hours - 8:.1f} × {hourly:.2f} × 8/3 = {after8:.0f}")
        legal = "《勞動基準法》第24條第2項（休息日加班費）"
    else:
        # 平日
        first2 = min(hours, 2) * hourly * (4 / 3)
        after2 = max(0, hours - 2) * hourly * (5 / 3)
        total = round(first2 + after2)
        steps.append(f"平日加班 {hours} 小時：")
        steps.append(f"  前 2h：{min(hours, 2):.1f} × {hourly:.2f} × 4/3 = {first2:.0f}")
        if hours > 2:
            steps.append(f"  第 3h 起：{hours - 2:.1f} × {hourly:.2f} × 5/3 = {after2:.0f}")
        legal = "《勞動基準法》第24條第1項（平日加班費）"

    steps.append(f"加班費合計 = {total:,} 元")

    return CalcResult(
        calc_type="overtime",
        formula="平日前2h×4/3 + 第3h起×5/3；休息日前2h×4/3 + 3~8h×5/3 + 9h起×8/3",
        steps=steps,
        result=f"{total:,} 元",
        result_value=total,
        legal_basis=legal,
    )


# ── 特休天數計算（勞基法第38條）──

_ANNUAL_LEAVE_TABLE = [
    # (min_years, max_years, days)
    (0.0, 0.5, 0),
    (0.5, 1.0, 3),
    (1.0, 2.0, 7),
    (2.0, 3.0, 10),
    (3.0, 5.0, 14),
    (5.0, 10.0, 15),
]
# 10 年以上：每多 1 年 +1 天，上限 30 天


def _annual_leave_days(years: float) -> int:
    if years < 0.5:
        return 0
    for min_y, max_y, days in _ANNUAL_LEAVE_TABLE:
        if min_y <= years < max_y:
            return days
    # 10 年以上：每滿 1 年加 1 天，上限 30 天
    base = 15
    extra = int(years) - 10
    return min(base + extra, 30)


def calc_annual_leave(question: str, ref_date: Optional[date] = None) -> Optional[CalcResult]:
    today = ref_date or date.today()
    years = _parse_years(question)
    start_date = _parse_start_date(question)

    if years is None and start_date is not None:
        years = _years_between(start_date, today)

    if years is None:
        return None

    days = _annual_leave_days(years)

    steps = [
        f"年資 = {years:.2f} 年" + (f"（到職日 {start_date} 至 {today}）" if start_date else ""),
        f"依勞基法第38條對照表 → 特休 {days} 天",
    ]

    return CalcResult(
        calc_type="annual_leave",
        formula="依年資對照勞基法第38條特休天數表",
        steps=steps,
        result=f"{days} 天",
        result_value=days,
        legal_basis="《勞動基準法》第38條",
    )


# ── 時薪計算 ──

def calc_hourly_wage(question: str) -> Optional[CalcResult]:
    salary = _parse_money(question)
    if salary is None:
        return None
    if "時薪" not in question:
        return None

    hourly = salary / 30 / 8
    steps = [
        f"月薪 = {salary:,} 元",
        f"時薪 = {salary:,} / 30 / 8 = {hourly:.2f} 元",
    ]

    return CalcResult(
        calc_type="hourly_wage",
        formula="時薪 = 月薪 / 30 / 8",
        steps=steps,
        result=f"{hourly:.2f} 元",
        result_value=hourly,
        legal_basis="《勞動基準法》施行細則第7條",
    )


# ── 主入口 ──

def try_hr_calculation(question: str) -> Optional[str]:
    """
    嘗試從問題中擷取數值並執行精確計算。
    回傳格式化的計算結果文字，供注入 LLM prompt。
    若無法辨識計算題型則回傳 None。
    """
    results: List[CalcResult] = []

    if "資遣費" in question:
        r = calc_severance(question)
        if r:
            results.append(r)

    if "加班" in question and ("費" in question or "薪" in question):
        r = calc_overtime(question)
        if r:
            results.append(r)

    if "特休" in question or "特別休假" in question:
        r = calc_annual_leave(question)
        if r:
            results.append(r)

    if "時薪" in question:
        r = calc_hourly_wage(question)
        if r:
            results.append(r)

    if not results:
        return None

    lines = ["⚠️ 以下為系統精確計算結果，回答時請直接採用，不要自行重新計算："]
    for r in results:
        lines.append(f"\n【{r.calc_type.upper()}】{r.formula}")
        lines.append(f"法條依據：{r.legal_basis}")
        for step in r.steps:
            lines.append(f"  {step}")
        lines.append(f"✅ 最終答案：{r.result}")
    return "\n".join(lines)
