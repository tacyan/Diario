#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日記エントリーモデルモジュール

このモジュールは、日記エントリーのデータモデルとデータベース操作を提供します。
日記の保存、取得、検索、編集などの機能を実装しています。

作成者: Claude AI
バージョン: 1.0.0
"""

import os
import json
import uuid
import datetime
import base64
import logging
from pathlib import Path
from sqlitedict import SqliteDict
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

logger = logging.getLogger(__name__)

class DiaryEntry:
    """
    日記エントリーのデータモデルクラス。
    1つの日記エントリーに関するデータと操作を提供します。
    """
    
    def __init__(self, title="", content="", mood=3, tags=None, 
                 location=None, media=None, created_at=None, updated_at=None):
        """
        DiaryEntryクラスのコンストラクタ。
        
        Args:
            title (str): 日記のタイトル
            content (str): 日記の本文（マークダウン形式）
            mood (int): 気分スコア（1-5）
            tags (list): タグのリスト
            location (dict): 位置情報 {'lat': float, 'lng': float, 'name': str}
            media (list): メディアファイルのリスト [{'type': str, 'data': str, 'desc': str}, ...]
            created_at (datetime): 作成日時
            updated_at (datetime): 更新日時
        """
        self.id = str(uuid.uuid4())
        self.title = title
        self.content = content
        self.mood = mood
        self.tags = tags or []
        self.location = location or {}
        self.media = media or []
        self.created_at = created_at or datetime.datetime.now()
        self.updated_at = updated_at or datetime.datetime.now()
    
    def to_dict(self):
        """
        日記エントリーを辞書形式に変換します。
        
        Returns:
            dict: 日記エントリーの辞書表現
        """
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "mood": self.mood,
            "tags": self.tags,
            "location": self.location,
            "media": self.media,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        辞書形式から日記エントリーを作成します。
        
        Args:
            data (dict): 日記エントリーの辞書表現
            
        Returns:
            DiaryEntry: 日記エントリーオブジェクト
        """
        entry = cls(
            title=data.get("title", ""),
            content=data.get("content", ""),
            mood=data.get("mood", 3),
            tags=data.get("tags", []),
            location=data.get("location", {}),
            media=data.get("media", []),
        )
        
        entry.id = data.get("id", entry.id)
        
        # 日時文字列をdatetimeオブジェクトに変換
        if "created_at" in data:
            entry.created_at = datetime.datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            entry.updated_at = datetime.datetime.fromisoformat(data["updated_at"])
            
        return entry
    
    def update(self, title=None, content=None, mood=None, tags=None, location=None, media=None):
        """
        日記エントリーの内容を更新します。
        
        Args:
            title (str, optional): 新しいタイトル
            content (str, optional): 新しい本文
            mood (int, optional): 新しい気分スコア
            tags (list, optional): 新しいタグリスト
            location (dict, optional): 新しい位置情報
            media (list, optional): 新しいメディアリスト
            
        Returns:
            DiaryEntry: 更新された日記エントリー（自身）
        """
        if title is not None:
            self.title = title
        if content is not None:
            self.content = content
        if mood is not None:
            self.mood = mood
        if tags is not None:
            self.tags = tags
        if location is not None:
            self.location = location
        if media is not None:
            self.media = media
            
        self.updated_at = datetime.datetime.now()
        return self
    
    def add_media(self, media_type, data, description=""):
        """
        メディアファイルを日記エントリーに追加します。
        
        Args:
            media_type (str): メディアのタイプ（'image', 'audio', 'video', 'sketch'）
            data (str): Base64エンコードされたメディアデータ
            description (str): メディアの説明
            
        Returns:
            str: 追加されたメディアのID
        """
        media_id = str(uuid.uuid4())
        self.media.append({
            "id": media_id,
            "type": media_type,
            "data": data,
            "description": description,
            "created_at": datetime.datetime.now().isoformat()
        })
        
        self.updated_at = datetime.datetime.now()
        return media_id
    
    def remove_media(self, media_id):
        """
        指定されたIDのメディアを削除します。
        
        Args:
            media_id (str): 削除するメディアのID
            
        Returns:
            bool: 削除が成功したかどうか
        """
        for i, media in enumerate(self.media):
            if media.get("id") == media_id:
                del self.media[i]
                self.updated_at = datetime.datetime.now()
                return True
        return False
    
    def add_tag(self, tag):
        """
        タグを追加します。
        
        Args:
            tag (str): 追加するタグ
            
        Returns:
            bool: 追加が成功したかどうか（すでに存在する場合はFalse）
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.datetime.now()
            return True
        return False
    
    def remove_tag(self, tag):
        """
        タグを削除します。
        
        Args:
            tag (str): 削除するタグ
            
        Returns:
            bool: 削除が成功したかどうか
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.datetime.now()
            return True
        return False

class DiaryEntryManager:
    """
    日記エントリーの管理を行うクラス。
    日記の保存、読み込み、検索、暗号化などの機能を提供します。
    """
    
    def __init__(self, password=None):
        """
        DiaryEntryManagerクラスのコンストラクタ。
        
        Args:
            password (str, optional): 暗号化に使用するパスワード
        """
        self.data_dir = Path.home() / ".diario" / "data"
        self.db_file = self.data_dir / "diary.sqlite"
        self.password = password
        self.entries_cache = {}
        
        # データディレクトリの作成
        if not self.data_dir.exists():
            os.makedirs(self.data_dir, exist_ok=True)
            logger.info(f"データディレクトリを作成しました: {self.data_dir}")
        
        # 必要な場合は暗号化キーを初期化
        self.key = None
        if self.password:
            self._init_encryption()
    
    def _init_encryption(self):
        """
        暗号化に必要なキーを初期化します。
        パスワードからキーを生成し、必要であれば新しいキーを生成して保存します。
        """
        key_file = self.data_dir / "key.bin"
        salt_file = self.data_dir / "salt.bin"
        
        if not salt_file.exists():
            # 新しいsaltを生成
            salt = get_random_bytes(16)
            with open(salt_file, "wb") as f:
                f.write(salt)
        else:
            # 既存のsaltを読み込み
            with open(salt_file, "rb") as f:
                salt = f.read()
        
        # パスワードからキーを生成（単純な方法、実際はより強固な方法を使うべき）
        import hashlib
        dk = hashlib.pbkdf2_hmac('sha256', self.password.encode(), salt, 100000)
        self.key = dk[:32]  # AES-256用に32バイトを使用
    
    def _encrypt_data(self, data):
        """
        JSONデータを暗号化します。
        
        Args:
            data (dict): 暗号化するデータ
            
        Returns:
            bytes: 暗号化されたデータ
        """
        if not self.key:
            return json.dumps(data).encode('utf-8')
        
        # JSONエンコード
        json_data = json.dumps(data).encode('utf-8')
        
        # 暗号化
        cipher = AES.new(self.key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(json_data, AES.block_size))
        
        # IV（初期化ベクトル）と暗号文を結合
        result = cipher.iv + ct_bytes
        return result
    
    def _decrypt_data(self, encrypted_data):
        """
        暗号化されたデータを復号化します。
        
        Args:
            encrypted_data (bytes): 復号化するデータ
            
        Returns:
            dict: 復号化されたデータ
        """
        if not self.key:
            try:
                return json.loads(encrypted_data.decode('utf-8'))
            except:
                return {}
        
        try:
            # IVと暗号文を分離
            iv = encrypted_data[:16]
            ct = encrypted_data[16:]
            
            # 復号化
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            
            # JSONデコード
            return json.loads(pt.decode('utf-8'))
        except Exception as e:
            logger.error(f"データの復号化に失敗しました: {e}")
            return {}
    
    def save_entry(self, entry):
        """
        日記エントリーを保存します。
        
        Args:
            entry (DiaryEntry): 保存する日記エントリー
            
        Returns:
            str: 保存されたエントリーのID
        """
        try:
            with SqliteDict(str(self.db_file), tablename='entries', autocommit=True) as db:
                # 更新日時を更新
                entry.updated_at = datetime.datetime.now()
                
                # エントリーを辞書に変換
                entry_dict = entry.to_dict()
                
                # 暗号化が有効な場合は暗号化
                if self.password:
                    encrypted_data = self._encrypt_data(entry_dict)
                    db[entry.id] = base64.b64encode(encrypted_data).decode('utf-8')
                else:
                    db[entry.id] = json.dumps(entry_dict)
                
                # キャッシュを更新
                self.entries_cache[entry.id] = entry
                
                logger.info(f"日記エントリーを保存しました: ID={entry.id}")
                return entry.id
        except Exception as e:
            logger.error(f"日記エントリーの保存に失敗しました: {e}")
            return None
    
    def get_entry(self, entry_id):
        """
        指定されたIDの日記エントリーを取得します。
        
        Args:
            entry_id (str): 取得する日記エントリーのID
            
        Returns:
            DiaryEntry: 取得した日記エントリー。存在しない場合はNone
        """
        # キャッシュにあればそれを返す
        if entry_id in self.entries_cache:
            return self.entries_cache[entry_id]
        
        try:
            with SqliteDict(str(self.db_file), tablename='entries') as db:
                if entry_id not in db:
                    return None
                
                # データを取得
                data = db[entry_id]
                
                # 暗号化されている場合は復号化
                if self.password:
                    encrypted_data = base64.b64decode(data)
                    entry_dict = self._decrypt_data(encrypted_data)
                else:
                    entry_dict = json.loads(data)
                
                # DiaryEntryオブジェクトを作成
                entry = DiaryEntry.from_dict(entry_dict)
                
                # キャッシュに追加
                self.entries_cache[entry_id] = entry
                
                return entry
        except Exception as e:
            logger.error(f"日記エントリーの取得に失敗しました: ID={entry_id}, エラー={e}")
            return None
    
    def delete_entry(self, entry_id):
        """
        指定されたIDの日記エントリーを削除します。
        
        Args:
            entry_id (str): 削除する日記エントリーのID
            
        Returns:
            bool: 削除が成功したかどうか
        """
        try:
            with SqliteDict(str(self.db_file), tablename='entries', autocommit=True) as db:
                if entry_id in db:
                    del db[entry_id]
                    
                    # キャッシュからも削除
                    if entry_id in self.entries_cache:
                        del self.entries_cache[entry_id]
                    
                    logger.info(f"日記エントリーを削除しました: ID={entry_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"日記エントリーの削除に失敗しました: ID={entry_id}, エラー={e}")
            return False
    
    def get_all_entries(self):
        """
        すべての日記エントリーを取得します。
        
        Returns:
            list: DiaryEntryオブジェクトのリスト
        """
        entries = []
        try:
            with SqliteDict(str(self.db_file), tablename='entries') as db:
                for entry_id in db:
                    entry = self.get_entry(entry_id)
                    if entry:
                        entries.append(entry)
                        
            # 作成日時の降順でソート
            entries.sort(key=lambda x: x.created_at, reverse=True)
            return entries
        except Exception as e:
            logger.error(f"すべての日記エントリーの取得に失敗しました: {e}")
            return []
    
    def search_entries(self, query=None, tags=None, date_from=None, date_to=None, mood=None):
        """
        指定された条件で日記エントリーを検索します。
        
        Args:
            query (str, optional): 検索クエリ
            tags (list, optional): 検索するタグのリスト
            date_from (datetime, optional): この日時以降のエントリーを検索
            date_to (datetime, optional): この日時以前のエントリーを検索
            mood (int, optional): 指定された気分スコアのエントリーを検索
            
        Returns:
            list: 検索条件に一致するDiaryEntryオブジェクトのリスト
        """
        all_entries = self.get_all_entries()
        filtered_entries = []
        
        for entry in all_entries:
            # テキスト検索
            if query and not (
                query.lower() in entry.title.lower() or 
                query.lower() in entry.content.lower()
            ):
                continue
            
            # タグ検索
            if tags and not any(tag in entry.tags for tag in tags):
                continue
            
            # 日付範囲検索
            if date_from and entry.created_at < date_from:
                continue
            if date_to and entry.created_at > date_to:
                continue
            
            # 気分スコア検索
            if mood is not None and entry.mood != mood:
                continue
            
            filtered_entries.append(entry)
        
        return filtered_entries
    
    def get_entries_by_date(self, year, month=None, day=None):
        """
        指定された年月日の日記エントリーを取得します。
        
        Args:
            year (int): 年
            month (int, optional): 月
            day (int, optional): 日
            
        Returns:
            list: 指定された日付に一致するDiaryEntryオブジェクトのリスト
        """
        all_entries = self.get_all_entries()
        filtered_entries = []
        
        for entry in all_entries:
            if entry.created_at.year != year:
                continue
            
            if month is not None and entry.created_at.month != month:
                continue
                
            if day is not None and entry.created_at.day != day:
                continue
            
            filtered_entries.append(entry)
        
        return filtered_entries
    
    def get_all_tags(self):
        """
        すべての日記エントリーで使用されているタグのリストを取得します。
        
        Returns:
            list: 使用されているすべてのタグのリスト
        """
        all_entries = self.get_all_entries()
        all_tags = set()
        
        for entry in all_entries:
            all_tags.update(entry.tags)
        
        return sorted(list(all_tags))
    
    def get_mood_stats(self, date_from=None, date_to=None):
        """
        指定された期間の気分統計を取得します。
        
        Args:
            date_from (datetime, optional): この日時以降の統計を計算
            date_to (datetime, optional): この日時以前の統計を計算
            
        Returns:
            dict: 気分スコアごとのエントリー数
        """
        entries = self.get_all_entries()
        
        # 日付でフィルタリング
        if date_from or date_to:
            filtered_entries = []
            for entry in entries:
                if date_from and entry.created_at < date_from:
                    continue
                if date_to and entry.created_at > date_to:
                    continue
                filtered_entries.append(entry)
            entries = filtered_entries
        
        # 気分スコアをカウント
        mood_stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for entry in entries:
            if entry.mood in mood_stats:
                mood_stats[entry.mood] += 1
        
        return mood_stats
    
    def change_password(self, new_password):
        """
        暗号化パスワードを変更します。すべてのエントリーを再暗号化します。
        
        Args:
            new_password (str): 新しいパスワード
            
        Returns:
            bool: パスワード変更が成功したかどうか
        """
        try:
            # すべてのエントリーを取得
            all_entries = self.get_all_entries()
            
            # 新しいパスワードでマネージャーを初期化
            old_password = self.password
            self.password = new_password
            self._init_encryption()
            
            # すべてのエントリーを新しいパスワードで再暗号化して保存
            for entry in all_entries:
                self.save_entry(entry)
            
            logger.info("パスワードが正常に変更されました")
            return True
        except Exception as e:
            # エラーが発生した場合は元のパスワードに戻す
            self.password = old_password
            if old_password:
                self._init_encryption()
            
            logger.error(f"パスワードの変更に失敗しました: {e}")
            return False 