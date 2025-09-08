"""
Backend модуль для генератора таблиц закупки.
Содержит всю бизнес-логику приложения.
"""

import threading
import subprocess
import platform
from pathlib import Path
import os
import json
from main import generate_general_table, generate_purchase_tables
from data_reader import DataReader


class PurchaseTableBackend:
    """Класс для управления бизнес-логикой генератора таблиц закупки"""

    def __init__(self):
        # Настройки по умолчанию
        self.images_dir = "data/images"
        self.database_file = "data/table/database.xlsx"
        self.output_dir = "output"

        # Данные для режима закупки
        self.order_items = {}
        self.filtered_items = {}
        self.all_products = []

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

    def load_initial_data(self):
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

                files, errors = generate_general_table(
                    images_dir=self.images_dir,
                    database_file=self.database_file,
                    output_dir=self.output_dir
                )

                if files:
                    self.update_status(f"Создано файлов: {len(files)}")
                    self.open_folder(self.output_dir)

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

    def load_default_order(self):
        """Загрузка заказа по умолчанию"""
        default_order = {
            "vl-cronier-ployka-cr-2018": 1,
        }

        self.order_items = {}
        loaded_count = 0

        for article, quantity in default_order.items():
            product = self.find_product_by_article(article)
            if product:
                self.order_items[article] = {
                    'product': product,
                    'quantity': quantity,
                    'enabled': True
                }
                loaded_count += 1

        self.update_status(f"Загружен заказ по умолчанию ({loaded_count} товаров)")
        return loaded_count

    def find_product_by_article(self, article):
        """Найти товар по артикулу"""
        for product in self.all_products:
            if product['article'] == article:
                return product
        return None

    def search_products(self, search_text):
        """Поиск товаров по артикулу или названию"""
        search_text = search_text.lower().strip()
        if len(search_text) < 2:
            return []

        found_products = []
        for product in self.all_products:
            article = product.get('article', '').lower()
            name = product.get('name', '').lower()
            if search_text in article or search_text in name:
                found_products.append(product)

        return found_products[:20]  # Максимум 20 результатов

    def add_product_to_order(self, product):
        """Добавить товар в заказ"""
        article = product.get('article')

        if not article:
            self.show_error("Ошибка", "У товара отсутствует артикул")
            return False

        if article in self.order_items:
            self.show_message("Информация", "Товар уже есть в списке")
            return False
        else:
            self.order_items[article] = {
                'product': product,
                'quantity': 1,
                'enabled': True
            }
            self.show_success("Успех", f"Товар '{article}' добавлен в список")
            return True

    def update_item_quantity(self, article, new_quantity):
        """Обновить количество товара"""
        if new_quantity < 0:
            self.show_error("Ошибка", "Количество не может быть меньше 0")
            return False
        if new_quantity > 9999:
            self.show_error("Ошибка", "Максимальное количество — 9999")
            return False

        if article in self.order_items:
            old_quantity = self.order_items[article]['quantity']
            self.order_items[article]['quantity'] = new_quantity
            print(f"DEBUG: Количество товара '{article}' изменено с {old_quantity} на {new_quantity}")
            return True
        else:
            print(f"DEBUG: Товар '{article}' не найден в order_items")
            return False

    def toggle_item_enabled(self, article):
        """Переключить состояние товара (включен/выключен)"""
        if article in self.order_items:
            self.order_items[article]['enabled'] = not self.order_items[article]['enabled']
            return True
        return False

    def get_order_items_for_display(self):
        """Получить список товаров для отображения"""
        display_items = []
        for article, item_data in self.order_items.items():
            product = item_data['product']
            quantity = item_data['quantity']
            enabled = item_data['enabled']

            try:
                price = float(product.get('price', 0))
            except (ValueError, TypeError):
                price = 0.0

            display_items.append({
                'article': article,
                'name': product.get('name', 'Неизвестно'),
                'price': price,
                'quantity': quantity,
                'enabled': enabled
            })

        return display_items

    def generate_purchase_list_async(self):
        """Асинхронная генерация листа закупки"""

        def generate_thread():
            try:
                self.update_status("Генерация листа закупки...")

                # Формируем заказ из включенных товаров
                order_dict = {}
                for article, item_data in self.order_items.items():
                    if item_data['enabled'] and item_data['quantity'] > 0:
                        order_dict[article] = item_data['quantity']

                if not order_dict:
                    self.show_error("Предупреждение", "Нет товаров для закупки")
                    self.update_status("Нет товаров для закупки")
                    return

                files, errors = generate_purchase_tables(
                    images_dir=self.images_dir,
                    database_file=self.database_file,
                    order_dict=order_dict,
                    output_dir=self.output_dir
                )

                if files:
                    self.update_status(f"Создано файлов: {len(files)}")
                    self.open_folder(self.output_dir)

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

    def load_order_from_json(self, filename):
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

    def save_order_to_json(self, filename):
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

    def open_folder(self, folder_path):
        """Открыть папку в проводнике"""
        try:
            folder_path = Path(folder_path).resolve()
            if not folder_path.exists():
                self.show_error("Ошибка", f"Папка не существует:\n{folder_path}")
                return

            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(folder_path)], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", str(folder_path)], check=True)

        except Exception as e:
            self.show_error("Ошибка", f"Не удалось открыть папку:\n{str(e)}")
            print(f"Не удалось открыть папку: {e}")