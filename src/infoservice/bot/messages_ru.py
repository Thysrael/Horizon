GROUP_PRIVATE_REDIRECT = "Пожалуйста, откройте бота в личный чат."
TIMEZONE_REQUEST = "Выберите ваш часовой пояс или отправьте корректное имя часового пояса IANA."
TIMEZONE_SAVED = "Часовой пояс сохранён."
TIMEZONE_INVALID = "Не удалось распознать часовой пояс. Например: Europe/Moscow."
WELCOME = "Добро пожаловать в InfoService."
MAIN_MENU = "Главное меню"
COMMAND_HELP = """Команды InfoService:
/menu — главное меню
/reports — мои отчёты
/newreport — создать отчёт
/sources — источники выбранного отчёта
/settings — часовой пояс и DeepSeek
/help — помощь и примеры
/cancel — отменить текущее действие

Примеры источников:
Telegram: @durov
GitHub: owner/repo
RSS: https://example.com/feed.xml
Hacker News добавляется без адреса."""
SETTINGS_MENU = "Настройки\nЧасовой пояс: {timezone}"
NOTHING_TO_CANCEL = "Сейчас нет незавершённого действия."
ACTION_CANCELLED_MENU = "Действие отменено.\nГлавное меню"
LLM_MENU = "Управление ключом DeepSeek."
KEY_REQUEST = "Отправьте ключ DeepSeek одним сообщением. После проверки это сообщение будет удалено."
REPLACE_CONFIRMATION = "Ключ DeepSeek уже добавлен. Заменить его?"
KEY_SAVED = "Ключ DeepSeek сохранён: {mask}"
KEY_DELETED = "Ключ DeepSeek удалён. Рассылки остановлены до добавления нового ключа."
KEY_MISSING = "Ключ DeepSeek ещё не добавлен."
KEY_INVALID = "Ключ DeepSeek отклонён провайдером."
KEY_UNAVAILABLE = "Не удалось проверить ключ. Повторите попытку позже."
ACTION_CANCELLED = "Действие отменено."
REPORTS_MENU = "Ваши отчёты"
REPORT_NAME_REQUEST = "Введите название отчёта."
REPORT_CONFIRMATION = "Создать отчёт «{name}»?"
REPORT_CREATED = "Отчёт создан."
REPORT_NOT_FOUND = "Отчёт не найден"
REPORT_DELETED = "Отчёт удалён."
REPORT_DELETE_CONFIRMATION = "Удалить отчёт и всю его историю?"
REPORT_PAUSED = "Отчёт приостановлен."
REPORT_RESUMED = "Отчёт возобновлён."
RULES_INVALID = "Проверьте параметры правил."
SCHEDULE_INVALID = "Некорректное расписание."
MANUAL_RUN_UNAVAILABLE = "Для запуска добавьте ключ DeepSeek."
MANUAL_RUN_COOLDOWN = "Отчёт уже запускался недавно."
HISTORY_EMPTY = "История запусков пуста."
SOURCES_MENU = "Источники отчёта"
SOURCE_CONFIG_REQUEST = "Отправьте JSON-конфигурацию источника. Поля: {fields}."
SOURCE_CREATED = "Источник добавлен."
SOURCE_NOT_FOUND = "Источник не найден"
SOURCE_INVALID = "Некорректная конфигурация источника."
SOURCE_DELETE_CONFIRMATION = "Удалить источник?"
SOURCE_DELETED = "Источник удалён."
SOURCE_UPDATED = "Источник обновлён."
SOURCE_UNAVAILABLE = "Этот источник сейчас недоступен на сервере."
SOURCE_OPTIONAL_PREREQUISITE = "Источник использует включённую серверную интеграцию; её доступность может меняться у администратора."
