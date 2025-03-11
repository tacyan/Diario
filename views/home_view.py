#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ホーム画面ビューモジュール

このモジュールは、アプリケーションのホーム画面のUIを構築します。
今日の日付、最近の日記、気分トラッカー、クイックアクセスなどを表示します。

作成者: Claude AI
バージョン: 1.0.0
"""

import flet as ft
import datetime
from dateutil.relativedelta import relativedelta
import logging
from components.diary_card import DiaryCard
from components.mood_tracker import MoodTracker
from components.prompt_card import PromptCard

logger = logging.getLogger(__name__)

class HomeView:
    """
    アプリケーションのホーム画面を構築するクラス。
    ユーザーの最近の日記エントリーと概要情報を表示します。
    """
    
    def __init__(self, app):
        """
        HomeViewクラスのコンストラクタ。
        
        Args:
            app: メインアプリケーションの参照
        """
        self.app = app
        self.diary_manager = app.diary_manager
        
        # 日本語の曜日
        self.weekdays_ja = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        
        # プロンプトのリスト
        self.prompts = [
            "今日の最高の瞬間は何でしたか？",
            "誰かに感謝したいことはありますか？",
            "今日学んだことを書き留めましょう",
            "明日の目標を3つ書き出しましょう",
            "今週のハイライトを振り返りましょう",
            "今の気持ちを言葉にしてみましょう",
            "自分を褒めたいことは何ですか？"
        ]
    
    def build(self):
        """
        ホーム画面のUIを構築します。
        
        Returns:
            ft.Container: ホーム画面のUIコンテナ
        """
        # 今日の日付と曜日
        today = datetime.datetime.now()
        weekday_index = today.weekday()
        weekday_ja = self.weekdays_ja[weekday_index]
        
        # 日付と曜日の表示
        date_display = ft.Container(
            content=ft.Column([
                ft.Text(
                    f"{today.year}年{today.month}月{today.day}日",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    weekday_ja,
                    size=18,
                    weight=ft.FontWeight.W_300,
                    italic=True,
                )
            ]),
            margin=ft.margin.only(bottom=20)
        )
        
        # クイックアクセスボタン
        quick_access = ft.Row([
            ft.ElevatedButton(
                "新規作成",
                icon=ft.icons.ADD,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                on_click=lambda _: self.app.navigate("editor")
            ),
            ft.ElevatedButton(
                "カレンダー",
                icon=ft.icons.CALENDAR_TODAY,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                on_click=lambda _: self.app.navigate("calendar")
            ),
        ], wrap=True, spacing=10)
        
        # 最近の日記
        recent_entries = self._build_recent_entries()
        
        # プロンプトカード
        import random
        random_prompts = random.sample(self.prompts, min(3, len(self.prompts)))
        prompt_cards = ft.Column([
            PromptCard(
                prompt=prompt,
                on_write=lambda p=prompt: self._on_prompt_selected(p)
            )
            for prompt in random_prompts
        ], spacing=10)
        
        # 小さなカレンダー
        this_month = today.month
        this_year = today.year
        mini_calendar = self._build_month_calendar(this_year, this_month)
        
        # 気分トラッカー
        mood_tracker = MoodTracker(
            on_mood_selected=self._on_mood_selected,
        )
        
        # レイアウト構築
        left_panel = ft.Column([
            date_display,
            quick_access,
            ft.Container(height=20),  # スペーサー
            ft.Text("今日の気分", size=16, weight=ft.FontWeight.W_500),
            mood_tracker,
            ft.Container(height=20),  # スペーサー
            ft.Text("今月", size=16, weight=ft.FontWeight.W_500),
            mini_calendar,
        ], expand=3)
        
        right_panel = ft.Column([
            ft.Container(
                content=ft.Text("最近の日記", size=18, weight=ft.FontWeight.W_500),
                margin=ft.margin.only(bottom=10),
            ),
            recent_entries,
            ft.Container(height=20),  # スペーサー
            ft.Container(
                content=ft.Text("書くためのヒント", size=18, weight=ft.FontWeight.W_500),
                margin=ft.margin.only(bottom=10),
            ),
            prompt_cards,
        ], expand=7)
        
        # レスポンシブレイアウト
        layout = ft.ResponsiveRow([
            ft.Column([left_panel], col={"sm": 12, "md": 4, "lg": 3, "xl": 2}),
            ft.Column([right_panel], col={"sm": 12, "md": 8, "lg": 9, "xl": 10}),
        ])
        
        # スクロール可能なコンテナとして返す
        return ft.Container(
            content=ft.Column([layout], scroll=ft.ScrollMode.AUTO, auto_scroll=False),
            padding=20,
            margin=ft.margin.all(0),
            width=float('inf'),
            height=float('inf'),
        )
    
    def _build_recent_entries(self):
        """
        最近の日記エントリーのリストを構築します。
        
        Returns:
            ft.Column: 最近の日記エントリーを表示するカラム
        """
        try:
            # 最近の日記エントリーを取得（最大5件）
            entries = self.diary_manager.get_all_entries()[:5]
            
            if not entries:
                return ft.Container(
                    content=ft.Text("まだ日記がありません。新しく作成してみましょう！", italic=True),
                    margin=ft.margin.symmetric(vertical=20),
                    alignment=ft.alignment.center
                )
            
            entry_cards = []
            for entry in entries:
                entry_card = DiaryCard(
                    entry=entry,
                    on_click=lambda e, entry_id=entry.id: self._open_entry(entry_id)
                )
                entry_cards.append(entry_card)
            
            return ft.Column(
                entry_cards,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                auto_scroll=False,
                height=400
            )
        
        except Exception as e:
            logger.error(f"最近の日記エントリーの取得中にエラーが発生しました: {e}")
            return ft.Text("エントリーの読み込み中にエラーが発生しました")
    
    def _build_month_calendar(self, year, month):
        """
        月間カレンダーを構築します。
        
        Args:
            year (int): 年
            month (int): 月
            
        Returns:
            ft.Container: カレンダーのコンテナ
        """
        # 指定された月の最初の日と最後の日
        first_day = datetime.datetime(year, month, 1)
        last_day = first_day + relativedelta(months=1, days=-1)
        
        # 週の始まりを月曜日とし、最初の日の曜日に合わせて空白を入れる
        weekday = first_day.weekday()  # 0: 月曜日, 6: 日曜日
        
        # 曜日のヘッダー
        weekday_header = ft.Row([
            ft.Container(
                ft.Text(day, size=12, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                width=30,
                height=30,
                alignment=ft.alignment.center,
            )
            for day in ["月", "火", "水", "木", "金", "土", "日"]
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # 日付のグリッド
        days = []
        
        # 空白のセルを追加
        for _ in range(weekday):
            days.append(
                ft.Container(
                    width=30,
                    height=30,
                )
            )
        
        # 実際の日付を追加
        entries_by_day = {}
        try:
            # この月の日記エントリーを取得し、日付ごとにグループ化
            month_entries = self.diary_manager.get_entries_by_date(year, month)
            for entry in month_entries:
                day = entry.created_at.day
                if day not in entries_by_day:
                    entries_by_day[day] = []
                entries_by_day[day].append(entry)
        except Exception as e:
            logger.error(f"月間エントリーの取得中にエラーが発生しました: {e}")
        
        # 日付セルを作成
        today = datetime.datetime.now().date()
        for day in range(1, last_day.day + 1):
            # 日付が今日かどうかをチェック
            is_today = (year == today.year and month == today.month and day == today.day)
            
            # エントリーがあるかチェック
            has_entries = day in entries_by_day
            
            # 色の設定
            bg_color = None
            if is_today:
                bg_color = ft.colors.PRIMARY_CONTAINER
            elif has_entries:
                bg_color = ft.colors.SECONDARY_CONTAINER
            
            days.append(
                ft.Container(
                    content=ft.Text(str(day), size=12, text_align=ft.TextAlign.CENTER),
                    width=30,
                    height=30,
                    border_radius=15,
                    bgcolor=bg_color,
                    alignment=ft.alignment.center,
                    on_click=lambda e, d=day: self._view_day_entries(year, month, d),
                )
            )
        
        # 週ごとに行を作成
        rows = []
        for i in range(0, len(days), 7):
            week = days[i:i+7]
            rows.append(
                ft.Row(
                    week,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )
        
        # カレンダー全体を返す
        return ft.Container(
            content=ft.Column(
                [weekday_header] + rows,
                spacing=5,
            ),
            padding=10,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=10,
        )
    
    def _view_day_entries(self, year, month, day):
        """
        指定された日の日記エントリーを表示するためのイベントハンドラ。
        
        Args:
            year (int): 年
            month (int): 月
            day (int): 日
        """
        # ここでは日付を選択した後の処理を実装
        # カレンダービューに移動して選択した日付の表示など
        logger.info(f"日付が選択されました: {year}年{month}月{day}日")
        
        # 選択された日付をアプリの状態に保存して、カレンダービューに移動する例
        self.app.selected_date = datetime.datetime(year, month, day)
        self.app.navigate("calendar")
    
    def _open_entry(self, entry_id):
        """
        指定されたIDの日記エントリーを開くためのイベントハンドラ。
        
        Args:
            entry_id (str): 開く日記エントリーのID
        """
        # エントリーIDをアプリの状態に保存してエディタービューに移動
        self.app.current_entry_id = entry_id
        self.app.navigate("editor")
    
    def _on_mood_selected(self, mood):
        """
        気分が選択されたときのイベントハンドラ。
        
        Args:
            mood (int): 選択された気分スコア（1-5）
        """
        logger.info(f"気分が選択されました: {mood}")
        
        # 今日のエントリーがあるか確認し、なければ新規作成
        today = datetime.datetime.now().date()
        today_entries = self.diary_manager.get_entries_by_date(
            today.year, today.month, today.day
        )
        
        if today_entries:
            # 今日のエントリーが存在する場合は最初のエントリーの気分を更新
            entry = today_entries[0]
            entry.update(mood=mood)
            self.diary_manager.save_entry(entry)
            
            # 成功メッセージを表示
            self.app.page.show_snack_bar(
                ft.SnackBar(ft.Text(f"今日の気分を更新しました！"))
            )
        else:
            # 新しいエントリーを作成
            self.app.current_mood = mood
            self.app.navigate("editor")
    
    def _on_prompt_selected(self, prompt):
        """
        プロンプトが選択されたときのイベントハンドラ。
        選択されたプロンプトをエディタービューに渡します。
        
        Args:
            prompt (str): 選択されたプロンプト
        """
        logger.info(f"プロンプトが選択されました: {prompt}")
        
        # プロンプトをアプリの状態に保存
        self.app.current_prompt = prompt
        
        # エディタービューに移動
        self.app.navigate("editor") 