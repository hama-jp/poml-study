### **プロンプトがごちゃごちゃ？ Microsoftの新言語「POML」で始める、構造化プロンプトエンジニアリング入門**

AI、特に大規模言語モデル（LLM）の活用が当たり前になってきましたね。しかし、多くの開発者が「プロンプトの管理」という課題に直面しています。プロンプトが複雑になるにつれて、コードは読みにくくなり、再利用も難しく、少し修正するだけでも一苦労…なんてことはありませんか？

そんな悩みを解決するためにMicrosoftが開発したのが、今回ご紹介する**POML (Prompt Orchestration Markup Language)** です。

POMLは、その名の通り「プロンプトを組み立てるためのマークアップ言語」。HTMLのようにタグを使ってプロンプトの構造を明確に記述することで、可読性、再利用性、メンテナンス性を劇的に向上させます。

この記事では、たくさんの実例を交えながら、POMLの基本的な使い方をクイックに解説していきます！

#### **1. POMLの基本構造：役割(Role)と指示(Task)**

まず、最もシンプルなPOMLファイルを見てみましょう。これは、AIに「優秀なアシスタント」として、「ユーザーの質問に答える」役割を指示するものです。

```xml
<!-- simple_prompt.poml -->
<poml>
    <role>
        You are a helpful and professional assistant.
    </role>
    <task>
        Answer the user's question.
    </task>
</poml>
```

どうでしょう？ HTMLやXMLに似ていて、直感的ですよね。
*   `<poml>`: すべてのPOMLコンテンツを囲むルートタグです。
*   `<role>`: LLMに与える役割やペルソナを定義します。「あなたは〜です」という部分ですね。
*   `<task>`: LLMに実行してほしい具体的なタスクを記述します。

これだけで、プロンプトの「役割設定」と「具体的な指示」が分離され、非常に見通しが良くなります。

#### **2. 具体例を与える (Few-shotプロンプティング)**

LLMは、いくつかのお手本（例）を見せると、より高い精度でタスクを実行してくれます。POMLでは `<example>` タグを使って、このお手本を簡単に記述できます。

例えば、ユーザーの入力文をJSON形式に変換するタスクを考えてみましょう。

```xml
<!-- json_converter.poml -->
<poml>
    <role>
        You are a data entry specialist.
    </role>
    <task>
        Extract the user's name and age from the text and provide it in JSON format.
    </task>

    <example>
        <user>
            My name is Alice and I am 30 years old.
        </user>
        <assistant>
            {
                "name": "Alice",
                "age": 30
            }
        </assistant>
    </example>

    <example>
        <user>
            I'm Bob, 25.
        </user>
        <assistant>
            {
                "name": "Bob",
                "age": 25
            }
        </assistant>
    </example>
</poml>
```

`<example>` タグの中に `<user>` (ユーザーの発話例) と `<assistant>` (AIの理想的な応答例) をペアで記述するだけです。これにより、AIはどのような形式で応答すればよいかを正確に学習できます。

#### **3. プロンプトを動的にする：テンプレート機能**

POMLの真骨頂とも言えるのが、テンプレート機能です。変数、ループ、条件分岐を使って、データに基づいた動的なプロンプトを生成できます。

例えば、製品リストから報告書を作成するプロンプトを書いてみましょう。

```xml
<!-- report_generator.poml -->
<poml>
    <role>
        You are an inventory manager.
    </role>
    <task>
        Create a stock report based on the following product list.
        Only include items with less than 20 units in stock.
    </task>

    <let>
        products = [
            {"name": "Laptop", "stock": 15},
            {"name": "Mouse", "stock": 50},
            {"name": "Keyboard", "stock": 5}
        ]
    </let>

    <prompt>
        Stock Report:
        {% for p in products %}
            {% if p.stock < 20 %}
            - Product: {{ p.name }}, Stock: {{ p.stock }} units
            {% endif %}
        {% endfor %}
    </prompt>
</poml>
```

*   `<let>`: プロンプト内で使う変数やデータを定義します。（実際には外部からデータを渡すことが多いです）
*   `{{ p.name }}`: `p` というオブジェクトの `name` プロパティを表示します。（変数）
*   `{% for p in products %}`: `products` リストをループ処理します。（ループ）
*   `{% if p.stock < 20 %}`: 在庫が20未満のアイテムだけを対象にします。（条件分岐）

これにより、同じプロンプト構造を使いながら、渡すデータに応じて全く異なる内容のプロンプトを生成できます。

#### **4. 外部ファイルを使う**

長い文章や定型文をプロンプトに含めたい場合、`<document>` タグが便利です。

```xml
<!-- file_importer.poml -->
<poml>
    <task>
        Summarize the following document.
    </task>
    <document src="./company_policy.txt" />
</poml>
```

`src`属性でファイルのパスを指定するだけで、そのファイルの内容がプロンプトに埋め込まれます。これにより、POMLファイル自体はシンプルに保ったまま、外部の豊富な情報を活用できます。

#### **5. どうやって使うの？**

POMLはそれ自体がプログラムを実行するわけではなく、PythonやNode.jsなどのSDK（ソフトウェア開発キット）と組み合わせて使います。

**セットアップ（例：Python）**
```bash
pip install poml
```

**Pythonコード（例）**
```python
import poml

# POMLファイルを読み込む
with open("report_generator.poml", "r") as f:
    markup = f.read()

# データを渡してプロンプトを生成
# （<let>の代わりに外部から動的にデータを渡す例）
data_context = {
    "products": [
        {"name": "Webcam", "stock": 10},
        {"name": "Monitor", "stock": 30}
    ]
}

# POMLを処理して最終的なプロンプト文字列を取得
final_prompt = poml.process(markup=markup, context=data_context)

print(final_prompt['content'])

# あとはこの final_prompt をお好きなLLM APIに渡すだけ！
```

また、**Visual Studio Codeの拡張機能**も提供されており、シンタックスハイライトや自動補完、プレビュー機能などを使って快適にPOMLファイルを編集できます。

#### **まとめ**

POMLは、複雑化するプロンプト開発に「構造」と「秩序」をもたらす強力なツールです。

*   **可読性の向上:** HTMLライクな構文で、誰が見ても分かりやすい。
*   **再利用性の向上:** コンポーネント（役割、タスク、例）を分離して管理できる。
*   **メンテナンス性の向上:** ロジックとデータを分離し、修正が容易になる。

プロンプトエンジニアリングをさらに本格的に、そして効率的に行いたい方は、ぜひPOMLを試してみてください。

**さらに学ぶには：**
*   **公式GitHubリポジトリ:** [https://github.com/microsoft/poml](https://github.com/microsoft/poml)
*   **公式ドキュメント:** [https://microsoft.github.io/poml/](https://microsoft.github.io/poml/)
