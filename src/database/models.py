"""
SQLAlchemy модели для базы данных deficit бота.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, Float, Date, DateTime, UniqueConstraint, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class UserProfile(Base):
    """
    Модель для хранения профиля и настроек пользователя.

    Поля:
    - user_id: Telegram user ID (первичный ключ)
    - start_date: Дата начала трекинга дефицита калорий
    - created_at: Timestamp создания профиля
    - updated_at: Timestamp последнего обновления
    """
    __tablename__ = 'user_profiles'

    user_id = Column(BigInteger, primary_key=True)
    start_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, start_date={self.start_date})>"


class Measurement(Base):
    """
    Модель для хранения ежедневных замеров пользователя.

    Поля:
    - id: Первичный ключ
    - user_id: Telegram user ID
    - date: Дата замера
    - weight: Вес в кг
    - waist: Объем талии в см (опционально, измеряется раз в неделю)
    - neck: Объем шеи в см (опционально, измеряется раз в неделю)
    - calories: Калории за день
    - created_at: Timestamp создания записи
    """
    __tablename__ = 'measurements'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    weight = Column(Float, nullable=True)  # Опционально (для записей только с калориями)
    waist = Column(Float, nullable=True)   # Опционально (измеряется раз в неделю)
    neck = Column(Float, nullable=True)    # Опционально (измеряется раз в неделю)
    calories = Column(Integer, nullable=True)  # Опционально (за предыдущий день)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Ограничение: одна запись на день для пользователя
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uix_user_date'),
    )

    def __repr__(self):
        return f"<Measurement(id={self.id}, user_id={self.user_id}, date={self.date}, weight={self.weight}kg)>"


# Database connection and session setup
import os
DB_PATH = os.getenv('DB_PATH', './data/deficit.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Инициализация базы данных - проверка подключения.

    Note: Таблицы создаются через Alembic migrations (см. migrate.py).
    Эта функция только проверяет что база доступна.
    """
    # Создать директорию для базы данных если не существует
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    # Проверить подключение к базе
    try:
        engine.connect()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise


def get_db():
    """
    Получить сессию базы данных.

    Usage:
        db = get_db()
        try:
            # работа с БД
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
