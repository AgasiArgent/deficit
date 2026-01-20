# Deployment Guide

Этот проект настроен для автоматического развертывания на VPS через GitHub Actions.

## Архитектура

```
GitHub Push → GitHub Actions → Build Docker Image → Deploy to VPS
```

## Настройка GitHub Secrets

Перед первым deploy нужно настроить secrets в GitHub репозитории.

### 1. Создать GitHub репозиторий

```bash
# В директории проекта
git remote add origin https://github.com/YOUR_USERNAME/deficit.git
git push -u origin master
```

### 2. Добавить Secrets

Перейди в репозиторий на GitHub:
`Settings → Secrets and variables → Actions → New repository secret`

Добавь следующие secrets:

| Secret Name | Value | Описание |
|-------------|-------|----------|
| `VPS_HOST` | `217.26.25.207` | IP адрес VPS |
| `VPS_USERNAME` | `root` | Username для SSH |
| `VPS_SSH_KEY` | `[содержимое приватного ключа]` | SSH приватный ключ (см. ниже) |
| `TELEGRAM_BOT_TOKEN` | `8586048540:AAEGaQ_daca976d1n-r0e2RqE9nRX4fiNIE` | Токен бота |
| `OWNER_USER_ID` | `43379140` | Твой Telegram User ID |

**Получить SSH приватный ключ:**

```bash
# На твоем Mac
cat ~/.ssh/id_ed25519_beget_vps
```

Скопируй весь вывод (включая `-----BEGIN OPENSSH PRIVATE KEY-----` и `-----END OPENSSH PRIVATE KEY-----`) и добавь как secret `VPS_SSH_KEY`.

**⚠️ После настройки SSH ключа:**
- Удали старый secret `VPS_PASSWORD` (он больше не нужен)
- SSH ключ безопаснее пароля

### 3. Настроить GitHub Container Registry

GitHub Container Registry (ghcr.io) используется автоматически с `GITHUB_TOKEN`.

Нужно сделать образ публичным (опционально):
1. Перейди в `Packages` на твоем GitHub профиле
2. Найди `deficit-bot`
3. `Package settings → Change visibility → Public` (или оставь Private)

## Локальное тестирование Docker

### Сборка образа

```bash
docker build -t deficit-bot .
```

### Запуск локально

```bash
# С docker-compose (рекомендуется)
docker-compose up -d

# Или напрямую
docker run -d \
  --name deficit-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  deficit-bot
```

### Просмотр логов

```bash
docker-compose logs -f bot
```

### Остановка

```bash
docker-compose down
```

## Автоматический Deploy

После настройки secrets, каждый push в `master` или `main` ветку автоматически:

1. ✅ Собирает Docker образ
2. ✅ Загружает в GitHub Container Registry
3. ✅ Деплоит на VPS
4. ✅ Перезапускает бота

### Проверка deploy

1. Перейди в `Actions` tab на GitHub
2. Найди последний workflow run
3. Проверь что все шаги успешны (зеленые галочки)

### Логи на VPS

```bash
ssh root@217.26.25.207

cd /root/deficit
docker-compose logs -f bot
```

## Ручной Deploy

Если нужно задеплоить вручную без commit:

1. Перейди в `Actions` на GitHub
2. Выбери `Deploy Deficit Bot`
3. Нажми `Run workflow`

## Откат к предыдущей версии

```bash
ssh root@217.26.25.207

cd /root/deficit

# Найти SHA предыдущего коммита
docker images | grep deficit-bot

# Изменить docker-compose.yml на нужный SHA
nano docker-compose.yml
# Замени :latest на :SHA_КОММИТА

# Перезапусти
docker-compose down
docker-compose up -d
```

## Мониторинг

### Статус контейнера

```bash
docker-compose ps
```

### Использование ресурсов

```bash
docker stats deficit-bot
```

### Логи последних 100 строк

```bash
docker-compose logs --tail=100 bot
```

## Troubleshooting

### Бот не запускается

```bash
# Проверить логи
docker-compose logs bot

# Проверить что .env на VPS правильный
cat /root/deficit/.env

# Пересоздать контейнер
docker-compose down
docker-compose up -d --force-recreate
```

### GitHub Actions fail

1. Проверь что все secrets добавлены
2. Проверь что `GITHUB_TOKEN` имеет права на packages
3. Проверь логи workflow в GitHub Actions

### SSH не работает

Проверь доступ:
```bash
ssh root@217.26.25.207
```

Если не работает, обнови `VPS_PASSWORD` в GitHub secrets.

## Структура на VPS

После deploy на VPS будет:

```
/root/deficit/
├── docker-compose.yml    # Автоматически создан
├── .env                  # Автоматически создан
└── data/                 # Volume для базы данных
    └── deficit.db        # SQLite база
```

## База данных

База данных хранится в `./data/` на VPS и персистентна между перезапусками контейнера.

### Миграции

Проект использует Alembic для управления схемой базы данных. Миграции запускаются автоматически при старте контейнера.

**Создание новой миграции (локально):**

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Создать миграцию после изменения моделей
alembic revision --autogenerate -m "Описание изменений"

# Применить миграции локально
python migrate.py

# Закоммитить и пушнуть - миграции применятся автоматически на VPS
git add .
git commit -m "feat: add database migration"
git push
```

**Проверка статуса миграций:**

```bash
# Локально
alembic current
alembic history

# На VPS (через SSH)
ssh root@217.26.25.207 "cd /root/deficit && docker-compose exec bot alembic current"
```

### Бэкап базы

```bash
ssh root@217.26.25.207
cd /root/deficit/data
cp deficit.db deficit.db.backup.$(date +%Y%m%d)
```

### Восстановление

```bash
ssh root@217.26.25.207
cd /root/deficit/data
cp deficit.db.backup.YYYYMMDD deficit.db
docker-compose restart
```

## Обновление

Для обновления бота просто:

```bash
git add .
git commit -m "Update: описание изменений"
git push
```

GitHub Actions автоматически задеплоит на VPS!

## Security Notes

⚠️ **ВАЖНО:**
- Secrets никогда не коммитятся в git
- `.env` файл в `.gitignore`
- GitHub secrets зашифрованы
- SSH credentials безопасно хранятся в GitHub

## Полезные команды

```bash
# Перезапуск бота на VPS
ssh root@217.26.25.207 "cd /root/deficit && docker-compose restart"

# Просмотр логов реального времени
ssh root@217.26.25.207 "cd /root/deficit && docker-compose logs -f bot"

# Обновление вручную
ssh root@217.26.25.207 "cd /root/deficit && docker-compose pull && docker-compose up -d"

# Остановка бота
ssh root@217.26.25.207 "cd /root/deficit && docker-compose down"

# Запуск бота
ssh root@217.26.25.207 "cd /root/deficit && docker-compose up -d"
```
