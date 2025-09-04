import poml
import json
from typing import Dict, Any, Optional

def convert_poml_to_prompt(poml_string: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    POML形式の文字列を、公式のpoml-python SDKを使用して最終的なプロンプトに変換します。

    Args:
        poml_string: 変換対象のPOML文字列。
        context: POMLテンプレートに渡す動的なデータを含む辞書。

    Returns:
        LLMに渡すことができる、レンダリング済みのプロンプト文字列。
    """
    if context is None:
        context = {}

    try:
        # POML SDKのpomlメソッドを使用。chat=Falseは単一プロンプトとして扱う。
        # format='raw' は、内部的にはJSON文字列を返すことがあるため、後処理でパースする。
        raw_output = poml.poml(markup=poml_string, context=context, format='raw', chat=False)

        # 出力がJSON形式の文字列であるか試す
        try:
            # JSONとしてパース
            parsed_json = json.loads(raw_output)
            # "messages"キーが存在すれば、その内容を返す
            if isinstance(parsed_json, dict) and 'messages' in parsed_json:
                return parsed_json['messages']
        except json.JSONDecodeError:
            # パースに失敗した場合は、元のraw_outputがそのままプロンプトであると見なす
            pass

        return raw_output

    except Exception as e:
        # POML処理自体のエラー
        # エラーメッセージに詳細が含まれていることが多いので、そのまま返す
        return f"Error processing POML: {e}"

# このスクリプトが直接実行された場合のテスト用コード
if __name__ == '__main__':
    # --- テストケース1: シンプルなPOML ---
    simple_poml = """
<poml>
    <role>あなたは優秀なアシスタントです。</role>
    <task>ユーザーの質問に簡潔に答えてください。</task>
</poml>
"""
    print("--- テスト1: シンプルなPOML ---")
    final_prompt_1 = convert_poml_to_prompt(simple_poml)
    print("生成されたプロンプト:")
    print(final_prompt_1)
    print("-" * 20)

    # --- テストケース2: テンプレート機能を使った動的なPOML (修正版) ---
    # <prompt> タグは無効なため、<p> (Paragraph) タグを使用
    template_poml = """
<poml>
    <role>あなたは製品レビューの専門家です。</role>
    <task>以下の製品について、レビューを生成してください。</task>
    <p>
製品名: {{ product.name }}<br />
カテゴリ: {{ product.category }}<br />
価格: {{ product.price }}円<br />
<br />
レビュー:
    </p>
</poml>
"""
    product_data = {
        "product": {
            "name": "スーパーキーボード",
            "category": "PC周辺機器",
            "price": 15000
        }
    }

    print("--- テスト2: テンプレート機能付きPOML ---")
    final_prompt_2 = convert_poml_to_prompt(template_poml, context=product_data)
    print("生成されたプロンプト:")
    print(final_prompt_2)
    print("-" * 20)

    # --- テストケース3: 不正なPOML ---
    invalid_poml = "<poml><role>This is an unterminated tag</role"

    print("--- テスト3: 不正なPOML ---")
    final_prompt_3 = convert_poml_to_prompt(invalid_poml)
    print("生成されたプロンプト:")
    print(final_prompt_3)
    print("-" * 20)
