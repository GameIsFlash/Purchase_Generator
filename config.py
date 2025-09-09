# config.py
"""
Глобальные конфигурации и сообщения об ошибках для всего проекта.
Используется в backend, data, utils.
"""

# === Сообщения об ошибках (группировка по категориям) ===
FILE_ERRORS = {
    'DATABASE_NOT_FOUND': 'Файл базы данных не найден: {}',
    'IMAGES_DIR_NOT_FOUND': 'Папка с изображениями не найдена: {}',
    'OUTPUT_DIR_NOT_FOUND': 'Выходная папка не существует: {}',
    'FILE_ACCESS_ERROR': 'Ошибка доступа к файлу: {}',
}

DATA_ERRORS = {
    'PRODUCT_NOT_FOUND': 'Товар с артикулом {} не найден в базе данных',
    'INVALID_QUANTITY': 'Неверное количество для артикула {}: {}',
    'EMPTY_ORDER': 'Список заказа пуст',
    'INVALID_ARTICLE': 'Неверный формат артикула: {}',
    'MISSING_REQUIRED_COLUMN': 'Не найдена обязательная колонка: {}',
}

IMAGE_ERRORS = {
    'IMAGE_PROCESSING_ERROR': 'Ошибка обработки изображения {}: {}',
    'IMAGE_NOT_FOUND': 'Изображение для артикула {} не найдено',
}

EXCEL_ERRORS = {
    'EXCEL_GENERATION_ERROR': 'Ошибка создания Excel файла: {}',
    'EXCEL_SAVE_ERROR': 'Ошибка сохранения Excel файла: {}',
}