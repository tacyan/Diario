#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
テーママネージャーモジュール

このモジュールは、アプリケーションのテーマ設定を管理するためのクラスを提供します。
ユーザーが選択したテーマモード（ライト/ダーク）の保存と取得、
カスタムテーマの適用などの機能を持ちます。

作成者: Claude AI
バージョン: 1.0.0
"""

import flet as ft
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ThemeManager:
    """
    アプリケーションのテーマを管理するクラス。
    テーマモードの切り替えと保存、カスタムテーマの適用を行います。
    """
    
    def __init__(self):
        """
        ThemeManagerクラスのコンストラクタ。
        設定ファイルの読み込みと初期テーマの設定を行います。
        """
        self.config_dir = Path.home() / ".diario"
        self.config_file = self.config_dir / "theme_config.json"
        self.theme_mode = ft.ThemeMode.SYSTEM
        self.current_theme = "default"
        
        # 設定ディレクトリの作成
        if not self.config_dir.exists():
            os.makedirs(self.config_dir, exist_ok=True)
            logger.info(f"設定ディレクトリを作成しました: {self.config_dir}")
        
        # 設定ファイルの読み込み
        self.load_config()
    
    def load_config(self):
        """
        設定ファイルからテーマ設定を読み込みます。
        ファイルが存在しない場合はデフォルト設定を保存します。
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                theme_mode_str = config.get("theme_mode", "system")
                self.theme_mode = self._string_to_theme_mode(theme_mode_str)
                self.current_theme = config.get("current_theme", "default")
                
                logger.info(f"テーマ設定を読み込みました: モード={theme_mode_str}, テーマ={self.current_theme}")
            except Exception as e:
                logger.error(f"テーマ設定の読み込み中にエラーが発生しました: {e}")
                self.save_config()  # デフォルト設定を保存
        else:
            logger.info("テーマ設定ファイルが見つかりませんでした。デフォルト設定を使用します。")
            self.save_config()  # デフォルト設定を保存
    
    def save_config(self):
        """
        現在のテーマ設定をファイルに保存します。
        """
        try:
            # テーマモードを文字列に変換
            theme_mode_str = self._theme_mode_to_string(self.theme_mode)
            
            config = {
                "theme_mode": theme_mode_str,
                "current_theme": self.current_theme
            }
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
                
            logger.info(f"テーマ設定を保存しました: モード={theme_mode_str}, テーマ={self.current_theme}")
        except Exception as e:
            logger.error(f"テーマ設定の保存中にエラーが発生しました: {e}")
    
    def get_theme_mode(self):
        """
        現在のテーマモードを取得します。
        
        Returns:
            ft.ThemeMode: 現在のテーマモード（ライト、ダーク、システム）
        """
        return self.theme_mode
    
    def set_theme_mode(self, mode):
        """
        テーマモードを設定します。
        
        Args:
            mode (ft.ThemeMode): 設定するテーマモード
        """
        if mode in [ft.ThemeMode.LIGHT, ft.ThemeMode.DARK, ft.ThemeMode.SYSTEM]:
            self.theme_mode = mode
            self.save_config()
            logger.info(f"テーマモードを変更しました: {self._theme_mode_to_string(mode)}")
        else:
            logger.warning(f"無効なテーマモードが指定されました: {mode}")
    
    def toggle_theme_mode(self):
        """
        ライトモードとダークモードを切り替えます。
        システムモードの場合はライトモードに切り替えます。
        """
        if self.theme_mode == ft.ThemeMode.LIGHT:
            self.set_theme_mode(ft.ThemeMode.DARK)
        else:
            self.set_theme_mode(ft.ThemeMode.LIGHT)
    
    def get_theme(self):
        """
        現在のテーマを取得します。
        
        Returns:
            ft.Theme: 現在のテーマオブジェクト
        """
        # カスタムカラースキーマの定義
        primary_color = ft.colors.BLUE
        secondary_color = ft.colors.TEAL
        
        # ライトモード用のカラースキーマ
        light_scheme = ft.ColorScheme(
            primary=primary_color,
            on_primary=ft.colors.WHITE,
            primary_container=ft.colors.BLUE_50,
            on_primary_container=ft.colors.BLUE_900,
            secondary=secondary_color,
            on_secondary=ft.colors.WHITE,
            secondary_container=ft.colors.TEAL_50,
            on_secondary_container=ft.colors.TEAL_900,
            surface=ft.colors.SURFACE,
            on_surface=ft.colors.BLACK,
            background=ft.colors.BACKGROUND,
            on_background=ft.colors.BLACK,
        )
        
        # ダークモード用のカラースキーマ
        dark_scheme = ft.ColorScheme(
            primary=ft.colors.BLUE_200,
            on_primary=ft.colors.BLUE_800,
            primary_container=ft.colors.BLUE_700,
            on_primary_container=ft.colors.BLUE_50,
            secondary=ft.colors.TEAL_200,
            on_secondary=ft.colors.TEAL_800,
            secondary_container=ft.colors.TEAL_700,
            on_secondary_container=ft.colors.TEAL_50,
            surface=ft.colors.SURFACE_VARIANT,
            on_surface=ft.colors.WHITE,
            background=ft.colors.BACKGROUND,
            on_background=ft.colors.WHITE,
        )
        
        # 現在のテーマモードに応じたテーマを返す
        if self.theme_mode == ft.ThemeMode.DARK:
            return ft.Theme(
                color_scheme=dark_scheme,
                color_scheme_seed=primary_color,
                visual_density=ft.ThemeVisualDensity.COMFORTABLE,
                use_material3=True,
            )
        else:
            return ft.Theme(
                color_scheme=light_scheme,
                color_scheme_seed=primary_color,
                visual_density=ft.ThemeVisualDensity.COMFORTABLE,
                use_material3=True,
            )
    
    def _theme_mode_to_string(self, mode):
        """
        テーマモードを文字列に変換します。
        
        Args:
            mode (ft.ThemeMode): 変換するテーマモード
            
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
            mode_str (str): 変換する文字列
            
        Returns:
            ft.ThemeMode: 変換されたテーマモード
        """
        mode_map = {
            "light": ft.ThemeMode.LIGHT,
            "dark": ft.ThemeMode.DARK,
            "system": ft.ThemeMode.SYSTEM
        }
        return mode_map.get(mode_str.lower(), ft.ThemeMode.SYSTEM) 