#!/usr/bin/env python3
"""
SQLiteからAWS RDS PostgreSQLへのデータ移行スクリプト
"""
import os
import sys
import sqlite3
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

# 環境変数を読み込み
load_dotenv()


def migrate_data():
    # SQLiteデータベースパス
    sqlite_path = os.path.join(os.path.dirname(
        __file__), 'src', 'database', 'app.db')

    # PostgreSQL接続情報
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("エラー: DATABASE_URL環境変数が設定されていません")
        return False

    # URLをパース
    url = urlparse(database_url)

    try:
        # SQLite接続
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()

        # PostgreSQL接続
        pg_conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],  # 先頭の'/'を除去
            user=url.username,
            password=url.password
        )
        pg_cursor = pg_conn.cursor()

        print("データベース接続成功")

        # テーブル一覧を取得
        tables = ['user', 'daily_report', 'curriculum', 'curriculum_progress']

        for table in tables:
            print(f"\n{table}テーブルを移行中...")

            # SQLiteからデータを取得
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()

            if not rows:
                print(f"{table}テーブルにデータがありません")
                continue

            # カラム名を取得
            columns = [description[0]
                       for description in sqlite_cursor.description]

            # PostgreSQLにデータを挿入
            placeholders = ','.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

            for row in rows:
                try:
                    pg_cursor.execute(insert_query, tuple(row))
                except Exception as e:
                    print(f"行の挿入エラー: {e}")
                    continue

            pg_conn.commit()
            print(f"{table}テーブルの移行完了: {len(rows)}行")

        print("\nデータ移行が完了しました")
        return True

    except sqlite3.Error as e:
        print(f"SQLiteエラー: {e}")
        return False
    except psycopg2.Error as e:
        print(f"PostgreSQLエラー: {e}")
        return False
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return False
    finally:
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()


if __name__ == "__main__":
    # if not os.path.exists(os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')):
    #         print("SQLiteデータベースファイルが見つかりません")
    #         sys.exit(1)

    # success = migrate_data()
    # sys.exit(0 if success else 1)
    pass
