import threading
import json
from pathlib import Path
from config import FILE_ERRORS, DATA_ERRORS, IMAGE_ERRORS, EXCEL_ERRORS
from backend.backend_config import DEFAULT_PATHS, ORDER_CONFIG
from data_engine.data_reader import DataReader
from utils.file_utils import open_folder


class PurchaseTableBackend:
    """Класс для управления бизнес-логикой генератора таблиц закупки"""

    def __init__(self):
        # Загружаем пути по умолчанию из конфига
        self.images_dir = DEFAULT_PATHS['images_dir']
        self.database_file = DEFAULT_PATHS['database_file']
        self.output_dir = DEFAULT_PATHS['output_dir']

        # Данные для режима закупки
        self.order_items = {}  # {артикул: {product, quantity, enabled}}
        # ❗ self.filtered_items удалён — не используется в новой архитектуре
        self.all_products = []  # список всех товаров из базы

        # Колбэки для уведомления UI
        self.status_callback = None
        self.message_callback = None
        self.error_callback = None
        self.success_callback = None

    def set_callbacks(self, status_callback=None, message_callback=None,
                      error_callback=None, success_callback=None):
        """Установка колбэков для взаимодействия с UI"""
        self.status_callback = status_callback
        self.message_callback = message_callback
        self.error_callback = error_callback
        self.success_callback = success_callback

    def update_status(self, message):
        """Обновление статуса через колбэк"""
        if self.status_callback:
            self.status_callback(message)

    def show_message(self, title, message):
        """Показ информационного сообщения через колбэк"""
        if self.message_callback:
            self.message_callback(title, message)

    def show_error(self, title, message):
        """Показ сообщения об ошибке через колбэк"""
        if self.error_callback:
            self.error_callback(title, message)

    def show_success(self, title, message):
        """Показ сообщения об успехе через колбэк"""
        if self.success_callback:
            self.success_callback(title, message)

    def update_paths(self, database_file, images_dir, output_dir):
        """Обновление путей к файлам и папкам"""
        self.database_file = database_file
        self.images_dir = images_dir
        self.output_dir = output_dir

    def load_initial_data(self) -> bool:
        """Загрузка начальных данных из базы"""
        try:
            data_reader = DataReader(self.database_file, self.images_dir)
            if data_reader.load_database():
                self.all_products = data_reader.get_all_products()
                self.update_status(f"Загружено {len(self.all_products)} товаров из базы данных")
                return True
            else:
                self.update_status("Ошибка загрузки базы данных")
                return False
        except Exception as e:
            self.update_status(f"Ошибка: {str(e)}")
            return False

    def generate_availability_list_async(self):
        """Асинхронная генерация листа наличия"""

        def generate_thread():
            try:
                self.update_status("Генерация листа наличия...")

                from main import generate_general_table  # импорт внутри функции для избежания циклических зависимостей

                files, errors = generate_general_table(
                    images_dir=self.images_dir,
                    database_file=self.database_file,
                    output_dir=self.output_dir
                )

                if files:
                    self.update_status(f"Создано файлов: {len(files)}")
                    open_folder(self.output_dir)

                    message = f"Успешно создано {len(files)} файлов:\n"
                    for file_path in files:
                        message += f"• {Path(file_path).name}\n"

                    if errors:
                        message += f"\nОшибок: {len(errors)}"

                    self.show_success("Готово", message)
                else:
                    error_text = "\n".join(errors) if errors else "Неизвестная ошибка"
                    self.show_error("Ошибка", f"Не удалось создать файлы:\n{error_text}")
                    self.update_status("Ошибка генерации")

            except Exception as e:
                self.show_error("Ошибка", EXCEL_ERRORS['EXCEL_GENERATION_ERROR'].format(str(e)))
                self.update_status("Ошибка генерации")

        # Запуск в отдельном потоке
        thread = threading.Thread(target=generate_thread)
        thread.daemon = True
        thread.start()

    def load_default_order(self) -> int:
        """Загрузка заказа по умолчанию из конфига с поддержкой поставщиков."""
        default_order = ORDER_CONFIG['default_order']
        self.order_items = {}
        loaded_count = 0

        for article, quantity in default_order.items():
            # Используем метод add_product_to_order, который уже поддерживает поставщиков
            product = self.find_product_by_article(article)
            if product:
                # Временно устанавливаем количество, чтобы не вызывать show_success
                # Сохраняем текущие колбэки
                original_success_callback = self.success_callback
                # Временно отключаем success_callback, чтобы не показывать сообщение для каждого товара
                self.success_callback = None

                if self.add_product_to_order(product):
                    # Восстанавливаем оригинальное количество, так как add_product_to_order ставит 1
                    self.order_items[article]['quantity'] = quantity
                    loaded_count += 1

                # Восстанавливаем колбэк
                self.success_callback = original_success_callback

        self.update_status(f"Загружен заказ по умолчанию ({loaded_count} товаров)")
        return loaded_count

    def find_product_by_article(self, article: str) -> dict | None:
        """Найти товар по артикулу"""
        for product in self.all_products:
            if product['article'] == article:
                return product
        return None

    def search_products(self, search_text: str) -> list[dict]:
        """Поиск товаров по артикулу или названию"""
        search_text = search_text.lower().strip()
        if len(search_text) < ORDER_CONFIG['min_search_length']:
            return []

        found_products = []
        for product in self.all_products:
            article = product.get('article', '').lower()
            name = product.get('name', '').lower()
            if search_text in article or search_text in name:
                found_products.append(product)

        return found_products[:ORDER_CONFIG['max_search_results']]

    def add_product_to_order(self, product: dict) -> bool:
        """Добавить товар в заказ. Автоматически находит всех поставщиков."""
        article = product.get('article')
        if not article:
            self.show_error("Ошибка", "У товара отсутствует артикул")
            return False

        if article in self.order_items:
            self.show_message("Информация", "Товар уже есть в списке")
            return False

        # Получаем всех поставщиков для этого артикула
        all_suppliers = self.find_all_suppliers_for_article(article)
        if not all_suppliers:
            self.show_error("Ошибка", f"Не удалось найти поставщиков для артикула {article}")
            return False

        # Выбираем поставщика с минимальной ценой по умолчанию
        default_supplier = min(all_suppliers, key=lambda x: x['price'])

        self.order_items[article] = {
            'product': product,  # Основная информация (наименование и т.д.)
            'all_suppliers': all_suppliers,  # Список всех поставщиков
            'selected_supplier': default_supplier['supplier'],  # Выбранный поставщик
            'quantity': 1,
            'enabled': True
        }
        self.show_success("Успех", f"Товар '{article}' добавлен в список")
        return True

    def update_item_quantity(self, article: str, new_quantity: int) -> bool:
        """Обновить количество товара"""
        if new_quantity < 0:
            self.show_error("Ошибка", "Количество не может быть меньше 0")
            return False
        if new_quantity > ORDER_CONFIG['max_quantity']:
            self.show_error("Ошибка", f"Максимальное количество — {ORDER_CONFIG['max_quantity']}")
            return False

        if article not in self.order_items:
            self.show_error("Ошибка", f"Товар '{article}' не найден в заказе")
            return False

        self.order_items[article]['quantity'] = new_quantity
        return True

    def toggle_item_enabled(self, article: str) -> bool:
        """Переключить состояние товара (включен/выключен)"""
        if article in self.order_items:
            self.order_items[article]['enabled'] = not self.order_items[article]['enabled']
            return True
        return False

    def find_all_suppliers_for_article(self, article: str) -> list[dict]:
        """Найти всех поставщиков для заданного артикула."""
        data_reader = DataReader(self.database_file, self.images_dir)
        if not data_reader.load_database():
            return []
        suppliers = data_reader.get_product_info(article)
        return suppliers if suppliers else []

    def update_item_supplier(self, article: str, new_supplier: str) -> bool:
        """Обновить выбранного поставщика для товара и обновить цену."""
        if article not in self.order_items:
            return False

        # Проверяем, что новый поставщик есть в списке доступных
        available_suppliers = [s['supplier'] for s in self.order_items[article]['all_suppliers']]
        if new_supplier not in available_suppliers:
            return False

        # Находим полную информацию о товаре у выбранного поставщика
        selected_product_info = next(
            (s for s in self.order_items[article]['all_suppliers'] if s['supplier'] == new_supplier),
            None
        )

        if not selected_product_info:
            return False

        # Обновляем выбранного поставщика
        self.order_items[article]['selected_supplier'] = new_supplier

        # Обновляем ЦЕНУ в основном объекте товара, чтобы UI отображал актуальные данные
        self.order_items[article]['product']['price'] = selected_product_info['price']

        return True

    def get_order_items_for_display(self) -> list[dict]:
        """Получить список товаров для отображения в UI, включая информацию о поставщике."""
        display_items = []
        for article, item_data in self.order_items.items():
            product = item_data['product']
            quantity = item_data['quantity']
            enabled = item_data['enabled']
            selected_supplier = item_data['selected_supplier']

            try:
                price = float(product.get('price', 0))
            except (ValueError, TypeError):
                price = 0.0

            display_items.append({
                'article': article,
                'name': product.get('name', 'Неизвестно'),
                'price': price,
                'quantity': quantity,
                'enabled': enabled,
                'selected_supplier': selected_supplier,  # Новое поле
                'all_suppliers': [s['supplier'] for s in item_data['all_suppliers']]  # Список имен для UI
            })

        return display_items

    def generate_purchase_list_async(self):
        """Асинхронная генерация листа закупки с использованием ExcelGenerator."""

        def generate_thread():
            try:
                self.update_status("Генерация листа закупки...")

                # Формируем заказ, сгруппированный по ПОСТАВЩИКАМ
                suppliers_order = {}  # {поставщик: {артикул: количество, ...}}
                for article, item_data in self.order_items.items():
                    if not (item_data['enabled'] and item_data['quantity'] > 0):
                        continue

                    selected_supplier = item_data['selected_supplier']
                    if selected_supplier not in suppliers_order:
                        suppliers_order[selected_supplier] = {}

                    suppliers_order[selected_supplier][article] = item_data['quantity']

                if not suppliers_order:
                    self.show_error("Предупреждение", "Нет товаров для закупки")
                    self.update_status("Нет товаров для закупки")
                    return

                # Инициализируем генератор Excel
                from data_engine.excel_generator import ExcelGenerator
                excel_generator = ExcelGenerator(output_dir=self.output_dir)

                files = []
                errors = []

                # Генерируем отдельный файл для КАЖДОГО поставщика
                for supplier_name, supplier_items in suppliers_order.items():
                    try:
                        # Формируем данные для генератора
                        supplier_data = {
                            'supplier': supplier_name,
                            'items': []
                        }

                        data_reader = DataReader(self.database_file, self.images_dir)
                        if not data_reader.load_database():
                            raise Exception("Не удалось загрузить базу данных")

                        for article, quantity in supplier_items.items():
                            # Находим полную информацию о товаре у этого поставщика
                            all_suppliers = self.find_all_suppliers_for_article(article)
                            selected_product = next((p for p in all_suppliers if p['supplier'] == supplier_name), None)
                            if selected_product:
                                # Обрабатываем изображение
                                processed_image = data_reader.process_image(article)
                                supplier_data['items'].append({
                                    'article': article,
                                    'name': selected_product['name'],
                                    'price': float(selected_product['price']),
                                    'quantity': quantity,
                                    'processed_image': processed_image
                                })
                            else:
                                errors.append(f"Товар {article} не найден у поставщика {supplier_name}")

                        if supplier_data['items']:
                            # Генерируем файл
                            file_path = excel_generator.generate_table(supplier_data)
                            files.append(file_path)

                    except Exception as e:
                        errors.append(f"Ошибка генерации для {supplier_name}: {str(e)}")

                if files:
                    self.update_status(f"Создано файлов: {len(files)}")
                    open_folder(self.output_dir)
                    message = f"Успешно создано {len(files)} файлов:\n"
                    for file_path in files:
                        message += f"• {Path(file_path).name}\n"
                    if errors:
                        message += f"\nОшибок: {len(errors)}"
                    self.show_success("Готово", message)
                else:
                    error_text = "\n".join(errors) if errors else "Неизвестная ошибка"
                    self.show_error("Ошибка", f"Не удалось создать файлы:\n{error_text}")
                    self.update_status("Ошибка генерации")

            except Exception as e:
                self.show_error("Ошибка", f"Произошла ошибка:\n{str(e)}")
                self.update_status("Ошибка генерации")

        # Запуск в отдельном потоке
        thread = threading.Thread(target=generate_thread)
        thread.daemon = True
        thread.start()

    def load_order_from_json(self, filename: str) -> bool:
        """Загрузить заказ из JSON файла"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                order_data = json.load(f)

            if not isinstance(order_data, dict):
                raise ValueError("Файл должен содержать объект (словарь) с артикулами и количеством")

            self.order_items = {}
            loaded_count = 0
            skipped_count = 0

            for article, quantity in order_data.items():
                # Проверяем, что количество — целое число
                try:
                    quantity = int(quantity)
                except (ValueError, TypeError):
                    skipped_count += 1
                    continue

                product = self.find_product_by_article(article)
                if product:
                    self.order_items[article] = {
                        'product': product,
                        'quantity': quantity,
                        'enabled': True
                    }
                    loaded_count += 1
                else:
                    skipped_count += 1

            message = f"Загружено товаров: {loaded_count}"
            if skipped_count:
                message += f"\nПропущено (не найдено/ошибка): {skipped_count}"

            self.show_success("Загрузка завершена", message)
            return True

        except Exception as e:
            self.show_error("Ошибка загрузки", f"Не удалось загрузить файл:\n{str(e)}")
            return False

    def save_order_to_json(self, filename: str) -> bool:
        """Сохранить заказ в JSON файл"""
        try:
            order_data = {}
            saved_count = 0

            for article, item_data in self.order_items.items():
                if item_data['enabled'] and item_data['quantity'] > 0:
                    order_data[article] = item_data['quantity']
                    saved_count += 1

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(order_data, f, ensure_ascii=False, indent=2)

            self.show_success("Сохранение завершено", f"Успешно сохранено {saved_count} товаров в:\n{filename}")
            return True

        except Exception as e:
            self.show_error("Ошибка сохранения", f"Не удалось сохранить файл:\n{str(e)}")
            return False