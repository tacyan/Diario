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
import markdown
from components.mood_tracker import MoodTracker

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
        
        # マークダウンプレビュー
        self.preview_container = None
        self.is_preview_mode = False
    
    def build(self):
        """
        エディター画面のUIを構築します。
        
        Returns:
            ft.Container: エディター画面のUIコンテナ
        """
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
        
        # ツールバー
        toolbar = ft.Row([
            ft.IconButton(
                icon=ft.icons.FORMAT_BOLD,
                tooltip="太字",
                on_click=lambda e: self._insert_markdown_syntax("**", "**"),
            ),
            ft.IconButton(
                icon=ft.icons.FORMAT_ITALIC,
                tooltip="斜体",
                on_click=lambda e: self._insert_markdown_syntax("*", "*"),
            ),
            ft.IconButton(
                icon=ft.icons.FORMAT_UNDERLINED,
                tooltip="下線",
                on_click=lambda e: self._insert_markdown_syntax("<u>", "</u>"),
            ),
            ft.IconButton(
                icon=ft.icons.FORMAT_STRIKETHROUGH,
                tooltip="取り消し線",
                on_click=lambda e: self._insert_markdown_syntax("~~", "~~"),
            ),
            ft.VerticalDivider(width=1),
            ft.IconButton(
                icon=ft.icons.FORMAT_LIST_BULLETED,
                tooltip="箇条書き",
                on_click=lambda e: self._insert_markdown_prefix("- "),
            ),
            ft.IconButton(
                icon=ft.icons.FORMAT_LIST_NUMBERED,
                tooltip="番号付きリスト",
                on_click=lambda e: self._insert_markdown_prefix("1. "),
            ),
            ft.IconButton(
                icon=ft.icons.FORMAT_QUOTE,
                tooltip="引用",
                on_click=lambda e: self._insert_markdown_prefix("> "),
            ),
            ft.VerticalDivider(width=1),
            ft.IconButton(
                icon=ft.icons.TITLE,
                tooltip="見出し",
                on_click=lambda e: self._insert_markdown_prefix("## "),
            ),
            ft.IconButton(
                icon=ft.icons.CODE,
                tooltip="コード",
                on_click=lambda e: self._insert_markdown_syntax("```", "```"),
            ),
            ft.IconButton(
                icon=ft.icons.LINK,
                tooltip="リンク",
                on_click=lambda e: self._insert_markdown_syntax("[", "](https://example.com)"),
            ),
        ], scroll=ft.ScrollMode.AUTO)
        
        # 本文テキストエリア
        self.content_field = ft.TextField(
            label="今日はどんな一日でしたか？",
            value=self.current_entry.content if self.current_entry else "",
            border_radius=10,
            multiline=True,
            min_lines=10,
            on_change=self._on_field_change,
        )
        
        # プレビュー切り替えボタン
        preview_button = ft.ElevatedButton(
            "プレビュー",
            icon=ft.icons.VISIBILITY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=self._toggle_preview,
        )
        
        # プレビューコンテナ
        self.preview_container = ft.Container(
            visible=False,
            content=ft.Column([
                ft.Text("プレビュー", weight=ft.FontWeight.BOLD, size=18),
                ft.Divider(),
                ft.Container(
                    content=ft.Markdown(""),
                    border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
                    border_radius=10,
                    padding=10,
                    expand=True,
                ),
            ]),
            expand=True,
        )
        
        # 保存と削除のボタン
        save_button = ft.ElevatedButton(
            "保存",
            icon=ft.icons.SAVE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                color=ft.colors.ON_PRIMARY,
                bgcolor=ft.colors.PRIMARY,
            ),
            on_click=self._on_save_click,
        )
        
        delete_button = ft.OutlinedButton(
            "削除",
            icon=ft.icons.DELETE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=self._on_delete_click,
        )
        
        # ボタンのコンテナ
        button_container = ft.Row([
            preview_button,
            ft.Container(expand=True),  # スペーサー
            delete_button,
            save_button,
        ])
        
        # メインコンテンツ
        content = ft.Column([
            # ヘッダー部分
            ft.Row([
                ft.Column([
                    self.title_field,
                    date_display,
                ], expand=True),
                media_button,
            ]),
            
            # 中央部分
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Text("気分", weight=ft.FontWeight.BOLD),
                        margin=ft.margin.only(top=20, bottom=10),
                    ),
                    self.mood_tracker,
                    
                    ft.Container(
                        content=ft.Text("タグ", weight=ft.FontWeight.BOLD),
                        margin=ft.margin.only(top=20, bottom=10),
                    ),
                    self.tag_field,
                    
                    ft.Container(
                        content=ft.Text("本文", weight=ft.FontWeight.BOLD),
                        margin=ft.margin.only(top=20, bottom=10),
                    ),
                    toolbar,
                    ft.Container(height=10),  # スペーサー
                    self.content_field,
                    self.preview_container,
                ]),
                expand=True,
            ),
            
            # フッター部分
            button_container,
        ], expand=True, scroll=ft.ScrollMode.AUTO)
        
        # 全体のコンテナ
        return ft.Container(
            content=content,
            padding=20,
            expand=True,
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
        
        Args:
            e: イベントデータ
        """
        # フィールドが変更されたら自動保存など
        pass
    
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
                    # TODO: 実際のメディア処理を実装
                    
                    # 画像のマークダウン構文を挿入
                    self._insert_markdown_syntax(f"![{f.name}](", f")")
        
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
        マークダウン構文を挿入します。
        
        Args:
            prefix: 選択範囲の前に挿入するテキスト
            suffix: 選択範囲の後に挿入するテキスト
        """
        # 現在の選択範囲を取得（実際のFletではこの機能は制限されているため、簡易的に実装）
        current_value = self.content_field.value or ""
        
        # 単純に現在のカーソル位置に挿入する
        new_value = current_value + prefix + "テキスト" + suffix
        self.content_field.value = new_value
        self.content_field.update()
    
    def _insert_markdown_prefix(self, prefix):
        """
        行の先頭にマークダウン構文を挿入します。
        
        Args:
            prefix: 行の先頭に挿入するテキスト
        """
        # 現在の値を取得
        current_value = self.content_field.value or ""
        
        # カーソル位置に応じて挿入（簡易的な実装）
        lines = current_value.split("\n")
        if lines:
            lines[0] = prefix + lines[0]
            self.content_field.value = "\n".join(lines)
            self.content_field.update()
    
    def _toggle_preview(self, e):
        """
        プレビューモードの切り替えを行います。
        
        Args:
            e: イベントデータ
        """
        self.is_preview_mode = not self.is_preview_mode
        
        # フィールドとプレビューの表示切り替え
        self.content_field.visible = not self.is_preview_mode
        self.preview_container.visible = self.is_preview_mode
        
        # プレビューモードなら、マークダウンをHTMLに変換して表示
        if self.is_preview_mode:
            content_html = markdown.markdown(self.content_field.value or "")
            self.preview_container.content.controls[2].content.value = content_html
            
        # ボタンのテキスト更新
        if isinstance(e.control, ft.ElevatedButton):
            if self.is_preview_mode:
                e.control.text = "編集に戻る"
                e.control.icon = ft.icons.EDIT
            else:
                e.control.text = "プレビュー"
                e.control.icon = ft.icons.VISIBILITY
        
        self.preview_container.update()
        self.content_field.update()
        e.control.update()
    
    def _on_save_click(self, e):
        """
        保存ボタンがクリックされたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        try:
            # フォームからデータを取得
            title = self.title_field.value
            content = self.content_field.value
            
            # タグを分割
            tags = [tag.strip() for tag in self.tag_field.value.split(",") if tag.strip()]
            
            # 気分スコア
            mood = self.mood_tracker.selected_mood or 3
            
            if self.is_new_entry:
                # 新規エントリーの作成
                entry = self.diary_manager.DiaryEntry(
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
            logger.error(f"日記の保存中にエラーが発生しました: {e}")
            
            # エラーメッセージを表示
            self.app.page.show_snack_bar(
                ft.SnackBar(ft.Text(f"エラー: 日記の保存に失敗しました"))
            )
    
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