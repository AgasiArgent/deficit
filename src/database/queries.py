"""
CRUD операции для работы с базой данных.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models import Measurement


def create_measurement(
    db: Session,
    user_id: int,
    measurement_date: date,
    weight: float,
    waist: float,
    neck: float,
    calories: int
) -> Measurement:
    """
    Создать новую запись замера.

    Args:
        db: Сессия БД
        user_id: Telegram user ID
        measurement_date: Дата замера
        weight: Вес в кг
        waist: Объем талии в см
        neck: Объем шеи в см
        calories: Калории за день

    Returns:
        Созданная запись Measurement

    Raises:
        IntegrityError: Если запись за эту дату уже существует
    """
    measurement = Measurement(
        user_id=user_id,
        date=measurement_date,
        weight=weight,
        waist=waist,
        neck=neck,
        calories=calories
    )
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


def get_measurement_by_date(
    db: Session,
    user_id: int,
    measurement_date: date
) -> Optional[Measurement]:
    """
    Получить запись за конкретную дату.

    Args:
        db: Сессия БД
        user_id: Telegram user ID
        measurement_date: Дата замера

    Returns:
        Measurement или None если нет записи
    """
    return db.query(Measurement).filter(
        Measurement.user_id == user_id,
        Measurement.date == measurement_date
    ).first()


def get_measurements_by_period(
    db: Session,
    user_id: int,
    days: int
) -> List[Measurement]:
    """
    Получить записи за последние N дней.

    Args:
        db: Сессия БД
        user_id: Telegram user ID
        days: Количество дней

    Returns:
        Список Measurement отсортированный по дате (старые → новые)
    """
    start_date = date.today() - timedelta(days=days)
    return db.query(Measurement).filter(
        Measurement.user_id == user_id,
        Measurement.date >= start_date
    ).order_by(Measurement.date.asc()).all()


def get_last_measurements(
    db: Session,
    user_id: int,
    limit: int = 5
) -> List[Measurement]:
    """
    Получить последние N записей.

    Args:
        db: Сессия БД
        user_id: Telegram user ID
        limit: Количество записей

    Returns:
        Список Measurement (последние записи сверху)
    """
    return db.query(Measurement).filter(
        Measurement.user_id == user_id
    ).order_by(desc(Measurement.date)).limit(limit).all()


def get_all_measurements(
    db: Session,
    user_id: int
) -> List[Measurement]:
    """
    Получить все записи пользователя.

    Args:
        db: Сессия БД
        user_id: Telegram user ID

    Returns:
        Список Measurement отсортированный по дате (старые → новые)
    """
    return db.query(Measurement).filter(
        Measurement.user_id == user_id
    ).order_by(Measurement.date.asc()).all()


def delete_measurement(
    db: Session,
    measurement_id: int
) -> bool:
    """
    Удалить запись по ID.

    Args:
        db: Сессия БД
        measurement_id: ID записи

    Returns:
        True если удалено, False если запись не найдена
    """
    measurement = db.query(Measurement).filter(
        Measurement.id == measurement_id
    ).first()

    if measurement:
        db.delete(measurement)
        db.commit()
        return True
    return False


def update_measurement(
    db: Session,
    measurement_id: int,
    weight: Optional[float] = None,
    waist: Optional[float] = None,
    neck: Optional[float] = None,
    calories: Optional[int] = None
) -> Optional[Measurement]:
    """
    Обновить существующую запись.

    Args:
        db: Сессия БД
        measurement_id: ID записи
        weight: Новый вес (опционально)
        waist: Новая талия (опционально)
        neck: Новая шея (опционально)
        calories: Новые калории (опционально)

    Returns:
        Обновленный Measurement или None если не найдена
    """
    measurement = db.query(Measurement).filter(
        Measurement.id == measurement_id
    ).first()

    if not measurement:
        return None

    if weight is not None:
        measurement.weight = weight
    if waist is not None:
        measurement.waist = waist
    if neck is not None:
        measurement.neck = neck
    if calories is not None:
        measurement.calories = calories

    db.commit()
    db.refresh(measurement)
    return measurement
