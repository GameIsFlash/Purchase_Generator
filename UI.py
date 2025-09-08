"""
UI модуль для генератора таблиц закупки.
Содержит весь пользовательский интерфейс на customtkinter.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from backend import PurchaseTableBackend


class PurchaseTableGUI:
    """Главный класс пользовательского интерфейса"""

    def __init__(self, root):
        self.root = root
        self.root.title("Генератор таблиц закупки")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Устанавливаем тему customtkinter
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Инициализация backend
        self.backend = PurchaseTableBackend()
        self.setup_backend_callbacks()

        # Настройка стиля Treeview
        self.setup_treeview_style()

        # Переменные для UI
        self.search_var = tk.StringVar()
        self.db_var = tk.StringVar(value=self.backend.database_file)
        self.img_var = tk.StringVar(value=self.backend.images_dir)
        self.out_var = tk.StringVar(value=self.backend.output_dir)

        # Создание интерфейса
        self.create_main_interface()

        # Загрузка данных при старте
        self.backend.load_initial_data()

    def setup_backend_callbacks(self):
        """Настройка колбэков для взаимодействия с backend"""
        self.backend.set_callbacks(
            status_callback=self.update_status,
            message_callback=self.show_message,
            error_callback=self.show_error,
            success_callback=self.show_success
        )

    def update_status(self, message):
        """Обновление статус-бара"""
        self.status_bar.configure(text=message)

    def show_message(self, title, message):
        """Показ информационного сообщения"""
        messagebox.showinfo(title, message)

    def show_error(self, title, message):
        """Показ сообщения об ошибке"""
        messagebox.showerror(title, message)

    def show_success(self, title, message):
        """Показ сообщения об успехе"""
        messagebox.showinfo(title, message)

    def setup_treeview_style(self):
        """Настройка стиля Treeview под customtkinter"""
        style = ttk.Style()

        def update_treeview_style():
            if ctk.get_appearance_mode() == "Dark":
                style.theme_use("clam")
                style.configure("Custom.Treeview",
                                background="#2A2A2A",
                                foreground="white",
                                fieldbackground="#2A2A2A",
                                rowheight=28,
                                font=("Arial", 11))
                style.configure("Custom.Treeview.Heading",
                                background="#3A3A3A",
                                foreground="white",
                                font=("Arial", 11, "bold"))
                style.map("Custom.Treeview.Heading",
                          background=[('active', '#4A4A4A')])
            else:
                style.theme_use("clam")
                style.configure("Custom.Treeview",
                                background="white",
                                foreground="black",
                                fieldbackground="white",
                                rowheight=28,
                                font=("Arial", 11))
                style.configure("Custom.Treeview.Heading",
                                background="#E0E0E0",
                                foreground="black",
                                font=("Arial", 11, "bold"))
                style.map("Custom.Treeview.Heading",
                          background=[('active', '#D0D0D0')])

        update_treeview_style()

    def create_main_interface(self):
        """Создание основного интерфейса на customtkinter"""

        # === Заголовок ===
        title_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            title_frame,
            text="Генератор таблиц закупки",
            font=("Arial", 20, "bold"),
            text_color=("black", "white")
        )
        title_label.pack()

        # === Основные кнопки ===
        buttons_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))

        # Кнопка "Лист наличия"
        availability_btn = self.create_button(
            buttons_frame, "Лист наличия", self.generate_availability_list,
            fg_color="#4CAF50", hover_color="#45a049"
        )

        # Кнопка "Лист закупки"
        purchase_btn = self.create_button(
            buttons_frame, "Лист закупки", self.show_purchase_interface,
            fg_color="#2196F3", hover_color="#1976D2"
        )

        # Кнопка "Генерировать лист закупки"
        generate_btn = self.create_button(
            buttons_frame, "Генерировать лист закупки", self.generate_purchase_list,
            fg_color="#FF9800", hover_color="#F57C00"
        )

        # === Настройки путей ===
        self.create_settings_frame()

        # === Фрейм для интерфейса закупки (изначально скрыт) ===
        self.purchase_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.create_purchase_interface()

        # === Статус-бар ===
        self.status_bar = ctk.CTkLabel(
            self.root,
            text="Готов к работе",
            font=("Arial", 11),
            text_color=("gray30", "gray70"),
            fg_color=("gray90", "gray20"),
            corner_radius=0,
            height=25,
            anchor="w",
            padx=10
        )
        self.status_bar.pack(side=tk.BOTTOM, fill="x")

    def create_button(self, parent, text, command,
                      width=180, height=45,
                      fg_color="#3B8ED0", hover_color="#367CBA",
                      text_color="white", corner_radius=10,
                      side=tk.LEFT, padx=(0, 15), pady=0,
                      font=("Arial", 12, "bold")):
        """Создаёт и упаковывает кнопку CTkButton"""
        btn = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            corner_radius=corner_radius,
            font=font
        )
        btn.pack(side=side, padx=padx, pady=pady)
        return btn

    def create_settings_frame(self):
        """Создание фрейма настроек на customtkinter"""

        # Основной фрейм настроек
        settings_container = ctk.CTkFrame(self.root, corner_radius=10)
        settings_container.pack(fill="x", padx=20, pady=(10, 20))

        # Заголовок "Настройки путей"
        header_label = ctk.CTkLabel(
            settings_container,
            text="Настройки путей",
            font=("Arial", 14, "bold"),
            text_color=("black", "white")
        )
        header_label.pack(anchor="w", padx=15, pady=(10, 5))

        # Внутренний контейнер для полей
        settings_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        settings_frame.pack(fill="x", padx=15, pady=(0, 15))

        # === База данных ===
        self.create_path_setting(settings_frame, "База данных:", self.db_var, self.browse_database)

        # === Папка изображений ===
        self.create_path_setting(settings_frame, "Изображения:", self.img_var, self.browse_images)

        # === Выходная папка ===
        self.create_path_setting(settings_frame, "Выходная папка:", self.out_var, self.browse_output)

    def create_path_setting(self, parent, label_text, var, browse_command):
        """Создание поля настройки пути"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)

        ctk.CTkLabel(frame, text=label_text, font=("Arial", 12), width=100).pack(side=tk.LEFT)

        entry = ctk.CTkEntry(
            frame,
            textvariable=var,
            placeholder_text=f"Путь к {label_text.lower()}",
            font=("Arial", 12),
            height=32
        )
        entry.pack(side=tk.LEFT, padx=8, fill="x", expand=True)

        ctk.CTkButton(
            frame,
            text="⋯",
            command=browse_command,
            width=32,
            height=32,
            fg_color="gray30",
            hover_color="gray40",
            corner_radius=6,
            font=("Arial", 14)
        ).pack(side=tk.RIGHT)

    def create_purchase_interface(self):
        """Создание интерфейса для режима закупки"""

        # === Заголовок ===
        header_frame = ctk.CTkFrame(self.purchase_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header_frame,
            text="Составление листа закупки",
            font=("Arial", 18, "bold"),
            text_color=("black", "white")
        ).pack()

        # === Панель поиска ===
        search_frame = ctk.CTkFrame(self.purchase_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(search_frame, text="Поиск по артикулу:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(0, 10))

        self.search_var.trace('w', self.on_search_change)
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Введите артикул...",
            font=("Arial", 12),
            height=32,
            width=250
        )
        search_entry.pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            search_frame,
            text="Добавить выбранный",
            command=self.add_selected_item,
            fg_color="#4CAF50",
            hover_color="#45a049",
            text_color="white",
            corner_radius=8,
            font=("Arial", 12, "bold"),
            height=32
        ).pack(side=tk.RIGHT, padx=5)

        # === Найденные товары ===
        self.create_found_items_section()

        # === Основной список товаров ===
        self.create_tree_section()

        # === Кнопки управления ===
        self.create_control_buttons()

    def create_found_items_section(self):
        """Создание секции найденных товаров"""
        found_container = ctk.CTkFrame(self.purchase_frame, corner_radius=10)
        found_container.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            found_container,
            text="Найденные товары",
            font=("Arial", 14, "bold"),
            text_color=("black", "white"),
            anchor="w"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        found_inner_frame = ctk.CTkFrame(found_container, fg_color="transparent")
        found_inner_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Определяем цвета в зависимости от темы
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            bg_color = "#333333"
            fg_color = "#FFFFFF"
            highlight_bg = "#555555"
        else:
            bg_color = "#F5F5F5"
            fg_color = "#000000"
            highlight_bg = "#D0D0D0"

        self.found_listbox = tk.Listbox(
            found_inner_frame,
            height=4,
            font=("Arial", 11),
            bg=bg_color,
            fg=fg_color,
            selectbackground="#2196F3",
            selectforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=highlight_bg,
            highlightcolor="#2196F3"
        )
        found_scrollbar = ttk.Scrollbar(found_inner_frame, orient=tk.VERTICAL, command=self.found_listbox.yview)
        self.found_listbox.config(yscrollcommand=found_scrollbar.set)

        self.found_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        found_scrollbar.pack(side=tk.RIGHT, fill="y")

    def create_tree_section(self):
        """Создание секции дерева товаров"""
        tree_container = ctk.CTkFrame(self.purchase_frame, corner_radius=10)
        tree_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        ctk.CTkLabel(
            tree_container,
            text="Список для закупки",
            font=("Arial", 14, "bold"),
            text_color=("black", "white"),
            anchor="w"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        tree_inner_frame = ctk.CTkFrame(tree_container, fg_color="transparent")
        tree_inner_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Treeview
        columns = ("Артикул", "Наименование", "Цена", "Количество")
        self.tree = ttk.Treeview(
            tree_inner_frame,
            columns=columns,
            show="tree headings",
            height=15,
            style="Custom.Treeview"
        )

        # Настройка колонок
        self.tree.column("#0", width=50, minwidth=50, anchor="center")
        self.tree.column("Артикул", width=200, minwidth=150)
        self.tree.column("Наименование", width=250, minwidth=200)
        self.tree.column("Цена", width=80, minwidth=80, anchor="e")
        self.tree.column("Количество", width=100, minwidth=80, anchor="center")

        # Заголовки
        self.tree.heading("#0", text="✓")
        self.tree.heading("Артикул", text="Артикул")
        self.tree.heading("Наименование", text="Наименование")
        self.tree.heading("Цена", text="Цена")
        self.tree.heading("Количество", text="Количество")

        # Scrollbar
        tree_scrollbar = ttk.Scrollbar(tree_inner_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.config(yscrollcommand=tree_scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill="y")

        # Биндинг событий
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Button-1>", self.on_tree_click)

    def create_control_buttons(self):
        """Создание кнопок управления"""
        control_frame = ctk.CTkFrame(self.purchase_frame, fg_color="transparent")
        control_frame.pack(fill="x", padx=20, pady=(15, 20))

        ctk.CTkButton(
            control_frame,
            text="Генерировать лист закупки",
            command=self.generate_purchase_list,
            fg_color="#FF9800",
            hover_color="#F57C00",
            text_color="white",
            corner_radius=8,
            font=("Arial", 12, "bold"),
            height=35
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            control_frame,
            text="Загрузить из JSON",
            command=self.load_from_json,
            fg_color="#9E9E9E",
            hover_color="#757575",
            text_color="white",
            corner_radius=8,
            font=("Arial", 12),
            height=35
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            control_frame,
            text="Сохранить в JSON",
            command=self.save_to_json,
            fg_color="#607D8B",
            hover_color="#455A64",
            text_color="white",
            corner_radius=8,
            font=("Arial", 12),
            height=35
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            control_frame,
            text="Назад",
            command=self.hide_purchase_interface,
            fg_color="#F44336",
            hover_color="#D32F2F",
            text_color="white",
            corner_radius=8,
            font=("Arial", 12, "bold"),
            height=35
        ).pack(side=tk.RIGHT, padx=5)

    # === ОБРАБОТЧИКИ СОБЫТИЙ ===

    def browse_database(self):
        """Выбор файла базы данных"""
        filename = filedialog.askopenfilename(
            title="Выберите файл базы данных",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.db_var.set(filename)
            self.backend.database_file = filename

    def browse_images(self):
        """Выбор папки изображений"""
        dirname = filedialog.askdirectory(title="Выберите папку с изображениями")
        if dirname:
            self.img_var.set(dirname)
            self.backend.images_dir = dirname

    def browse_output(self):
        """Выбор выходной папки"""
        dirname = filedialog.askdirectory(title="Выберите выходную папку")
        if dirname:
            self.out_var.set(dirname)
            self.backend.output_dir = dirname

    def generate_availability_list(self):
        """Генерация листа наличия"""
        # Обновляем пути в backend
        self.backend.update_paths(
            self.db_var.get(),
            self.img_var.get(),
            self.out_var.get()
        )
        self.backend.generate_availability_list_async()

    def show_purchase_interface(self):
        """Показать интерфейс закупки"""
        self.backend.load_default_order()
        self.update_tree()
        self.purchase_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.update_status("Режим составления листа закупки")

    def hide_purchase_interface(self):
        """Скрыть интерфейс закупки"""
        self.purchase_frame.pack_forget()
        self.update_status("Готов к работе")

    def on_search_change(self, *args):
        """Обработка изменения поиска"""
        search_text = self.search_var.get()
        found_products = self.backend.search_products(search_text)

        # Обновление списка найденных
        self.found_listbox.delete(0, tk.END)
        self.filtered_items = {}

        for i, product in enumerate(found_products):
            article = product.get('article', '???')
            name = product.get('name', 'Без названия')[:40]
            display_text = f"{article} - {name}..."
            self.found_listbox.insert(tk.END, display_text)
            self.filtered_items[i] = product

    def add_selected_item(self):
        """Добавить выбранный товар"""
        selection = self.found_listbox.curselection()
        if not selection:
            self.show_error("Предупреждение", "Выберите товар для добавления")
            return

        index = selection[0]
        if index not in self.filtered_items:
            self.show_error("Ошибка", "Товар не найден в кэше")
            return

        product = self.filtered_items[index]
        if self.backend.add_product_to_order(product):
            self.update_tree()

    def on_tree_click(self, event):
        """Обработка клика по дереву"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "tree":
            item = self.tree.identify_row(event.y)
            if item:
                values = self.tree.item(item)['values']
                if values:
                    article = values[0]
                    if self.backend.toggle_item_enabled(article):
                        self.update_tree()

    def on_tree_double_click(self, event):
        """Обработка двойного клика - изменение количества"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return

        values = self.tree.item(item)['values']
        if not values:
            return

        article = values[0]
        try:
            current_qty = int(values[3])
        except (ValueError, IndexError):
            current_qty = 1

        # Используем CTkInputDialog
        dialog = ctk.CTkInputDialog(
            title="Изменить количество",
            text=f"Введите новое количество для {article}:"
        )
        dialog._entry.delete(0, "end")
        dialog._entry.insert(0, str(current_qty))
        new_qty_str = dialog.get_input()

        if new_qty_str is None:
            return  # пользователь нажал Cancel

        try:
            new_qty = int(new_qty_str)
            if self.backend.update_item_quantity(article, new_qty):
                self.update_tree()
        except ValueError:
            self.show_error("Ошибка", "Введите корректное число")

    def update_tree(self):
        """Обновление дерева товаров"""
        # Очищаем дерево
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Получаем данные от backend
        display_items = self.backend.get_order_items_for_display()

        # Добавляем товары
        for item_data in display_items:
            checkbox = "☑" if item_data['enabled'] else "☐"
            values = (
                item_data['article'],
                item_data['name'],
                f"{item_data['price']:.2f}",
                item_data['quantity']
            )
            self.tree.insert("", tk.END, text=checkbox, values=values)

    def generate_purchase_list(self):
        """Генерация листа закупки"""
        # Обновляем пути в backend
        self.backend.update_paths(
            self.db_var.get(),
            self.img_var.get(),
            self.out_var.get()
        )
        self.backend.generate_purchase_list_async()

    def load_from_json(self):
        """Загрузка заказа из JSON файла"""
        filename = filedialog.askopenfilename(
            title="Загрузить заказ из JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            if self.backend.load_order_from_json(filename):
                self.update_tree()

    def save_to_json(self):
        """Сохранение заказа в JSON файл"""
        filename = filedialog.asksaveasfilename(
            title="Сохранить заказ в JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.backend.save_order_to_json(filename)

    def update_listbox_colors(self):
        """Обновление цветов listbox при смене темы"""
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            bg_color = "#333333"
            fg_color = "#FFFFFF"
            highlight_bg = "#555555"
        else:
            bg_color = "#F5F5F5"
            fg_color = "#000000"
            highlight_bg = "#D0D0D0"

        self.found_listbox.configure(
            bg=bg_color,
            fg=fg_color,
            highlightbackground=highlight_bg
        )


def main():
    """Запуск GUI приложения на customtkinter"""
    # Создаём главное окно CTk
    root = ctk.CTk()
    root.title("Генератор таблиц закупки")

    # Устанавливаем тему и цветовую схему
    ctk.set_appearance_mode("light")      # "light", "dark", "system"
    ctk.set_default_color_theme("blue")   # "blue", "green", "dark-blue"

    # Создаём приложение
    app = PurchaseTableGUI(root)

    # Запускаем главный цикл
    root.mainloop()


if __name__ == "__main__":
    main()