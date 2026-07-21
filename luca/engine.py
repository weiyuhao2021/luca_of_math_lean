"""Main Evolution Loop -- the LUCA evolutionary engine with catastrophe system."""

import concurrent.futures
import json
import math
import os
import random
import re
import tempfile
import time
from typing import Optional

from luca.config import (
    MAX_URN_SIZE,
    INNOVATION_RATE,
    DECAY_RATE,
    CATASTROPHE_BASE_P,
    CATASTROPHE_SIZE_EXPONENT,
    CATASTROPHE_MIN_INTERVAL,
    MAX_EXPRESSION_TOKENS,
    EVOLUTION_OUTPUT_FILE,
    URN_STATE_FILE,
    EVOLUTION_LOG_FILE,
)
from luca.urn import PolyaUrn
from luca.grammar import LeanAssembler
from luca.physics import LeanSandbox
from luca.pruner import Pruner
from luca.syllogism import SyllogismRenderer

# Rich is optional but highly recommended for colored output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.live import Live
    from rich.layout import Layout
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False


# ---------------------------------------------------------------------------
# Catastrophe definitions
# ---------------------------------------------------------------------------

_CATASTROPHE_NAMES: dict[str, str] = {
    "mass_extinction": "质量灭绝",
    "moderate_extinction": "中等灭绝",
    "genetic_drift": "基因漂变",
    "cambrian_explosion": "寒武纪大爆发",
    "asteroid_impact": "小行星撞击",
    "ice_age": "冰河期",
}

_CATASTROPHE_DESCRIPTIONS: dict[str, str] = {
    "mass_extinction": "环境剧变——低权重 token 被大量清除，仅强者幸存",
    "moderate_extinction": "生态收缩——弱势 token 批量消亡，中等阶层面临洗牌",
    "genetic_drift": "种群瓶颈——所有基因权重向均值回归，多样性骤降",
    "cambrian_explosion": "共生大爆发——存活基因两两杂交，新复合 token 涌现",
    "asteroid_impact": "天外撞击——随机半数基因湮灭，幸存者获得超强选择优势",
    "ice_age": "冰河降临——万物凋零，唯抽象结构（fun/λ/match）独享抗冻加成",
}


def _apply_catastrophe(urn: PolyaUrn, catastrophe_type: str) -> str:
    """Apply a catastrophe to the urn and return a human-readable description."""
    weights = urn.weights

    if catastrophe_type == "mass_extinction":
        # Remove 80-90% of the lowest-weight tokens (per calibration: 大灭绝须彻底)
        fraction = random.uniform(0.8, 0.9)
        sorted_items = sorted(weights.items(), key=lambda x: x[1])
        kill_count = max(1, int(len(sorted_items) * fraction))
        for t, _ in sorted_items[:kill_count]:
            del weights[t]
        return f"大灭绝——移除 {kill_count} 个低权重 token（{fraction:.0%}），仅强者幸存"

    elif catastrophe_type == "moderate_extinction":
        # Remove 40-60% of the lowest-weight tokens (中等生态危机)
        fraction = random.uniform(0.4, 0.6)
        sorted_items = sorted(weights.items(), key=lambda x: x[1])
        kill_count = max(1, int(len(sorted_items) * fraction))
        for t, _ in sorted_items[:kill_count]:
            del weights[t]
        # Survivors get a modest boost (selection pressure)
        for t in weights:
            weights[t] *= random.uniform(1.1, 1.5)
        return f"中等灭绝——清除 {kill_count} 个 token（{fraction:.0%}），幸存者权重增强"

    elif catastrophe_type == "genetic_drift":
        # Regress all weights toward the mean by 30%
        if not weights:
            return "瓮已空，无漂变可施"
        mean_w = sum(weights.values()) / len(weights)
        for t in list(weights.keys()):
            weights[t] = weights[t] * 0.7 + mean_w * 0.3
        return f"所有权重向均值 {mean_w:.2f} 回归 30%"

    elif catastrophe_type == "cambrian_explosion":
        # Combine pairs of high-weight tokens into new compound tokens
        top_tokens = sorted(weights.items(), key=lambda x: -x[1])
        top_n = min(20, len(top_tokens))
        top_items = top_tokens[:top_n]
        new_tokens = 0
        for i in range(min(10, len(top_items))):
            for j in range(i + 1, min(10, len(top_items))):
                if random.random() < 0.3:
                    a, b = top_items[i][0], top_items[j][0]
                    new_name = f"{a}_{b}"
                    if new_name not in weights:
                        avg_w = (weights[a] + weights[b]) / 2 * 0.5
                        weights[new_name] = avg_w
                        new_tokens += 1
        return f"杂交生成 {new_tokens} 个新复合 token"

    elif catastrophe_type == "asteroid_impact":
        # Randomly delete 50% of tokens, double weight of survivors
        all_tokens = list(weights.keys())
        kill_count = max(1, len(all_tokens) // 2)
        victims = set(random.sample(all_tokens, kill_count))
        for t in victims:
            del weights[t]
        for t in weights:
            weights[t] *= 2.0
        return f"湮灭 {kill_count} 个 token，幸存者权重翻倍"

    elif catastrophe_type == "ice_age":
        # Halve all weights, but fun/λ/match/def get a bonus
        cold_resistant = {"fun", "λ", "match", "def", "theorem", "let", "have"}
        for t in list(weights.keys()):
            if t in cold_resistant:
                weights[t] *= 1.5  # Anti-freeze bonus
            else:
                weights[t] *= 0.5
            if weights[t] < 0.1:
                del weights[t]
        return "抽象构造 token（fun/λ/match/def）获得抗冻加成，其余权重减半"

    return "未知天灾"


# ---------------------------------------------------------------------------
# Evolution Engine
# ---------------------------------------------------------------------------

class EvolutionEngine:
    """Orchestrates the continuous open-ended evolution loop.

    The loop follows the Pólya urn reinforcement cycle:

    1. Sample tokens from urn
    2. Assemble Lean candidate via grammar
    3. Verify with Lean compiler (physics)
    4. If alive: reinforce, innovate, log, prune
    5. If dead: discard, slight penalty
    6. Occasionally trigger random catastrophes
    """

    def __init__(
        self,
        max_generations: int = 10_000,
        lean_timeout: Optional[float] = None,
        output_file: Optional[str] = None,
        resume: bool = False,
        workers: int = 8,
        seed_file: Optional[str] = None,
    ) -> None:
        self.max_generations = max_generations
        self._workers = max(1, workers)
        self.output_file = output_file or EVOLUTION_OUTPUT_FILE

        # Modules
        self.urn = PolyaUrn()
        self.assembler = LeanAssembler()
        self.sandbox = LeanSandbox()
        self.pruner = Pruner()
        self.renderer = SyllogismRenderer()

        # State
        self.generation: int = 0
        self.alive_count: int = 0
        self.dead_count: int = 0
        self.start_time: float = 0.0
        self._running: bool = False
        self._catastrophe_timer: int = random.randint(50, 200)
        self._last_catastrophe_gen: int = 0   # For minimum interval enforcement

        # --- Evolution event trackers ---
        self._tainted_genes: set[str] = set()       # Genes containing/depending on sorry
        self._living_genes: list[dict] = []    # [{"name":..., "code":...}, ...] parent survivors
        self._multicellular_count: int = 0          # Genes that reference other gene_N
        self._era: str = "太古宙"                   # Current evolutionary era
        self._era_transitions: list[tuple[int, str, str]] = []  # (gen, from_era, to_era)

        # --- Library cache for compilation context ---
        self._library_cache: str = ""  # Contents of evolved_library.lean

        # Rich console
        self.console = Console() if _HAS_RICH else None

        # Resume from previous state
        if resume:
            self._load_state()
        elif seed_file:
            self._init_seed(seed_file)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the evolution loop."""
        self._print_banner()

        if not self.sandbox.is_lean_available():
            self._print_error(
                "Lean 4 compiler ('lean') not found on PATH.\n"
                "Install Lean 4: https://lean-lang.org/lean4/doc/setup.html\n"
                "Then ensure 'lean' is on your PATH and try again."
            )
            return

        self._running = True
        self.start_time = time.perf_counter()

        # Save initial state so files exist from the start
        self._save_state()

        try:
            while self._running and self.generation < self.max_generations:
                self._step()
        except KeyboardInterrupt:
            self._print_warning("\n演化被用户中断。")
        finally:
            self._save_state()
            self._print_summary()

    def stop(self) -> None:
        """Gracefully stop the evolution loop."""
        self._running = False

    # ------------------------------------------------------------------
    # Single generation step
    # ------------------------------------------------------------------

    def _step(self) -> None:
        """Execute one generation: parent reproduction + primordial soup.

        ~70% of candidates come from parent copy/mutation (genetic continuity).
        ~30% come from weighted urn sampling (non-Markovian historical memory).
        The urn preserves token weights across all of evolutionary history,
        enabling convergent evolution and re-discovery of extinct patterns.
        """
        batch: list[tuple[list[str], str, str]] = []

        # --- Parent reproduction (always, if parents exist) ---
        if self._living_genes:
            gene_pool = [t for t in self.urn.weights
                         if re.match(r"^(gene_\d+|luca|I|K|S)$", t)]
            for parent in self._living_genes:
                p_name = parent["name"]
                p_code = parent["code"]
                # 1 exact copy (new name)
                self.assembler._gene_counter += 1
                c_name = f"gene_{self.assembler._gene_counter}"
                c_code = p_code.replace(p_name, c_name)
                if not self.pruner.is_duplicate(c_code):
                    batch.append(([], c_code, c_name))
                # 1-2 mutated copies
                for _ in range(random.randint(1, 2)):
                    self.assembler._gene_counter += 1
                    c_name = f"gene_{self.assembler._gene_counter}"
                    c_code = self._mutate_code(p_code, p_name, c_name, gene_pool)
                    if not self.pruner.is_duplicate(c_code):
                        batch.append(([], c_code, c_name))

        # --- Primordial soup: ~30% from historical urn memory ---
        # The urn is the non-Markovian record; even extinct lineages
        # can be partially rediscovered through convergent assembly.
        soup_count = max(1, int(self.urn.size() * 0.3))
        for _ in range(soup_count):
            k = random.randint(3, MAX_EXPRESSION_TOKENS)
            tokens = self.urn.sample(k)
            code, gene_name = self.assembler.assemble(tokens)
            if not self.pruner.is_duplicate(code):
                batch.append((tokens, code, gene_name))

        # Parallel Lean verification
        new_living: list[dict] = []
        if batch:
            lib = self._library_cache
            workers = min(len(batch), self._workers)
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
                future_map = {
                    pool.submit(
                        self.sandbox.verify, code, gene_name, lib
                    ): (tokens, code, gene_name)
                    for tokens, code, gene_name in batch
                }
                for future in concurrent.futures.as_completed(future_map):
                    tokens, code, gene_name = future_map[future]
                    result = future.result()
                    alive_code = self._handle_candidate(tokens, code, gene_name, result)
                    if alive_code:
                        new_living.append({"name": gene_name, "code": alive_code})

        self._living_genes = new_living

        # Catastrophe check
        self._catastrophe_timer -= 1
        if self._catastrophe_timer <= 0:
            urn_ratio = self.urn.size() / max(1, MAX_URN_SIZE)
            p_catastrophe = CATASTROPHE_BASE_P * (urn_ratio ** CATASTROPHE_SIZE_EXPONENT)
            if random.random() < p_catastrophe:
                self._trigger_catastrophe("热力学灾变")
                self._last_catastrophe_gen = self.generation
            self._catastrophe_timer = CATASTROPHE_MIN_INTERVAL

        # Per-generation maintenance
        if self.generation % 10 == 0:
            self.urn.decay(DECAY_RATE)
        if self.generation % 5 == 0 and self.urn.size() > 0:
            for t in self.urn.weights:
                self.urn.weights[t] *= 0.99
        self.pruner.prune_urn(self.urn, MAX_URN_SIZE)

        # Periodic state save
        if self.generation % 50 == 0:
            self._save_state()

        # Commit generation
        self.generation += 1

    # ------------------------------------------------------------------
    # Mutation operators (blind string manipulation)
    # ------------------------------------------------------------------

    def _mutate_code(
        self, parent_code: str, parent_name: str,
        child_name: str, gene_pool: list[str],
    ) -> str:
        """Create a mutated child: token swap/insert + 10% endosymbiosis."""
        code = parent_code.replace(parent_name, child_name)
        tokens = code.split()
        if not tokens:
            return code
        urn_tokens = list(self.urn.weights.keys())
        if not urn_tokens:
            return code
        pos = random.randint(0, len(tokens) - 1)
        if random.random() < 0.5:
            tokens[pos] = random.choice(urn_tokens)
        else:
            tokens.insert(pos, random.choice(urn_tokens))
        if random.random() < 0.10 and gene_pool:
            pos2 = random.randint(0, len(tokens) - 1)
            tokens.insert(pos2, random.choice(gene_pool))
        return " ".join(tokens)

    # ------------------------------------------------------------------
    # Per-candidate result handler
    # ------------------------------------------------------------------

    def _handle_candidate(
        self, tokens: list[str], code: str, gene_name: str, result
    ) -> Optional[str]:
        """Process a single candidate's Lean verification result.

        Returns the gene's source code if alive, None if dead."""
        if result.alive:
            # --- Sorry detection ---
            has_sorry = "sorry" in code

            # --- Taint propagation ---
            referenced_genes = set(re.findall(r"\bgene_\d+\b", code))
            referenced_genes.discard(gene_name)
            is_tainted = has_sorry or bool(referenced_genes & self._tainted_genes)
            if is_tainted:
                self._tainted_genes.add(gene_name)

            penalty = self.pruner.metabolic_penalty(code)
            self.urn.reinforce(tokens, count=penalty)
            self.urn.innovate(gene_name)
            self.alive_count += 1

            self._detect_events(code, gene_name, tokens)
            self._append_to_library(code, gene_name)
            self._library_cache = self._load_library_cache()
            self._log_alive(gene_name, code, result, penalty, is_tainted)
            self._write_log_entry(gene_name, code, "ALIVE", is_tainted)
            return code
        else:
            self.dead_count += 1
            self.pruner.record_code(code)
            self._log_dead(gene_name, code, "COMPILE_ERROR")
            self._write_log_entry(gene_name, code, "DEAD", False)
            return None

    # ------------------------------------------------------------------
    # Catastrophe system
    # ------------------------------------------------------------------

    def _trigger_catastrophe(self, reason: str = "定时触发") -> None:
        """Randomly select and apply a catastrophe."""
        ctype = random.choice(list(_CATASTROPHE_NAMES.keys()))
        name = _CATASTROPHE_NAMES[ctype]
        desc = _CATASTROPHE_DESCRIPTIONS[ctype]
        detail = _apply_catastrophe(self.urn, ctype)

        # Detect era transition after catastrophe
        self._check_era_transition()

        if self.console:
            panel = Panel(
                f"[bold red]╔══════════════════════════════════════╗[/bold red]\n"
                f"[bold red]║[/bold red]  [bold yellow]天灾降临: {name}[/bold yellow]  [dim]({reason})[/dim]\n"
                f"[bold red]║[/bold red]  {desc}\n"
                f"[bold red]║[/bold red]  {detail}\n"
                f"[bold red]║[/bold red]  [dim]当前纪元: {self._era}[/dim]\n"
                f"[bold red]╚══════════════════════════════════════╝[/bold red]",
                border_style="red",
            )
            self.console.print(panel)
        else:
            print(f"\n!!! 天灾: {name} ({reason}) — {desc} ({detail})\n")

    # ------------------------------------------------------------------
    # Evolution event detection
    # ------------------------------------------------------------------

    def _detect_events(self, code: str, gene_name: str, tokens: list[str]) -> None:
        """Detect milestone evolution events in newly compiled code.

        Tracks:
        - Multicellularity: gene composes with other gene_N
        - Sorry ratio: monitor for Great Oxidation Event
        """
        # --- Multicellular detection: does code reference other gene_N? ---
        referenced_genes = re.findall(r"\bgene_\d+\b", code)
        other_genes = [g for g in referenced_genes if g != gene_name]
        if other_genes:
            self._multicellular_count += 1
            self._print_multicellular_event(gene_name, code, other_genes)

        # --- Track sorry usage for Great Oxidation Event ---
        # (era transition is checked in _check_era_transition)

    def _check_era_transition(self) -> None:
        """Check if the system has crossed an evolutionary era boundary."""
        total = self.alive_count + self.dead_count
        if total < 50:
            return  # Not enough data

        # Calculate sorry ratio from urn weights
        sorry_keywords = {"sorry"}
        sorry_weight = sum(
            self.urn.weights.get(t, 0.0) for t in sorry_keywords if t in self.urn.weights
        )
        total_weight = self.urn.total_weight()
        sorry_ratio = sorry_weight / max(1.0, total_weight)

        # Count gene tokens in urn (evidence of multicellular building blocks)
        gene_tokens = [t for t in self.urn.weights if re.match(r"^gene_\d+$", t)]
        gene_count = len(gene_tokens)

        new_era = self._era
        if self._era == "太古宙":
            # Transition to 原初汤时代: first gene tokens appear
            if gene_count >= 3 and self._multicellular_count >= 1:
                new_era = "原初汤时代"
        elif self._era == "原初汤时代":
            # Transition to 大氧化时代: sorry dominates (>50%) and multicellular > 5
            if sorry_ratio > 0.5 and self._multicellular_count >= 2:
                new_era = "大氧化时代"
        elif self._era == "大氧化时代":
            # Transition to 真核时代: sorry drops below 20%
            if sorry_ratio < 0.2 and gene_count >= 10:
                new_era = "真核时代"
        elif self._era == "真核时代":
            # Transition to 多细胞时代: lots of gene references
            if self._multicellular_count >= 10 and gene_count >= 30:
                new_era = "多细胞时代"

        if new_era != self._era:
            old_era = self._era
            self._era = new_era
            self._era_transitions.append((self.generation, old_era, new_era))
            self._print_era_transition(old_era, new_era, sorry_ratio, gene_count)

    def _print_multicellular_event(
        self, gene_name: str, code: str, other_genes: list[str]
    ) -> None:
        """Print a multicellularity detection event."""
        code_short = code.replace("\n", " ").strip()
        if len(code_short) > 100:
            code_short = code_short[:97] + "..."

        genes_str = ", ".join(other_genes[:5])
        if len(other_genes) > 5:
            genes_str += f" ... (+{len(other_genes)-5})"

        if self.console:
            self.console.print(
                f"  [bold magenta]🧬 多细胞化![/bold magenta] "
                f"{gene_name} 共生基因: [cyan]{genes_str}[/cyan]"
            )
        else:
            print(f"  🧬 多细胞化! {gene_name} 共生基因: {genes_str}")

    def _print_era_transition(
        self, old_era: str, new_era: str, sorry_ratio: float, gene_count: int
    ) -> None:
        """Print a major era transition milestone."""
        if self.console:
            panel = Panel(
                f"[bold green]╔══════════════════════════════════════╗[/bold green]\n"
                f"[bold green]║[/bold green]  [bold yellow]🔥 纪元更迭![/bold yellow]\n"
                f"[bold green]║[/bold green]  {old_era} → [bold cyan]{new_era}[/bold cyan]\n"
                f"[bold green]║[/bold green]  Sorry 占比: {sorry_ratio:.1%} | 基因 Token: {gene_count}\n"
                f"[bold green]║[/bold green]  多细胞事件: {self._multicellular_count}\n"
                f"[bold green]╚══════════════════════════════════════╝[/bold green]",
                border_style="green",
            )
            self.console.print(panel)
        else:
            print(f"\n🔥 纪元更迭! {old_era} → {new_era}")
            print(f"   Sorry 占比: {sorry_ratio:.1%} | 基因 Token: {gene_count}")
            print(f"   多细胞事件: {self._multicellular_count}\n")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _print_banner(self) -> None:
        """Print welcome banner."""
        banner = r"""
╔══════════════════════════════════════════════════════════╗
║         luca_of_math_lean  — 数学演化内核 v0.1            ║
║  零 API 成本 · Pólya 瓮动力学 · Lean 4 物理定律           ║
╚══════════════════════════════════════════════════════════╝
"""
        if self.console:
            self.console.print(banner, style="bold cyan")
        else:
            print(banner)

    def _log_alive(
        self, gene_name: str, code: str, result, penalty: float,
        is_tainted: bool = False,
    ) -> None:
        """Log a successful compilation."""
        code_short = code.replace("\n", " ").strip()
        if len(code_short) > 80:
            code_short = code_short[:77] + "..."

        # Detect if this gene is multicellular
        other_refs = re.findall(r"\bgene_\d+\b", code)
        is_multicellular = any(g != gene_name for g in other_refs)
        multi_tag = " [🧬多细胞]" if is_multicellular else ""

        # Lineage tag
        if is_tainted:
            alive_tag = "[ALIVE★]"  # axiomatic lineage
            lineage = "公理化谱系"
        else:
            alive_tag = "[ALIVE]"   # closed lineage
            lineage = "封闭谱系"

        syllogism = self.renderer.render(code, gene_name)

        if self.console:
            self.console.print(
                f"[bold cyan][LUCA Epoch {self.generation:05d}][/bold cyan] "
                f"[green]SAMPLING → CHECKING LEAN... {alive_tag}{multi_tag}[/green] "
                f"({result.elapsed_ms:.0f}ms)"
            )
            self.console.print(f"  [dim]└─ Code:[/dim] {code_short}")
            self.console.print(f"  [dim]└─[/dim] [green]{syllogism}[/green]")
            self.console.print(
                f"  [dim]└─ Urn: {self.urn.size()} tokens | "
                f"Alive={self.alive_count} Dead={self.dead_count} | "
                f"纪元: [yellow]{self._era}[/yellow] | {lineage}[/dim]"
            )
        else:
            print(f"[LUCA Epoch {self.generation:05d}] SAMPLING → CHECKING LEAN... {alive_tag}{multi_tag} ({result.elapsed_ms:.0f}ms)")
            print(f"  └─ Code: {code_short}")
            print(f"  └─ {syllogism}")
            print(f"  └─ Urn: {self.urn.size()} tokens | Alive={self.alive_count} Dead={self.dead_count} | 纪元: {self._era} | {lineage}")

    def _log_dead(self, gene_name: str, code: str, reason: str) -> None:
        """Log a failed compilation."""
        code_short = code.replace("\n", " ").strip()
        if len(code_short) > 80:
            code_short = code_short[:77] + "..."

        if self.console:
            self.console.print(
                f"[bold cyan][LUCA Epoch {self.generation:05d}][/bold cyan] "
                f"[red]SAMPLING → CHECKING LEAN... [DEAD][/red] "
                f"[dim]({reason})[/dim]"
            )
            self.console.print(f"  [dim]└─ Code:[/dim] {code_short}")
        else:
            print(f"[LUCA Epoch {self.generation:05d}] SAMPLING → CHECKING LEAN... [DEAD] ({reason})")
            print(f"  └─ Code: {code_short}")

    def _print_error(self, msg: str) -> None:
        """Print an error message."""
        if self.console:
            self.console.print(f"[bold red]ERROR:[/bold red] {msg}")
        else:
            print(f"ERROR: {msg}")

    def _print_warning(self, msg: str) -> None:
        """Print a warning."""
        if self.console:
            self.console.print(f"[yellow]{msg}[/yellow]")
        else:
            print(msg)

    def _print_summary(self) -> None:
        """Print final evolution statistics."""
        elapsed = time.perf_counter() - self.start_time
        top_tokens = self.urn.top(10)

        if self.console:
            self.console.print("\n" + "=" * 60)
            self.console.print("[bold]演化终止 — 最终统计[/bold]")
            self.console.print(f"  总代数:     {self.generation}")
            self.console.print(f"  存活:       [green]{self.alive_count}[/green]")
            self.console.print(f"  消亡:       [red]{self.dead_count}[/red]")
            survival_rate = (
                self.alive_count / max(1, self.alive_count + self.dead_count) * 100
            )
            self.console.print(f"  存活率:     {survival_rate:.1f}%")
            self.console.print(f"  瓮中 Token: {self.urn.size()}")
            self.console.print(f"  当前纪元:   [yellow]{self._era}[/yellow]")
            self.console.print(f"  封闭谱系:   [green]{self.alive_count - len(self._tainted_genes)}[/green]")
            self.console.print(f"  公理化谱系: [yellow]{len(self._tainted_genes)}[/yellow]  (含/依赖sorry)")
            self.console.print(f"  多细胞事件: {self._multicellular_count}")
            self.console.print(f"  耗时:       {elapsed:.1f}s")

            if self._era_transitions:
                self.console.print("\n[bold]纪元更迭史:[/bold]")
                for gen, fr, to in self._era_transitions:
                    self.console.print(f"  第{gen:06d}代: {fr} → [cyan]{to}[/cyan]")

            if top_tokens:
                self.console.print("\n[bold]权重 TOP 10:[/bold]")
                for t, w in top_tokens:
                    self.console.print(f"  {t:30s} {w:.2f}")
            self.console.print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("演化终止 — 最终统计")
            print(f"  总代数:     {self.generation}")
            print(f"  存活:       {self.alive_count}")
            print(f"  消亡:       {self.dead_count}")
            print(f"  瓮中 Token: {self.urn.size()}")
            print(f"  当前纪元:   {self._era}")
            print(f"  封闭谱系:   {self.alive_count - len(self._tainted_genes)}")
            print(f"  公理化谱系: {len(self._tainted_genes)}  (含/依赖sorry)")
            print(f"  多细胞事件: {self._multicellular_count}")
            print(f"  耗时:       {elapsed:.1f}s")
            if self._era_transitions:
                print("\n纪元更迭史:")
                for gen, fr, to in self._era_transitions:
                    print(f"  第{gen:06d}代: {fr} → {to}")
            if top_tokens:
                print("\n权重 TOP 10:")
                for t, w in top_tokens:
                    print(f"  {t:30s} {w:.2f}")
            print("=" * 60)

    # ------------------------------------------------------------------
    # Seed initialization (the First Cause)
    # ------------------------------------------------------------------

    def _init_seed(self, seed_path: str) -> None:
        """Compile a seed .lean file and inject its genes as ancestral tokens.

        The seed file is verified by Lean, appended to evolved_library.lean,
        and each defined name becomes a token in the urn.  This provides
        a LUCA (Last Universal Common Ancestor) for evolution to build on,
        rather than starting from random noise alone.
        """
        if not os.path.isfile(seed_path):
            self._print_error(f"Seed file not found: {seed_path}")
            return

        with open(seed_path, "r", encoding="utf-8") as f:
            seed_code = f.read()

        # Verify the seed compiles
        result = self.sandbox.verify(seed_code, "genesis_seed")
        if not result.alive:
            self._print_error(
                f"Seed file '{seed_path}' failed Lean verification.\n"
                f"The seed must be valid Lean 4 code.\n"
                f"Lean error: {result.stderr[:200]}"
            )
            return

        # Extract gene names (def / theorem / lemma / example)
        gene_names: list[str] = re.findall(
            r"^\s*(?:def|theorem|lemma|example)\s+(\w+)",
            seed_code, re.MULTILINE,
        )
        if not gene_names:
            self._print_error("Seed file contains no def/theorem/lemma/example declarations.")
            return

        # Append seed to library
        self._append_to_library(seed_code, "genesis_seed")
        self._library_cache = self._load_library_cache()

        # Inject each gene name as a token into the urn
        for name in gene_names:
            self.urn.weights[name] = self.urn.weights.get(name, 0.0) + INNOVATION_RATE

        if self.console:
            self.console.print(
                f"[green]创世完成: 注入 {len(gene_names)} 个祖先基因"
                f" ({', '.join(gene_names)})[/green]"
            )
        else:
            print(f"创世完成: 注入 {len(gene_names)} 个祖先基因 ({', '.join(gene_names)})")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _write_log_entry(
        self, gene_name: str, code: str, status: str, is_tainted: bool = False
    ) -> None:
        """Append one JSON line to evolution_log.jsonl."""
        entry = {
            "generation": self.generation,
            "gene": gene_name,
            "status": status,
            "tainted": is_tainted,
            "urn_size": self.urn.size(),
        }
        try:
            with open(EVOLUTION_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def _append_to_library(self, code: str, gene_name: str) -> None:
        """Append a successfully verified definition to the evolved library."""
        header = f"\n-- [{self.generation:05d}] {gene_name} (ALIVE)\n"
        try:
            with open(self.output_file, "a", encoding="utf-8") as f:
                f.write(header)
                f.write(code + "\n")
        except OSError:
            pass

    def _save_state(self) -> None:
        """Save urn state to JSON for resumption (atomic write for crash safety)."""
        state = {
            "generation": self.generation,
            "alive_count": self.alive_count,
            "dead_count": self.dead_count,
            "urn": self.urn.to_dict(),
            "last_alive_generation": self._last_catastrophe_gen,
            "multicellular_count": self._multicellular_count,
            "tainted_genes": list(self._tainted_genes),
            "era": self._era,
            "era_transitions": self._era_transitions,
        }
        try:
            # Atomic write: write to temp file first, then rename.
            # This prevents corruption if the process crashes mid-write.
            dirname = os.path.dirname(URN_STATE_FILE) or "."
            fd, tmp_path = tempfile.mkstemp(
                suffix=".json", prefix="urn_state_", dir=dirname
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
                os.replace(tmp_path, URN_STATE_FILE)
            except Exception:
                # Clean up temp file on failure
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise
        except OSError:
            pass

    def _load_state(self) -> None:
        """Load urn state from a previous run.

        Restores generation counter, alive/dead tallies, urn weights,
        and sets the assembler's gene counter to avoid name collisions.
        """
        if not os.path.exists(URN_STATE_FILE):
            return
        try:
            with open(URN_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            self.generation = state.get("generation", 0)
            self.alive_count = state.get("alive_count", 0)
            self.dead_count = state.get("dead_count", 0)
            self._last_catastrophe_gen = state.get("last_alive_generation", 0)
            self._multicellular_count = state.get("multicellular_count", 0)
            self._tainted_genes = set(state.get("tainted_genes", []))
            self._era = state.get("era", "太古宙")
            self._era_transitions = state.get("era_transitions", [])
            urn_data = state.get("urn", {})
            self.urn = PolyaUrn.from_dict(urn_data)

            # Restore gene counter so gene names don't collide across sessions.
            # We set it to generation * 2 as a safe upper bound (each generation
            # produces exactly one gene_name, so generation is sufficient).
            self.assembler._gene_counter = max(
                self.assembler._gene_counter, self.generation
            )

            # Reset catastrophe timer to a fresh random interval
            self._catastrophe_timer = random.randint(50, 200)
            # Rebuild library cache for compilation context
            self._library_cache = self._load_library_cache()

            if self.console:
                self.console.print(
                    f"[green]已恢复状态: 第 {self.generation} 代, "
                    f"瓮中有 {self.urn.size()} 个 token[/green]"
                )
            else:
                print(
                    f"已恢复状态: 第 {self.generation} 代, "
                    f"瓮中有 {self.urn.size()} 个 token"
                )
        except (OSError, json.JSONDecodeError):
            pass

    # ------------------------------------------------------------------
    # Library cache (compilation context)
    # ------------------------------------------------------------------

    def _load_library_cache(self) -> str:
        """Load evolved_library.lean contents for compilation context."""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    return f.read()
            except OSError:
                pass
        return ""

    # ------------------------------------------------------------------
    # Top tokens display
    # ------------------------------------------------------------------

    def show_top_tokens(self, n: int = 10) -> None:
        """Display the highest-weight tokens."""
        top = self.urn.top(n)
        if self.console:
            table = Table(title=f"Top {n} Tokens")
            table.add_column("Token", style="cyan")
            table.add_column("Weight", style="green", justify="right")
            for t, w in top:
                table.add_row(t, f"{w:.3f}")
            self.console.print(table)
        else:
            print(f"\nTop {n} Tokens:")
            for t, w in top:
                print(f"  {t:30s} {w:.3f}")
