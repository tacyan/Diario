#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
設定ビューモジュール

このモジュールは、アプリケーションの設定画面UIを提供します。
テーマ切り替え、プライバシー設定、バックアップなどの設定機能を含みます。

作成者: Claude AI
バージョン: 1.0.0
"""

import flet as ft
import logging
import json
import os
from pathlib import Path
import datetime
import shutil

logger = logging.getLogger(__name__)

class SettingsView:
    """
    アプリケーションの設定画面を構築するクラス。
    ユーザーがアプリの設定を変更するためのインターフェースを提供します。
    """
    
    def __init__(self, app):
        """
        SettingsViewクラスのコンストラクタ。
        
        Args:
            app: メインアプリケーションの参照
        """
        self.app = app
        self.diary_manager = app.diary_manager
        self.theme_manager = app.theme_manager
        
        # 設定項目の状態
        self.theme_mode = self.theme_manager.get_theme_mode()
        self.has_password = bool(self.diary_manager.password)
        
        # パスワード入力フィールドの参照
        self.current_password_field = None
        self.new_password_field = None
        self.confirm_password_field = None
    
    def build(self):
        """
        設定画面のUIを構築します。
        
        Returns:
            ft.Container: 設定画面のUIコンテナ
        """
        # 設定カテゴリのタブ
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="外観",
                    icon=ft.icons.COLOR_LENS,
                    content=self._build_appearance_settings(),
                ),
                ft.Tab(
                    text="プライバシー",
                    icon=ft.icons.SECURITY,
                    content=self._build_privacy_settings(),
                ),
                ft.Tab(
                    text="バックアップ",
                    icon=ft.icons.BACKUP,
                    content=self._build_backup_settings(),
                ),
                ft.Tab(
                    text="このアプリについて",
                    icon=ft.icons.INFO,
                    content=self._build_about_section(),
                ),
            ],
            expand=1,
        )
        
        # 戻るボタン
        back_button = ft.ElevatedButton(
            "ホームに戻る",
            icon=ft.icons.HOME,
            on_click=lambda _: self.app.navigate("home"),
        )
        
        # 全体のレイアウト
        return ft.Container(
            content=ft.Column([
                ft.Text("設定", size=32, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),  # スペーサー
                tabs,
                ft.Container(height=20),  # スペーサー
                back_button,
            ]),
            padding=20,
            expand=True,
        )
    
    def _build_appearance_settings(self):
        """
        外観設定のUIを構築します。
        
        Returns:
            ft.Container: 外観設定のUIコンテナ
        """
        # テーママネージャからテーマモードを取得
        theme_mode = self.theme_manager.get_theme_mode()
        
        # テーマ選択ラジオボタン
        theme_radio = ft.RadioGroup(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.WB_SUNNY_OUTLINED),
                    ft.Container(width=10),
                    ft.Radio(value="light", label="ライトモード"),
                ]),
                ft.Row([
                    ft.Icon(ft.icons.NIGHTLIGHT_ROUND),
                    ft.Container(width=10),
                    ft.Radio(value="dark", label="ダークモード"),
                ]),
                ft.Row([
                    ft.Icon(ft.icons.SETTINGS_OUTLINED),
                    ft.Container(width=10),
                    ft.Radio(value="system", label="システム設定に従う"),
                ]),
            ]),
            value=self._theme_mode_to_string(theme_mode),
            on_change=self._on_theme_change,
        )
        
        # 設定セクション
        return ft.Container(
            content=ft.Column([
                ft.Text("テーマ設定", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),  # スペーサー
                theme_radio,
                
                ft.Container(height=30),  # スペーサー
                
                ft.Text("フォントサイズ", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),  # スペーサー
                ft.Slider(
                    min=0.8,
                    max=1.5,
                    divisions=7,
                    value=1.0,
                    label="{value}倍",
                    on_change=self._on_font_size_change,
                ),
            ]),
            padding=20,
        )
    
    def _build_privacy_settings(self):
        """
        プライバシー設定のUIを構築します。
        
        Returns:
            ft.Container: プライバシー設定のUIコンテナ
        """
        # パスワード保護の切り替えスイッチ
        password_switch = ft.Switch(
            label="パスワード保護",
            value=self.has_password,
            on_change=self._on_password_switch_change,
        )
        
        # 現在のパスワードフィールド（パスワード変更時のみ）
        self.current_password_field = ft.TextField(
            label="現在のパスワード",
            password=True,
            visible=self.has_password,
            can_reveal_password=True,
        )
        
        # 新しいパスワードフィールド
        self.new_password_field = ft.TextField(
            label="新しいパスワード",
            password=True,
            visible=password_switch.value,
            can_reveal_password=True,
        )
        
        # パスワード確認フィールド
        self.confirm_password_field = ft.TextField(
            label="パスワードの確認",
            password=True,
            visible=password_switch.value,
            can_reveal_password=True,
        )
        
        # パスワード変更ボタン
        password_button = ft.ElevatedButton(
            "パスワードを設定",
            visible=password_switch.value,
            on_click=self._on_password_change,
            icon=ft.icons.LOCK,
        )
        
        # 設定セクション
        return ft.Container(
            content=ft.Column([
                ft.Text("セキュリティ設定", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),  # スペーサー
                password_switch,
                ft.Container(height=10),  # スペーサー
                self.current_password_field,
                self.new_password_field,
                self.confirm_password_field,
                password_button,
                
                ft.Container(height=30),  # スペーサー
                
                ft.Text("プライバシーオプション", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),  # スペーサー
                ft.Checkbox(label="アプリ起動時にパスワードを要求"),
                ft.Checkbox(label="エントリー単位での暗号化を有効にする"),
            ]),
            padding=20,
        )
    
    def _build_backup_settings(self):
        """
        バックアップ設定のUIを構築します。
        
        Returns:
            ft.Container: バックアップ設定のUIコンテナ
        """
        # 最終バックアップ日時の取得
        backup_info = ft.Text("最終バックアップ: なし", italic=True)
        
        # バックアップディレクトリをチェック
        backup_dir = Path.home() / ".diario" / "backup"
        if backup_dir.exists():
            # 最新のバックアップファイルを探す
            backup_files = list(backup_dir.glob("*.zip"))
            if backup_files:
                # 最新のバックアップファイルの情報を表示
                latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
                backup_time = datetime.datetime.fromtimestamp(latest_backup.stat().st_mtime)
                backup_info.value = f"最終バックアップ: {backup_time.strftime('%Y年%m月%d日 %H:%M')}"
        
        # バックアップボタン
        backup_button = ft.ElevatedButton(
            "今すぐバックアップ",
            icon=ft.icons.SAVE,
            on_click=self._on_backup,
        )
        
        # 復元ボタン
        restore_button = ft.ElevatedButton(
            "バックアップから復元",
            icon=ft.icons.RESTORE,
            on_click=self._on_restore,
        )
        
        # 自動バックアップの設定
        auto_backup_switch = ft.Switch(
            label="自動バックアップ",
            value=False,
        )
        
        # バックアップ頻度の選択
        backup_frequency = ft.Dropdown(
            label="自動バックアップの頻度",
            options=[
                ft.dropdown.Option("daily", "毎日"),
                ft.dropdown.Option("weekly", "毎週"),
                ft.dropdown.Option("monthly", "毎月"),
            ],
            value="weekly",
            disabled=not auto_backup_switch.value,
        )
        
        # 自動バックアップの切り替え時の処理
        def on_auto_backup_change(e):
            backup_frequency.disabled = not e.control.value
            backup_frequency.update()
        
        auto_backup_switch.on_change = on_auto_backup_change
        
        # 設定セクション
        return ft.Container(
            content=ft.Column([
                ft.Text("バックアップと復元", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),  # スペーサー
                backup_info,
                ft.Container(height=10),  # スペーサー
                ft.Row([
                    backup_button,
                    ft.Container(width=10),  # スペーサー
                    restore_button,
                ]),
                
                ft.Container(height=30),  # スペーサー
                
                ft.Text("自動バックアップ設定", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),  # スペーサー
                auto_backup_switch,
                backup_frequency,
            ]),
            padding=20,
        )
    
    def _build_about_section(self):
        """
        アプリについての情報セクションを構築します。
        
        Returns:
            ft.Container: アプリ情報のUIコンテナ
        """
        # アプリ情報
        return ft.Container(
            content=ft.Column([
                ft.Text("Diario", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("バージョン 1.0.0", italic=True),
                ft.Container(height=20),  # スペーサー
                
                ft.Text(
                    "Diarioは、日々の思い出や感情を美しく記録できる多機能日記アプリです。"
                    "シンプルながらも洗練されたデザインで、誰でも直感的に使えます。",
                    text_align=ft.TextAlign.CENTER,
                ),
                
                ft.Container(height=30),  # スペーサー
                
                ft.Text("開発者情報", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),  # スペーサー
                ft.Text("制作: Claude AI"),
                
                ft.Container(height=30),  # スペーサー
                
                ft.Text("オープンソースライセンス", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),  # スペーサー
                ft.Text("このアプリは以下のオープンソースライブラリを使用しています:"),
                ft.Text("- Flet: 美しいFlutterアプリをPythonで"),
                ft.Text("- SQLiteDict: Pythonディクショナリインターフェースを持つSQLiteデータベース"),
                ft.Text("- Markdown: マークダウンからHTMLへの変換"),
                ft.Text("- PyCryptodome: 高度な暗号化ライブラリ"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            alignment=ft.alignment.center,
        )
    
    def _theme_mode_to_string(self, mode):
        """
        テーマモードを文字列に変換します。
        
        Args:
            mode: 変換するテーマモード
            
        Returns:
            str: テーマモードを表す文字列
        """
        mode_map = {
            ft.ThemeMode.LIGHT: "light",
            ft.ThemeMode.DARK: "dark",
            ft.ThemeMode.SYSTEM: "system"
        }
        return mode_map.get(mode, "system")
    
    def _string_to_theme_mode(self, mode_str):
        """
        文字列からテーマモードに変換します。
        
        Args:
            mode_str: 変換する文字列
            
        Returns:
            ft.ThemeMode: 変換されたテーマモード
        """
        mode_map = {
            "light": ft.ThemeMode.LIGHT,
            "dark": ft.ThemeMode.DARK,
            "system": ft.ThemeMode.SYSTEM
        }
        return mode_map.get(mode_str, ft.ThemeMode.SYSTEM)
    
    def _on_theme_change(self, e):
        """
        テーマ設定が変更されたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        # 選択されたテーマモードを取得
        selected_value = e.control.value
        theme_mode = self._string_to_theme_mode(selected_value)
        
        # テーマを更新
        self.theme_manager.set_theme_mode(theme_mode)
        self.app.page.theme_mode = theme_mode
        
        # アイコンの更新
        self.app.page.appbar.actions[0].icon = (
            ft.icons.WB_SUNNY_OUTLINED 
            if theme_mode == ft.ThemeMode.LIGHT 
            else ft.icons.NIGHTLIGHT_ROUND
        )
        
        # UIを更新
        self.app.page.update()
        logger.info(f"テーマモードを変更しました: {selected_value}")
    
    def _on_font_size_change(self, e):
        """
        フォントサイズが変更されたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        # フォントサイズの変更処理
        # 注: 現在のFletではグローバルなフォントサイズの変更はサポートされていないため、
        # 各コンポーネントを個別に更新する必要があります
        logger.info(f"フォントサイズを変更しました: {e.control.value}倍")
    
    def _on_password_switch_change(self, e):
        """
        パスワード保護スイッチが切り替えられたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        # パスワードフィールドの表示/非表示を切り替え
        is_enabled = e.control.value
        
        self.current_password_field.visible = is_enabled and self.has_password
        self.new_password_field.visible = is_enabled
        self.confirm_password_field.visible = is_enabled
        
        # パスワードフィールドの親をたどってボタンを見つける
        password_button = None
        for control in e.control.page.controls[0].content.controls[2].tabs[1].content.content.controls:
            if isinstance(control, ft.ElevatedButton):
                password_button = control
                break
        
        if password_button:
            password_button.visible = is_enabled
            password_button.update()
        
        # フィールドを更新
        self.current_password_field.update()
        self.new_password_field.update()
        self.confirm_password_field.update()
        
        logger.info(f"パスワード保護: {is_enabled}")
    
    def _on_password_change(self, e):
        """
        パスワード変更ボタンがクリックされたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        # 入力値を取得
        current_password = self.current_password_field.value
        new_password = self.new_password_field.value
        confirm_password = self.confirm_password_field.value
        
        # 入力チェック
        if self.has_password and not current_password:
            self.app.page.show_snack_bar(
                ft.SnackBar(ft.Text("現在のパスワードを入力してください"))
            )
            return
        
        if not new_password:
            self.app.page.show_snack_bar(
                ft.SnackBar(ft.Text("新しいパスワードを入力してください"))
            )
            return
        
        if new_password != confirm_password:
            self.app.page.show_snack_bar(
                ft.SnackBar(ft.Text("パスワードが一致しません"))
            )
            return
        
        try:
            # パスワードをデータベースに設定
            success = False
            
            if self.has_password:
                # パスワード変更
                if self.diary_manager.password == current_password:
                    success = self.diary_manager.change_password(new_password)
                else:
                    self.app.page.show_snack_bar(
                        ft.SnackBar(ft.Text("現在のパスワードが正しくありません"))
                    )
                    return
            else:
                # 新規パスワード設定
                self.diary_manager.password = new_password
                self.diary_manager._init_encryption()
                # すべてのエントリーを再保存
                all_entries = self.diary_manager.get_all_entries()
                for entry in all_entries:
                    self.diary_manager.save_entry(entry)
                success = True
            
            if success:
                self.has_password = True
                self.app.page.show_snack_bar(
                    ft.SnackBar(ft.Text("パスワードを設定しました"))
                )
                
                # フィールドをクリア
                self.current_password_field.value = ""
                self.new_password_field.value = ""
                self.confirm_password_field.value = ""
                
                # UIを更新
                self.current_password_field.update()
                self.new_password_field.update()
                self.confirm_password_field.update()
            else:
                self.app.page.show_snack_bar(
                    ft.SnackBar(ft.Text("パスワードの設定に失敗しました"))
                )
                
        except Exception as ex:
            logger.error(f"パスワード設定中にエラーが発生しました: {ex}")
            self.app.page.show_snack_bar(
                ft.SnackBar(ft.Text(f"エラー: パスワードの設定に失敗しました"))
            )
    
    def _on_backup(self, e):
        """
        バックアップボタンがクリックされたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        try:
            # バックアップディレクトリの作成
            backup_dir = Path.home() / ".diario" / "backup"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # バックアップファイル名の生成
            now = datetime.datetime.now()
            backup_file = backup_dir / f"diario_backup_{now.strftime('%Y%m%d_%H%M%S')}.zip"
            
            # データディレクトリをZIPにアーカイブ
            data_dir = Path.home() / ".diario" / "data"
            
            # ダイアログを表示
            def close_backup_dialog(e):
                dialog.open = False
                self.app.page.update()
                
                # エクスポートパス情報
                self.app.page.show_snack_bar(
                    ft.SnackBar(ft.Text(f"バックアップを作成しました: {backup_file}"))
                )
                
                # バックアップ情報を更新
                backup_info = e.control.page.controls[0].content.controls[2].tabs[2].content.content.controls[2]
                backup_info.value = f"最終バックアップ: {now.strftime('%Y年%m月%d日 %H:%M')}"
                backup_info.update()
            
            # バックアップ処理のダイアログ
            dialog = ft.AlertDialog(
                title=ft.Text("バックアップ中..."),
                content=ft.Column([
                    ft.ProgressRing(),
                    ft.Text("データのバックアップを作成しています...")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            )
            
            # ダイアログを表示
            self.app.page.dialog = dialog
            dialog.open = True
            self.app.page.update()
            
            # バックアップ処理（実際のアプリではもっと高度な実装が必要）
            shutil.make_archive(
                str(backup_file).replace(".zip", ""),
                'zip',
                data_dir.parent,
                data_dir.name
            )
            
            # 完了ダイアログを表示
            dialog.title = ft.Text("バックアップ完了")
            dialog.content = ft.Column([
                ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=50),
                ft.Text("バックアップが正常に作成されました。"),
                ft.TextButton("閉じる", on_click=close_backup_dialog),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self.app.page.update()
            
            logger.info(f"バックアップを作成しました: {backup_file}")
            
        except Exception as ex:
            logger.error(f"バックアップ作成中にエラーが発生しました: {ex}")
            self.app.page.show_snack_bar(
                ft.SnackBar(ft.Text(f"エラー: バックアップの作成に失敗しました"))
            )
    
    def _on_restore(self, e):
        """
        復元ボタンがクリックされたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        # バックアップフォルダをチェック
        backup_dir = Path.home() / ".diario" / "backup"
        if not backup_dir.exists() or not list(backup_dir.glob("*.zip")):
            self.app.page.show_snack_bar(
                ft.SnackBar(ft.Text("復元可能なバックアップがありません"))
            )
            return
        
        try:
            # バックアップファイルのリストを取得
            backup_files = list(backup_dir.glob("*.zip"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # ドロップダウンのオプションを作成
            backup_options = []
            for file in backup_files:
                backup_time = datetime.datetime.fromtimestamp(file.stat().st_mtime)
                option_text = f"{backup_time.strftime('%Y年%m月%d日 %H:%M')}"
                backup_options.append(ft.dropdown.Option(str(file), option_text))
            
            # バックアップ選択ドロップダウン
            backup_dropdown = ft.Dropdown(
                label="復元するバックアップを選択",
                options=backup_options,
                value=str(backup_files[0]),
                width=400,
            )
            
            # 確認ダイアログの完了ボタンの処理
            def confirm_restore(e):
                dialog.open = False
                self.app.page.update()
                
                # 復元処理のダイアログを表示
                restore_dialog = ft.AlertDialog(
                    title=ft.Text("復元中..."),
                    content=ft.Column([
                        ft.ProgressRing(),
                        ft.Text("バックアップからデータを復元しています...")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                )
                
                self.app.page.dialog = restore_dialog
                restore_dialog.open = True
                self.app.page.update()
                
                try:
                    # 選択されたバックアップファイル
                    selected_backup = Path(backup_dropdown.value)
                    
                    # データディレクトリ
                    data_dir = Path.home() / ".diario" / "data"
                    
                    # 既存のデータを一時バックアップ
                    temp_backup = data_dir.parent / "data_temp_backup"
                    if temp_backup.exists():
                        shutil.rmtree(temp_backup)
                    if data_dir.exists():
                        shutil.copytree(data_dir, temp_backup)
                    
                    try:
                        # 既存のデータディレクトリをクリア
                        if data_dir.exists():
                            shutil.rmtree(data_dir)
                        
                        # バックアップを展開
                        import zipfile
                        with zipfile.ZipFile(selected_backup, 'r') as zip_ref:
                            zip_ref.extractall(data_dir.parent)
                        
                        # 一時バックアップを削除
                        if temp_backup.exists():
                            shutil.rmtree(temp_backup)
                        
                        # 完了ダイアログを更新
                        restore_dialog.title = ft.Text("復元完了")
                        restore_dialog.content = ft.Column([
                            ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=50),
                            ft.Text("データが正常に復元されました。"),
                            ft.Text("変更を適用するにはアプリを再起動してください。"),
                            ft.TextButton("閉じる", on_click=lambda e: self._close_restore_dialog(e, restore_dialog)),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        self.app.page.update()
                        
                        logger.info(f"バックアップから復元しました: {selected_backup}")
                        
                    except Exception as ex:
                        # エラーが発生した場合、一時バックアップから復元
                        if temp_backup.exists():
                            if data_dir.exists():
                                shutil.rmtree(data_dir)
                            shutil.copytree(temp_backup, data_dir)
                            shutil.rmtree(temp_backup)
                        
                        # エラーダイアログを表示
                        restore_dialog.title = ft.Text("復元エラー")
                        restore_dialog.content = ft.Column([
                            ft.Icon(ft.icons.ERROR, color=ft.colors.RED, size=50),
                            ft.Text("データの復元中にエラーが発生しました。"),
                            ft.Text("元のデータは保持されています。"),
                            ft.TextButton("閉じる", on_click=lambda e: self._close_restore_dialog(e, restore_dialog)),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        self.app.page.update()
                        
                        logger.error(f"復元中にエラーが発生しました: {ex}")
                
                except Exception as ex:
                    # その他のエラー
                    restore_dialog.title = ft.Text("エラー")
                    restore_dialog.content = ft.Column([
                        ft.Icon(ft.icons.ERROR, color=ft.colors.RED, size=50),
                        ft.Text(f"エラーが発生しました: {str(ex)}"),
                        ft.TextButton("閉じる", on_click=lambda e: self._close_restore_dialog(e, restore_dialog)),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    self.app.page.update()
                    
                    logger.error(f"復元処理でエラーが発生しました: {ex}")
            
            # 確認ダイアログのキャンセルボタンの処理
            def cancel_restore(e):
                dialog.open = False
                self.app.page.update()
            
            # 確認ダイアログ
            dialog = ft.AlertDialog(
                title=ft.Text("バックアップから復元"),
                content=ft.Column([
                    ft.Text("バックアップからデータを復元すると、現在のデータはすべて上書きされます。"),
                    ft.Text("続行しますか？", weight=ft.FontWeight.BOLD),
                    ft.Container(height=20),  # スペーサー
                    backup_dropdown,
                ]),
                actions=[
                    ft.TextButton("キャンセル", on_click=cancel_restore),
                    ft.TextButton("復元する", on_click=confirm_restore),
                ],
            )
            
            # ダイアログを表示
            self.app.page.dialog = dialog
            dialog.open = True
            self.app.page.update()
            
        except Exception as ex:
            logger.error(f"復元ダイアログの表示中にエラーが発生しました: {ex}")
            self.app.page.show_snack_bar(
                ft.SnackBar(ft.Text(f"エラー: {str(ex)}"))
            )
    
    def _close_restore_dialog(self, e, dialog):
        """
        復元完了ダイアログを閉じる処理。
        
        Args:
            e: イベントデータ
            dialog: 閉じるダイアログ
        """
        dialog.open = False
        self.app.page.update()
        
        # アプリを再起動するかの確認
        restart_dialog = ft.AlertDialog(
            title=ft.Text("アプリの再起動"),
            content=ft.Text("変更を適用するには、アプリを再起動する必要があります。"),
            actions=[
                ft.TextButton("後で再起動", on_click=lambda e: self._close_dialog(e, restart_dialog)),
                ft.TextButton("今すぐ再起動", on_click=self._restart_app),
            ],
        )
        
        self.app.page.dialog = restart_dialog
        restart_dialog.open = True
        self.app.page.update()
    
    def _close_dialog(self, e, dialog):
        """
        ダイアログを閉じる汎用処理。
        
        Args:
            e: イベントデータ
            dialog: 閉じるダイアログ
        """
        dialog.open = False
        self.app.page.update()
    
    def _restart_app(self, e):
        """
        アプリを再起動する処理。
        
        Args:
            e: イベントデータ
        """
        # 現実のアプリでは再起動処理を実装
        # ここではホーム画面に戻るだけ
        self.app.page.show_snack_bar(
            ft.SnackBar(ft.Text("アプリを再起動します..."))
        )
        
        # 短い遅延の後にホーム画面に戻る
        def navigate_home():
            # ダイアログを閉じる
            self.app.page.dialog.open = False
            self.app.page.update()
            
            # ホームに戻る
            self.app.navigate("home")
        
        # ダイアログを閉じる
        self.app.page.dialog.open = False
        self.app.page.update()
        
        # 遅延処理（実際のアプリでは適切な再起動処理を実装）
        import threading
        threading.Timer(1.0, navigate_home).start() 