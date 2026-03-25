"""
UniHR 文件切片模板 (Document Chunk Templates)

根據 HR 文件的常見結構，偵測文件類型並提供最佳切片策略：
  - 員工手冊：按「第 X 章」、「第 X 條」邊界切分
  - 請假規定：按假別（特休、婚假、產假…）切分
  - 薪資 / 獎懲制度：按薪資組成項目切分
  - 績效考核：按 KPI 類別切分
  - 法規合約：按「第 X 條」切分

每個模板定義：
  - section_patterns: 用於偵測章節邊界的 regex 清單（依優先序）
  - atomic_patterns: 匹配到的區塊不可再拆分（如單條法規）
  - min_section_tokens: 該類文件章節的最小 token 數
  - metadata_extractor: 從章節標題萃取結構化 metadata
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Pattern

logger = logging.getLogger(__name__)


@dataclass
class ChunkTemplate:
    """單一文件類型的切片模板"""

    name: str  # 模板名稱（用於追蹤）
    detect_patterns: List[Pattern]  # 偵測此文件類型的 regex
    detect_threshold: int  # 至少命中幾個 pattern 才判定
    section_patterns: List[Pattern]  # 章節邊界 regex（依優先序）
    atomic_patterns: List[Pattern] = field(default_factory=list)  # 不可拆分區塊
    min_section_tokens: int = 80  # 章節最小 token 數
    merge_undersized: bool = True  # 是否合併過小章節
    priority: int = 0  # 優先級（結構型 > 主題型）


# ── 預定義模板 ──

_HANDBOOK_TEMPLATE = ChunkTemplate(
    name="employee_handbook",
    detect_patterns=[
        re.compile(r"第[一二三四五六七八九十百]+章", re.MULTILINE),
        re.compile(r"員工手冊|工作規則|管理辦法|服務規章", re.MULTILINE),
    ],
    detect_threshold=2,
    priority=10,  # 結構型模板優先：有「第X章」就是手冊
    section_patterns=[
        re.compile(r"(?:^|\n)(?=第[一二三四五六七八九十百]+章)"),  # 第X章
        re.compile(r"(?:^|\n)(?=第[一二三四五六七八九十百\d]+條)"),  # 第X條
        re.compile(r"(?:^|\n)(?=#{1,3}\s)"),  # Markdown 標題
    ],
    atomic_patterns=[
        re.compile(r"第[一二三四五六七八九十百\d]+條[^\n]*\n[\s\S]*?(?=第[一二三四五六七八九十百\d]+條|\Z)"),
    ],
    min_section_tokens=40,
)

_LEAVE_POLICY_TEMPLATE = ChunkTemplate(
    name="leave_policy",
    detect_patterns=[
        re.compile(r"請假|休假|假別|假期", re.MULTILINE),
        re.compile(r"特休|婚假|喪假|病假|產假|陪產假|生理假|公假|事假", re.MULTILINE),
    ],
    detect_threshold=3,
    section_patterns=[
        re.compile(r"(?:^|\n)(?=(?:一|二|三|四|五|六|七|八|九|十)[、.])"),  # 一、二、...
        re.compile(
            r"(?:^|\n)(?=(?:特休|婚假|喪假|病假|產假|陪產假|陪產檢假|生理假|公假|事假|家庭照顧假|育嬰留職停薪))"
        ),
        re.compile(r"(?:^|\n)(?=#{1,3}\s)"),
        re.compile(r"(?:^|\n)(?=第[一二三四五六七八九十百\d]+條)"),
    ],
    min_section_tokens=60,
)

_SALARY_TEMPLATE = ChunkTemplate(
    name="salary_structure",
    detect_patterns=[
        re.compile(r"薪資|薪酬|待遇|報酬", re.MULTILINE),
        re.compile(r"底薪|津貼|獎金|加班費|全勤|年終", re.MULTILINE),
    ],
    detect_threshold=3,
    section_patterns=[
        re.compile(r"(?:^|\n)(?=(?:一|二|三|四|五|六|七|八|九|十)[、.])"),
        re.compile(r"(?:^|\n)(?=#{1,3}\s)"),
        re.compile(r"(?:^|\n)(?=第[一二三四五六七八九十百\d]+條)"),
    ],
    min_section_tokens=60,
)

_PERFORMANCE_TEMPLATE = ChunkTemplate(
    name="performance_evaluation",
    detect_patterns=[
        re.compile(r"績效|考核|KPI|考績|評核", re.MULTILINE),
        re.compile(r"評分|等級|晉升|獎懲", re.MULTILINE),
    ],
    detect_threshold=3,
    section_patterns=[
        re.compile(r"(?:^|\n)(?=(?:一|二|三|四|五|六|七|八|九|十)[、.])"),
        re.compile(r"(?:^|\n)(?=#{1,3}\s)"),
    ],
    min_section_tokens=80,
)

_LEGAL_CONTRACT_TEMPLATE = ChunkTemplate(
    name="legal_contract",
    detect_patterns=[
        re.compile(r"勞動基準法|勞基法|勞工保險|就業服務法", re.MULTILINE),
        re.compile(r"第[一二三四五六七八九十百\d]+條", re.MULTILINE),
        re.compile(r"合約|契約|協議書", re.MULTILINE),
    ],
    detect_threshold=3,
    priority=10,  # 結構型模板優先
    section_patterns=[
        re.compile(r"(?:^|\n)(?=第[一二三四五六七八九十百\d]+條)"),
        re.compile(r"(?:^|\n)(?=#{1,3}\s)"),
    ],
    atomic_patterns=[
        re.compile(r"第[一二三四五六七八九十百\d]+條[^\n]*\n[\s\S]*?(?=第[一二三四五六七八九十百\d]+條|\Z)"),
    ],
    min_section_tokens=50,
)

# 模板清單（依偵測優先序排列）
TEMPLATES: List[ChunkTemplate] = [
    _LEAVE_POLICY_TEMPLATE,
    _SALARY_TEMPLATE,
    _PERFORMANCE_TEMPLATE,
    _HANDBOOK_TEMPLATE,  # 員工手冊放後面，因 detect_threshold 較低
    _LEGAL_CONTRACT_TEMPLATE,
]


def detect_template(text: str) -> Optional[ChunkTemplate]:
    """
    根據文件內容偵測最適合的切片模板。

    掃描前 3000 字元的關鍵字命中數，達到門檻即回傳對應模板。
    回傳 None 表示使用預設通用切片。
    """
    sample = text[:3000]
    best: Optional[ChunkTemplate] = None
    best_score = 0

    for tmpl in TEMPLATES:
        hits = 0
        for pattern in tmpl.detect_patterns:
            matches = pattern.findall(sample)
            hits += min(len(matches), 3)  # 每個 pattern 最多計 3 分
        if hits < tmpl.detect_threshold:
            continue
        # 優先級 > 分數（結構型模板優先於主題型）
        if (tmpl.priority, hits) > (best.priority if best else -1, best_score):
            best = tmpl
            best_score = hits

    if best:
        logger.info("文件模板偵測: %s（分數 %d）", best.name, best_score)
    return best


def split_by_template(
    text: str,
    template: ChunkTemplate,
) -> List[str]:
    """
    依模板的 section_patterns 切分文本為初始章節。

    回傳的 sections 清單已：
      1. 依模板邊界 regex 切分
      2. 過濾空白章節

    呼叫者（TextChunker）再負責 token 大小控制、overlap、合併。
    """
    if not text.strip():
        return []

    # 依優先序嘗試每個 section pattern
    for pattern in template.section_patterns:
        sections = pattern.split(text)
        non_empty = [s for s in sections if s.strip()]
        if len(non_empty) >= 2:
            logger.debug(
                "模板 %s 使用 pattern %s 切出 %d 段",
                template.name,
                pattern.pattern,
                len(non_empty),
            )
            return non_empty

    # 所有 pattern 都無法有效切分 → 回退到段落切分
    sections = text.split("\n\n")
    return [s for s in sections if s.strip()]


def extract_section_metadata(section_text: str, template_name: str) -> Dict[str, str]:
    """
    從章節文本萃取結構化 metadata。

    回傳 dict 包含：
      - template_name: 使用的模板名稱
      - section_title: 章節標題（若偵測到）
      - section_type: 章節類型分類
    """
    meta: Dict[str, str] = {"template_name": template_name}
    first_line = section_text.strip().split("\n")[0].strip()

    # 偵測「第 X 章」標題
    chapter = re.match(r"(第[一二三四五六七八九十百]+章\s*.+)", first_line)
    if chapter:
        meta["section_title"] = chapter.group(1).strip()
        meta["section_type"] = "chapter"
        return meta

    # 偵測「第 X 條」
    article = re.match(r"(第[一二三四五六七八九十百\d]+條\s*.+)", first_line)
    if article:
        meta["section_title"] = article.group(1).strip()
        meta["section_type"] = "article"
        return meta

    # Markdown 標題
    heading = re.match(r"(#{1,6})\s+(.+)", first_line)
    if heading:
        meta["section_title"] = heading.group(2).strip()
        meta["section_type"] = f"h{len(heading.group(1))}"
        return meta

    # 中文編號（一、二、...）
    cn_num = re.match(r"([一二三四五六七八九十][、.])\s*(.+)", first_line)
    if cn_num:
        meta["section_title"] = cn_num.group(2).strip()
        meta["section_type"] = "numbered_section"
        return meta

    # 假別關鍵字
    leave_type = re.match(
        r"(特休|婚假|喪假|病假|產假|陪產假|陪產檢假|生理假|公假|事假|家庭照顧假|育嬰留職停薪)",
        first_line,
    )
    if leave_type:
        meta["section_title"] = first_line[:50]
        meta["section_type"] = "leave_type"
        return meta

    meta["section_title"] = first_line[:60] if first_line else ""
    meta["section_type"] = "paragraph"
    return meta
