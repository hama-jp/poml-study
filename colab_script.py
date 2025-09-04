# ==============================================================================
# POML(Prompt Optimization Meta-Language) 変換・実行ツール
#
# 使い方:
# 1. このコード全体をGoogle Colabのセルにコピー＆ペーストします。
# 2. Colabのランタイムが「Pro」または「Pro+」に設定されていることを確認してください。
#    (google.colab.ai はPro以上のサブスクリプションで利用可能です)
# 3. セルを実行すると、サンプルプロンプトの変換とレンダリングが行われます。
#
# カスタマイズ:
# - `why_why_prompt` 変数の内容を、ご自身のMarkdownプロンプトに書き換えてください。
# - `user_variables` 辞書の内容を、実際の入力値に書き換えてください。
# ==============================================================================

import re
from xml.dom import minidom
import xml.etree.ElementTree as ET

# ==============================================================================
# STEP 2: POMLレンダリング関数 (ルールベース)
# ==============================================================================
def _render_element(element, variables):
    """【内部関数】XML要素を再帰的に解析し、Markdown風テキストに変換します。"""
    output = []
    tag = element.tag
    text = element.text or ''

    if tag == 'h1':
        output.append(f"# {text}\n\n")
    elif tag == 'h2':
        output.append(f"## {text}\n\n")
    elif tag == 'h3':
        output.append(f"### {text}\n\n")
    elif tag == 'p':
        output.append(f"{text}\n\n")
    elif tag == 'list':
        for i, item in enumerate(element.findall('item'), 1):
            output.append(f"{i}. {item.text or ''}\n")
        output.append("\n")
    elif tag == 'code':
        code_type = element.attrib.get('type', '')
        code_content = text.strip()
        output.append(f"```{code_type}\n{code_content}\n```\n\n")
    elif tag == 'field':
        name = element.attrib['name']
        value = variables.get(name, element.attrib.get('default', ''))

        if element.attrib.get('type') == 'list':
            list_items = value.split('\n')
            output.append(f"- **{name}**:\n")
            for item in list_items:
                if item:
                    output.append(f"  - [{item}]\n")
        else:
            output.append(f"- **{name}**: [{value}]\n")

    for child in element:
        output.extend(_render_element(child, variables))
    return output

def render_poml(poml_text: str, variables: dict) -> str:
    """
    POMLテキストと変数を元に、最終的なプロンプトを生成します。
    """
    if not poml_text or not poml_text.strip().startswith('<poml>'):
        return f"エラー: 無効なPOMLテキストです。<poml>タグで始まっているか確認してください。\n受け取ったテキスト:\n---\n{poml_text}"
    try:
        root = ET.fromstring(poml_text)
    except ET.ParseError as e:
        return f"エラー: POMLのXML解析に失敗しました。\n{e}\n受け取ったテキスト:\n---\n{poml_text}"

    if root.tag != 'poml':
        return "エラー: <poml> ルートタグが見つかりません。"

    output_parts = []
    for element in root:
        output_parts.extend(_render_element(element, variables))

    return "".join(output_parts)

# ==============================================================================
# STEP 1: Markdown -> POML 変換関数 (LLM利用)
# ==============================================================================
def convert_markdown_to_poml_with_llm(md_text: str) -> str:
    """
    Markdownテキストを、LLM(google.colab.ai)を使ってPOMLに変換します。
    """
    try:
        from google.colab import ai
    except (ImportError, ModuleNotFoundError):
        print("--- 警告: 'google.colab.ai'が見つかりません。Colab Pro/Pro+環境ではない可能性があります。---")
        print("--- テスト用に、サンプルPOMLを返します。 ---")
        return """<poml>
  <h1>なぜなぜ分析プロンプト</h1>
  <p>原因分析の専門家として、不具合事象に対し「なぜなぜ分析」を多角的に実行する。</p>
  <input_template>
    <h3>事象の初期情報</h3>
    <field name="事象名" type="text" default="Webサーバー応答遅延"/>
    <field name="発生日時" type="text" default="2025/07/28 10:00頃"/>
    <field name="把握している初期情報" type="list" default="CPU利用率95%超過\n特定IPからのアクセス急増\nエラーログなし"/>
  </input_template>
</poml>"""

    system_prompt = """
You are a highly skilled AI assistant specializing in prompt engineering. Your task is to convert a user's structured Markdown prompt into a machine-readable POML (Prompt Optimization Meta-Language) format.

**POML Conversion Rules:**
1. The root element must be `<poml>`.
2. Parse the general structure: `## Title` -> `<h2>Title</h2>`, paragraphs -> `<p>Text</p>`, `1. ...` -> `<list type="ordered"><item>...</item></list>`, etc.
3. Code blocks (```...```) become `<code><![CDATA[...]]></code>`. If "mermaid" is present, add `type="mermaid"`.
4. The content in the code block under "## 入力テンプレート" must be in an `<input_template>` tag. Inside it, `### ...` becomes `<h3>...</h3>`.
5. Inside `<input_template>`, convert fields: `- **Key**: [Value]` becomes `<field name="Key" type="text" default="Value"/>`.
6. For list fields like `**把握している初期情報**:`, create a single `<field type="list" ...>` with newline-separated default values.

**Output Format:**
Your output must be ONLY the raw XML content, starting with `<poml>` and ending with `</poml>`. Do not include any other text or markdown fences.
---
Please convert the following Markdown text to POML:
"""
    full_prompt = f"{system_prompt}\n\n{md_text}"

    print("Geminiモデルを呼び出し、MarkdownをPOMLに変換します... (少し時間がかかる場合があります)")
    response = ai.generate_text(full_prompt, model_name='google/gemini-1.5-pro-latest')

    if not response:
        return "エラー: LLMからの応答が空でした。"
    print("応答を受信しました。XMLを整形します...")

    cleaned_response = re.sub(r'```(xml)?\n?', '', response.strip())
    cleaned_response = re.sub(r'```$', '', cleaned_response)
    cleaned_response = cleaned_response.strip()

    try:
        dom = minidom.parseString(cleaned_response)
        pretty_xml = dom.toprettyxml(indent="  ")
        pretty_xml = "\n".join(line for line in pretty_xml.split('\n')[1:] if line.strip())
        return pretty_xml
    except Exception as e:
        print(f"--- エラー: LLMの出力をXMLとして解析できませんでした。エラー: {e} ---")
        return f"LLMの出力は無効なXMLでした:\n---\n{response}"

# ==============================================================================
# 実行セクション
# ==============================================================================
if __name__ == '__main__':
    # --- 1. 元となるMarkdownプロンプト ---
    why_why_prompt = """
# なぜなぜ分析プロンプト

原因分析の専門家として、不具合事象に対し「なぜなぜ分析」を多角的に実行する。

## 分析手順

1. **事象特定**: 不具合事象を根本的な問いとして設定
2. **多角的分析**: ハードウェア、ソフトウェア、ネットワーク、データ、ヒューマンエラー、プロセス等、あらゆる観点から「なぜ？」を繰り返し原因を洗い出す
3. **原因評価**:
   - **◎(主な原因)**: 直接的な引き金、最も寄与したと強く推測される
   - **〇(副次的原因)**: 発生を助長した間接的要因
   - **△(可能性あり)**: 追加調査が必要
   - **×(阻却)**: 明確に否定できる
4. **情報不足対応**: △は判断できない理由と必要な追加情報を明記、×は阻却根拠を記載
5. **出力**: Mermaid形式`graph TD`で木構造表現。各ノードに`原因名(評価記号)`を含める

## 入力テンプレート

```
### 事象の初期情報
- **事象名**: [例:Webサーバー応答遅延]
- **発生日時**: [例:2025/07/28 10:00頃]
- **発生箇所**: [本番環境のWebサーバー群]
- **具体的な事象**: [特定時間帯にアクセス遅延、タイムアウト発生]
- **把握している初期情報**:
  - [CPU利用率95%超過]
  - [特定IPからのアクセス急増]
  - [エラーログなし]
- **影響範囲**: [サービス全体]
- **これまでの対応**: [該当IP遮断で解消]
```

## 出力形式

```mermaid
graph TD
    A[事象] -->|なぜ?| B(原因1 ◎)
    A -->|なぜ?| C(原因2 〇)
    B -->|なぜ?| B1(詳細原因 △)
```

各原因の詳細評価と、△の場合は必要な追加情報をリスト化。
"""

    print("==================================================")
    print("STEP 1: MarkdownからPOMLへの変換を開始します。")
    print("==================================================")

    poml_output = convert_markdown_to_poml_with_llm(why_why_prompt)

    print("\n\n--- ▼ 生成されたPOML ▼ ---\n")
    print(poml_output)
    print("\n--- ▲ 生成されたPOML ▲ ---\n")

    # --- 2. ユーザーが具体的な情報を入力 ---
    # (POMLを編集したり、以下の辞書を書き換えたりする)
    user_variables = {
        "事象名": "本番DBのCPU使用率が100%に張り付く",
        "発生日時": "2025/09/03 20:00頃",
        "発生箇所": "PostgreSQL 15 on AWS RDS",
        "具体的な事象": "特定の参照系クエリが異常に遅く、CPUを消費している。",
        "把握している初期情報": "・pg_stat_activityで怪しいクエリを特定\n・該当クエリはJOINが多く、実行計画が不適切になっている可能性がある\n・昨日のデプロイでインデックスの変更があった",
        "影響範囲": "ユーザー向けレポート機能全体",
        "これまでの対応": "該当クエリを使っている機能を一時的に停止"
    }

    print("\n==================================================")
    print("STEP 2: POMLとユーザー入力から最終プロンプトを生成します。")
    print("==================================================")

    final_prompt = render_poml(poml_output, user_variables)

    print("\n\n--- ▼ 生成された最終プロンプト ▼ ---\n")
    print(final_prompt)
    print("\n--- ▲ 生成された最終プロンプト ▲ ---\n")
