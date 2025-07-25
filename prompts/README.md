# Prompt模板目录

这个目录包含系统使用的所有Prompt模板文件。

## 目录结构

```
prompts/
├── query_rewriting/          # 查询重写模板
│   └── v1_multi_perspective.txt
├── generation/               # 生成模板
│   ├── v1_drafting.txt
│   └── v1_refinement.txt
├── style_alignment/          # 风格对齐模板
│   └── v1_dyp_style.txt
└── llm_as_judge/            # LLM评判模板
    └── v2_multi_dimension.txt
```

## 使用说明

- 每个模板文件都有版本号，支持A/B测试
- 模板使用Python字符串格式化语法
- 通过配置文件指定使用的模板版本

## 模板变量

常用的模板变量包括：
- `{query}`: 用户查询
- `{context}`: 检索到的上下文
- `{draft}`: 初稿内容
- `{sources}`: 来源信息