"""CLI entry point for luca_of_math_lean -- the zero-cost mathematical evolution kernel.

Usage:
    python main.py                    # Start evolution with defaults
    python main.py --max-generations 500
    python main.py --resume           # Resume from saved state
    python main.py --show-top 10      # Show top tokens from saved state
"""

import sys
from typing import Optional

try:
    import click
except ImportError:
    print("Error: 'click' is required. Install it with: pip install click")
    sys.exit(1)

from luca.engine import EvolutionEngine
from luca.urn import PolyaUrn
from luca.config import (
    EVOLUTION_OUTPUT_FILE,
    URN_STATE_FILE,
    LEAN_TIMEOUT,
    POPULATION_SIZE,
)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--max-generations", "-n",
    type=int,
    default=10_000,
    show_default=True,
    help="Maximum number of generations to evolve.",
)
@click.option(
    "--timeout", "-t",
    type=float,
    default=LEAN_TIMEOUT,
    show_default=True,
    help="Lean compiler timeout per candidate (seconds).",
)
@click.option(
    "--output", "-o",
    type=str,
    default=EVOLUTION_OUTPUT_FILE,
    show_default=True,
    help="File to append successfully evolved definitions.",
)
@click.option(
    "--resume", "-r",
    is_flag=True,
    default=False,
    help="Resume evolution from a previously saved urn state.",
)
@click.option(
    "--show-top",
    type=int,
    default=None,
    metavar="N",
    help="Show top N tokens from saved state and exit.",
)
@click.option(
    "--population", "-p",
    type=int,
    default=POPULATION_SIZE,
    show_default=True,
    help="Candidates per generation (verified in parallel).",
)
def main(
    max_generations: int,
    timeout: float,
    output: str,
    resume: bool,
    show_top: Optional[int],
    population: int,
) -> None:
    """luca_of_math_lean — 零 API 成本的数学演化内核.

    \b
    基于 Pólya 瓮过程 (非马尔可夫随机过程) 与 Lean 4 编译器,
    在纯粹的计算与逻辑驱动下进行开放式演化.

    \b
    工作原理:
      1. 从 Pólya 瓮中按权重采样 Lean 语法 token
      2. 组装成 Lean 4 候选表达式
      3. 由 Lean 编译器验证 (自然选择)
      4. 通过则强化 token、注册新基因; 失败则丢弃
      5. 随机触发天灾事件 (质量灭绝、寒武纪大爆发等)
    """
    # --show-top mode: inspect saved state
    if show_top is not None:
        _show_top_tokens(show_top)
        return

    # Normal evolution mode
    engine = EvolutionEngine(
        max_generations=max_generations,
        lean_timeout=timeout,
        output_file=output,
        resume=resume,
        population_size=population,
    )
    engine.run()


def _show_top_tokens(n: int) -> None:
    """Load saved urn state and display top N tokens."""
    import json
    import os

    if not os.path.exists(URN_STATE_FILE):
        click.echo(f"未找到保存的状态文件: {URN_STATE_FILE}")
        click.echo("请先运行一次演化,或检查当前目录。")
        return

    try:
        with open(URN_STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        click.echo(f"无法读取状态文件: {e}")
        return

    urn_data = state.get("urn", {})
    urn = PolyaUrn.from_dict(urn_data)
    generation = state.get("generation", 0)
    alive = state.get("alive_count", 0)
    dead = state.get("dead_count", 0)

    click.echo(f"\n状态快照 (第 {generation} 代, Alive={alive}, Dead={dead})")
    click.echo(f"瓮中 Token 总数: {urn.size()}")
    click.echo(f"\n权重 TOP {n}:")
    click.echo("-" * 50)

    top = urn.top(n)
    for token, weight in top:
        bar = "█" * max(1, int(weight))
        click.echo(f"  {token:35s} {weight:8.2f}  {bar}")


if __name__ == "__main__":
    main()
