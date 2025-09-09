"""
Класс DataReader — чтение данных из Excel-базы и обработка изображений товаров.
"""

import pandas as pd
from pathlib import Path
from PIL import Image
from decimal import Decimal
import logging

# Импортируем конфигурацию из data_config.py
from .data_config import REQUIRED_COLUMNS, IMAGE_CONFIG
from config import FILE_ERRORS, DATA_ERRORS, IMAGE_ERRORS

# Настраиваем логгер
logger = logging.getLogger(__name__)


class DataReader:
    """
    Класс для чтения и обработки данных о товарах из Excel-файла и изображений.
    """

    def __init__(self, database_path: str, images_dir: str):
        """
        Инициализация DataReader.

        :param database_path: Путь к Excel-файлу с базой данных.
        :param images_dir: Путь к папке с изображениями товаров.
        :raises FileNotFoundError: Если файл базы или папка с изображениями не существуют.
        """
        self.database_path = Path(database_path)
        self.images_dir = Path(images_dir)
        self.data = None
        self.columns = None

        # Проверяем существование файлов и папок
        if not self.database_path.exists():
            raise FileNotFoundError(FILE_ERRORS['DATABASE_NOT_FOUND'].format(database_path))
        if not self.images_dir.exists():
            raise FileNotFoundError(FILE_ERRORS['IMAGES_DIR_NOT_FOUND'].format(images_dir))

    def load_database(self) -> bool:
        """
        Загружает данные из Excel-файла.

        :return: True, если загрузка успешна, иначе False.
        """
        try:
            self.data = pd.read_excel(self.database_path, engine='openpyxl')
            self.columns = self._map_columns()
            logger.info(f"Загружено товаров: {len(self.data)} строк")
            return True
        except Exception as e:
            logger.error(f"Ошибка при загрузке базы данных: {e}")
            return False

    def _map_columns(self) -> dict:
        """
        Маппит названия колонок из Excel в внутренние имена.

        :return: Словарь {внутреннее_имя: название_в_excel}
        :raises ValueError: Если обязательная колонка не найдена.
        """
        columns_map = {}
        for key, name in REQUIRED_COLUMNS.items():
            if name in self.data.columns:
                columns_map[key] = name
            else:
                raise ValueError(DATA_ERRORS['MISSING_REQUIRED_COLUMN'].format(name))
        return columns_map

    def get_product_info(self, article: str) -> list[dict] | None:
        """
        Получает информацию о ВСЕХ записях товара по артикулу (может быть несколько поставщиков).
        :param article: Артикул товара.
        :return: Список словарей с данными товара от разных поставщиков или None, если не найден.
        """
        if self.data is None:
            self.load_database()
        article_col = self.columns['article']
        product_rows = self.data[self.data[article_col] == article]
        if product_rows.empty:
            return None

        suppliers = []
        for _, row in product_rows.iterrows():
            supplier_info = {
                'article': str(row[self.columns['article']]),
                'name': str(row[self.columns['name']]),
                'price': Decimal(str(row[self.columns['price']])),
                'supplier': str(row[self.columns['supplier']])
            }
            suppliers.append(supplier_info)
        return suppliers

    def get_all_products(self) -> list[dict]:
        """
        Получает информацию о всех УНИКАЛЬНЫХ товарах из базы данных.
        Для товаров с несколькими поставщиками, выбирается запись с минимальной ценой.
        :return: Список словарей с данными товаров (уникальные артикулы).
        """
        if self.data is None:
            self.load_database()
        if self.data is None or self.data.empty:
            return []

        products = {}
        for _, row in self.data.iterrows():
            try:
                article = str(row[self.columns['article']])
                if pd.isna(row[self.columns['article']]) or article.strip() == '' or article == 'nan':
                    continue

                product_info = {
                    'article': article,
                    'name': str(row[self.columns['name']]) if not pd.isna(row[self.columns['name']]) else '',
                    'price': Decimal(str(row[self.columns['price']])) if not pd.isna(
                        row[self.columns['price']]) else Decimal('0'),
                    'supplier': str(row[self.columns['supplier']]) if not pd.isna(
                        row[self.columns['supplier']]) else 'Неизвестный поставщик'
                }

                # Если артикул уже есть, оставляем поставщика с минимальной ценой
                if article in products:
                    if product_info['price'] < products[article]['price']:
                        products[article] = product_info
                else:
                    products[article] = product_info

            except Exception as e:
                logger.warning(f"Ошибка обработки строки в БД: {e}")
                continue

        result = list(products.values())
        logger.info(f"Получено {len(result)} уникальных товаров из базы данных")
        return result

    def process_image(self, article: str) -> Image.Image | None:
        """
        Обрабатывает изображение товара: ищет, ресайзит, конвертирует в RGB.

        :param article: Артикул товара.
        :return: Обработанное изображение (PIL.Image) или None, если не найдено/ошибка.
        """
        base_name = Path(article).stem
        for ext in IMAGE_CONFIG['supported_extensions']:
            test_path = self.images_dir / f"{base_name}{ext}"
            if test_path.exists():
                try:
                    with Image.open(test_path) as img:
                        # Конвертируем в RGB, если нужно
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        # Ресайзим
                        img_resized = img.resize(
                            (IMAGE_CONFIG['width'], IMAGE_CONFIG['height']),
                            Image.Resampling.LANCZOS
                        )
                        return img_resized.copy()
                except Exception as e:
                    logger.error(IMAGE_ERRORS['IMAGE_PROCESSING_ERROR'].format(test_path, e))
                    return None

        logger.warning(f"Файл изображения не найден для артикула: {article}")
        return None