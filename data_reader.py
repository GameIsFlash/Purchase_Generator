import pandas as pd
from pathlib import Path
from PIL import Image
from decimal import Decimal
import logging
from config import ERROR_MESSAGES, IMAGE_CONFIG

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    'article': 'Артикул',
    'name': 'Артикул продавца',
    'price': 'Цена закупки',
    'supplier': 'Поставщик'
}


class DataReader:
    def __init__(self, database_path: str, images_dir: str):
        self.database_path = Path(database_path)
        self.images_dir = Path(images_dir)
        self.data = None
        self.columns = None

        if not self.database_path.exists():
            raise FileNotFoundError(ERROR_MESSAGES['DATABASE_NOT_FOUND'].format(database_path))
        if not self.images_dir.exists():
            raise FileNotFoundError(ERROR_MESSAGES['IMAGES_DIR_NOT_FOUND'].format(images_dir))

    def load_database(self):
        try:
            self.data = pd.read_excel(self.database_path, engine='openpyxl')
            self.columns = self._map_columns()
            logger.info(f"Загружено товаров: {len(self.data)} строк")
            return True
        except Exception as e:
            logger.error(f"Ошибка при загрузке базы данных: {e}")
            return False

    def _map_columns(self):
        columns_map = {}
        for key, name in REQUIRED_COLUMNS.items():
            if name in self.data.columns:
                columns_map[key] = name
            else:
                raise ValueError(f"Не найдена обязательная колонка: {name}")
        return columns_map

    def get_product_info(self, article: str):
        if self.data is None:
            self.load_database()

        article_col = self.columns['article']
        product_row = self.data[self.data[article_col] == article]

        if product_row.empty:
            return None

        row = product_row.iloc[0]
        return {
            'article': str(row[self.columns['article']]),
            'name': str(row[self.columns['name']]),
            'price': Decimal(str(row[self.columns['price']])),
            'supplier': str(row[self.columns['supplier']])
        }

    def get_all_products(self):
        """Получить информацию о всех товарах из базы данных"""
        if self.data is None:
            self.load_database()

        if self.data is None or self.data.empty:
            return []

        products = []
        for _, row in self.data.iterrows():
            try:
                # Пропускаем строки с пустыми артикулами
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
                products.append(product_info)

            except Exception as e:
                logger.warning(f"Ошибка обработки строки в БД: {e}")
                continue

        logger.info(f"Получено {len(products)} товаров из базы данных")
        return products

    def process_image(self, article: str):
        base_name = Path(article).stem
        for ext in IMAGE_CONFIG['supported_extensions']:
            test_path = self.images_dir / f"{base_name}{ext}"
            if test_path.exists():
                try:
                    with Image.open(test_path) as img:
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        img_resized = img.resize(
                            (IMAGE_CONFIG['width'], IMAGE_CONFIG['height']),
                            Image.Resampling.LANCZOS
                        )
                        return img_resized.copy()
                except Exception as e:
                    logger.error(ERROR_MESSAGES['IMAGE_PROCESSING_ERROR'].format(test_path, e))
                    return None
        logger.warning(f"Файл изображения не найден для артикула: {article}")
        return None