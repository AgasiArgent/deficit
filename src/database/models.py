"""
SQLAlchemy модели для базы данных deficit бота.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, Float, Date, DateTime, UniqueConstraint, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Measurement(Base):
    """
    Модель для хранения ежедневных замеров пользователя.

    Поля:
    - id: Первичный ключ
    - user_id: Telegram user ID
    - date: Дата замера
    - weight: Вес в кг
    - waist: Объем талии в см
    - neck: Объем шеи в см
    - calories: Калории за день
    - created_at: Timestamp создания записи
    """
    __tablename__ = 'measurements'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    weight = Column(Float, nullable=False)
    waist = Column(Float, nullable=False)
    neck = Column(Float, nullable=False)
    calories = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Ограничение: одна запись на день для пользователя
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uix_user_date'),
    )

    def __repr__(self):
        return f"<Measurement(id={self.id}, user_id={self.user_id}, date={self.date}, weight={self.weight}kg)>"


# Database connection and session setup
DATABASE_URL = "sqlite:///./deficit.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Инициализация базы данных - создание всех таблиц.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")


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
