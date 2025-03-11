#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
エディタービューモジュール

このモジュールは、日記の作成と編集のためのエディターUIを提供します。
リッチテキスト編集、タイトル設定、タグ付け、感情記録などの機能を含みます。

作成者: Claude AI
バージョン: 1.0.0
"""

import flet as ft
import datetime
import logging
import os
import re
from components.mood_tracker import MoodTracker
from models.diary_entry import DiaryEntry

logger = logging.getLogger(__name__)

class EditorView:
    """
    日記の作成と編集のためのエディタービュークラス。
    リッチテキスト編集機能と各種メタデータ入力フォームを提供します。
    """
    
    def __init__(self, app):
        """
        EditorViewクラスのコンストラクタ。
        
        Args:
            app: メインアプリケーションの参照
        """
        self.app = app
        self.diary_manager = app.diary_manager
        self.current_entry = None
        self.is_new_entry = True
        
        # 編集フィールドの参照
        self.title_field = None
        self.content_field = None
        self.tag_field = None
        self.mood_tracker = None
        
        # リアルタイムプレビュー用の参照
        self.preview_title_ref = ft.Ref[ft.Text]()
        self.preview_content_ref = ft.Ref[ft.Markdown]()
        
        # フォーマットモード管理
        self.active_format = None
        self.format_modes = {
            "bold": False,
            "italic": False,
            "underline": False,
            "strikethrough": False,
            "code": False,
            "link": False,
        }
    
    def build(self):
        """
        エディター画面のUIを構築します。
        エラーが発生した場合は適切なエラーメッセージを表示します。
        
        Returns:
            ft.Container: エディター画面のUIコンテナ
        """
        try:
            # 既存のエントリーを編集するか、新規作成するかを判断
            self._load_entry()
            
            # タイトル入力フィールド
            self.title_field = ft.TextField(
                label="タイトル",
                value=self.current_entry.title if self.current_entry else "",
                border_radius=10,
                text_size=18,
                autofocus=True,
                prefix_icon=ft.icons.TITLE,
                on_change=self._on_field_change,
            )
            
            # 日付表示
            created_date = self.current_entry.created_at if self.current_entry else datetime.datetime.now()
            date_str = created_date.strftime("%Y年%m月%d日 %H:%M")
            date_display = ft.Text(f"作成日時: {date_str}", size=14, color=ft.colors.ON_SURFACE_VARIANT)
            
            # タグ入力フィールド
            current_tags = ", ".join(self.current_entry.tags) if self.current_entry and self.current_entry.tags else ""
            self.tag_field = ft.TextField(
                label="タグ（カンマ区切り）",
                value=current_tags,
                border_radius=10,
                prefix_icon=ft.icons.TAG,
                on_change=self._on_field_change,
                helper_text="例: 仕事, 家族, 旅行",
            )
            
            # 気分トラッカー
            initial_mood = None
            if self.current_entry:
                initial_mood = self.current_entry.mood
            elif hasattr(self.app, 'current_mood') and self.app.current_mood:
                initial_mood = self.app.current_mood
            
            self.mood_tracker = MoodTracker(
                on_mood_selected=self._on_mood_selected,
                initial_mood=initial_mood
            )
            
            # メディアボタン
            media_button = ft.ElevatedButton(
                "画像を追加",
                icon=ft.icons.IMAGE,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                on_click=self._on_add_media_click,
            )
            
            # フォーマットツールバー
            formatting_toolbar = self._build_formatting_toolbar()
            
            # コンテンツ入力フィールド
            self.content_field = ft.TextField(
                value=self.current_entry.content if self.current_entry else "",
                multiline=True,
                min_lines=10,
                max_lines=30,
                text_size=16,
                border_radius=10,
                on_change=self._on_field_change,
            )
            
            # メディアツールバー
            media_toolbar = self._build_media_toolbar()
            
            # 保存ボタンとその他のアクションボタン
            action_buttons = ft.Row([
                ft.FilledButton(
                    text="保存",
                    icon=ft.icons.SAVE,
                    on_click=self._on_save_click,
                ),
                ft.OutlinedButton(
                    text="記事表示モード",
                    icon=ft.icons.VISIBILITY,
                    on_click=self._on_preview_click,
                ),
                ft.OutlinedButton(
                    text=f"{'マークダウン' if self.current_entry and getattr(self.current_entry, 'is_markdown', False) else 'リッチテキスト'}として保存",
                    icon=ft.icons.CODE,
                    on_click=self._on_format_toggle,
                    tooltip="マークダウンとリッチテキスト形式を切り替えます",
                )
            ])

            # エディター部分
            editor_section = ft.Column([
                self.title_field,
                # 日付表示とタグフィールドを水平に配置し、間にスペースを挿入
                ft.Row([date_display, ft.Container(expand=True), self.tag_field], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                formatting_toolbar,
                self.content_field,
                media_toolbar,
                action_buttons,
            ], spacing=15)

            # プレビューコンテナ（初期状態では表示しない）
            self.preview_container = ft.Container(
                visible=False,
                content=self._build_preview(),
                bgcolor=ft.colors.SURFACE,
                border_radius=10,
                padding=20,
                margin=ft.margin.only(top=20),
            )
            
            # メインのスクロール可能なコンテンツ領域
            main_content = ft.Column(
                [
                    editor_section,
                    self.preview_container
                ],
                scroll=ft.ScrollMode.AUTO,
                auto_scroll=False,
                spacing=20
            )
            
            # 全体のコンテナ
            return ft.Container(
                content=main_content,
                padding=20,
                width=float('inf'),
                height=float('inf'),
            )
        except Exception as e:
            logger.error(f"エディター画面の構築中にエラーが発生しました: {e}", exc_info=True)
            return ft.Container(
                content=ft.Column([
                    ft.Text("エラーが発生しました。後でもう一度お試しください。", style=ft.TextStyle(color=ft.colors.ERROR)),
                    ft.ElevatedButton("ホームに戻る", on_click=lambda _: self.app.navigate("home")),
                ]),
                padding=20,
                width=float('inf'),
                height=float('inf'),
            )
    
    def _load_entry(self):
        """
        編集するエントリーを読み込みます。
        """
        # アプリの状態から編集するエントリーIDを取得
        entry_id = getattr(self.app, 'current_entry_id', None)
        
        if entry_id:
            # 既存のエントリーを読み込む
            self.current_entry = self.diary_manager.get_entry(entry_id)
            self.is_new_entry = False
            
            # エントリーが見つからない場合は新規作成
            if not self.current_entry:
                self.current_entry = None
                self.is_new_entry = True
                logger.warning(f"エントリーが見つかりません: ID={entry_id}")
        else:
            # 新規エントリーの作成
            self.current_entry = None
            self.is_new_entry = True
        
        # 編集後はIDをクリア
        if hasattr(self.app, 'current_entry_id'):
            delattr(self.app, 'current_entry_id')
    
    def _on_field_change(self, e):
        """
        フィールドの値が変更されたときのイベントハンドラ。
        フォーマットモードが有効な場合は、入力テキストに適用します。
        
        Args:
            e: イベントデータ
        """
        # アクティブなフォーマットモードがある場合の処理
        if e.control == self.content_field and self.active_format:
            # 最後に入力された文字を取得（簡易的）
            current_value = self.content_field.value or ""
            last_char = current_value[-1:] if current_value else ""
            
            # スペースや改行が入力された場合はフォーマットを適用
            if last_char in [' ', '\n', '\t', '.', ',', '!', '?', ')', ']', '}']:
                self._apply_active_format()
        
        # リアルタイムプレビューモードの場合も更新
        if hasattr(self, 'is_realtime_preview') and self.is_realtime_preview:
            # コンテンツの更新
            if e.control == self.content_field:
                self._update_realtime_preview_content()
            
            # タイトルの更新
            if e.control == self.title_field:
                self._update_realtime_preview_title()
    
    def _on_mood_selected(self, mood):
        """
        気分が選択されたときのイベントハンドラ。
        
        Args:
            mood: 選択された気分スコア（1-5）
        """
        # 現在の気分を更新
        if hasattr(self.app, 'current_mood'):
            delattr(self.app, 'current_mood')
    
    def _on_add_media_click(self, e):
        """
        メディア追加ボタンがクリックされたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        # ファイル選択ダイアログを表示
        def pick_files_result(e: ft.FilePickerResultEvent):
            if e.files:
                for f in e.files:
                    logger.info(f"選択されたファイル: {f.name}, {f.path}")
                    
                    # ファイルパスを取得
                    file_path = f.path
                    
                    # 画像のマークダウン構文を挿入
                    if file_path:
                        self._insert_markdown_syntax(f"![{f.name}](", f"{file_path})")
                    else:
                        # パスが取得できない場合はエラーメッセージを表示
                        self.app.page.show_snack_bar(
                            ft.SnackBar(ft.Text("画像パスの取得に失敗しました"))
                        )
        
        # ファイルピッカーを作成
        file_picker = ft.FilePicker(on_result=pick_files_result)
        self.app.page.overlay.append(file_picker)
        self.app.page.update()
        
        # 画像ファイルのみ選択可能に
        file_picker.pick_files(
            allowed_extensions=["png", "jpg", "jpeg", "gif"],
            allow_multiple=False,
        )
    
    def _insert_markdown_syntax(self, prefix, suffix):
        """
        マークダウン構文を挿入または、フォーマットモードを切り替えます。
        
        Args:
            prefix: 選択範囲の前に挿入するテキスト
            suffix: 選択範囲の後に挿入するテキスト
        """
        # フォーマットタイプを特定
        format_type = None
        if prefix == "**" and suffix == "**":
            format_type = "bold"
        elif prefix == "*" and suffix == "*":
            format_type = "italic"
        elif prefix == "<u>" and suffix == "</u>":
            format_type = "underline"
        elif prefix == "~~" and suffix == "~~":
            format_type = "strikethrough"
        elif prefix == "```" and suffix == "```":
            format_type = "code"
        elif prefix == "[" and suffix.startswith("]("):
            format_type = "link"
        
        # 画像挿入の場合は特別処理
        if prefix.startswith("![") and suffix.endswith(")"):
            # 現在の値を取得
            current_value = self.content_field.value or ""
            # 挿入 (suffixにはすでにパスが含まれている)
            new_value = current_value + prefix + suffix
            self.content_field.value = new_value
            self.content_field.update()
            
            # リアルタイムプレビューの更新
            if hasattr(self, 'is_realtime_preview') and self.is_realtime_preview:
                self._update_realtime_preview_content()
            return
        
        # フォーマットモード切替え
        if format_type and format_type in self.format_modes:
            # 現在のモードを反転
            self.format_modes[format_type] = not self.format_modes[format_type]
            
            # アクティブなフォーマットを設定
            if self.format_modes[format_type]:
                self.active_format = format_type
                # アクティブなボタンの表示を変更
                self._update_format_button_state(format_type, True)
                # ユーザーに通知
                self.app.page.show_snack_bar(
                    ft.SnackBar(ft.Text(f"{self._get_format_name(format_type)}モードがオンになりました"))
                )
            else:
                self.active_format = None
                # ボタンの表示を戻す
                self._update_format_button_state(format_type, False)
                # ユーザーに通知
                self.app.page.show_snack_bar(
                    ft.SnackBar(ft.Text(f"{self._get_format_name(format_type)}モードがオフになりました"))
                )
        else:
            # 従来の方法（直接挿入）
            # 現在の選択範囲を取得
            current_value = self.content_field.value or ""
            
            # 選択テキストがない場合は、プレースホルダーを表示
            placeholder = ""
            if prefix == "**" and suffix == "**":
                placeholder = "太字テキスト"
            elif prefix == "*" and suffix == "*":
                placeholder = "斜体テキスト"
            elif prefix == "<u>" and suffix == "</u>":
                placeholder = "下線テキスト"
            elif prefix == "~~" and suffix == "~~":
                placeholder = "取り消し線テキスト"
            elif prefix == "```" and suffix == "```":
                placeholder = "コードブロック"
            elif prefix == "[" and suffix.startswith("]("):
                placeholder = "リンクテキスト"
            else:
                placeholder = "テキスト"
            
            # 挿入
            new_value = current_value + prefix + placeholder + suffix
            self.content_field.value = new_value
            self.content_field.update()
        
        # リアルタイムプレビューの更新
        if hasattr(self, 'is_realtime_preview') and self.is_realtime_preview:
            self._update_realtime_preview_content()
    
    def _get_format_name(self, format_type):
        """
        フォーマットタイプの日本語名を取得します。
        
        Args:
            format_type: フォーマットタイプ
            
        Returns:
            str: フォーマットの日本語名
        """
        format_names = {
            "bold": "太字",
            "italic": "斜体",
            "underline": "下線",
            "strikethrough": "取り消し線",
            "code": "コード",
            "link": "リンク",
        }
        return format_names.get(format_type, format_type)
    
    def _update_format_button_state(self, format_type, is_active):
        """
        フォーマットボタンの状態を更新します。
        
        Args:
            format_type: フォーマットタイプ
            is_active: アクティブかどうか
        """
        # 現在のところ実装なし（将来的にボタンの外観を変更する場合に実装）
        pass
    
    def _insert_markdown_prefix(self, prefix):
        """
        行の先頭にマークダウン構文を挿入します。
        
        Args:
            prefix: 行の先頭に挿入するテキスト
        """
        # 現在の値を取得
        current_value = self.content_field.value or ""
        
        # 見出しの場合は、プレースホルダーを追加
        placeholder = ""
        if prefix.startswith("#"):
            heading_level = prefix.count("#")
            placeholder = f" 見出し{heading_level}"
        elif prefix == "- ":
            placeholder = "箇条書き項目"
        elif prefix == "1. ":
            placeholder = "番号付き項目"
        elif prefix == "> ":
            placeholder = "引用テキスト"
        
        # カーソル位置に応じて挿入（簡易的な実装）
        lines = current_value.split("\n")
        if lines:
            lines[0] = prefix + placeholder
            self.content_field.value = "\n".join(lines)
            self.content_field.update()
            
        # リアルタイムプレビューの更新
        if hasattr(self, 'is_realtime_preview') and self.is_realtime_preview:
            self._update_realtime_preview_content()
            
    def _update_realtime_preview_content(self):
        """
        リアルタイムプレビューのコンテンツを更新します。
        マークダウンを直接コンポーネントに設定します。
        """
        if self.preview_content_ref.current:
            # コンテンツをそのままMarkdownウィジェットに設定
            md_content = self.content_field.value or ""
            
            # 画像パスをフルパスに変換
            md_content = self._process_markdown_image_paths(md_content)
            
            # マークダウンに設定
            self.preview_content_ref.current.value = md_content
            self.preview_content_ref.current.update()
        
        self.preview_container.update()
        
    def _process_markdown_image_paths(self, md_text):
        """
        マークダウン内の画像パスを表示用に処理します。
        Base64エンコードを使わず、file:// プロトコルを使用します。
        
        Args:
            md_text (str): 処理するマークダウンテキスト
            
        Returns:
            str: 画像パスが処理されたマークダウンテキスト
        """
        try:
            # マークダウンの画像パターン: ![alt](path)
            img_pattern = r'!\[.*?\]\((.*?)\)'
            
            def replace_img_path(match):
                img_path = match.group(1)
                
                # 既にURLや埋め込み画像の場合はそのまま
                if img_path.startswith(('http://', 'https://', 'data:')):
                    return match.group(0)
                    
                # 既にfile://で始まる場合は そのまま返す
                if img_path.startswith('file://'):
                    return match.group(0)
                
                # ローカルパスの場合は適切なURIに変換
                if os.path.exists(img_path):
                    # 絶対パスに変換
                    abs_path = os.path.abspath(img_path)
                    
                    # パスを変換
                    if os.name == 'nt':  # Windows
                        # バックスラッシュをスラッシュに変換
                        abs_path = abs_path.replace('\\', '/')
                        # file:///C:/path 形式のURIを作成
                        img_uri = f"file:///{abs_path}"
                    else:  # Unix系
                        img_uri = f"file://{abs_path}"
                    
                    logger.info(f"画像パス変換: {img_path} -> {img_uri}")
                    return match.group(0).replace(img_path, img_uri)
                
                # ファイルが存在しない場合は警告ログを出力
                logger.warning(f"画像ファイルが見つかりません: {img_path}")
                return match.group(0)
            
            return re.sub(img_pattern, replace_img_path, md_text)
        except Exception as e:
            logger.error(f"画像パス処理エラー: {e}", exc_info=True)
            return md_text
    
    def _toggle_realtime_preview(self, e):
        """
        リアルタイムプレビューモードの切り替えを行います。
        
        Args:
            e: イベントデータ
        """
        # 初期化
        if not hasattr(self, 'is_realtime_preview'):
            self.is_realtime_preview = False
            
        self.is_realtime_preview = not self.is_realtime_preview
        
        # フィールドとプレビューの表示切り替え
        self.content_field.visible = not self.is_realtime_preview
        self.preview_container.visible = self.is_realtime_preview
        
        # プレビューモードなら、マークダウンをHTMLに変換して表示
        if self.is_realtime_preview:
            # プレビューコンテンツを更新
            self._update_realtime_preview_title()
            self._update_realtime_preview_content()
            
        # ボタンのテキスト更新
        try:
            # プレビューコンテナの最初の子要素（タイトルバー）を取得
            title_bar = self.preview_container.content.controls[0]
            # タイトルバーの中のボタンを取得
            button = title_bar.content.controls[0]
            
            if self.is_realtime_preview:
                button.text = "編集モードに戻る"
                button.icon = ft.icons.EDIT
            else:
                button.text = "記事表示モード"
                button.icon = ft.icons.ARTICLE_OUTLINED
                
            button.update()
        except Exception as e:
            logger.error(f"プレビューボタンの更新中にエラーが発生しました: {e}", exc_info=True)
        
        self.preview_container.update()
        self.content_field.update()
        self.preview_container.content.update()
        
    def _update_realtime_preview_title(self):
        """
        リアルタイムプレビューのタイトルを更新します。
        """
        if self.preview_title_ref.current:
            self.preview_title_ref.current.value = self.title_field.value
            self.app.page.update()
            
    def _on_preview_title_change(self, e):
        """
        プレビュータイトルが変更されたときの処理を行います。
        
        Args:
            e (ft.ControlEvent): コントロールイベント
        """
        if self.title_field:
            self.title_field.value = e.control.value
            self.app.page.update()
    
    def _on_save_click(self, e):
        """
        保存ボタンがクリックされたときのイベントハンドラ。
        記事をマークダウン形式で保存します。
        
        Args:
            e: イベントデータ
        """
        try:
            # フォームからデータを取得
            title = self.title_field.value
            content = self.content_field.value
            
            # 画像パスを保存可能な形式に処理
            content = self._prepare_markdown_for_save(content)
            
            # タグを分割
            tags = [tag.strip() for tag in self.tag_field.value.split(",") if tag.strip()]
            
            # 気分スコア
            mood = self.mood_tracker.selected_mood or 3
            
            if self.is_new_entry:
                # 新規エントリーの作成
                entry = DiaryEntry(
                    title=title,
                    content=content,
                    mood=mood,
                    tags=tags,
                )
                self.diary_manager.save_entry(entry)
                entry_id = entry.id
                logger.info(f"新しい日記エントリーを作成しました: ID={entry_id}")
            else:
                # 既存エントリーの更新
                self.current_entry.update(
                    title=title,
                    content=content,
                    mood=mood,
                    tags=tags,
                )
                self.diary_manager.save_entry(self.current_entry)
                entry_id = self.current_entry.id
                logger.info(f"日記エントリーを更新しました: ID={entry_id}")
            
            # 成功メッセージを表示
            self.app.page.show_snack_bar(
                ft.SnackBar(ft.Text("日記を保存しました！"))
            )
            
            # ホーム画面に戻る
            self.app.navigate("home")
            
        except Exception as e:
            logger.error(f"日記の保存中にエラーが発生しました: {e}", exc_info=True)
            
            # エラーメッセージを表示
            self.app.page.show_snack_bar(
                ft.SnackBar(ft.Text(f"エラー: 日記の保存に失敗しました"))
            )
    
    def _prepare_markdown_for_save(self, md_text):
        """
        マークダウン内の画像パスを保存用に処理します。
        表示用URIをローカルパスに戻します。
        
        Args:
            md_text (str): 処理するマークダウンテキスト
            
        Returns:
            str: 保存用に処理されたマークダウンテキスト
        """
        try:
            # 画像参照パターン: ![alt](path)
            img_pattern = r'!\[.*?\]\((.*?)\)'
            
            def process_image_path(match):
                img_path = match.group(1)
                
                # HTTP(S)やデータURIの場合はそのまま
                if img_path.startswith(('http://', 'https://', 'data:')):
                    return match.group(0)
                
                # ファイルURIの場合(file:///C:/path/to/file.jpg)
                if img_path.startswith('file:///'):
                    # Windowsの場合: file:///C:/path/to/file.jpg -> C:/path/to/file.jpg
                    file_path = img_path[8:]
                    return match.group(0).replace(img_path, file_path)
                elif img_path.startswith('file://'):
                    # Unixの場合: file:///path/to/file.jpg -> /path/to/file.jpg
                    file_path = img_path[7:]
                    return match.group(0).replace(img_path, file_path)
                
                # その他の場合（既に相対パスなど）
                return match.group(0)
            
            return re.sub(img_pattern, process_image_path, md_text)
        
        except Exception as e:
            logger.error(f"マークダウン保存前処理エラー: {e}", exc_info=True)
            # エラーが発生した場合は元のテキストをそのまま返す
            return md_text
    
    def _on_delete_click(self, e):
        """
        削除ボタンがクリックされたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        # 新規エントリーの場合は単にホームに戻る
        if self.is_new_entry:
            self.app.navigate("home")
            return
        
        # 確認ダイアログを表示
        def close_dialog(e):
            # ダイアログを閉じる
            dialog.open = False
            self.app.page.update()
            
            # 削除ボタンが押された場合
            if e.control.text == "削除":
                try:
                    # エントリーを削除
                    self.diary_manager.delete_entry(self.current_entry.id)
                    logger.info(f"日記エントリーを削除しました: ID={self.current_entry.id}")
                    
                    # 成功メッセージを表示
                    self.app.page.show_snack_bar(
                        ft.SnackBar(ft.Text("日記を削除しました"))
                    )
                    
                    # ホーム画面に戻る
                    self.app.navigate("home")
                    
                except Exception as ex:
                    logger.error(f"日記の削除中にエラーが発生しました: {ex}")
                    
                    # エラーメッセージを表示
                    self.app.page.show_snack_bar(
                        ft.SnackBar(ft.Text(f"エラー: 日記の削除に失敗しました"))
                    )
        
        # 確認ダイアログ
        dialog = ft.AlertDialog(
            title=ft.Text("日記の削除"),
            content=ft.Text("この日記を削除してもよろしいですか？この操作は元に戻せません。"),
            actions=[
                ft.TextButton("キャンセル", on_click=close_dialog),
                ft.TextButton("削除", on_click=close_dialog),
            ],
        )
        
        # ダイアログを表示
        self.app.page.dialog = dialog
        dialog.open = True
        self.app.page.update()
    
    def _apply_active_format(self):
        """
        アクティブなフォーマットモードを現在のテキストに適用します。
        """
        if not self.active_format:
            return
            
        # 現在のテキストを取得
        current_value = self.content_field.value or ""
        
        # 最後の単語を抽出（簡易的な実装）
        words = current_value.split()
        if not words:
            return
            
        last_word = words[-1]
        # 句読点などを分離
        punctuation = ''
        if last_word and last_word[-1] in ['.', ',', '!', '?', ')', ']', '}']:
            punctuation = last_word[-1]
            last_word = last_word[:-1]
            
        if not last_word:
            return
            
        # フォーマットを適用
        formatted_word = last_word
        if self.active_format == "bold":
            formatted_word = f"**{last_word}**"
        elif self.active_format == "italic":
            formatted_word = f"*{last_word}*"
        elif self.active_format == "underline":
            formatted_word = f"<u>{last_word}</u>"
        elif self.active_format == "strikethrough":
            formatted_word = f"~~{last_word}~~"
        elif self.active_format == "code":
            formatted_word = f"`{last_word}`"
        elif self.active_format == "link":
            formatted_word = f"[{last_word}](https://example.com)"
            
        # 句読点を戻す
        formatted_word += punctuation
            
        # テキストを置換
        words[-1] = formatted_word
        self.content_field.value = ' '.join(words)
        self.content_field.update()
        
        # リアルタイムプレビューの更新
        if hasattr(self, 'is_realtime_preview') and self.is_realtime_preview:
            self._update_realtime_preview_content() 
    
    def _build_formatting_toolbar(self):
        """
        テキスト書式設定用のツールバーを構築します。
        
        Returns:
            ft.Row: 書式設定ツールバーのUI
        """
        return ft.Row([
            ft.IconButton(
                icon=ft.icons.FORMAT_BOLD,
                icon_color=ft.colors.PRIMARY,
                tooltip="太字",
                on_click=lambda e: self._insert_markdown_syntax("**", "**"),
            ),
            ft.IconButton(
                icon=ft.icons.FORMAT_ITALIC,
                icon_color=ft.colors.PRIMARY,
                tooltip="斜体",
                on_click=lambda e: self._insert_markdown_syntax("*", "*"),
            ),
            ft.IconButton(
                icon=ft.icons.FORMAT_UNDERLINED,
                icon_color=ft.colors.PRIMARY,
                tooltip="下線",
                on_click=lambda e: self._insert_markdown_syntax("<u>", "</u>"),
            ),
            ft.IconButton(
                icon=ft.icons.FORMAT_STRIKETHROUGH,
                icon_color=ft.colors.PRIMARY,
                tooltip="取り消し線",
                on_click=lambda e: self._insert_markdown_syntax("~~", "~~"),
            ),
            ft.VerticalDivider(width=1),
            ft.IconButton(
                icon=ft.icons.FORMAT_LIST_BULLETED,
                icon_color=ft.colors.PRIMARY,
                tooltip="箇条書き",
                on_click=lambda e: self._insert_markdown_prefix("- "),
            ),
            ft.IconButton(
                icon=ft.icons.FORMAT_LIST_NUMBERED,
                icon_color=ft.colors.PRIMARY,
                tooltip="番号付きリスト",
                on_click=lambda e: self._insert_markdown_prefix("1. "),
            ),
            ft.IconButton(
                icon=ft.icons.FORMAT_QUOTE,
                icon_color=ft.colors.PRIMARY,
                tooltip="引用",
                on_click=lambda e: self._insert_markdown_prefix("> "),
            ),
            ft.VerticalDivider(width=1),
            # 見出しドロップダウン
            ft.PopupMenuButton(
                icon=ft.icons.TITLE,
                tooltip="見出し",
                items=[
                    ft.PopupMenuItem(
                        text="見出し 1",
                        on_click=lambda e: self._insert_markdown_prefix("# "),
                    ),
                    ft.PopupMenuItem(
                        text="見出し 2",
                        on_click=lambda e: self._insert_markdown_prefix("## "),
                    ),
                    ft.PopupMenuItem(
                        text="見出し 3",
                        on_click=lambda e: self._insert_markdown_prefix("### "),
                    ),
                ],
            ),
            ft.IconButton(
                icon=ft.icons.CODE,
                icon_color=ft.colors.PRIMARY,
                tooltip="コード",
                on_click=lambda e: self._insert_markdown_syntax("```", "```"),
            ),
            ft.IconButton(
                icon=ft.icons.LINK,
                icon_color=ft.colors.PRIMARY,
                tooltip="リンク",
                on_click=lambda e: self._insert_markdown_syntax("[", "](https://example.com)"),
            ),
        ], scroll=ft.ScrollMode.AUTO)
        
    def _build_media_toolbar(self):
        """
        メディア挿入用のツールバーを構築します。
        
        Returns:
            ft.Row: メディアツールバーのUI
        """
        return ft.Row([
            ft.ElevatedButton(
                "画像を追加",
                icon=ft.icons.IMAGE,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                on_click=self._on_add_media_click,
            ),
        ], alignment=ft.MainAxisAlignment.END)
    
    def _build_preview(self):
        """
        記事プレビュー画面のUIを構築します。
        
        Returns:
            ft.Column: プレビュー画面のUI
        """
        return ft.Column([
            # タイトルバー
            ft.Container(
                content=ft.Row(
                    [
                        ft.OutlinedButton(
                            text="編集モードに戻る",
                            icon=ft.icons.EDIT,
                            on_click=self._toggle_realtime_preview,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
                padding=10,
                border_radius=ft.border_radius.only(
                    top_left=10, top_right=10
                ),
            ),
            # プレビューコンテンツ
            ft.Container(
                content=ft.Column(
                    [
                        # タイトル表示
                        ft.Container(
                            content=ft.TextField(
                                value=self.title_field.value if self.title_field else "",
                                label=None,
                                border="none",
                                text_size=28,
                                text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                                on_change=self._on_preview_title_change,
                                ref=self.preview_title_ref,
                            ),
                            margin=ft.margin.only(bottom=20),
                        ),
                        # 本文コンテンツ - マークダウン表示に変更
                        ft.Container(
                            content=ft.Markdown(
                                value=self.content_field.value if self.content_field else "",
                                selectable=True,
                                extension_set="commonmark",
                                code_theme="atom-one-dark",
                                on_tap_link=lambda e: self.app.page.launch_url(e.data),
                                ref=self.preview_content_ref,
                            ),
                            expand=True,
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    auto_scroll=False,
                ),
                padding=ft.padding.all(30),
                bgcolor=ft.colors.SURFACE_VARIANT,
                border_radius=ft.border_radius.only(
                    bottom_left=10, bottom_right=10
                ),
                expand=True,
            ),
        ])
    
    def _on_preview_click(self, e):
        """
        プレビューボタンがクリックされたときのイベントハンドラ。
        リアルタイムプレビューを切り替えます。
        
        Args:
            e: イベントデータ
        """
        self._toggle_realtime_preview(e)
    
    def _on_format_toggle(self, e):
        """
        フォーマット切り替えボタンがクリックされたときのイベントハンドラ。
        マークダウンとリッチテキスト形式を切り替えます。
        
        Args:
            e: イベントデータ
        """
        if self.current_entry:
            # 現在のフォーマットを反転
            is_markdown = getattr(self.current_entry, 'is_markdown', False)
            self.current_entry.is_markdown = not is_markdown
            
            # ボタンテキストを更新
            new_text = "リッチテキスト" if self.current_entry.is_markdown else "マークダウン"
            e.control.text = f"{new_text}として保存"
            e.control.update()
            
            # ユーザーに通知
            format_name = "マークダウン" if self.current_entry.is_markdown else "リッチテキスト"
            self.app.page.show_snack_bar(
                ft.SnackBar(ft.Text(f"保存形式を{format_name}に変更しました"))
            )
        else:
            # 新規エントリーの場合
            self.app.page.show_snack_bar(
                ft.SnackBar(ft.Text("先に保存してから形式を変更してください"))
            ) 