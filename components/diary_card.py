#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日記カードコンポーネントモジュール

このモジュールは、日記エントリーを表示するためのカードコンポーネントを提供します。
各日記エントリーのプレビュー表示に使用されます。

作成者: Claude AI
バージョン: 1.0.0
"""

import flet as ft
import datetime

class DiaryCard(ft.Card):
    """
    日記エントリーを表示するカードコンポーネント。
    ホーム画面やカレンダービューでエントリーのプレビューを表示します。
    """
    
    def __init__(self, entry, on_click=None):
        """
        DiaryCardクラスのコンストラクタ。
        
        Args:
            entry: 表示する日記エントリーオブジェクト
            on_click: カードがクリックされたときのコールバック関数
        """
        super().__init__()
        
        self.entry = entry
        self.on_click = on_click
        
        # 気分に対応する絵文字
        self.mood_emojis = {
            1: "😞",
            2: "😕",
            3: "😐",
            4: "🙂",
            5: "😄"
        }
        
        # カードの内容を構築
        self._build_card()
    
    def _build_card(self):
        """
        カードのコンテンツを構築します。
        """
        # タイトルと日付
        title_text = self.entry.title if self.entry.title else "無題の日記"
        
        # 日付の表示形式
        date_obj = self.entry.created_at
        today = datetime.datetime.now().date()
        yesterday = today - datetime.timedelta(days=1)
        
        if date_obj.date() == today:
            date_str = "今日"
        elif date_obj.date() == yesterday:
            date_str = "昨日"
        else:
            date_str = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"
        
        time_str = f"{date_obj.hour:02d}:{date_obj.minute:02d}"
        
        # 本文のプレビュー
        # 最大100文字まで表示し、それ以上は「...」で省略
        content_preview = self.entry.content[:100] + ("..." if len(self.entry.content) > 100 else "")
        
        # 気分の絵文字
        mood_emoji = self.mood_emojis.get(self.entry.mood, "😐")
        
        # タグのチップ
        tag_chips = []
        for tag in self.entry.tags[:3]:  # 最初の3つのタグのみ表示
            tag_chips.append(
                ft.Chip(
                    label=ft.Text(tag),
                    leading=ft.Icon(ft.icons.TAG),
                )
            )
        
        # タグが3つ以上ある場合は「+n」を表示
        if len(self.entry.tags) > 3:
            tag_chips.append(
                ft.Chip(
                    label=ft.Text(f"+{len(self.entry.tags) - 3}"),
                )
            )
        
        # メディアの数を表示するアイコン
        media_indicator = None
        if self.entry.media:
            media_count = len(self.entry.media)
            media_indicator = ft.Row([
                ft.Icon(ft.icons.IMAGE),
                ft.Text(f"{media_count}")
            ], spacing=2)
        
        # カードのコンテンツ
        self.content = ft.Container(
            content=ft.Column([
                # ヘッダー部分（タイトル、日付、気分）
                ft.Row([
                    ft.Column([
                        ft.Text(
                            title_text,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(
                            f"{date_str} {time_str}",
                            size=12,
                            weight=ft.FontWeight.W_400,
                            color=ft.colors.ON_SURFACE_VARIANT,
                        ),
                    ], expand=True),
                    ft.Text(
                        mood_emoji,
                        size=24,
                    ),
                ]),
                
                # 区切り線
                ft.Divider(height=1, color=ft.colors.OUTLINE_VARIANT),
                
                # 本文プレビュー
                ft.Container(
                    content=ft.Text(
                        content_preview,
                        size=14,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        max_lines=3,
                    ),
                    margin=ft.margin.symmetric(vertical=10),
                ),
                
                # フッター部分（タグ、メディア表示）
                ft.Row([
                    ft.Row(
                        tag_chips,
                        wrap=True,
                        expand=True,
                    ),
                    media_indicator or ft.Container(),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ]),
            padding=15,
            on_click=self.on_click,
        )
        
        # カードの設定
        self.elevation = 2
        self.margin = ft.margin.only(bottom=10)
        self.surface_tint_color = ft.colors.SECONDARY_CONTAINER 