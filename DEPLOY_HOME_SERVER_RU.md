# InfoService на Linux-машине

Это руководство разворачивает InfoService на Linux-машине. На ней будут работать PostgreSQL, Telegram-бот, scheduler и worker в Docker Compose.

Для Telegram-бота не нужен публичный IP-адрес: он использует исходящее long-polling соединение с Telegram. Не открывайте наружу PostgreSQL или Docker API.

## 1. Подготовить машину

Рекомендуется Ubuntu Server 24.04 LTS или Debian 12, постоянное питание и Ethernet. В BIOS включите автоматическое включение после отключения питания, если такая опция есть.

После установки системы обновите её:

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

После перезагрузки отключите автоматический сон:

```bash
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

Создайте отдельного пользователя для администрирования, если во время установки его не создали. Для удалённого доступа настройте SSH-ключи; вход по паролю лучше отключить после проверки ключа.

## 2. Установить Docker и Git

Установите Docker Engine и Compose Plugin по официальной инструкции Docker для вашей системы. На Ubuntu минимальный вариант:

```bash
sudo apt install -y docker.io docker-compose-v2 git
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

Перелогиньтесь в SSH-сессию, затем проверьте:

```bash
docker --version
docker compose version
git --version
```

Если пакет `docker-compose-v2` недоступен в вашем репозитории, установите актуальный Docker Compose Plugin по официальной документации Docker, а не старый пакет `docker-compose`.

## 3. Скачать проект

Выберите постоянную директорию, например `/opt/infoservice`:

```bash
sudo mkdir -p /opt/infoservice
sudo chown "$USER":"$USER" /opt/infoservice
git clone https://github.com/AntonL9vov/InfoService.git /opt/infoservice
cd /opt/infoservice
```

Проверьте, что активна ветка `main`:

```bash
git branch --show-current
git pull --ff-only
```

## 4. Создать Telegram-бота и подготовить секреты

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram.
2. Выполните `/newbot`, придумайте имя и username.
3. Скопируйте полученный токен — это `TELEGRAM_BOT_TOKEN`.
4. Создайте локальный Fernet-ключ шифрования:

   ```bash
   python3 -c "from base64 import urlsafe_b64encode; import os; print(urlsafe_b64encode(os.urandom(32)).decode())"
   ```

   Это будет `APP_ENCRYPTION_KEY`. Не теряйте его: без него нельзя расшифровать уже сохранённые ключи пользователей.

5. Сгенерируйте пароль для PostgreSQL:

   ```bash
   openssl rand -base64 32
   ```

Пользователи вводят свои ключи DeepSeek в личном чате с ботом. Общий `DEEPSEEK_API_KEY` на сервере не нужен.

## 5. Создать `.env`

В каталоге проекта:

```bash
cd /opt/infoservice
cp .env.example .env
chmod 600 .env
nano .env
```

Заполните минимум эти значения:

```dotenv
POSTGRES_PASSWORD=ваш_длинный_случайный_пароль
DATABASE_URL=postgresql+asyncpg://infoservice:ваш_длинный_случайный_пароль@postgres:5432/infoservice
TELEGRAM_BOT_TOKEN=токен_из_BotFather
APP_ENCRYPTION_KEY=ваш_Fernet_ключ
```

Остальные безопасные значения уже есть в шаблоне. Для первого запуска оставьте:

```dotenv
APP_IMAGE_TARGET=runtime
ENABLE_TWITTER=false
ENABLE_OPENBB=false
```

Никогда не отправляйте `.env`, `APP_ENCRYPTION_KEY`, токен BotFather или резервную копию базы в GitHub/Telegram.

## 6. Запустить сервис

```bash
cd /opt/infoservice
docker compose up -d --build
docker compose ps
```

Первый запуск собирает образ, запускает PostgreSQL и миграции, затем стартуют `bot`, `scheduler` и `worker`.

Смотрите логи:

```bash
docker compose logs -f bot
docker compose logs -f worker
docker compose logs -f scheduler
```

Когда всё готово, найдите бота в Telegram, откройте личный чат, нажмите `/start`, выберите часовой пояс и добавьте личный ключ DeepSeek. Создайте тестовый отчёт с одним RSS-источником и запустите его вручную.

## 7. Доступ к серверу без открытия портов: Tailscale

Это рекомендуемый способ удалённо управлять машиной. Установите Tailscale на клиентском устройстве и на сервере по [официальной инструкции](https://tailscale.com/download), войдите в один аккаунт и подключайтесь по внутреннему Tailscale-адресу:

```bash
ssh ваш_пользователь@100.x.y.z
```

Не пробрасывайте наружу порт PostgreSQL `5432` и Docker socket. Telegram-боту достаточно исходящего интернет-доступа.

## 8. Обновить сервис

Перед обновлением сделайте резервную копию базы, затем:

```bash
cd /opt/infoservice
git pull --ff-only
docker compose up -d --build
docker compose ps
```

Compose применит миграции до запуска основных процессов.

## 9. Резервные копии и восстановление

Создать резервную копию:

```bash
cd /opt/infoservice
mkdir -p backups
docker compose exec -T postgres pg_dump -U infoservice infoservice > "backups/infoservice-$(date +%F).sql"
```

Храните копии вне этой машины в зашифрованном месте. В резервной базе находятся зашифрованные пользовательские ключи; для их расшифровки всё равно нужен `APP_ENCRYPTION_KEY`.

Восстановление делайте только при остановленных приложениях и с понятной целью:

```bash
docker compose stop bot scheduler worker
docker compose exec -T postgres psql -U infoservice -d infoservice < backups/имя-файла.sql
docker compose up -d
```

## 10. Частые команды

```bash
# Статус контейнеров
docker compose ps

# Последние 200 строк всех логов
docker compose logs --tail=200

# Перезапустить только worker
docker compose restart worker

# Остановить всё, сохранив базу в Docker volume
docker compose down

# Проверить конфигурацию Compose без запуска
ENV_FILE=.env.example docker compose config --quiet
```

Не используйте `docker compose down -v`, если не хотите удалить PostgreSQL volume и все данные.

## 11. GitHub CI/CD — позже

Сейчас обновление вручную через `git pull` безопаснее и проще. Когда базовый запуск стабилен, можно поставить self-hosted GitHub Actions runner прямо на эту машину. Тогда push в `main` будет автоматически выполнять тесты, миграции и `docker compose up -d --build`, без публичного SSH-порта.

Перед включением автодеплоя обязательно оставьте рабочие резервные копии базы и ограничьте права runner-пользователя.
