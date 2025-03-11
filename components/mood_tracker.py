#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
気分トラッカーコンポーネントモジュール

このモジュールは、ユーザーの感情状態を記録するための気分トラッカーコンポーネントを提供します。
5段階の気分スコアを選択できるインターフェースです。

作成者: Claude AI
バージョン: 1.0.0
"""

import flet as ft

class MoodTracker(ft.Container):
    """
    ユーザーの気分を記録するためのトラッカーコンポーネント。
    5段階の気分スコアをボタンで選択できます。
    """
    
    def __init__(self, on_mood_selected=None, initial_mood=None):
        """
        MoodTrackerクラスのコンストラクタ。
        
        Args:
            on_mood_selected: 気分が選択されたときのコールバック関数
            initial_mood: 初期選択されている気分スコア（1-5）
        """
        super().__init__()
        
        self.on_mood_selected = on_mood_selected
        self.selected_mood = initial_mood
        
        # 気分スコアと絵文字・説明のマッピング
        self.mood_data = {
            1: {"emoji": "😞", "label": "最悪"},
            2: {"emoji": "😕", "label": "イマイチ"},
            3: {"emoji": "😐", "label": "普通"},
            4: {"emoji": "🙂", "label": "良い"},
            5: {"emoji": "😄", "label": "最高"}
        }
        
        # コンポーネントを構築
        self._build_tracker()
    
    def _build_tracker(self):
        """
        気分トラッカーのUIを構築します。
        """
        mood_buttons = []
        
        # 各気分スコアのボタンを作成
        for mood_score, mood_info in self.mood_data.items():
            emoji = mood_info["emoji"]
            label = mood_info["label"]
            
            # 選択中かどうかで見た目を変える
            is_selected = self.selected_mood == mood_score
            
            mood_button = ft.Container(
                content=ft.Column([
                    ft.Text(
                        emoji,
                        size=30,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        label,
                        size=12,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                    )
                ], spacing=5, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=50,
                height=70,
                border_radius=10,
                bgcolor=ft.colors.PRIMARY_CONTAINER if is_selected else None,
                border=ft.border.all(2, ft.colors.PRIMARY) if is_selected else None,
                on_click=lambda e, score=mood_score: self._on_mood_button_click(score),
                ink=True,
                padding=5,
            )
            
            mood_buttons.append(mood_button)
        
        # 気分ボタンを水平に並べる
        self.content = ft.Container(
            content=ft.Row(
                mood_buttons,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=10,
            border_radius=10,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
        )
    
    def _on_mood_button_click(self, mood_score):
        """
        気分ボタンがクリックされたときのイベントハンドラ。
        
        Args:
            mood_score: 選択された気分スコア（1-5）
        """
        self.selected_mood = mood_score
        
        # UIを更新
        self._build_tracker()
        self.update()
        
        # コールバック関数があれば呼び出す
        if self.on_mood_selected:
            self.on_mood_selected(mood_score) 