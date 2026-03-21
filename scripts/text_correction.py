import os
import glob
import re

base_dir = r"d:\大三下\软管\InterviewEcho\knowledge-base"

replacements = {
    # 算法与后端概念错别字修复
    "大预言模型": "大语言模型",
    "strids": "strides",
    "极数复平面": "极坐标复平面",
    "防备灾难性偏见": "防备灾难性遗忘",
    "去重去重防毒化": "去重防毒化",
    "发抽风案例": "异常情况（Bad Cases）",
    
    # 前端概念与错别字修复
    "块那么多": "快那么多",
    "大发作为立足点": "大局作为立足点",
    "纯绪发泄": "纯情绪发泄",
    "提取得Top 10": "提取的Top 10",
    "文件片段": "文档片段（DocumentFragment）", # DocumentFragment中文是文档片段
    "长链属性": "深层嵌套属性",
    "1个参数占4字节，加上优化器矩占很大空间": "1个FP32参数占4字节，加上优化器动量、方差等占用巨大显存",
    "把控模型的极限分类能力底线": "准确评估模型在极度不平衡数据下的真实分类能力",
    "导致页面直接白屏，而且徒增双倍的后期维护联调成本。": "导致页面直接白屏，极大增加了后期维护联调成本。",
    "用大带小（逻辑蒸馏出小众传统XGB树）解决高时耗部署危机": "用大模型蒸馏小模型（如XGBoost等传统树模型）解决高延迟部署危机",
    "盲猜正类都有99%准确率": "全判负类（多数类）都有99%准确率" # 不平衡样本，1正99负，全部猜负才有99%准确率，所以原本这里的描述反了！
}

changed_files = []

for root, _, files in os.walk(base_dir):
    for file in files:
        if file.endswith('.json') or file.endswith('.md'):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for old_str, new_str in replacements.items():
                    new_content = new_content.replace(old_str, new_str)
                
                # regex fix: "如果有算子需要参数通过All-Gather向其他卡借完后直接丢弃" -> 
                # "如果某层算子需要参数前向传播，通过All-Gather向其他卡拉取，计算完后立即丢弃"
                new_content = re.sub(r"如果有算子需要参数通过All-Gather向其他卡借完后直接丢弃", 
                                        "如果前向或反向传播需要某层参数，通过All-Gather向其他卡拉取，计算完后立即释放", new_content) if "All-Gather向其他卡借完后直接丢弃" in new_content else new_content
                
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    changed_files.append(file_path)
            except Exception as e:
                pass

print("Fixed files:")
for cf in changed_files:
    print(f"- {cf}")

