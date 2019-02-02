"""
初版：2018-12-30

eelをインストールしておきます

pip install eel

表示に'chrome'、'chrome-app' を使う場合は Chrome を使うので必須
アプリのモード（ 'chrome'、 'chrome-app'、None）で None なら既定のブラウザで見れる

https://github.com/ChrisKnott/Eel

htmlファイルには下のjavascriptを読み込む
<script type="text/javascript" src="/eel.js"></script>
"""
# pipで追加するもの
import eel

# 最初から入っているもの
import sqlite3
import json
import os
import html
import logging

print("""
Eelを起動中…
終了するには、ブラウザのタブを閉じるか、
このコマンドプロンプトを閉じるかしてください
""")

# sqliteのデータベースファイルのパス（この例は同階層）
DB_PATH = "../notes.db"


def create_table():
    """もしデータベースファイルがなければ新規にテーブルを作る関数"""

    # データベース接続
    conn = sqlite3.connect(DB_PATH)
    # カーソル生成
    cursor = conn.cursor()

    # executeメソッドでSQL文を実行する
    cursor.execute("""
CREATE TABLE `category` (
	`id`	integer,
	`name`	text,
	PRIMARY KEY(`id`)
);
    """)

    # executeメソッドでSQL文を実行する
    cursor.execute("""
CREATE TABLE `memo` (
	`id`	integer,
	`category_id`	integer,
	`title`	text,
	`detail`	text,
	PRIMARY KEY(`id`)
);
    """)

    conn.commit()

    cursor.close()
    conn.close()


def dbaccess():
    """sqliteの接続関数"""

    # もしファイルがなければテーブルを作る
    if not os.path.isfile(DB_PATH):
        create_table()

    # データベース接続
    conn = sqlite3.connect(DB_PATH)
    # カーソル生成
    cursor = conn.cursor()

    return conn, cursor


@eel.expose
def index_list(id, q):
    """index.htmlのJavaScriptにjsonを渡す関数 (Python → JavaScript)"""

    conn, cursor = dbaccess()

    # 検索
    if len(q) > 0:
        cursor.execute("""
SELECT t.id, t.category_id, c.name, t.title, t.detail 
FROM memo as t LEFT OUTER JOIN category as c ON
t.category_id = c.id
WHERE c.name LIKE ? OR t.title LIKE ? OR t.detail LIKE ? ORDER BY t.id DESC;
        """, ("%"+q+"%", "%"+q+"%", "%"+q+"%"))

    # カテゴリ
    elif id > 0:
        cursor.execute("""
SELECT t.id, t.category_id, c.name, t.title
FROM memo as t
LEFT OUTER JOIN category as c ON
t.category_id = c.id
WHERE t.category_id = ?
ORDER BY t.id DESC;
        """, (id,))

    # 全件
    else:
        cursor.execute("""
SELECT t.id, t.category_id, c.name, t.title
FROM memo as t
LEFT OUTER JOIN category as c ON
t.category_id = c.id
ORDER BY t.id DESC;
        """)

    # 全件取得は cursor.fetchall()
    # 一つ一つ取り出す場合はfetchoneを使います。
    lists = cursor.fetchall()

    cursor.close()
    conn.close()

    # jsonにして返す
    return json.dumps(lists)


@eel.expose
def detail(id):
    """detail.htmlのJavaScriptにjsonを渡す関数 (Python → JavaScript)"""

    conn, cursor = dbaccess()

    cursor.execute("""
SELECT t.id, t.category_id, c.name, t.title, t.detail 
FROM memo as t LEFT OUTER JOIN category as c ON
t.category_id = c.id WHERE t.id = ?;
    """, (id,))
    obj = cursor.fetchone()

    cursor.close()
    conn.close()

    # タプルからリストへ
    obj = list(obj)
    # html.escapeしておく
    obj[2] = html.escape(obj[2])
    obj[3] = html.escape(obj[3])
    obj[4] = html.escape(obj[4])

    # jsonにして返す
    return json.dumps(obj)


@eel.expose
def add_form_list():
    """add_form.htmlのJavaScriptにカテゴリ一覧をjsonにして渡す関数 (Python → JavaScript)"""

    conn, cursor = dbaccess()

    cursor.execute("""SELECT * FROM category ORDER BY name;""")
    lists = cursor.fetchall()

    cursor.close()
    conn.close()

    # jsonにして返す
    return json.dumps(lists)


@eel.expose
def add_form_insert(category_id, title, detail):
    """add_form.htmlから新規入力する関数 (JavaScript → Python)"""

    conn, cursor = dbaccess()

    try:
        cursor.execute("""
INSERT INTO memo (category_id, title, detail) VALUES (?,?,?);
        """, (category_id, title, detail))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        logging.warning(ex)
    finally:
        cursor.close()
        conn.close()


@eel.expose
def edit_form(id):
    """edit_form.htmlにjsonにして渡す関数 (Python → JavaScript)"""

    conn, cursor = dbaccess()

    cursor.execute("""SELECT * FROM category ORDER BY name;""")
    lists = cursor.fetchall()

    cursor.execute("""
SELECT t.id, t.category_id, c.name, t.title, t.detail 
FROM memo as t LEFT OUTER JOIN category as c ON
t.category_id = c.id WHERE t.id = ?;
    """, (id,))
    obj = cursor.fetchone()

    cursor.close()
    conn.close()

    # ２つのリストを１つの辞書にする
    # JavaScript側では一度に１つのjsonしか送れないようなので、ここはポイント
    mydict = {
        "c": lists,
        "d": obj
    }

    # jsonにして返す
    return json.dumps(mydict)


@eel.expose
def edit_form_update(id, category_id, title, detail):
    """edit_form.htmlから送信された引数をもとに更新する関数 (JavaScript → Python)"""

    conn, cursor = dbaccess()

    try:
        cursor.execute("""
UPDATE memo SET category_id = ?, title = ?, detail = ? WHERE id = ?;
        """, (category_id, title, detail, id))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        logging.warning(ex)
    finally:
        cursor.close()
        conn.close()


@eel.expose
def edit_form_delete(id):
    """edit_form.htmlから送信された引数をもとに削除する関数 (JavaScript → Python)"""

    conn, cursor = dbaccess()

    try:
        cursor.execute("""DELETE FROM memo WHERE id=?""", (id,))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        logging.warning(ex)
    finally:
        cursor.close()
        conn.close()


@eel.expose
def category_list():
    """category.htmlのJavaScriptにカテゴリ一覧をjsonにして渡す関数 (Python → JavaScript)"""

    conn, cursor = dbaccess()

    cursor.execute("""SELECT * FROM category;""")
    lists = cursor.fetchall()

    cursor.close()
    conn.close()

    # jsonにして返す
    return json.dumps(lists)


@eel.expose
def category_insert(name):
    """category.htmlで新規にカテゴリを追加する関数 (JavaScript → Python)"""

    conn, cursor = dbaccess()

    try:
        cursor.execute("""INSERT INTO category (name) VALUES (?);""", (name,))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        logging.warning(ex)
    finally:
        cursor.close()
        conn.close()


@eel.expose
def category_update(id, name):
    """category.htmlで既存カテゴリを編集する関数 (JavaScript → Python)"""

    conn, cursor = dbaccess()

    try:
        cursor.execute("""UPDATE category SET name=? WHERE id=?""", (name, id))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        logging.warning(ex)
    finally:
        cursor.close()
        conn.close()


@eel.expose
def category_delete(id):
    """category.htmlで既存カテゴリを削除する関数 (JavaScript → Python)"""

    conn, cursor = dbaccess()

    try:
        cursor.execute("""DELETE FROM category WHERE id=?""", (id,))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        logging.warning(ex)
    finally:
        cursor.close()
        conn.close()


@eel.expose
def vacuum():
    """
    SQLiteの空き領域開放
    """

    # 最初のファイルサイズ取得
    size1 = os.path.getsize(DB_PATH) / 1024

    conn, cursor = dbaccess()

    try:
        cursor.execute("""VACUUM;""")
        conn.commit()
    except:
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    # 次のファイルサイズ取得
    size2 = os.path.getsize(DB_PATH) / 1024

    mydict = {
        "size1": size1,
        "size2": size2
    }

    # jsonにして返す
    return json.dumps(mydict)


# すべてのフロントエンドファイルをwebというディレクトリに置いたとします。
eel.init("web")

# eelのオプション
# オプションには、
# アプリのモード（ "chrome'、 'chrome-app'、None）、
# アプリが実行されるポート、
# アプリのホスト名、
# Chrome / Chromiumコマンドラインフラグの追加などがあります。
web_app_options = {
    "mode": "",  # （ 'chrome'、 'chrome-app'、None）
    "port": 8899
}
# 開始ページindex.htmlを含めて、このようにアプリケーションを起動します。
eel.start("index.html", options=web_app_options)
