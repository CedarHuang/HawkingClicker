import ast
import collections
import os
from pathlib import Path
from typing import Set, Dict, List
import collections

def extract_i18n_keys(directory: str) -> collections.OrderedDict:
    """从指定目录的所有Python文件中提取i18n调用键(保持出现顺序)"""
    i18n_keys = collections.OrderedDict()

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read(), filename=str(filepath))
                        for node in ast.walk(tree):
                            if (isinstance(node, ast.Call) and 
                                isinstance(node.func, ast.Name) and 
                                node.func.id == 'i18n' and 
                                len(node.args) > 0 and 
                                isinstance(node.args[0], ast.Constant)):

                                key = node.args[0].value
                                i18n_keys.setdefault(key)
                    except:
                        continue
    return i18n_keys

def update_dicts(i18n_keys: collections.OrderedDict, lang_dicts: Dict[str, Dict], lang_files: Dict[str, str]):
    """更新语言字典文件，按i18n_keys顺序排列key"""
    for lang, lang_dict in lang_dicts.items():
        # 创建有序字典，按i18n_keys顺序排列
        ordered_dict = collections.OrderedDict()

        # 添加i18n_keys中的key（保持顺序）
        for key in i18n_keys:
            if key in lang_dict:
                ordered_dict[key] = lang_dict[key]
            else:
                ordered_dict[key] = None  # 新增key

        # 准备文件内容
        content = "i18n = {\n"
        for key, value in ordered_dict.items():
            if value is None:
                content += f"    '{key}': None,\n"
            else:
                content += f"    '{key}': '{value}',\n"
        content += "}\n"

        # 写入文件
        with open(lang_files[lang], 'w', encoding='utf-8') as f:
            f.write(content)

def generate_report(i18n_keys: collections.OrderedDict, lang_dicts: Dict[str, Dict], lang_files: Dict[str, str]) -> str:
    """生成翻译需求报告并更新字典文件"""
    report = []
    report.append("=== 翻译需求报告 ===")
    report.append(f"总翻译键数: {len(i18n_keys)}")

    # 更新字典文件
    update_dicts(i18n_keys, lang_dicts, lang_files)

    # 检查每种语言的翻译情况
    for lang in lang_dicts:
        missing = [k for k in i18n_keys if k not in lang_dicts[lang] or lang_dicts[lang][k] is None]
        report.append(f"\n=== 缺失 {lang} 翻译 ===")
        report.extend(missing if missing else ["无"])

    return '\n'.join(report)

if __name__ == '__main__':
    # 扫描src目录下的所有Python文件
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    keys = extract_i18n_keys(src_dir)

    # 从i18n模块导入翻译字典
    lang_dicts = {}
    i18n_dir = os.path.join(src_dir, 'i18n')
    for filename in os.listdir(i18n_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            lang = filename[:-3]
            try:
                module = __import__(f'src.i18n.{lang}', fromlist=['i18n'])
                lang_dicts[lang] = module.i18n
            except ImportError:
                continue

    # 准备语言文件路径映射
    lang_files = {
        lang: os.path.join(i18n_dir, f"{lang}.py")
        for lang in lang_dicts.keys()
    }

    # 生成报告并更新字典
    report = generate_report(keys, lang_dicts, lang_files)
    print(report)
