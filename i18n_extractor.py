import ast
import collections
import os
from pathlib import Path
from typing import Dict, List, Union

# 定义一个AST访问器来提取i18n键
class I18nKeyExtractor(ast.NodeVisitor):
    def __init__(self):
        self.i18n_keys = collections.OrderedDict()
        # 用于存储当前作用域内变量的字面量值
        # 键是变量名，值可以是字符串、字符串列表或None（表示无法静态解析）
        self.variable_assignments: Dict[str, Union[str, List[str], None]] = {}
        # 用于处理for循环中的变量，这是一个栈，每个元素是(循环变量名, 循环可能的值列表)
        self.loop_var_contexts: List[tuple[str, List[str]]] = []

    def visit_Assign(self, node: ast.Assign):
        """处理变量赋值语句"""
        # 假设只有一个目标（例如：x = 10，而不是 x = y = 10）
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id

            if isinstance(node.value, ast.Constant):
                # 处理 x = 'string'
                if isinstance(node.value.value, str):
                    self.variable_assignments[target_name] = node.value.value
                else:
                    self.variable_assignments[target_name] = None # 非字符串字面量
            elif isinstance(node.value, (ast.Tuple, ast.List)):
                # 处理 x = ('a', 'b') 或 x = ['a', 'b']
                values = []
                all_constants = True
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        values.append(elt.value)
                    else:
                        all_constants = False
                        break
                if all_constants:
                    self.variable_assignments[target_name] = values
                else:
                    self.variable_assignments[target_name] = None # 包含非字面量字符串或非字符串
            else:
                self.variable_assignments[target_name] = None # 无法静态解析的赋值

        self.generic_visit(node) # 继续访问子节点

    def visit_For(self, node: ast.For):
        """处理for循环语句"""
        loop_var_name = None
        iterable_values: List[str] = []

        # 获取循环变量名 (e.g., 'col' in 'for col in columns:')
        if isinstance(node.target, ast.Name):
            loop_var_name = node.target.id

        # 获取迭代器 (e.g., 'columns' in 'for col in columns:')
        if isinstance(node.iter, ast.Name):
            iterable_name = node.iter.id
            if iterable_name in self.variable_assignments:
                assigned_val = self.variable_assignments[iterable_name]
                if isinstance(assigned_val, list) and all(isinstance(v, str) for v in assigned_val):
                    iterable_values = assigned_val

        if loop_var_name and iterable_values:
            # 将循环变量及其可能的值推入上下文栈
            self.loop_var_contexts.append((loop_var_name, iterable_values))
            self.generic_visit(node) # 访问循环体
            self.loop_var_contexts.pop() # 循环结束后弹出上下文
        else:
            self.generic_visit(node) # 无法解析的循环，正常访问子节点

    def visit_Call(self, node: ast.Call):
        """处理函数调用"""
        if (isinstance(node.func, ast.Name) and 
            node.func.id == 'i18n' and 
            len(node.args) > 0):

            arg = node.args[0]
            if isinstance(arg, ast.Constant):
                # 识别 i18n('literal_string')
                if isinstance(arg.value, str):
                    self.i18n_keys.setdefault(arg.value)
            elif isinstance(arg, ast.Name):
                # 识别 i18n(variable_name)
                var_name = arg.id

                # 1. 检查当前作用域的变量赋值
                if var_name in self.variable_assignments:
                    assigned_val = self.variable_assignments[var_name]
                    if isinstance(assigned_val, str):
                        self.i18n_keys.setdefault(assigned_val)
                    # 如果变量被赋值为列表，但i18n(var)通常只取一个值，这里不处理
                    # 除非是for循环中的变量，那会在loop_var_contexts中处理

                # 2. 检查for循环上下文 (从最近的循环开始检查)
                for loop_var, loop_values in reversed(self.loop_var_contexts):
                    if var_name == loop_var:
                        for val in loop_values:
                            self.i18n_keys.setdefault(val)
                        break # 找到匹配的循环变量，不再向上查找

        self.generic_visit(node) # 继续访问子节点

def extract_i18n_keys(directory: str) -> collections.OrderedDict:
    """从指定目录的所有Python文件中提取i18n调用键(保持出现顺序)"""
    i18n_keys = collections.OrderedDict()

    for root, _, files in os.walk(directory):
        # 对文件列表进行排序，确保处理顺序是确定的
        for file in sorted(files):
            if file.endswith('.py'):
                filepath = Path(root) / file
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read(), filename=str(filepath))
                        extractor = I18nKeyExtractor()
                        extractor.visit(tree)
                        # 将提取器找到的键合并到主有序字典中
                        for key in extractor.i18n_keys:
                            i18n_keys.setdefault(key)
                    except Exception as e:
                        print(f"Error parsing {filepath}: {e}")
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
            # 确保值是字符串，如果为None则写入None
            if value is None:
                content += f"    '{key}': None,\n"
            else:
                # 对值进行转义，以防包含单引号等特殊字符
                escaped_value = value.replace("'", "\\'")
                content += f"    '{key}': '{escaped_value}',\n"
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
                # 使用importlib.machinery来加载模块，避免污染sys.modules
                from importlib.machinery import SourceFileLoader
                module = SourceFileLoader(f'src.i18n.{lang}', os.path.join(i18n_dir, filename)).load_module()
                lang_dicts[lang] = module.i18n
            except Exception as e:
                print(f"Error loading i18n module {lang}: {e}")
                continue

    # 准备语言文件路径映射
    lang_files = {
        lang: os.path.join(i18n_dir, f"{lang}.py")
        for lang in lang_dicts.keys()
    }

    # 生成报告并更新字典
    report = generate_report(keys, lang_dicts, lang_files)
    print(report)
