"""Lean code → philosophical syllogism proposition translator.

Translates mechanically-generated Lean 4 expressions back into a human-readable
"major premise → minor premise → conclusion" syllogism, making the evolution
process legible as a philosophical argument.
"""

import re
import random
from typing import Optional


class SyllogismRenderer:
    """Renders Lean code as a philosophical syllogism (三段论).

    Each translation follows the form:

        大前提: <major premise>
        小前提: <minor premise>
        结论:   <conclusion>

    The mapping is heuristic and poetic -- it captures the philosophical
    spirit rather than providing a rigorous formal translation.
    """

    # ------------------------------------------------------------------
    # Pattern matchers (order matters: more specific first)
    # ------------------------------------------------------------------

    _PATTERNS: list[tuple[str, str, str, str]] = [
        # (regex, major_premise, minor_premise, conclusion)
        # --- Arithmetic ---
        (
            r"Nat\.add\s+(\S+)\s+(\S+)",
            "自然数对加法封闭",
            "{a} 与 {b} 皆为自然数",
            "{gene} 断言 {a}+{b} 为一自然数",
        ),
        (
            r"Nat\.mul\s+(\S+)\s+(\S+)",
            "自然数对乘法封闭",
            "{a} 与 {b} 皆为自然数",
            "{gene} 断言 {a}*{b} 为一自然数",
        ),
        (
            r"Nat\.sub\s+(\S+)\s+(\S+)",
            "自然数的截断减法为部分函数",
            "{a} 不小于 {b} 时差有定义",
            "{gene} 断言 {a}-{b} 为一自然数",
        ),
        (
            r"Nat\.succ\s+(\S+)",
            "每个自然数皆有唯一后继",
            "{a} 为一自然数",
            "{gene} 断言 {a} 的后继为一自然数",
        ),
        (
            r"Nat\.pred\s+(\S+)",
            "每个非零自然数皆有唯一前驱",
            "{a} 非零（否则前驱为0）",
            "{gene} 断言 {a} 的前驱为一自然数",
        ),
        (
            r"Nat\.pow\s+(\S+)\s+(\S+)",
            "自然数的幂运算封闭",
            "{a} 为底数，{b} 为指数",
            "{gene} 断言 {a}^{b} 为一自然数",
        ),
        (
            r"Nat\.(mod|div|min|max)\s+(\S+)\s+(\S+)",
            "自然数上的运算具有良定义性",
            "{a} 与 {b} 满足运算前提",
            "{gene} 断言该运算结果为一自然数",
        ),
        # --- Boolean ---
        (
            r"Bool\.(and|or)\s+(\S+)\s+(\S+)",
            "布尔代数对逻辑运算封闭",
            "{a} 与 {b} 各为布尔值",
            "{gene} 断言 {a} 与 {b} 的布尔运算结果可判定",
        ),
        (
            r"Bool\.not\s+(\S+)",
            "布尔代数对否定运算封闭",
            "{a} 为布尔值",
            "{gene} 断言非 {a} 可判定",
        ),
        # --- Equality ---
        (
            r"(\S+)\s*=\s*(\S+).*by\s+rfl",
            "等同性自反——任一表达式皆等于自身",
            "{a} 与 {b} 在定义上计算归约至同一范式",
            "{gene} 断言 {a} 等于 {b}——此命题自反性可证",
        ),
        (
            r"(\S+)\s*=\s*(\S+)",
            "等同性为类型论之基石关系",
            "{a} 与 {b} 为同类型之项",
            "{gene} 断言 {a} 等于 {b}",
        ),
        # --- Logic connectives ---
        (
            r"\bAnd\b.*?(\S+).*?(\S+)",
            "合取命题之真值条件——两 conjunct 皆须为真",
            "{a} 与 {b} 各自成立",
            "{gene} 断言 {a} 且 {b} 同时成立",
        ),
        (
            r"\bOr\b.*?(\S+).*?(\S+)",
            "析取命题之真值条件——至少一 disjunct 为真",
            "{a} 或 {b} 至少其一成立",
            "{gene} 断言 {a} 或 {b} 成立",
        ),
        (
            r"\bNot\b\s+(\S+)",
            "否定命题之真值条件——原命题导致矛盾",
            "{a} 若成立则导出荒谬",
            "{gene} 断言非 {a}",
        ),
        (
            r"\bIff\b\s+(\S+)\s+(\S+)",
            "等价关系之双向蕴含",
            "{a} 蕴含 {b} 且 {b} 蕴含 {a}",
            "{gene} 断言 {a} 当且仅当 {b}",
        ),
        # --- If-then-else ---
        (
            r"if\s+(\S+)\s+then\s+(\S+)\s+else\s+(\S+)",
            "排中律——任一命题或真或假",
            "条件 {a} 可判定",
            "{gene} 依 {a} 之真伪在 {b} 与 {c} 间择一",
        ),
        # --- Lambda / fun ---
        (
            r"(?:fun|λ)\s+(\S+)\s*=>\s*(.+)",
            "函数类型的构造规则——对任意输入给出唯一输出",
            "对任意 {a}，{b} 为合法项",
            "{gene} 定义了一个从 {a} 到 {b} 的映射",
        ),
        # --- match ---
        (
            r"match\s+(\S+)\s+with",
            "自然数的归纳原理——基例与归纳步",
            "对 {a} 之每一构造子皆有对应分支",
            "{gene} 以结构递归定义了一个函数",
        ),
        # --- List operations ---
        (
            r"List\.map\s+(\S+)\s+(\S+)",
            "函子映射保持列表结构",
            "{a} 为一函数，{b} 为一列表",
            "{gene} 断言将 {a} 应用于 {b} 之每一元素仍得列表",
        ),
        (
            r"List\.filter\s+(\S+)\s+(\S+)",
            "筛选命题保持列表类型",
            "{a} 为一谓词，{b} 为一列表",
            "{gene} 断言筛选后之元素仍构成列表",
        ),
        (
            r"List\.foldl\s+(\S+)\s+(\S+)\s+(\S+)",
            "左折叠为列表上的泛型聚合算子",
            "{a} 为二元函数，{b} 为初始值，{c} 为列表",
            "{gene} 断言左折叠之结果类型良构",
        ),
        (
            r"List\.length\s+(\S+)",
            "列表长度为一自然数",
            "{a} 为有限列表",
            "{gene} 断言 {a} 之长度为自然数",
        ),
        (
            r"List\.append\s+(\S+)\s+(\S+)",
            "列表拼接保持列表类型",
            "{a} 与 {b} 各为列表",
            "{gene} 断言拼接结果仍为列表",
        ),
        (
            r"List\.reverse\s+(\S+)",
            "列表反转保持列表类型与长度",
            "{a} 为有限列表",
            "{gene} 断言反转后仍为列表",
        ),
        # --- let / have ---
        (
            r"\blet\s+(\S+)\s*:=\s*(.+?)\s*;",
            "let 绑定引入局部定义",
            "{a} 被绑定为 {b}",
            "{gene} 在 {a}={b} 的上下文中构造后续表达式",
        ),
        # --- sorry (admit) ---
        (
            r"\bsorry\b",
            "任何命题皆可被 sorry 占据——此乃形式系统中的信仰之跃",
            "人类尚未给出该命题之证明",
            "{gene} 以 sorry 悬置该命题——待后人来证",
        ),
    ]

    # Fallback template
    _FALLBACK = (
        "类型论的基本构造法则",
        "所有子项类型良构",
        "{gene} 为合法 Lambda 项",
    )

    # Poetic flourishes for variation
    _FLOURISHES: list[str] = [
        "——此即数之大道也",
        "——逻辑之轮至此又转一齿",
        "——演化之河在此分叉",
        "——形式系统欣然接纳此子",
        "——瓮中又添一石",
        "——真理之树又生一枝",
        "——类型之网捕获此式",
        "",
    ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render(self, code: str, gene_name: str) -> str:
        """Translate Lean code into a philosophical syllogism.

        Args:
            code: The Lean 4 source code.
            gene_name: The gene identifier (e.g. 'gene_42').

        Returns:
            A multi-line string in syllogism form.
        """
        # Collapse whitespace for pattern matching
        flat = " ".join(code.split())

        for pattern, major, minor, conclusion in self._PATTERNS:
            m = re.search(pattern, flat)
            if m:
                groups = m.groups()
                major = self._fill(major, gene_name, groups)
                minor = self._fill(minor, gene_name, groups)
                conclusion = self._fill(conclusion, gene_name, groups)
                return self._format(major, minor, conclusion)

        # Fallback
        major, minor, conclusion = self._FALLBACK
        major = self._fill(major, gene_name, ())
        minor = self._fill(minor, gene_name, ())
        conclusion = self._fill(conclusion, gene_name, ())
        return self._format(major, minor, conclusion)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fill(
        self, template: str, gene_name: str, groups: tuple[str, ...]
    ) -> str:
        """Substitute placeholders in a template string.

        {gene} → gene_name
        {a}, {b}, {c} → groups[0], groups[1], groups[2]
        """
        result = template.replace("{gene}", gene_name)
        for i, g in enumerate(groups):
            result = result.replace(f"{{{chr(97+i)}}}", g)
        return result

    def _format(self, major: str, minor: str, conclusion: str) -> str:
        """Assemble the final syllogism string with optional flourish."""
        flourish = random.choice(self._FLOURISHES)
        lines = [
            f"  大前提: {major}",
            f"  小前提: {minor}",
            f"  结论:   {conclusion}",
        ]
        if flourish:
            lines.append(f"         {flourish}")
        return "\n".join(lines)
