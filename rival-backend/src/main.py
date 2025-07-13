from firebase_admin import credentials
import firebase_admin
from src.routes.concentration import concentration_bp
from src.routes.curriculum import curriculum_bp
from src.routes.user import user_bp
from src.models.user import db
from flask_cors import CORS
from flask import Flask
import os
import sys
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


app = Flask(__name__)

# --- 設定 ---
# SECRET_KEYを環境変数から取得
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
if app.config['SECRET_KEY'] == 'default_secret_key':
    print("警告: SECRET_KEYが環境変数に設定されていません。デフォルト値を使用します。")

# データベース設定
if os.environ.get('DATABASE_URL'):
    # AWS RDS PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
elif os.environ.get('AWS_REGION') or os.environ.get('AWS_EXECUTION_ENV'):
    # AWS環境でDATABASE_URLが未設定の場合の警告
    print("警告: AWS環境ですがDATABASE_URLが設定されていません。SQLiteを使用します。")
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
else:
    # ローカル開発用SQLite
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Firebase Admin SDKの初期化（エラーハンドリング強化）
firebase_initialized = False
if os.environ.get('APP_ENV') != 'build':
    try:
        cred_path = os.environ.get('FIREBASE_ADMIN_SDK_PATH')
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            firebase_initialized = True
            print("Firebase Admin SDKを初期化しました。")
        else:
            print("警告: FIREBASE_ADMIN_SDK_PATHが設定されていないか、ファイルが存在しません。")
            # ローカル開発用に、プロジェクト内の特定のパスをフォールバックとして使用
            fallback_path = os.path.join(os.path.dirname(os.path.dirname(
                __file__)), 'ai-study-buddy-rival-firebase-adminsdk-fbsvc-31b2ce778c.json')
            if os.path.exists(fallback_path):
                try:
                    cred = credentials.Certificate(fallback_path)
                    firebase_admin.initialize_app(cred)
                    firebase_initialized = True
                    print(
                        f"フォールバックパス {fallback_path} を使用してFirebase Admin SDKを初期化しました。")
                except Exception as e:
                    print(f"エラー: フォールバックパスからのFirebase Admin SDKの初期化に失敗しました: {e}")
            else:
                print("エラー: Firebase Admin SDKの認証情報が見つかりません。一部の機能が制限される可能性があります。")
    except Exception as e:
        print(f"Firebase Admin SDKの初期化でエラーが発生しました: {e}")
        print("Firebase機能なしでアプリケーションを続行します。")

# --- CORS ---
CORS(app, resources={r"/api/*": {"origins": "*"}})  # APIルートに対してのみCORSを許可

# --- データベース ---
database_initialized = False
if os.environ.get('APP_ENV') != 'build':
    try:
        db.init_app(app)
        with app.app_context():
            if os.environ.get('DATABASE_URL'):
                # AWS RDS用 - 常にテーブル作成を試行（存在する場合はスキップされる）
                db.create_all()
                print("AWS RDSデータベースに接続しました。")
            else:
                # ローカル開発用SQLite
                db_path = os.path.join(os.path.dirname(
                    __file__), 'database', 'app.db')
                if not os.path.exists(db_path):
                    # データベースディレクトリが存在しない場合は作成
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    db.create_all()
                    print("ローカルデータベースを新規作成しました。")
                else:
                    db.create_all()
                    print("既存のローカルデータベースに接続しました。")
        database_initialized = True
    except Exception as e:
        print(f"データベース初期化でエラーが発生しました: {e}")
        print("データベース機能なしでアプリケーションを続行します。")

# --- ルートエンドポイント ---


@app.route('/')
def home():
    return {
        'message': 'Learning Platform API is running!',
        'status': 'healthy',
        'firebase_initialized': firebase_initialized,
        'database_initialized': database_initialized
    }

# --- ヘルスチェック用エンドポイント ---


@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'firebase_initialized': firebase_initialized,
        'database_initialized': database_initialized
    }


# --- Blueprints ---
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(curriculum_bp, url_prefix='/api')
app.register_blueprint(concentration_bp, url_prefix='/api/concentration')

# --- 実行 ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
