"""
批量编译 .ui 文件为 Python 模块
================================
将 src/ui/ 下的所有 .ui 文件通过 pyside6-uic 编译为 Python 代码，
输出到 src/ui/generated/ 目录。

用法:
    python compile_ui.py            # 编译所有 .ui 文件
    python compile_ui.py --clean    # 清空 generated 目录后重新编译
    python compile_ui.py --check    # 仅检查哪些文件需要重新编译（不执行）
"""

import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# ---- 路径常量 ----
_PROJECT_ROOT = Path(__file__).resolve().parent
_UI_DIR = _PROJECT_ROOT / "src" / "ui"
_OUTPUT_DIR = _UI_DIR / "generated"

# 产物文件名前缀
_OUTPUT_PREFIX = "ui_"


def _find_ui_files() -> list[Path]:
    """扫描 src/ui/ 下所有 .ui 文件（不递归子目录）"""
    return sorted(_UI_DIR.glob("*.ui"))


def _output_path(ui_file: Path) -> Path:
    """根据 .ui 文件路径计算对应的输出 .py 路径
    例如: main_window.ui -> generated/ui_main_window.py
    """
    return _OUTPUT_DIR / f"{_OUTPUT_PREFIX}{ui_file.stem}.py"


def _needs_compile(ui_file: Path, py_file: Path) -> bool:
    """判断是否需要重新编译（.ui 比 .py 更新，或 .py 不存在）"""
    if not py_file.exists():
        return True
    return ui_file.stat().st_mtime > py_file.stat().st_mtime


def _ensure_output_dir():
    """确保输出目录存在，并创建 __init__.py"""
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    init_file = _OUTPUT_DIR / "__init__.py"
    if not init_file.exists():
        init_file.write_text("", encoding="utf-8")


def _find_uic() -> str:
    """查找 pyside6-uic 可执行文件路径"""
    # 优先使用 PySide6 包目录下的 uic
    try:
        import PySide6
        uic_path = Path(PySide6.__file__).parent / ("uic.exe" if sys.platform == "win32" else "uic")
        if uic_path.exists():
            return str(uic_path)
    except ImportError:
        pass

    # 回退：尝试 PATH 中的 pyside6-uic
    result = shutil.which("pyside6-uic")
    if result:
        return result

    return ""


def _compile_ui(ui_file: Path, py_file: Path, uic_path: str) -> bool:
    """调用 pyside6-uic 编译单个 .ui 文件，返回是否成功"""
    cmd = [uic_path, str(ui_file), "-o", str(py_file), "-g", "python"]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ 编译失败: {ui_file.name}")
        if e.stderr:
            print(f"    错误信息: {e.stderr.strip()}")
        return False


def cmd_compile(force: bool = False):
    """编译所有 .ui 文件"""
    ui_files = _find_ui_files()
    if not ui_files:
        print("未找到任何 .ui 文件。")
        return

    uic_path = _find_uic()
    if not uic_path:
        print("✗ 未找到 pyside6-uic，请确认已安装 PySide6:")
        print("  pip install PySide6")
        sys.exit(1)

    _ensure_output_dir()

    compiled = 0
    skipped = 0
    failed = 0

    print(f"扫描到 {len(ui_files)} 个 .ui 文件\n")

    for ui_file in ui_files:
        py_file = _output_path(ui_file)

        if not force and not _needs_compile(ui_file, py_file):
            skipped += 1
            print(f"  ⊘ 跳过（未变更）: {ui_file.name}")
            continue

        print(f"  ▸ 编译: {ui_file.name} → generated/{py_file.name}")
        if _compile_ui(ui_file, py_file, uic_path):
            compiled += 1
        else:
            failed += 1

    print(f"\n完成: {compiled} 个编译, {skipped} 个跳过, {failed} 个失败")

    if failed > 0:
        sys.exit(1)


def cmd_clean():
    """清空 generated 目录后重新编译"""
    if _OUTPUT_DIR.exists():
        shutil.rmtree(_OUTPUT_DIR)
        print(f"已清空: {_OUTPUT_DIR.relative_to(_PROJECT_ROOT)}\n")
    cmd_compile(force=True)


def cmd_check():
    """检查哪些文件需要重新编译"""
    ui_files = _find_ui_files()
    if not ui_files:
        print("未找到任何 .ui 文件。")
        return

    needs_compile = []
    up_to_date = []

    for ui_file in ui_files:
        py_file = _output_path(ui_file)
        if _needs_compile(ui_file, py_file):
            needs_compile.append(ui_file)
        else:
            up_to_date.append(ui_file)

    if needs_compile:
        print(f"需要编译 ({len(needs_compile)}):")
        for f in needs_compile:
            print(f"  ▸ {f.name}")
    else:
        print("所有文件均为最新，无需编译。")

    if up_to_date:
        print(f"\n已是最新 ({len(up_to_date)}):")
        for f in up_to_date:
            print(f"  ✓ {f.name}")


def main():
    parser = argparse.ArgumentParser(
        description="批量编译 .ui 文件为 Python 模块",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python compile_ui.py            编译有变更的 .ui 文件（增量）
  python compile_ui.py --clean    清空产物目录后全量重新编译
  python compile_ui.py --check    仅检查，不执行编译
        """,
    )
    parser.add_argument("--clean", action="store_true", help="清空 generated 目录后重新编译")
    parser.add_argument("--check", action="store_true", help="仅检查哪些文件需要重新编译")

    args = parser.parse_args()

    if args.clean:
        cmd_clean()
    elif args.check:
        cmd_check()
    else:
        cmd_compile()


if __name__ == "__main__":
    main()
