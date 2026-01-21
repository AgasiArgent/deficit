"""
CRUD операции для работы с базой данных.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models import Measurement, UserProfile


def create_measurement(
    db: Session,
    user_id: int,
    measurement_date: date,
    weight: Optional[float] = None,
    calories: Optional[int] = None,
    waist: Optional[float] = None,
    neck: Optional[float] = None
) -> Measurement:
    """
    Создать новую запись замера.

    Args:
        db: Сессия БД
        user_id: Telegram user ID
        measurement_date: Дата замера
        weight: Вес в кг (опционально)
        calories: Калории за день (опционально)
        waist: Объем талии в см (опционально)
        neck: Объем шеи в см (опционально)

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


def update_or_create_calories(
    db: Session,
    user_id: int,
    measurement_date: date,
    calories: int
) -> Measurement:
    """
    Обновить калории в существующей записи или создать новую запись только с калориями.

    Args:
        db: Сессия БД
        user_id: Telegram user ID
        measurement_date: Дата для калорий
        calories: Калории за день

    Returns:
        Обновленная или созданная запись Measurement
    """
    # Попытаться найти существующую запись
    measurement = db.query(Measurement).filter(
        Measurement.user_id == user_id,
        Measurement.date == measurement_date
    ).first()

    if measurement:
        # Обновить калории в существующей записи
        measurement.calories = calories
        measurement.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(measurement)
    else:
        # Создать новую запись только с калориями
        measurement = Measurement(
            user_id=user_id,
            date=measurement_date,
            weight=None,
            waist=None,
            neck=None,
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


# User Profile operations

def get_or_create_user_profile(db: Session, user_id: int) -> UserProfile:
    """
    Получить или создать профиль пользователя.

    Args:
        db: Сессия БД
        user_id: Telegram user ID

    Returns:
        UserProfile
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def set_start_date(db: Session, user_id: int, start_date: date) -> UserProfile:
    """
    Установить дату начала трекинга для пользователя.

    Args:
        db: Сессия БД
        user_id: Telegram user ID
        start_date: Дата начала трекинга

    Returns:
        Обновленный UserProfile
    """
    profile = get_or_create_user_profile(db, user_id)
    profile.start_date = start_date
    db.commit()
    db.refresh(profile)
    return profile


def get_user_start_date(db: Session, user_id: int) -> Optional[date]:
    """
    Получить дату начала трекинга пользователя.

    Args:
        db: Сессия БД
        user_id: Telegram user ID

    Returns:
        Дата начала или None если не установлена
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    return profile.start_date if profile else None
