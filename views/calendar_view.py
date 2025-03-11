#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
カレンダービューモジュール

このモジュールは、月単位で日記エントリーを表示するカレンダーUIを提供します。
特定の日付のエントリーを選択して表示することができます。

作成者: Claude AI
バージョン: 1.0.0
"""

import flet as ft
import datetime
import calendar
from dateutil.relativedelta import relativedelta
import logging
from components.diary_card import DiaryCard

logger = logging.getLogger(__name__)

class CalendarView:
    """
    月単位のカレンダーと日記エントリーリストを表示するビュークラス。
    日付選択と過去の日記の閲覧に使用されます。
    """
    
    def __init__(self, app):
        """
        CalendarViewクラスのコンストラクタ。
        
        Args:
            app: メインアプリケーションの参照
        """
        self.app = app
        self.diary_manager = app.diary_manager
        
        # 現在表示中の年月
        self.current_year = datetime.datetime.now().year
        self.current_month = datetime.datetime.now().month
        
        # 選択された日付
        self.selected_date = getattr(app, 'selected_date', None) or datetime.datetime.now().date()
        
        # 日本語の曜日と月名
        self.weekdays_ja = ["月", "火", "水", "木", "金", "土", "日"]
        self.months_ja = ["1月", "2月", "3月", "4月", "5月", "6月", 
                         "7月", "8月", "9月", "10月", "11月", "12月"]
        
        # カレンダーのUIコントロール参照
        self.month_year_text = None
        self.calendar_grid = None
        self.entries_list = None
    
    def build(self):
        """
        カレンダービューのUIを構築します。
        
        Returns:
            ft.Container: カレンダービューのUIコンテナ
        """
        # 月・年の表示
        self.month_year_text = ft.Text(
            f"{self.current_year}年 {self.months_ja[self.current_month-1]}",
            size=24,
            weight=ft.FontWeight.BOLD,
        )
        
        # 月切り替えボタン
        prev_month_btn = ft.IconButton(
            icon=ft.icons.CHEVRON_LEFT,
            tooltip="前月",
            on_click=self._on_prev_month,
        )
        
        next_month_btn = ft.IconButton(
            icon=ft.icons.CHEVRON_RIGHT,
            tooltip="次月",
            on_click=self._on_next_month,
        )
        
        today_btn = ft.TextButton(
            text="今日",
            on_click=self._on_today_click,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )
        
        # カレンダーヘッダー
        calendar_header = ft.Row([
            prev_month_btn,
            self.month_year_text,
            next_month_btn,
            ft.Container(width=20),  # スペーサー
            today_btn,
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        # カレンダーグリッド
        self.calendar_grid = ft.Container()
        self._build_calendar_grid()
        
        # 選択された日のエントリーリスト
        self.entries_list = ft.Container()
        self._build_entries_list()
        
        # 新規作成ボタン
        new_entry_btn = ft.FloatingActionButton(
            icon=ft.icons.ADD,
            text="新規作成",
            on_click=lambda _: self._on_new_entry(),
        )
        
        # カレンダーを含むコンテナ
        calendar_container = ft.Container(
            content=ft.Column([
                calendar_header,
                ft.Container(height=20),  # スペーサー
                self.calendar_grid,
            ]),
            padding=20,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            border_radius=10,
            margin=ft.margin.only(bottom=20),
        )
        
        # エントリーリストのヘッダー
        entries_header = ft.Text(
            self._format_selected_date(),
            size=20,
            weight=ft.FontWeight.BOLD,
        )
        
        # メインコンテンツを含むスクロール可能なコンテナ
        main_content = ft.Column([
            calendar_container,
            entries_header,
            self.entries_list,
        ], scroll=ft.ScrollMode.AUTO, auto_scroll=False)
        
        # 全体のレイアウト
        return ft.Stack([
            # メインコンテンツ
            ft.Container(
                content=main_content,
                padding=20,
                width=float('inf'),
                height=float('inf'),
            ),
            # 右下の新規作成ボタン
            ft.Container(
                content=new_entry_btn,
                alignment=ft.alignment.bottom_right,
                padding=20,
            ),
        ])
    
    def _build_calendar_grid(self):
        """
        カレンダーグリッドを構築します。
        """
        # 現在の月の最初の日と最後の日
        first_day = datetime.date(self.current_year, self.current_month, 1)
        last_day = (first_day + relativedelta(months=1) - datetime.timedelta(days=1)).day
        
        # 月の最初の日の曜日（0: 月曜日, 6: 日曜日）
        first_weekday = first_day.weekday()
        
        # 曜日のヘッダー行
        weekday_row = ft.Row([
            ft.Container(
                content=ft.Text(day, weight=ft.FontWeight.BOLD),
                width=40,
                height=40,
                alignment=ft.alignment.center,
            )
            for day in self.weekdays_ja
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
        
        # カレンダーの週ごとの行
        calendar_rows = []
        day_num = 1
        
        # この月の日記エントリーを取得
        month_entries = {}
        try:
            entries = self.diary_manager.get_entries_by_date(self.current_year, self.current_month)
            for entry in entries:
                day = entry.created_at.day
                if day not in month_entries:
                    month_entries[day] = []
                month_entries[day].append(entry)
        except Exception as e:
            logger.error(f"月間エントリーの取得中にエラーが発生しました: {e}")
        
        # 今日の日付
        today = datetime.datetime.now().date()
        
        # 週ごとにカレンダー行を作成
        for week in range(6):  # 最大6週間分
            week_days = []
            
            for weekday in range(7):  # 各曜日
                # 月の開始前または終了後の空白セル
                if (week == 0 and weekday < first_weekday) or day_num > last_day:
                    week_days.append(
                        ft.Container(
                            width=40,
                            height=40,
                        )
                    )
                else:
                    # 日付を持つセル
                    day_date = datetime.date(self.current_year, self.current_month, day_num)
                    
                    # 今日、選択日、エントリーがある日かをチェック
                    is_today = day_date == today
                    # selected_dateがdatetimeオブジェクトかdateオブジェクトかをチェック
                    if hasattr(self.selected_date, 'date'):
                        selected_date = self.selected_date.date()
                    else:
                        selected_date = self.selected_date
                    is_selected = day_date == selected_date
                    has_entries = day_num in month_entries
                    
                    # 見た目の設定
                    bg_color = None
                    text_color = None
                    border = None
                    
                    if is_selected:
                        bg_color = ft.colors.PRIMARY
                        text_color = ft.colors.ON_PRIMARY
                    elif is_today:
                        bg_color = ft.colors.PRIMARY_CONTAINER
                        text_color = ft.colors.ON_PRIMARY_CONTAINER
                    
                    if has_entries and not is_selected:
                        border = ft.border.all(2, ft.colors.SECONDARY)
                    
                    # 日付セル
                    day_cell = ft.Container(
                        content=ft.Column([
                            ft.Text(
                                str(day_num),
                                color=text_color,
                                weight=ft.FontWeight.BOLD if is_today or is_selected else None,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Container(
                                content=ft.Icon(
                                    ft.icons.CIRCLE,
                                    size=8,
                                    color=ft.colors.SECONDARY,
                                ) if has_entries and not is_selected else None,
                                height=8,
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=2),
                        width=40,
                        height=40,
                        border_radius=20,
                        bgcolor=bg_color,
                        border=border,
                        alignment=ft.alignment.center,
                        on_click=lambda e, d=day_num: self._on_day_click(d),
                    )
                    
                    week_days.append(day_cell)
                    day_num += 1
            
            # 週の行を追加
            calendar_rows.append(
                ft.Row(
                    week_days,
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                )
            )
            
            # 月の最終日を過ぎたら終了
            if day_num > last_day:
                break
        
        # カレンダーグリッドを更新
        self.calendar_grid.content = ft.Column(
            [weekday_row] + calendar_rows,
            spacing=10,
        )
    
    def _build_entries_list(self):
        """
        選択された日付の日記エントリーリストを構築します。
        """
        # 選択された日のエントリーを取得
        entries = []
        try:
            entries = self.diary_manager.get_entries_by_date(
                self.selected_date.year, 
                self.selected_date.month, 
                self.selected_date.day
            )
        except Exception as e:
            logger.error(f"日付のエントリー取得中にエラーが発生しました: {e}")
        
        # エントリーが無い場合のメッセージ
        if not entries:
            self.entries_list.content = ft.Container(
                content=ft.Column([
                    ft.Text("この日の日記はありません", italic=True),
                    ft.ElevatedButton(
                        "新しく書く",
                        icon=ft.icons.EDIT,
                        on_click=lambda _: self._on_new_entry(),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                padding=40,
            )
            return
        
        # エントリーカードのリスト
        entry_cards = []
        for entry in entries:
            entry_card = DiaryCard(
                entry=entry,
                on_click=lambda e, entry_id=entry.id: self._open_entry(entry_id),
            )
            entry_cards.append(entry_card)
        
        # リストを更新
        self.entries_list.content = ft.Column(
            entry_cards,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
    
    def _format_selected_date(self):
        """
        選択された日付を表示用にフォーマットします。
        
        Returns:
            str: フォーマットされた日付文字列
        """
        weekday_ja = self.weekdays_ja[self.selected_date.weekday()]
        return f"{self.selected_date.year}年{self.selected_date.month}月{self.selected_date.day}日（{weekday_ja}）"
    
    def _on_prev_month(self, e):
        """
        前月ボタンがクリックされたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        # 前月に移動
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
            
        # UIを更新
        self.month_year_text.value = f"{self.current_year}年 {self.months_ja[self.current_month-1]}"
        self._build_calendar_grid()
        self.month_year_text.update()
        self.calendar_grid.update()
    
    def _on_next_month(self, e):
        """
        次月ボタンがクリックされたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        # 次月に移動
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
            
        # UIを更新
        self.month_year_text.value = f"{self.current_year}年 {self.months_ja[self.current_month-1]}"
        self._build_calendar_grid()
        self.month_year_text.update()
        self.calendar_grid.update()
    
    def _on_today_click(self, e):
        """
        「今日」ボタンがクリックされたときのイベントハンドラ。
        
        Args:
            e: イベントデータ
        """
        # 今日の日付に設定
        today = datetime.datetime.now()
        self.current_year = today.year
        self.current_month = today.month
        self.selected_date = today
        
        # UIを更新
        self.month_year_text.value = f"{self.current_year}年 {self.months_ja[self.current_month-1]}"
        self._build_calendar_grid()
        self._build_entries_list()
        
        # 選択日表示を更新
        self.app.page.controls[0].content.controls[2].value = self._format_selected_date()
        
        # 全て更新
        self.month_year_text.update()
        self.calendar_grid.update()
        self.entries_list.update()
        self.app.page.controls[0].content.controls[2].update()
    
    def _on_day_click(self, day):
        """
        日付セルがクリックされたときのイベントハンドラ。
        
        Args:
            day: クリックされた日
        """
        # 選択された日付を更新
        self.selected_date = datetime.datetime(self.current_year, self.current_month, day)
        
        # UIを更新
        self._build_calendar_grid()
        self._build_entries_list()
        
        # 選択日表示を更新
        self.app.page.controls[0].content.controls[2].value = self._format_selected_date()
        
        # 更新
        self.calendar_grid.update()
        self.entries_list.update()
        self.app.page.controls[0].content.controls[2].update()
    
    def _open_entry(self, entry_id):
        """
        エントリーを開くためのイベントハンドラ。
        
        Args:
            entry_id: 開くエントリーのID
        """
        # エントリーIDをアプリの状態に保存
        self.app.current_entry_id = entry_id
        
        # エディター画面に移動
        self.app.navigate("editor")
    
    def _on_new_entry(self):
        """
        新規エントリー作成ボタンがクリックされたときのイベントハンドラ。
        """
        # 選択された日付をアプリの状態に保存
        if hasattr(self.app, 'current_entry_id'):
            delattr(self.app, 'current_entry_id')
            
        # エディター画面に移動
        self.app.navigate("editor") 