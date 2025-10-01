# DuckDuckAgoでWeb検索したり、Webページの内容を取得するMCPサーバー

## 概要
* DuckDuckAgoでWeb検索したり、Webページの内容を取得するMCPサーバー

### 前提条件
* 以下のソフトウェアがインストール済みであること
    * vscode
    * cline
    * Python
    * uv
    * Edge

## 準備
1. このGitリポジトリをclineします。
    ```bash
    git clone https://github.com/knd3dayo/web_search_mcp.git
    ```

1. Python仮想環境を作成します.
    ```batch
    python -m venv venv
    ```

1. venv環境を有効にして、Web検索MCPサーバーをインストールします
    ```batch
    venv\Scripts\Activate
    pip install .
    ```

1. `sample_cline_mcp_settings.json`の内容を編集して、`cline_mcp_settings.json`に追加します.
    <PATH_TO_VENV>はvenvへのパス、<PATH_TO_AUTH_JSON IF NEEDED>は、あらかじめログインが必要なサイトの認証済みのセッションなどを保存したjsonファイル。必要に応じて設定

    ```json
    "web_search_mcp": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "<PATH_TO_VENV>",
        "run",
        "-m",
        "web_search_mcp.mcp_modules.mcp_server"
      ],
      "env": {
        "PLAYWRIGHT_HEADLESS": "false",
        "PLAYWRIGHT_BROWSER": "msedge",
        "PLAYWRIGHT_AUTH_JSON": "<PATH_TO_AUTH_JSON IF NEEDED>"
      }
    }
    ```

1. ClineのMCPサーバー一覧に`web_search_mcp`が表示されて有効になっていれば設定完了です。

1. 認証済みのセッションを保存したjsonファイルが必要な場合は下記コマンドでブラウザを起動。認証を行った後ブラウザを閉じる。その後、MCPサーバーを再読み込み

```batch
venv\Script\Activate

playwright codegen --channel=msedge --save-strorage <PATH_TO_AUTH_JSON IF NEEDED>

```
