"""
Генерация графиков с помощью matplotlib.
"""
import io
from datetime import date, timedelta
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure

from database.models import Measurement


def generate_progress_chart(
    measurements: List[Measurement],
    period_days: int = 30
) -> Tuple[io.BytesIO, Optional[dict]]:
    """
    Генерирует PNG-график с 4 показателями.

    Args:
        measurements: Список записей Measurement (отсортированных по дате)
        period_days: Период для отображения (по умолчанию 30 дней)

    Returns:
        Tuple[BytesIO, dict]:
            - BytesIO с PNG-изображением
            - dict с метриками прогресса (начальный → текущий) или None если нет данных
    """
    if not measurements:
        return None, None

    # Извлечь данные (с фильтрацией None)
    dates = [m.date for m in measurements]

    # Для графика нужны параллельные списки (date, value), None заменяем на пропуски
    weights = [m.weight if m.weight is not None else None for m in measurements]
    waists = [m.waist if m.waist is not None else None for m in measurements]
    necks = [m.neck if m.neck is not None else None for m in measurements]
    calories_list = [m.calories if m.calories is not None else None for m in measurements]

    # Для метрик берем только не-None значения
    weights_filtered = [m.weight for m in measurements if m.weight is not None]
    waists_filtered = [m.waist for m in measurements if m.waist is not None]
    necks_filtered = [m.neck for m in measurements if m.neck is not None]

    # Вычислить метрики прогресса (только если есть данные)
    metrics = {}
    if weights_filtered:
        metrics['weight_start'] = weights_filtered[0]
        metrics['weight_current'] = weights_filtered[-1]
        metrics['weight_diff'] = weights_filtered[-1] - weights_filtered[0]

    if waists_filtered:
        metrics['waist_start'] = waists_filtered[0]
        metrics['waist_current'] = waists_filtered[-1]
        metrics['waist_diff'] = waists_filtered[-1] - waists_filtered[0]

    if necks_filtered:
        metrics['neck_start'] = necks_filtered[0]
        metrics['neck_current'] = necks_filtered[-1]
        metrics['neck_diff'] = necks_filtered[-1] - necks_filtered[0]

    # Создать фигуру
    fig, ax1 = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor('white')

    # Основная ось Y (слева) - для веса
    color_weight = '#2E86AB'
    ax1.set_xlabel('Дата', fontsize=12)
    ax1.set_ylabel('Вес (кг)', color=color_weight, fontsize=12)
    ax1.plot(dates, weights, color=color_weight, linewidth=2.5,
             marker='o', markersize=6, label='Вес', alpha=0.9)
    ax1.tick_params(axis='y', labelcolor=color_weight)
    ax1.grid(True, alpha=0.3, linestyle='--')

    # Вторичная ось Y (справа) - для талии, шеи, калорий
    ax2 = ax1.twinx()

    # Цвета для остальных показателей
    color_waist = '#A23B72'
    color_neck = '#F18F01'
    color_calories = '#06A77D'

    ax2.plot(dates, waists, color=color_waist, linewidth=2,
             marker='s', markersize=5, label='Талия (см)', alpha=0.8)
    ax2.plot(dates, necks, color=color_neck, linewidth=2,
             marker='^', markersize=5, label='Шея (см)', alpha=0.8)

    # Калории на отдельной шкале (нормализуем для визуализации)
    # Делим калории на 30 для приближения к масштабу см (пропускаем None)
    calories_scaled = [c / 30 if c is not None else None for c in calories_list]
    ax2.plot(dates, calories_scaled, color=color_calories, linewidth=2,
             marker='D', markersize=4, label='Калории (×30)', alpha=0.8, linestyle='--')

    ax2.set_ylabel('Объемы (см) / Калории (×30)', fontsize=12)
    ax2.tick_params(axis='y')

    # Форматирование оси X (даты)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates) // 10)))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Заголовок
    title = f'Прогресс за {period_days} дней'
    if period_days == 7:
        title = 'Прогресс за неделю'
    elif period_days == 60:
        title = 'Прогресс за 2 месяца'

    fig.suptitle(title, fontsize=16, fontweight='bold')

    # Объединенная легенда
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               loc='upper left', framealpha=0.9, fontsize=10)

    # Плотная компоновка
    fig.tight_layout()

    # Сохранить в BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf, metrics


def format_metrics_message(metrics: dict) -> str:
    """
    Форматирует метрики прогресса в текстовое сообщение.

    Args:
        metrics: Словарь с метриками (поля опциональны)

    Returns:
        Отформатированная строка с метриками
    """
    message_parts = ["📊 Прогресс:\n"]

    # Вес
    if 'weight_diff' in metrics:
        weight_emoji = "📉" if metrics['weight_diff'] < 0 else "📈" if metrics['weight_diff'] > 0 else "➡️"
        message_parts.append(
            f"{weight_emoji} Вес: {metrics['weight_start']:.1f}кг → {metrics['weight_current']:.1f}кг "
            f"({metrics['weight_diff']:+.1f}кг)\n"
        )

    # Талия
    if 'waist_diff' in metrics:
        waist_emoji = "📉" if metrics['waist_diff'] < 0 else "📈" if metrics['waist_diff'] > 0 else "➡️"
        message_parts.append(
            f"{waist_emoji} Талия: {metrics['waist_start']:.1f}см → {metrics['waist_current']:.1f}см "
            f"({metrics['waist_diff']:+.1f}см)\n"
        )

    # Шея
    if 'neck_diff' in metrics:
        neck_emoji = "📉" if metrics['neck_diff'] < 0 else "📈" if metrics['neck_diff'] > 0 else "➡️"
        message_parts.append(
            f"{neck_emoji} Шея: {metrics['neck_start']:.1f}см → {metrics['neck_current']:.1f}см "
            f"({metrics['neck_diff']:+.1f}см)\n"
        )

    return "".join(message_parts)
