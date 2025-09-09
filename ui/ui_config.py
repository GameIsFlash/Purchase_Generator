# === Цвета кнопок ===
BUTTON_COLORS = {
    'availability': ('#4CAF50', '#45a049'),    # зелёный
    'purchase': ('#2196F3', '#1976D2'),       # синий
    'generate': ('#FF9800', '#F57C00'),       # оранжевый
    'back': ('#F44336', '#D32F2F'),           # красный
    'json_load': ('#9E9E9E', '#757575'),      # серый
    'json_save': ('#607D8B', '#455A64'),      # сине-серый
    'browse': ('gray30', 'gray40'),           # серый для "..."
}

# === Размеры и шрифты ===
UI_SIZES = {
    'main_button': {'width': 180, 'height': 45},
    'small_button': {'width': 32, 'height': 32},
    'control_button': {'height': 35},
    'entry_height': 32,
    'font_main': ("Arial", 12, "bold"),
    'font_header': ("Arial", 20, "bold"),
    'font_small': ("Arial", 11),
}

# === Тексты интерфейса ===
UI_TEXTS = {
    'title': "Генератор таблиц закупки",
    'purchase_title': "Составление листа закупки",
    'settings_header': "Настройки путей",
    'search_label': "Поиск по артикулу:",
    'found_label': "Найденные товары",
    'tree_label': "Список для закупки",
    'add_button': "Добавить выбранный",
    'browse_button': "⋯",
    'path_placeholders': {
        'database': "Путь к файлу базы данных",
        'images': "Путь к папке с изображениями",
        'output': "Путь к выходной папке"
    }
}