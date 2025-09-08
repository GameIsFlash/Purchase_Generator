"""Конфигурация и сообщения об ошибках"""

# Сообщения об ошибках
ERROR_MESSAGES = {
    'DATABASE_NOT_FOUND': 'Файл базы данных не найден: {}',
    'IMAGES_DIR_NOT_FOUND': 'Папка с изображениями не найдена: {}',
    'PRODUCT_NOT_FOUND': 'Товар с артикулом {} не найден в базе данных',
    'INVALID_QUANTITY': 'Неверное количество для артикула {}: {}',
    'IMAGE_PROCESSING_ERROR': 'Ошибка обработки изображения {}: {}',
    'EXCEL_GENERATION_ERROR': 'Ошибка создания Excel файла: {}',
    'EMPTY_ORDER': 'Список заказа пуст',
    'INVALID_ARTICLE': 'Неверный формат артикула: {}'
}

# Настройки изображений
IMAGE_CONFIG = {
    'width': 215,
    'height': 200,
    'supported_extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
    'background_color': (255, 255, 255)
}

# Настройки таблицы
TABLE_CONFIG = {
    'column_widths': {'A': 30, 'B': 25, 'C': 12, 'D': 15, 'E': 20},
    'row_height': 150,
    'header_color': '0066CC',
    'headers': ['Фото', 'Наименование', 'Цена', 'Кол-во', 'Сумма']
}

# Маппинг колонок в Excel файле
EXCEL_COLUMNS = {
    'article': 'Артикул',
    'name': 'Наименование',
    'price': 'Цена закупки',
    'image': 'Фото',
    'supplier': 'Поставщик'
}