#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Diario - 魅力的な日記アプリケーション

このスクリプトは、Fletフレームワークを使用した多機能日記アプリケーション「Diario」のメインエントリーポイントです。
ユーザーは日々の思い出や感情を美しく記録できるインターフェースを提供します。

主な機能:
- リッチテキストエディタ
- メディア対応（画像、音声、ビデオ）
- 感情トラッキング
- カレンダービューとタイムライン表示
- プライバシーとセキュリティ機能
- カスタマイズ可能なテーマ

作成者: Claude AI
バージョン: 1.0.0
"""

import flet as ft
import os
import sys
import logging
from datetime import datetime

# 内部モジュールのインポート
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from views.home_view import HomeView
from views.editor_view import EditorView
from views.calendar_view import CalendarView
from views.settings_view import SettingsView
from models.diary_entry import DiaryEntryManager
from utils.theme_manager import ThemeManager

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("diario.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DiarioApp:
    """
    Diarioアプリケーションのメインクラス。
    アプリケーションの状態管理とビュー間のナビゲーションを担当します。
    """
    
    def __init__(self):
        """
        DiarioAppクラスのコンストラクタ。
        アプリケーションの初期化と必要なマネージャーの設定を行います。
        """
        self.diary_manager = DiaryEntryManager()
        self.theme_manager = ThemeManager()
        self.current_view = "home"
        self.views = {}
        
    def initialize(self, page: ft.Page):
        """
        アプリケーションの初期化とページの設定を行います。
        
        Args:
            page (ft.Page): Fletのページオブジェクト
        """
        self.page = page
        self.page.title = "Diario - あなたの日記"
        self.page.theme = self.theme_manager.get_theme()
        self.page.theme_mode = self.theme_manager.get_theme_mode()
        
        # レスポンシブ設定
        self.page.responsive = True
        self.page.window.width = 1000
        self.page.window.height = 800
        self.page.window.min_width = 400
        self.page.window.min_height = 600
        
        # スクロール設定
        self.page.scroll = ft.ScrollMode.AUTO
        
        # ビューの初期化
        self.views = {
            "home": HomeView(self),
            "editor": EditorView(self),
            "calendar": CalendarView(self),
            "settings": SettingsView(self)
        }
        
        # アプリバー
        self.page.appbar = ft.AppBar(
            title=ft.Text("Diario", size=32, weight=ft.FontWeight.BOLD),
            center_title=False,
            bgcolor=ft.colors.SURFACE_VARIANT,
            actions=[
                ft.IconButton(
                    icon=ft.icons.WB_SUNNY_OUTLINED if self.theme_manager.get_theme_mode() == ft.ThemeMode.LIGHT else ft.icons.NIGHTLIGHT_ROUND,
                    tooltip="テーマ切替",
                    on_click=self.toggle_theme
                ),
                ft.IconButton(
                    icon=ft.icons.SETTINGS,
                    tooltip="設定",
                    on_click=lambda _: self.navigate("settings")
                ),
            ],
        )
        
        # ナビゲーションバー（画面下部のメニュー）
        self.page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.icons.HOME_OUTLINED,
                    selected_icon=ft.icons.HOME,
                    label="ホーム",
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.EDIT_OUTLINED,
                    selected_icon=ft.icons.EDIT,
                    label="新規作成",
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.CALENDAR_MONTH_OUTLINED,
                    selected_icon=ft.icons.CALENDAR_MONTH,
                    label="カレンダー",
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.ANALYTICS_OUTLINED,
                    selected_icon=ft.icons.ANALYTICS,
                    label="分析",
                ),
            ],
            on_change=self.handle_navigation_change,
        )
        
        # 初期ビューの設定
        self.navigate("home")
        
    def handle_navigation_change(self, e):
        """
        ナビゲーションバーの変更イベントを処理します。
        
        Args:
            e: イベントデータ
        """
        index_to_view = {
            0: "home",
            1: "editor",
            2: "calendar",
            3: "analytics"
        }
        self.navigate(index_to_view.get(e.control.selected_index, "home"))
        
    def navigate(self, view_name):
        """
        指定されたビューに移動します。
        
        Args:
            view_name (str): 移動先のビュー名
        """
        logger.info(f"ビュー切替: {self.current_view} -> {view_name}")
        self.current_view = view_name
        
        # ビューが存在するか確認
        if view_name in self.views:
            self.page.clean()
            self.page.add(self.views[view_name].build())
            
            # ナビゲーションバーの選択状態を更新
            view_to_index = {
                "home": 0,
                "editor": 1,
                "calendar": 2,
                "analytics": 3
            }
            if view_name in view_to_index:
                self.page.navigation_bar.selected_index = view_to_index[view_name]
                
            self.page.update()
        else:
            logger.error(f"ビュー '{view_name}' が見つかりません")
            
    def toggle_theme(self, e):
        """
        ライト/ダークテーマを切り替えます。
        
        Args:
            e: イベントデータ
        """
        self.theme_manager.toggle_theme_mode()
        self.page.theme_mode = self.theme_manager.get_theme_mode()
        
        # アイコンの更新
        self.page.appbar.actions[0].icon = (
            ft.icons.WB_SUNNY_OUTLINED 
            if self.theme_manager.get_theme_mode() == ft.ThemeMode.LIGHT 
            else ft.icons.NIGHTLIGHT_ROUND
        )
        
        self.page.update()
        logger.info(f"テーマモード変更: {self.theme_manager.get_theme_mode()}")

def main(page: ft.Page):
    """
    アプリケーションのメインエントリポイント。
    
    Args:
        page (ft.Page): Fletのページオブジェクト
    """
    app = DiarioApp()
    app.initialize(page)

if __name__ == "__main__":
    try:
        logger.info("Diarioアプリケーションを起動しています...")
        ft.app(target=main)
    except Exception as e:
        logger.error(f"アプリケーションの実行中にエラーが発生しました: {e}", exc_info=True)
