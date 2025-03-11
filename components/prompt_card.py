#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
プロンプトカードコンポーネントモジュール

このモジュールは、ユーザーに日記のインスピレーションを提供するためのプロンプトカードを提供します。
質問やお題を表示し、それに基づいて日記を書くことを促します。

作成者: Claude AI
バージョン: 1.0.0
"""

import flet as ft
import random

class PromptCard(ft.Card):
    """
    日記のインスピレーションを提供するプロンプトカードコンポーネント。
    ホーム画面でランダムな質問やお題を表示します。
    """
    
    def __init__(self, prompt=None, on_write=None, on_refresh=None):
        """
        PromptCardクラスのコンストラクタ。
        
        Args:
            prompt (str, optional): 表示するプロンプト。指定しない場合はデフォルトから選択。
            on_write: 「書く」ボタンが押されたときのコールバック関数
            on_refresh: 「更新」ボタンが押されたときのコールバック関数
        """
        super().__init__()
        
        self.prompt = prompt
        self.on_write = on_write
        self.on_refresh = on_refresh
        
        # デフォルトのプロンプトリスト
        self.default_prompts = [
            "今日一番印象に残った出来事は何ですか？",
            "最近感謝していることを3つ書いてみましょう",
            "今週達成したい目標を書き出してみてください",
            "今日の気分を色で表すと何色ですか？その理由は？",
            "今日出会った人で印象に残った人について書いてみましょう",
            "最近読んだ本や観た映画から得た気づきは？",
            "今日の天気はあなたの気分にどう影響しましたか？",
            "今週末にやりたいことを考えてみましょう",
            "今日の自分を褒めたいところはどこですか？",
            "明日の自分への応援メッセージを書いてみましょう"
        ]
        
        # プロンプトが指定されていない場合はランダムに選択
        if self.prompt is None:
            self.prompt = random.choice(self.default_prompts)
        
        # カードの内容を構築
        self._build_card()
    
    def _build_card(self):
        """
        カードのコンテンツを構築します。
        """
        # カードのコンテンツ
        self.content = ft.Container(
            content=ft.Column([
                # プロンプトテキスト
                ft.Text(
                    self.prompt,
                    size=16,
                    italic=True,
                    text_align=ft.TextAlign.CENTER,
                ),
                
                # ボタンのコンテナ
                ft.Container(
                    content=ft.Row([
                        # 更新ボタン
                        ft.IconButton(
                            icon=ft.icons.REFRESH,
                            tooltip="別のプロンプトを表示",
                            on_click=self._on_refresh_click,
                        ),
                        
                        # 間隔
                        ft.Container(width=10),
                        
                        # 書くボタン
                        ft.ElevatedButton(
                            "このお題で書く",
                            icon=ft.icons.EDIT,
                            on_click=self._on_write_click,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                        ),
                    ], alignment=ft.MainAxisAlignment.END),
                    margin=ft.margin.only(top=10),
                ),
            ]),
            padding=15,
        )
        
        # カードの設定
        self.elevation = 3
        self.color = ft.colors.SECONDARY_CONTAINER
        
    def _on_refresh_click(self, e):
        """
        更新ボタンがクリックされたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        # 新しいプロンプトをランダムに選択（前回と異なるもの）
        old_prompt = self.prompt
        while self.prompt == old_prompt and len(self.default_prompts) > 1:
            self.prompt = random.choice(self.default_prompts)
        
        # UIを更新
        self._build_card()
        self.update()
        
        # コールバック関数があれば呼び出す
        if self.on_refresh:
            self.on_refresh(self.prompt)
    
    def _on_write_click(self, e):
        """
        「書く」ボタンがクリックされたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        # コールバック関数があれば呼び出す
        if self.on_write:
            self.on_write() 