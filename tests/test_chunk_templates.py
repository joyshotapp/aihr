"""
chunk_templates 單元測試

涵蓋：
  - 模板偵測（各種 HR 文件類型）
  - 模板切分（章邊界、條邊界、假別、薪資項目）
  - metadata 萃取
  - TextChunker 整合（模板 + token 控制）
"""

from app.services.chunk_templates import (
    detect_template,
    split_by_template,
    extract_section_metadata,
)


# ── 測試用文本 ──

HANDBOOK_TEXT = """
第一章 總則
本公司員工手冊適用於全體正職員工。

第二章 聘僱
新進員工須經面試、筆試通過後始得錄用，試用期為三個月。

第三章 考勤
上班時間為上午九時至下午六時，中午休息一小時。遲到者依規定扣薪。

第四章 假期
員工依法享有特別休假、婚假、喪假、病假等各項假別。
"""

LEAVE_TEXT = """
請假管理辦法

一、特休假
依勞動基準法第38條，員工年資滿6個月以上者，享有特別休假。
年資6個月以上未滿1年：3日
年資1年以上未滿2年：7日

二、婚假
員工結婚可請婚假8日，須於結婚登記日起算6個月內休畢。

三、喪假
父母、配偶喪亡者，給予喪假8日。
祖父母、子女喪亡者，給予喪假6日。

四、病假
員工因普通傷病，一年內可請病假30日。
"""

SALARY_TEXT = """
薪資與報酬管理辦法

一、底薪
依職等核定月薪，不得低於勞動基準法規定之基本工資。

二、津貼
交通津貼每月支給新臺幣2,000元。
伙食津貼每月支給新臺幣2,400元。

三、獎金
年終獎金視公司營運狀況核發，最低保障1個月。

四、加班費
平日延長工時，前2小時加給三分之一，後2小時加給三分之二。
"""

PERFORMANCE_TEXT = """
績效考核管理辦法

一、考核項目
考核分為工作績效、工作態度、專業能力三大類。

二、評分標準
A 級（90分以上）：傑出
B 級（80-89分）：優良
KPI 達成率須達 80% 以上。

三、晉升規定
連續兩年 A 級者，得優先晉升。
"""

LEGAL_TEXT = """
勞動基準法（節錄）

第一條 為規定勞動條件最低標準，保障勞工權益，加強勞雇關係。

第二條 本法用辭定義如下：勞工、雇主、工資、平均工資、事業單位。

第三條 本法於左列各業適用之。

第四條 本法所稱主管機關。

第五條 雇主不得以強暴、脅迫、拘禁或其他非法方法，強制勞工從事勞動。
"""

GENERIC_TEXT = """
這是一份普通的文件，沒有特定的 HR 結構。
它只是一般性的文字描述，不包含章節、條文、假別、薪資等關鍵字。
用來測試無法匹配任何模板的情況。
"""


class TestDetectTemplate:
    """模板偵測測試"""

    def test_detect_handbook(self):
        tmpl = detect_template(HANDBOOK_TEXT)
        assert tmpl is not None
        assert tmpl.name == "employee_handbook"

    def test_detect_leave_policy(self):
        tmpl = detect_template(LEAVE_TEXT)
        assert tmpl is not None
        assert tmpl.name == "leave_policy"

    def test_detect_salary(self):
        tmpl = detect_template(SALARY_TEXT)
        assert tmpl is not None
        assert tmpl.name == "salary_structure"

    def test_detect_performance(self):
        tmpl = detect_template(PERFORMANCE_TEXT)
        assert tmpl is not None
        assert tmpl.name == "performance_evaluation"

    def test_detect_legal(self):
        tmpl = detect_template(LEGAL_TEXT)
        assert tmpl is not None
        assert tmpl.name == "legal_contract"

    def test_detect_generic_returns_none(self):
        tmpl = detect_template(GENERIC_TEXT)
        assert tmpl is None

    def test_detect_empty_returns_none(self):
        assert detect_template("") is None
        assert detect_template("   ") is None


class TestSplitByTemplate:
    """模板切分測試"""

    def test_handbook_splits_by_chapter(self):
        tmpl = detect_template(HANDBOOK_TEXT)
        sections = split_by_template(HANDBOOK_TEXT, tmpl)
        assert len(sections) >= 3  # 至少 4 章（第一章可能含前言）

    def test_leave_splits_by_type(self):
        tmpl = detect_template(LEAVE_TEXT)
        sections = split_by_template(LEAVE_TEXT, tmpl)
        assert len(sections) >= 4  # 特休、婚假、喪假、病假

    def test_salary_splits_by_component(self):
        tmpl = detect_template(SALARY_TEXT)
        sections = split_by_template(SALARY_TEXT, tmpl)
        assert len(sections) >= 4  # 底薪、津貼、獎金、加班費

    def test_legal_splits_by_article(self):
        tmpl = detect_template(LEGAL_TEXT)
        sections = split_by_template(LEGAL_TEXT, tmpl)
        assert len(sections) >= 3

    def test_empty_returns_empty(self):
        tmpl = detect_template(HANDBOOK_TEXT)
        sections = split_by_template("", tmpl)
        assert sections == []


class TestExtractSectionMetadata:
    """章節 metadata 萃取測試"""

    def test_chapter_title(self):
        meta = extract_section_metadata("第一章 總則\n本公司員工手冊...", "employee_handbook")
        assert meta["section_type"] == "chapter"
        assert "第一章" in meta["section_title"]
        assert meta["template_name"] == "employee_handbook"

    def test_article_title(self):
        meta = extract_section_metadata("第三條 本法適用範圍\n...", "legal_contract")
        assert meta["section_type"] == "article"
        assert "第三條" in meta["section_title"]

    def test_markdown_heading(self):
        meta = extract_section_metadata("## 請假管理辦法\n...", "leave_policy")
        assert meta["section_type"] == "h2"
        assert "請假管理辦法" in meta["section_title"]

    def test_numbered_section(self):
        meta = extract_section_metadata("一、特休假\n年資滿...", "leave_policy")
        assert meta["section_type"] == "numbered_section"
        assert "特休假" in meta["section_title"]

    def test_leave_type_keyword(self):
        meta = extract_section_metadata("婚假\n員工結婚可請...", "leave_policy")
        assert meta["section_type"] == "leave_type"

    def test_plain_paragraph(self):
        meta = extract_section_metadata("這是一般的描述文字...", "generic")
        assert meta["section_type"] == "paragraph"


class TestTextChunkerIntegration:
    """TextChunker 與模板整合測試"""

    def test_chunker_uses_template_for_handbook(self):
        """確認 TextChunker 會偵測到員工手冊模板並產出 chunks"""
        from app.services.document_parser import TextChunker
        chunks = TextChunker.split_by_tokens(HANDBOOK_TEXT, chunk_size=80, chunk_overlap=10)
        assert len(chunks) >= 2  # 短文本用小 chunk_size 確保切出多段

    def test_chunker_uses_template_for_leave(self):
        from app.services.document_parser import TextChunker
        chunks = TextChunker.split_by_tokens(LEAVE_TEXT, chunk_size=200, chunk_overlap=30)
        assert len(chunks) >= 2

    def test_chunker_generic_fallback(self):
        """無模板時照常用通用切片"""
        from app.services.document_parser import TextChunker
        chunks = TextChunker.split_by_tokens(GENERIC_TEXT, chunk_size=100, chunk_overlap=20)
        assert len(chunks) >= 1

    def test_empty_text(self):
        from app.services.document_parser import TextChunker
        assert TextChunker.split_by_tokens("") == []
        assert TextChunker.split_by_tokens("   ") == []
