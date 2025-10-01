# backend/backend_config.py
"""
Конфигурация, специфичная для backend-логики.
Содержит настройки по умолчанию, параметры заказа, лимиты.
"""

# === Пути по умолчанию ===
DEFAULT_PATHS = {
    'images_dir': "data/images",
    'database_file': "data/table/database.xlsx",
    'output_dir': "output"
}

# === Параметры заказа и поиска ===
ORDER_CONFIG = {
    # Заказ по умолчанию (для демо/тестирования)
    'default_order': {
    },
    # Ограничения
    'max_quantity': 9999,        # Максимально допустимое количество товара
    'min_search_length': 2,      # Минимальная длина строки поиска
    'max_search_results': 20     # Максимальное количество результатов поиска
}