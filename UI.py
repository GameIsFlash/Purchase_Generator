import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import platform
from pathlib import Path
import os
import json
from main import generate_general_table, generate_purchase_tables
from data_reader import DataReader


class PurchaseTableGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор таблиц закупки")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Настройки по умолчанию
        self.images_dir = "data/images"
        self.database_file = "data/table/database.xlsx"
        self.output_dir = "output"

        # Данные для режима закупки
        self.order_items = {}
        self.filtered_items = {}
        self.all_products = []

        # Создание интерфейса
        self.create_main_interface()

        # Загрузка данных при старте
        self.load_initial_data()


    def create_main_interface(self):
        """Создание основного интерфейса"""
        # Заголовок
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)

        title_label = ttk.Label(title_frame, text="Генератор таблиц закупки",
                                font=("Arial", 16, "bold"))
        title_label.pack()

        # Основные кнопки
        buttons_frame = ttk.Frame(self.root, padding="10")
        buttons_frame.pack(fill=tk.X)

        # Кнопка "Лист наличия"
        availability_btn = ttk.Button(buttons_frame, text="Лист наличия",
                                      command=self.generate_availability_list,
                                      style="Accent.TButton")
        availability_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=5)

        # Кнопка "Лист закупки"
        purchase_btn = ttk.Button(buttons_frame, text="Лист закупки",
                                  command=self.show_purchase_interface,
                                  style="Accent.TButton")
        purchase_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=5)

        # Кнопка "Генерировать лист закупки"
        generate_btn = ttk.Button(buttons_frame, text="Генерировать лист закупки",
                                  command=self.generate_purchase_list,
                                  style="Accent.TButton")
        generate_btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=5)

        # Настройки путей
        self.create_settings_frame()

        # Фрейм для интерфейса закупки (изначально скрыт)
        self.purchase_frame = ttk.Frame(self.root)
        self.create_purchase_interface()

        # Статус бар
        self.status_bar = ttk.Label(self.root, text="Готов к работе",
                                    relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_settings_frame(self):
        """Создание фрейма настроек"""
        settings_frame = ttk.LabelFrame(self.root, text="Настройки путей", padding="10")
        settings_frame.pack(fill=tk.X, padx=10, pady=5)

        # База данных
        db_frame = ttk.Frame(settings_frame)
        db_frame.pack(fill=tk.X, pady=2)
        ttk.Label(db_frame, text="База данных:").pack(side=tk.LEFT)
        self.db_var = tk.StringVar(value=self.database_file)
        db_entry = ttk.Entry(db_frame, textvariable=self.db_var, width=50)
        db_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(db_frame, text="...", command=self.browse_database,
                   width=3).pack(side=tk.RIGHT)

        # Папка изображений
        img_frame = ttk.Frame(settings_frame)
        img_frame.pack(fill=tk.X, pady=2)
        ttk.Label(img_frame, text="Изображения:").pack(side=tk.LEFT)
        self.img_var = tk.StringVar(value=self.images_dir)
        img_entry = ttk.Entry(img_frame, textvariable=self.img_var, width=50)
        img_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(img_frame, text="...", command=self.browse_images,
                   width=3).pack(side=tk.RIGHT)

        # Выходная папка
        out_frame = ttk.Frame(settings_frame)
        out_frame.pack(fill=tk.X, pady=2)
        ttk.Label(out_frame, text="Выходная папка:").pack(side=tk.LEFT)
        self.out_var = tk.StringVar(value=self.output_dir)
        out_entry = ttk.Entry(out_frame, textvariable=self.out_var, width=50)
        out_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(out_frame, text="...", command=self.browse_output,
                   width=3).pack(side=tk.RIGHT)

    def create_purchase_interface(self):
        """Создание интерфейса для режима закупки"""
        # Заголовок
        header_frame = ttk.Frame(self.purchase_frame, padding="10")
        header_frame.pack(fill=tk.X)

        ttk.Label(header_frame, text="Составление листа закупки",
                  font=("Arial", 14, "bold")).pack()

        # Панель поиска
        search_frame = ttk.Frame(self.purchase_frame, padding="5")
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="Поиск по артикулу:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(search_frame, text="Добавить выбранный",
                   command=self.add_selected_item).pack(side=tk.RIGHT, padx=5)

        # Список найденных товаров
        found_frame = ttk.LabelFrame(self.purchase_frame, text="Найденные товары", padding="5")
        found_frame.pack(fill=tk.X, padx=10, pady=5)

        # Listbox для найденных товаров
        self.found_listbox = tk.Listbox(found_frame, height=4)
        found_scrollbar = ttk.Scrollbar(found_frame, orient=tk.VERTICAL, command=self.found_listbox.yview)
        self.found_listbox.config(yscrollcommand=found_scrollbar.set)
        self.found_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        found_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Основной список товаров
        main_frame = ttk.LabelFrame(self.purchase_frame, text="Список для закупки", padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Treeview для основного списка
        columns = ("Артикул", "Наименование", "Цена", "Количество")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="tree headings", height=15)

        # Настройка колонок
        self.tree.column("#0", width=50, minwidth=50)  # Чекбокс
        self.tree.column("Артикул", width=200, minwidth=150)
        self.tree.column("Наименование", width=250, minwidth=200)
        self.tree.column("Цена", width=80, minwidth=80)
        self.tree.column("Количество", width=100, minwidth=80)

        # Заголовки
        self.tree.heading("#0", text="✓")
        self.tree.heading("Артикул", text="Артикул")
        self.tree.heading("Наименование", text="Наименование")
        self.tree.heading("Цена", text="Цена")
        self.tree.heading("Количество", text="Количество")

        # Scrollbar для дерева
        tree_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.config(yscrollcommand=tree_scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Биндинг событий
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Button-1>", self.on_tree_click)

        # Кнопки управления
        control_frame = ttk.Frame(self.purchase_frame, padding="10")
        control_frame.pack(fill=tk.X)

        ttk.Button(control_frame, text="Генерировать лист закупки",
                   command=self.generate_purchase_list,
                   style="Accent.TButton").pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Назад",
                   command=self.hide_purchase_interface).pack(side=tk.RIGHT, padx=5)

        ttk.Button(control_frame, text="Загрузить из JSON",
                   command=self.load_from_json).pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Сохранить в JSON",
                   command=self.save_to_json).pack(side=tk.LEFT, padx=5)

    def load_initial_data(self):
        """Загрузка начальных данных"""
        try:
            data_reader = DataReader(self.database_file, self.images_dir)
            if data_reader.load_database():
                self.all_products = data_reader.get_all_products()
                self.status_bar.config(text=f"Загружено {len(self.all_products)} товаров из базы данных")
            else:
                self.status_bar.config(text="Ошибка загрузки базы данных")
        except Exception as e:
            self.status_bar.config(text=f"Ошибка: {str(e)}")

    def browse_database(self):
        """Выбор файла базы данных"""
        filename = filedialog.askopenfilename(
            title="Выберите файл базы данных",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.db_var.set(filename)
            self.database_file = filename

    def browse_images(self):
        """Выбор папки изображений"""
        dirname = filedialog.askdirectory(title="Выберите папку с изображениями")
        if dirname:
            self.img_var.set(dirname)
            self.images_dir = dirname

    def browse_output(self):
        """Выбор выходной папки"""
        dirname = filedialog.askdirectory(title="Выберите выходную папку")
        if dirname:
            self.out_var.set(dirname)
            self.output_dir = dirname

    def generate_availability_list(self):
        """Генерация листа наличия"""

        def generate_thread():
            try:
                self.status_bar.config(text="Генерация листа наличия...")
                self.root.update()

                # Обновляем пути из интерфейса
                self.database_file = self.db_var.get()
                self.images_dir = self.img_var.get()
                self.output_dir = self.out_var.get()

                files, errors = generate_general_table(
                    images_dir=self.images_dir,
                    database_file=self.database_file,
                    output_dir=self.output_dir
                )

                if files:
                    self.status_bar.config(text=f"Создано файлов: {len(files)}")
                    # Открываем папку с файлами
                    self.open_folder(self.output_dir)

                    message = f"Успешно создано {len(files)} файлов:\n"
                    for file_path in files:
                        message += f"• {Path(file_path).name}\n"

                    if errors:
                        message += f"\nОшибок: {len(errors)}"

                    messagebox.showinfo("Готово", message)
                else:
                    error_text = "\n".join(errors) if errors else "Неизвестная ошибка"
                    messagebox.showerror("Ошибка", f"Не удалось создать файлы:\n{error_text}")
                    self.status_bar.config(text="Ошибка генерации")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Произошла ошибка:\n{str(e)}")
                self.status_bar.config(text="Ошибка генерации")

        # Запуск в отдельном потоке
        thread = threading.Thread(target=generate_thread)
        thread.daemon = True
        thread.start()

    def show_purchase_interface(self):
        """Показать интерфейс закупки"""
        # Загружаем начальные данные заказа
        self.load_default_order()
        self.purchase_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.status_bar.config(text="Режим составления листа закупки")

    def hide_purchase_interface(self):
        """Скрыть интерфейс закупки"""
        self.purchase_frame.pack_forget()
        self.status_bar.config(text="Готов к работе")

    def load_default_order(self):
        """Загрузка заказа по умолчанию"""
        default_order = {
            "vl-cronier-ployka-cr-2018": 1,
        }

        self.order_items = {}
        for article, quantity in default_order.items():
            product = self.find_product_by_article(article)
            if product:
                self.order_items[article] = {
                    'product': product,
                    'quantity': quantity,
                    'enabled': True
                }

        self.update_tree()

    def find_product_by_article(self, article):
        """Найти товар по артикулу"""
        for product in self.all_products:
            if product['article'] == article:
                return product
        return None

    def update_tree(self):
        """Обновление дерева товаров"""
        # Очищаем дерево
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Добавляем товары
        for article, item_data in self.order_items.items():
            product = item_data['product']
            quantity = item_data['quantity']
            enabled = item_data['enabled']

            checkbox = "☑" if enabled else "☐"
            values = (article, product['name'], f"{float(product['price']):.2f}", quantity)

            self.tree.insert("", tk.END, text=checkbox, values=values)

    def on_search_change(self, *args):
        """Обработка изменения поиска"""
        search_text = self.search_var.get().lower()
        if len(search_text) < 2:
            self.found_listbox.delete(0, tk.END)
            return

        # Поиск товаров
        found_products = []
        for product in self.all_products:
            if search_text in product['article'].lower() or search_text in product['name'].lower():
                found_products.append(product)

        # Обновление списка найденных
        self.found_listbox.delete(0, tk.END)
        self.filtered_items = {}

        for i, product in enumerate(found_products[:20]):  # Показываем максимум 20 результатов
            display_text = f"{product['article']} - {product['name'][:40]}..."
            self.found_listbox.insert(tk.END, display_text)
            self.filtered_items[i] = product

    def add_selected_item(self):
        """Добавить выбранный товар"""
        selection = self.found_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите товар для добавления")
            return

        index = selection[0]
        if index in self.filtered_items:
            product = self.filtered_items[index]
            article = product['article']

            if article in self.order_items:
                messagebox.showinfo("Информация", "Товар уже есть в списке")
            else:
                self.order_items[article] = {
                    'product': product,
                    'quantity': 1,
                    'enabled': True
                }
                self.update_tree()
                messagebox.showinfo("Успех", "Товар добавлен в список")

    def on_tree_click(self, event):
        """Обработка клика по дереву"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "tree":
            item = self.tree.identify_row(event.y)
            if item:
                self.toggle_item_enabled(item)

    def on_tree_double_click(self, event):
        """Обработка двойного клика - изменение количества"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return

        values = self.tree.item(item)['values']
        if not values:
            return

        article = values[0]
        current_qty = values[3]

        # Диалог изменения количества
        new_qty = tk.simpledialog.askinteger(
            "Изменить количество",
            f"Введите новое количество для {article}:",
            initialvalue=current_qty,
            minvalue=0,
            maxvalue=9999
        )

        if new_qty is not None:
            self.order_items[article]['quantity'] = new_qty
            self.update_tree()

    def toggle_item_enabled(self, item):
        """Переключение состояния товара"""
        values = self.tree.item(item)['values']
        if not values:
            return

        article = values[0]
        if article in self.order_items:
            self.order_items[article]['enabled'] = not self.order_items[article]['enabled']
            self.update_tree()

    def generate_purchase_list(self):
        """Генерация листа закупки"""

        def generate_thread():
            try:
                self.status_bar.config(text="Генерация листа закупки...")
                self.root.update()

                # Формируем заказ из включенных товаров
                order_dict = {}
                for article, item_data in self.order_items.items():
                    if item_data['enabled'] and item_data['quantity'] > 0:
                        order_dict[article] = item_data['quantity']

                if not order_dict:
                    messagebox.showwarning("Предупреждение", "Нет товаров для закупки")
                    self.status_bar.config(text="Нет товаров для закупки")
                    return

                # Обновляем пути из интерфейса
                self.database_file = self.db_var.get()
                self.images_dir = self.img_var.get()
                self.output_dir = self.out_var.get()

                files, errors = generate_purchase_tables(
                    images_dir=self.images_dir,
                    database_file=self.database_file,
                    order_dict=order_dict,
                    output_dir=self.output_dir
                )

                if files:
                    self.status_bar.config(text=f"Создано файлов: {len(files)}")
                    # Открываем папку с файлами
                    self.open_folder(self.output_dir)

                    message = f"Успешно создано {len(files)} файлов:\n"
                    for file_path in files:
                        message += f"• {Path(file_path).name}\n"

                    if errors:
                        message += f"\nОшибок: {len(errors)}"

                    messagebox.showinfo("Готово", message)
                else:
                    error_text = "\n".join(errors) if errors else "Неизвестная ошибка"
                    messagebox.showerror("Ошибка", f"Не удалось создать файлы:\n{error_text}")
                    self.status_bar.config(text="Ошибка генерации")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Произошла ошибка:\n{str(e)}")
                self.status_bar.config(text="Ошибка генерации")

        # Запуск в отдельном потоке
        thread = threading.Thread(target=generate_thread)
        thread.daemon = True
        thread.start()

    def load_from_json(self):
        """Загрузка заказа из JSON файла"""
        filename = filedialog.askopenfilename(
            title="Загрузить заказ из JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    order_data = json.load(f)

                self.order_items = {}
                for article, quantity in order_data.items():
                    product = self.find_product_by_article(article)
                    if product:
                        self.order_items[article] = {
                            'product': product,
                            'quantity': quantity,
                            'enabled': True
                        }

                self.update_tree()
                messagebox.showinfo("Успех", f"Загружено {len(self.order_items)} товаров")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")

    def save_to_json(self):
        """Сохранение заказа в JSON файл"""
        filename = filedialog.asksaveasfilename(
            title="Сохранить заказ в JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                order_data = {}
                for article, item_data in self.order_items.items():
                    if item_data['enabled'] and item_data['quantity'] > 0:
                        order_data[article] = item_data['quantity']

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(order_data, f, ensure_ascii=False, indent=2)

                messagebox.showinfo("Успех", f"Сохранено {len(order_data)} товаров")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def open_folder(self, folder_path):
        """Открытие папки в проводнике"""
        try:
            folder_path = Path(folder_path).resolve()
            if folder_path.exists():
                if platform.system() == "Windows":
                    os.startfile(folder_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(folder_path)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(folder_path)])
        except Exception as e:
            print(f"Не удалось открыть папку: {e}")


def main():
    """Запуск GUI приложения"""
    root = tk.Tk()

    # Настройка стиля
    style = ttk.Style()
    style.theme_use('clam')

    app = PurchaseTableGUI(root)

    # Импорт для диалогов
    import tkinter.simpledialog
    tk.simpledialog = tkinter.simpledialog

    root.mainloop()


if __name__ == "__main__":
    main()