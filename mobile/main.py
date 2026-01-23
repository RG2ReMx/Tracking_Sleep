import os
import json
import random
from datetime import datetime, timedelta
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty, NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.list import OneLineListItem

Builder.load_file('sleep_tracker.kv')


class SleepPhaseAnalyzer:
    @staticmethod
    def generate_sleep_phases(total_minutes):
        if total_minutes < 30:
            return []

        phases = []
        remaining = total_minutes
        cycle_num = 1

        while remaining > 20:
            light = min(random.randint(5, 15), remaining)
            if light > 0:
                phases.append({'type': 'light', 'duration': light, 'cycle': cycle_num})
                remaining -= light

            medium = min(random.randint(20, 35), remaining)
            if medium > 0:
                phases.append({'type': 'medium', 'duration': medium, 'cycle': cycle_num})
                remaining -= medium

            deep = min(random.randint(15, 40), remaining)
            if deep > 0:
                phases.append({'type': 'deep', 'duration': deep, 'cycle': cycle_num})
                remaining -= deep

            rem = min(random.randint(10, 25), remaining)
            if rem > 0:
                phases.append({'type': 'rem', 'duration': rem, 'cycle': cycle_num})
                remaining -= rem

            cycle_num += 1

        return phases

    @staticmethod
    def analyze_phases(phases):
        if not phases:
            return {
                'total_score': 0,
                'analysis': ['Недостаточно данных'],
                'phase_distribution': {},
                'total_duration': 0,
                'deep_sleep': 0,
                'rem_sleep': 0,
                'cycles': 0
            }

        total_duration = sum(p['duration'] for p in phases)
        phase_dist = {}

        for phase in phases:
            phase_type = phase['type']
            phase_dist[phase_type] = phase_dist.get(phase_type, 0) + phase['duration']

        cycles = len(set(p.get('cycle', 0) for p in phases))
        score = 0

        if total_duration >= 420:
            score += 40
        elif total_duration >= 360:
            score += 30
        elif total_duration >= 300:
            score += 20
        else:
            score += 10

        deep_sleep = phase_dist.get('deep', 0)
        if deep_sleep >= 90:
            score += 30
        elif deep_sleep >= 60:
            score += 25
        elif deep_sleep >= 30:
            score += 20
        elif deep_sleep > 0:
            score += 10

        rem_sleep = phase_dist.get('rem', 0)
        if rem_sleep >= 90:
            score += 20
        elif rem_sleep >= 60:
            score += 15
        elif rem_sleep >= 30:
            score += 10
        elif rem_sleep > 0:
            score += 5

        if cycles >= 5:
            score += 10
        elif cycles >= 4:
            score += 8
        elif cycles >= 3:
            score += 5
        elif cycles >= 2:
            score += 3

        analysis = []
        if total_duration < 360:
            analysis.append("Слишком короткий сон")
        if deep_sleep < 30:
            analysis.append("Мало глубокого сна")
        if rem_sleep < 30:
            analysis.append("Мало REM-сна")
        if cycles < 4:
            analysis.append(f"Мало циклов сна ({cycles})")

        if not analysis:
            analysis.append("Отличное качество сна")

        return {
            'total_score': min(score, 100),
            'analysis': analysis,
            'phase_distribution': phase_dist,
            'total_duration': total_duration,
            'deep_sleep': deep_sleep,
            'rem_sleep': rem_sleep,
            'cycles': cycles
        }


class SleepAdvisor:
    @staticmethod
    def get_recommendations(sleep_data):
        if not sleep_data or len(sleep_data) < 3:
            return ["Соберите больше данных о сне (минимум 3 записи)"]

        recent_data = sleep_data[-7:] if len(sleep_data) >= 7 else sleep_data
        total_records = len(recent_data)
        total_minutes = sum(r['duration_hours'] * 60 + r['duration_minutes'] for r in recent_data)
        avg_minutes = total_minutes // total_records if total_records > 0 else 0
        total_quality = sum(r.get('quality_10', 5) for r in recent_data)
        avg_quality = total_quality // total_records if total_records > 0 else 5

        bed_times = []
        wake_times = []

        for record in recent_data:
            if 'start_time' in record:
                try:
                    hour = int(record['start_time'].split(':')[0])
                    bed_times.append(hour)
                except:
                    pass

            if 'end_time' in record:
                try:
                    hour = int(record['end_time'].split(':')[0])
                    wake_times.append(hour)
                except:
                    pass

        recommendations = []

        if avg_minutes < 360:
            recommendations.append("Увеличьте продолжительность сна до 7-9 часов")
            recommendations.append("Попробуйте ложиться на 30-60 минут раньше")
        elif avg_minutes > 540:
            recommendations.append("Слишком долгий сон (более 9 часов)")
            recommendations.append("Установите будильник на 8-9 часов")
        elif 420 <= avg_minutes <= 480:
            recommendations.append("Отличная длительность сна")

        if avg_quality < 5:
            recommendations.append("Качество сна низкое")
            recommendations.append("Поддерживайте температуру 18-20°C")
        elif avg_quality >= 8:
            recommendations.append("Отличное качество сна")
        else:
            recommendations.append("Качество сна среднее")

        if bed_times and len(bed_times) >= 3:
            bed_time_std = max(bed_times) - min(bed_times)
            if bed_time_std > 2:
                recommendations.append("Нерегулярное время отхода ко сну")

        if wake_times and len(wake_times) >= 3:
            wake_time_std = max(wake_times) - min(wake_times)
            if wake_time_std > 2:
                recommendations.append("Просыпайтесь в одно и то же время")

        general_recs = [
            "Отложите электронные устройства за 1-2 часа до сна",
            "Избегайте кофеина после 14:00",
            "Не ешьте тяжелую пищу за 3 часа до сна",
            "Регулярные физические упражнения улучшают сон",
            "Поддерживайте водный баланс"
        ]

        if len(recommendations) < 5:
            num_to_add = min(5 - len(recommendations), len(general_recs))
            recommendations.extend(general_recs[:num_to_add])

        return recommendations[:10]

    @staticmethod
    def get_daily_tip():
        tips = [
            "Сегодня попробуйте почитать бумажную книгу перед сном",
            "Проветрите комнату перед сном",
            "Попробуйте медитацию перед сном",
            "Заведите дневник сна",
            "Установите постоянное время подъема",
            "Избегайте тяжелой пищи перед сном",
            "Теплая ванна помогает расслабиться",
            "Белый шум может помочь заснуть",
            "Утром получайте солнечный свет",
            "Если не можете заснуть 20 минут, встаньте"
        ]
        return random.choice(tips)

    @staticmethod
    def get_quick_tips():
        return [
            "Выключите уведомления перед сном",
            "Используйте ночной режим на устройствах",
            "Попробуйте ароматерапию с лавандой",
            "Наденьте носки если мерзнут ноги",
            "Читайте бумажные книги перед сном"
        ]


class WeeklyTable(BoxLayout):
    def __init__(self, weekly_data, **kwargs):
        super().__init__(**kwargs)
        self.weekly_data = weekly_data or []
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.padding = [5, 5, 5, 5]
        self.spacing = 2
        self.create_table()

    def create_table(self):
        self.clear_widgets()

        if not self.weekly_data:
            no_data_label = Label(
                text="Нет данных о сне за последние 7 дней",
                halign='center',
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None,
                height=40
            )
            self.add_widget(no_data_label)
            self.height = 50
            return

        title_label = Label(
            text="Данные за неделю",
            bold=True,
            halign='center',
            color=(0.2, 0.2, 0.6, 1),
            font_size='16sp',
            size_hint_y=None,
            height=30
        )
        self.add_widget(title_label)

        table_grid = GridLayout(
            cols=4,
            size_hint_y=None,
            spacing=2,
            padding=[2, 2, 2, 2]
        )
        table_grid.height = 35 * 8
        table_grid.row_default_height = 35

        headers = ["День", "Длит.", "Кач.", "Дата"]
        for header in headers:
            header_label = Label(
                text=header,
                bold=True,
                halign='center',
                color=(0.3, 0.3, 0.7, 1),
                font_size='14sp'
            )
            table_grid.add_widget(header_label)

        days_order = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

        for day in days_order:
            day_data = next((d for d in self.weekly_data if d.get('day') == day), None)

            day_label = Label(
                text=day,
                halign='center',
                color=(0.2, 0.2, 0.2, 1),
                font_size='13sp'
            )
            table_grid.add_widget(day_label)

            if day_data and (day_data['duration_hours'] > 0 or day_data['duration_minutes'] > 0):
                duration = f"{day_data['duration_hours']}ч {day_data['duration_minutes']}м"
                duration_label = Label(
                    text=duration,
                    halign='center',
                    color=(0.3, 0.3, 0.3, 1),
                    font_size='13sp'
                )
                table_grid.add_widget(duration_label)

                quality = day_data.get('quality_10', 5)
                quality_color = self.get_quality_color(quality)
                quality_label = Label(
                    text=f"{quality}/10",
                    halign='center',
                    color=quality_color,
                    font_size='13sp'
                )
                table_grid.add_widget(quality_label)

                date_label = Label(
                    text=day_data['date'],
                    halign='center',
                    color=(0.4, 0.4, 0.4, 1),
                    font_size='12sp'
                )
                table_grid.add_widget(date_label)
            else:
                for _ in range(3):
                    empty_label = Label(
                        text="-",
                        halign='center',
                        color=(0.7, 0.7, 0.7, 1),
                        font_size='13sp'
                    )
                    table_grid.add_widget(empty_label)

        self.add_widget(table_grid)
        self.height = 60 + table_grid.height

    def get_quality_color(self, quality):
        if quality >= 8:
            return (0, 0.6, 0, 1)
        elif quality >= 5:
            return (0.2, 0.6, 1, 1)
        else:
            return (1, 0.4, 0.4, 1)


class SleepTrackerScreen(Screen):
    is_tracking = BooleanProperty(False)
    current_duration = StringProperty("00:00:00")
    total_sleep_today = StringProperty("0ч 0м")
    sleep_quality = StringProperty("5/10")
    elapsed_hours = NumericProperty(0)
    elapsed_minutes = NumericProperty(0)
    elapsed_seconds = NumericProperty(0)
    weekly_data = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sleep_start_time = None
        self.sleep_data = []
        self.timer_event = None
        self.sleep_advisor = SleepAdvisor()
        self.load_data()
        self.update_display()
        self.update_weekly_chart()
        self.cleanup_old_data()

    def load_data(self):
        try:
            if os.path.exists('sleep_data.json'):
                with open('sleep_data.json', 'r', encoding='utf-8') as f:
                    self.sleep_data = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            self.sleep_data = []

    def save_data(self):
        try:
            with open('sleep_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.sleep_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def cleanup_old_data(self):
        if not self.sleep_data:
            return

        current_date = datetime.now()
        cutoff_date = current_date - timedelta(days=7)
        new_data = []

        for record in self.sleep_data:
            try:
                record_date = datetime.strptime(record['date'], '%Y-%m-%d')
                if record_date >= cutoff_date:
                    new_data.append(record)
            except:
                continue

        if len(new_data) < len(self.sleep_data):
            self.sleep_data = new_data
            self.save_data()

    def show_menu(self, *args):
        dialog = MDDialog(
            title="Меню",
            text="Трекер сна",
            buttons=[
                MDFlatButton(
                    text="ЗАКРЫТЬ",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def show_recommendations(self, *args):
        recommendations = self.sleep_advisor.get_recommendations(self.sleep_data)
        daily_tip = self.sleep_advisor.get_daily_tip()
        quick_tips = self.sleep_advisor.get_quick_tips()

        content_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)

        content = BoxLayout(orientation='vertical', spacing=10, padding=20, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        tip_label = Label(
            text=f"Совет дня:\n{daily_tip}",
            font_size='16sp',
            bold=True,
            color=(0.2, 0.4, 0.6, 1),
            size_hint_y=None,
            height=80,
            text_size=(350, None),
            halign='left',
            valign='top'
        )
        content.add_widget(tip_label)

        if quick_tips:
            quick_label = Label(
                text="Быстрые советы:",
                font_size='16sp',
                bold=True,
                color=(0.3, 0.5, 0.3, 1),
                size_hint_y=None,
                height=30
            )
            content.add_widget(quick_label)

            for i, tip in enumerate(quick_tips[:3]):
                tip_item = Label(
                    text=f"{i + 1}. {tip}",
                    font_size='14sp',
                    color=(0.4, 0.4, 0.4, 1),
                    size_hint_y=None,
                    height=30,
                    text_size=(350, None),
                    halign='left'
                )
                content.add_widget(tip_item)

        if recommendations:
            rec_label = Label(
                text="Персональные рекомендации:",
                font_size='16sp',
                bold=True,
                color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=30
            )
            content.add_widget(rec_label)

            for i, rec in enumerate(recommendations):
                rec_item = Label(
                    text=f"{i + 1}. {rec}",
                    font_size='14sp',
                    color=(0.4, 0.4, 0.4, 1),
                    size_hint_y=None,
                    height=40,
                    text_size=(350, None),
                    halign='left',
                    valign='top'
                )
                content.add_widget(rec_item)

        if len(self.sleep_data) >= 3:
            total_records = len(self.sleep_data)
            total_minutes = sum(r['duration_hours'] * 60 + r['duration_minutes'] for r in self.sleep_data[-7:])
            avg_minutes = total_minutes // min(7, total_records) if min(7, total_records) > 0 else 0
            avg_hours = avg_minutes // 60
            avg_minutes_remainder = avg_minutes % 60

            stats_label = Label(
                text=f"\nСтатистика за неделю:\nСредний сон: {avg_hours}ч {avg_minutes_remainder}м",
                font_size='14sp',
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None,
                height=50,
                text_size=(350, None),
                halign='left'
            )
            content.add_widget(stats_label)
        elif self.sleep_data:
            stats_label = Label(
                text=f"\nУ вас {len(self.sleep_data)} запись(ей) о сне.",
                font_size='14sp',
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None,
                height=50,
                text_size=(350, None),
                halign='left'
            )
            content.add_widget(stats_label)

        content_scroll.add_widget(content)

        container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        container.height = 500
        container.add_widget(content_scroll)

        close_button = MDRaisedButton(
            text="ЗАКРЫТЬ",
            size_hint_y=None,
            height=50,
            md_bg_color=(0.2, 0.5, 0.8, 1),
            on_press=lambda x: dialog.dismiss()
        )
        container.add_widget(close_button)

        dialog = MDDialog(
            title="Рекомендации по сну",
            type="custom",
            content_cls=container,
            size_hint=(0.95, 0.9),
            auto_dismiss=False
        )
        dialog.open()

    def show_manual_delete_dialog(self, *args):
        dialog = MDDialog(
            title="Удаление всех данных",
            text="Вы уверены, что хотите удалить ВСЕ данные о сне?\n\n",
            buttons=[
                MDFlatButton(
                    text="ОТМЕНА",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDFlatButton(
                    text="УДАЛИТЬ ВСЁ",
                    text_color=(1, 0, 0, 1),
                    on_release=lambda x: self.confirm_manual_delete(dialog)
                )
            ]
        )
        dialog.open()

    def confirm_manual_delete(self, dialog):
        self.sleep_data = []
        self.save_data()
        self.update_display()
        self.update_weekly_chart()
        dialog.dismiss()
        self.show_message("Данные удалены", "Все записи удалены.")

    def show_sleep_analysis(self, *args):
        if not self.sleep_data:
            self.show_message("Анализ сна", "Нет записей о сне.")
            return

        last_record = None
        for record in reversed(self.sleep_data):
            if 'sleep_phases' in record and record['sleep_phases']:
                last_record = record
                break

        if not last_record:
            last_record = self.sleep_data[-1] if self.sleep_data else None

        if not last_record:
            self.show_message("Анализ сна", "Нет записей для анализа.")
            return

        total_minutes = last_record['duration_hours'] * 60 + last_record['duration_minutes']

        if 'sleep_phases' not in last_record or not last_record['sleep_phases']:
            if total_minutes > 30:
                last_record['sleep_phases'] = SleepPhaseAnalyzer.generate_sleep_phases(total_minutes)
                self.save_data()
            else:
                self.show_message("Анализ сна",
                                  f"Недостаточно данных.\n\n"
                                  f"Последний сон: {last_record['duration_hours']}ч {last_record['duration_minutes']}м")
                return

        analysis = SleepPhaseAnalyzer.analyze_phases(last_record['sleep_phases'])

        # Создаем ScrollView для контента (как в show_recommendations)
        content_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)

        content = BoxLayout(orientation='vertical', spacing=10, padding=20, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        score_text = f"Общая оценка сна: {analysis['total_score']}/100"
        if analysis['total_score'] >= 80:
            score_text += " (Отлично)"
        elif analysis['total_score'] >= 60:
            score_text += " (Хорошо)"
        else:
            score_text += " (Можно лучше)"

        score_label = Label(
            text=score_text,
            font_size='16sp',
            bold=True,
            color=(0.2, 0.4, 0.6, 1),
            size_hint_y=None,
            height=40,
            text_size=(350, None),
            halign='left',
            valign='middle'
        )
        content.add_widget(score_label)

        info_text = (f"Дата: {last_record['date']}\n"
                     f"Длительность: {last_record['duration_hours']}ч {last_record['duration_minutes']}м\n"
                     f"Циклов сна: {analysis['cycles']}")

        info_label = Label(
            text=info_text,
            font_size='14sp',
            color=(0.4, 0.4, 0.4, 1),
            size_hint_y=None,
            height=60,
            text_size=(350, None),
            halign='left',
            valign='top'
        )
        content.add_widget(info_label)

        dist_label = Label(
            text="Распределение фаз сна:",
            font_size='16sp',
            bold=True,
            color=(0.3, 0.5, 0.3, 1),
            size_hint_y=None,
            height=30
        )
        content.add_widget(dist_label)

        phase_names = {
            'light': 'Легкий сон',
            'medium': 'Средний сон',
            'deep': 'Глубокий сон',
            'rem': 'REM-сон'
        }

        for phase_type, duration in analysis['phase_distribution'].items():
            phase_name = phase_names.get(phase_type, phase_type)
            hours = duration // 60
            minutes = duration % 60

            phase_text = f"{phase_name}: {hours}ч {minutes}м"
            phase_label = Label(
                text=phase_text,
                font_size='14sp',
                color=(0.4, 0.4, 0.4, 1),
                size_hint_y=None,
                height=30,
                text_size=(350, None),
                halign='left',
                valign='middle'
            )
            content.add_widget(phase_label)

        if analysis['analysis']:
            rec_label = Label(
                text="Рекомендации:",
                font_size='16sp',
                bold=True,
                color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=30
            )
            content.add_widget(rec_label)

            for rec in analysis['analysis']:
                rec_item = Label(
                    text=f"• {rec}",
                    font_size='14sp',
                    color=(0.4, 0.4, 0.4, 1),
                    size_hint_y=None,
                    height=30,
                    text_size=(350, None),
                    halign='left',
                    valign='middle'
                )
                content.add_widget(rec_item)

        content_scroll.add_widget(content)

        # Контейнер с кнопкой (как в show_recommendations)
        container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        container.height = 500
        container.add_widget(content_scroll)

        close_button = MDRaisedButton(
            text="ЗАКРЫТЬ",
            size_hint_y=None,
            height=50,
            md_bg_color=(0.2, 0.5, 0.8, 1),
            on_press=lambda x: dialog.dismiss()
        )
        container.add_widget(close_button)

        dialog = MDDialog(
            title="Анализ фаз сна",
            type="custom",
            content_cls=container,
            size_hint=(0.95, 0.9),
            auto_dismiss=False
        )
        dialog.open()

    def show_weekly_chart(self, *args):
        self.update_weekly_chart()

        if not self.weekly_data:
            self.show_message("Нет данных", "Нет данных о сне за последние 7 дней.")
            return

        table = WeeklyTable(self.weekly_data)
        scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        scroll_view.add_widget(table)

        container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        container.height = 400
        container.add_widget(scroll_view)

        close_button = MDRaisedButton(
            text="ЗАКРЫТЬ",
            size_hint_y=None,
            height=50,
            md_bg_color=(0.2, 0.5, 0.8, 1),
            on_press=lambda x: dialog.dismiss()
        )
        container.add_widget(close_button)

        dialog = MDDialog(
            title="Данные за неделю",
            type="custom",
            content_cls=container,
            size_hint=(0.95, 0.8),
            auto_dismiss=False
        )
        dialog.open()

    def update_weekly_chart(self):
        self.weekly_data = []

        if not self.sleep_data:
            return

        days_order = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

        for i in range(7):
            target_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            day_name = days_order[(datetime.now() - timedelta(days=i)).weekday()]

            day_records = [r for r in self.sleep_data if r.get('date') == target_date]

            if day_records:
                total_hours = sum(r['duration_hours'] for r in day_records)
                total_minutes = sum(r['duration_minutes'] for r in day_records)

                total_hours += total_minutes // 60
                total_minutes = total_minutes % 60

                total_quality = sum(r.get('quality_10', 5) for r in day_records)
                avg_quality = total_quality // len(day_records) if day_records else 5

                self.weekly_data.append({
                    'day': day_name,
                    'duration_hours': total_hours,
                    'duration_minutes': total_minutes,
                    'quality_10': avg_quality,
                    'date': target_date
                })

    def calculate_sleep_quality_10(self, hours, minutes):
        total_hours = hours + minutes / 60

        if total_hours <= 3:
            return max(1, min(3, int(total_hours)))
        elif total_hours <= 6:
            return max(4, min(6, int(total_hours + 1)))
        elif total_hours <= 9:
            return max(7, min(9, int(total_hours + 1)))
        else:
            return 10

    def start_sleep_tracking(self):
        if not self.is_tracking:
            self.is_tracking = True
            self.sleep_start_time = datetime.now()

            self.elapsed_hours = 0
            self.elapsed_minutes = 0
            self.elapsed_seconds = 0
            self.update_duration_display()

            self.ids.status_label.text = "Спит..."
            self.ids.start_button.disabled = True
            self.ids.stop_button.disabled = False
            self.ids.start_button.md_bg_color = (0.5, 0.5, 0.5, 1)
            self.ids.stop_button.md_bg_color = (0.9, 0, 0, 1)

            self.timer_event = Clock.schedule_interval(self.update_timer, 1)

    def update_timer(self, dt):
        if self.is_tracking:
            self.elapsed_seconds += 1

            if self.elapsed_seconds >= 60:
                self.elapsed_seconds = 0
                self.elapsed_minutes += 1

            if self.elapsed_minutes >= 60:
                self.elapsed_minutes = 0
                self.elapsed_hours += 1

            self.update_duration_display()

    def update_duration_display(self):
        self.current_duration = f"{self.elapsed_hours:02d}:{self.elapsed_minutes:02d}:{self.elapsed_seconds:02d}"

    def stop_sleep_tracking(self):
        if self.is_tracking:
            self.is_tracking = False

            if self.timer_event:
                Clock.unschedule(self.timer_event)
                self.timer_event = None

            quality = self.calculate_sleep_quality_10(self.elapsed_hours, self.elapsed_minutes)

            total_minutes = self.elapsed_hours * 60 + self.elapsed_minutes
            sleep_phases = []
            if total_minutes > 30:
                sleep_phases = SleepPhaseAnalyzer.generate_sleep_phases(total_minutes)

            record = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'start_time': self.sleep_start_time.strftime('%H:%M') if self.sleep_start_time else "00:00",
                'end_time': datetime.now().strftime('%H:%M'),
                'duration_hours': self.elapsed_hours,
                'duration_minutes': self.elapsed_minutes,
                'quality_10': quality,
                'sleep_phases': sleep_phases,
                'timestamp': datetime.now().isoformat()
            }

            self.sleep_data.append(record)
            self.save_data()

            self.ids.status_label.text = "Не отслеживается"
            self.ids.start_button.disabled = False
            self.ids.stop_button.disabled = True
            self.ids.start_button.md_bg_color = (0, 0.7, 0, 1)
            self.ids.stop_button.md_bg_color = (0.5, 0.5, 0.5, 1)

            self.show_message("Сон записан",
                              f"Длительность: {self.elapsed_hours}ч {self.elapsed_minutes}м\n"
                              f"Качество: {quality}/10")

            self.update_display()
            self.update_weekly_chart()

            self.elapsed_hours = 0
            self.elapsed_minutes = 0
            self.elapsed_seconds = 0
            self.update_duration_display()

    def update_display(self):
        today = datetime.now().strftime('%Y-%m-%d')
        today_sleep = 0
        today_records = []

        for record in self.sleep_data:
            if record['date'] == today:
                today_sleep += record['duration_hours'] * 60 + record['duration_minutes']
                today_records.append(record)

        hours = today_sleep // 60
        minutes = today_sleep % 60
        self.total_sleep_today = f"{hours}ч {minutes}м"

        if today_records:
            total_quality = 0
            for record in today_records:
                if 'quality_10' in record:
                    total_quality += record['quality_10']
                elif 'quality' in record:
                    total_quality += record['quality'] * 2

            avg_quality = total_quality // len(today_records) if today_records else 5
            self.sleep_quality = f"{avg_quality}/10"

            if hours > 0 or minutes > 0:
                self.ids.weekly_summary_label.text = f"Сегодня: {hours}ч {minutes}м | Кач: {avg_quality}/10"
            else:
                self.ids.weekly_summary_label.text = "Сегодня сна не было"
        else:
            self.sleep_quality = "5/10"
            self.ids.weekly_summary_label.text = "Начните отслеживать сон"

        self.ids.sleep_records_list.clear_widgets()

        if self.sleep_data:
            recent_records = sorted(self.sleep_data,
                                    key=lambda x: x.get('timestamp', ''),
                                    reverse=True)[:5]

            for record in recent_records:
                if 'quality_10' in record:
                    quality = record['quality_10']
                elif 'quality' in record:
                    quality = record['quality'] * 2
                else:
                    quality = 5

                item_text = f"{record['date']} - {record['duration_hours']}ч {record['duration_minutes']}м - {quality}/10"

                item = OneLineListItem(text=item_text)
                self.ids.sleep_records_list.add_widget(item)

    def show_stats(self, *args):
        if not self.sleep_data:
            self.show_message("Статистика", "Нет записей о сне.")
            return

        total_records = len(self.sleep_data)
        total_minutes = sum(r['duration_hours'] * 60 + r['duration_minutes'] for r in self.sleep_data)

        avg_minutes = total_minutes // total_records if total_records > 0 else 0
        avg_hours = avg_minutes // 60
        avg_minutes_remainder = avg_minutes % 60

        total_quality = 0
        for record in self.sleep_data:
            if 'quality_10' in record:
                total_quality += record['quality_10']
            elif 'quality' in record:
                total_quality += record['quality'] * 2
        avg_quality = total_quality // total_records if total_records > 0 else 5

        stats_text = (
            f"Статистика сна:\n\n"
            f"• Всего записей: {total_records}\n"
            f"• Средний сон: {avg_hours}ч {avg_minutes_remainder}м\n"
            f"• Среднее качество: {avg_quality}/10\n"
            f"• Общее время сна: {total_minutes // 60}ч {total_minutes % 60}м"
        )

        dialog = MDDialog(
            title="Статистика сна",
            text=stats_text,
            buttons=[
                MDFlatButton(
                    text="ЗАКРЫТЬ",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="АНАЛИЗ СНА",
                    md_bg_color=(0.2, 0.6, 1, 1),
                    on_release=lambda x: (dialog.dismiss(), self.show_sleep_analysis())
                ),
                MDRaisedButton(
                    text="РЕКОМЕНДАЦИИ",
                    md_bg_color=(0.8, 0.6, 0.2, 1),
                    on_release=lambda x: (dialog.dismiss(), self.show_recommendations())
                )
            ]
        )
        dialog.open()

    def show_tips(self, *args):
        daily_tip = self.sleep_advisor.get_daily_tip()

        dialog = MDDialog(
            title="Совет дня",
            text=f"{daily_tip}",
            buttons=[
                MDFlatButton(
                    text="ЗАКРЫТЬ",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="БОЛЬШЕ РЕКОМЕНДАЦИЙ",
                    md_bg_color=(0.8, 0.6, 0.2, 1),
                    on_release=lambda x: (dialog.dismiss(), self.show_recommendations())
                )
            ]
        )
        dialog.open()

    def show_message(self, title, message):
        dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class SleepTrackerApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        return SleepTrackerScreen(name='sleep_tracker')

    def on_pause(self):
        if self.root:
            self.root.save_data()
        return True

    def on_resume(self):
        if self.root:
            self.root.update_display()
            self.root.update_weekly_chart()
        return True


if __name__ == '__main__':
    print("Запуск Трекера Сна...")
    SleepTrackerApp().run()