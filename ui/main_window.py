"""
UI модуль для генератора таблиц закупки.
Содержит весь пользовательский интерфейс на customtkinter.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import customtkinter as ctk
from backend.backend import PurchaseTableBackend
from utils.image_utils import create_rounded_image, pil_to_photoimage
from . import ui_config
import json
from .ui_config import CONFIG_FILE


class SearchDialog:
    """Диалоговое окно для поиска товаров"""

    def __init__(self, parent, backend, update_tree_callback, update_status_callback):
        self.result = None
        self.backend = backend
        self.update_tree_callback = update_tree_callback
        self.update_status_callback = update_status_callback
        self.filtered_items = {}
        self.added_count = 0  # Счетчик добавленных товаров

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Поиск товара")
        self.dialog.geometry("300x300")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Центрируем диалог
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))

        # Заголовок
        header_label = ctk.CTkLabel(
            self.dialog,
            text="Поиск товара",
            font=("Arial", 20, "bold")
        )
        header_label.pack(pady=(20, 10))

        # Поле поиска
        search_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(search_frame, text="Поиск по артикулу:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(0, 8))

        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)

        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Введите артикул...",
            font=("Arial", 12),
            height=32,
            width=400
        )
        search_entry.pack(side=tk.LEFT, fill="x", expand=True)
        search_entry.focus()

        # Список найденных товаров
        found_label = ctk.CTkLabel(
            self.dialog,
            text="Найденные товары (двойной клик для добавления)",
            font=("Arial", 12, "bold")
        )
        found_label.pack(anchor="w", padx=20, pady=(10, 5))

        list_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Определяем цвета в зависимости от темы
        if ctk.get_appearance_mode() == "Dark":
            listbox_bg = "#333333"
            listbox_fg = "#FFFFFF"
            listbox_highlight_bg = "#555555"
        else:
            listbox_bg = "#F5F5F5"
            listbox_fg = "#000000"
            listbox_highlight_bg = "#D0D0D0"

        self.found_listbox = tk.Listbox(
            list_frame,
            height=12,
            font=("Arial", 11),
            bg=listbox_bg,
            fg=listbox_fg,
            selectbackground="#2196F3",
            selectforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=listbox_highlight_bg,
            highlightcolor="#2196F3"
        )
        found_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.found_listbox.yview)
        self.found_listbox.config(yscrollcommand=found_scrollbar.set)
        self.found_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        found_scrollbar.pack(side=tk.RIGHT, fill="y")

        # Привязываем двойной клик
        self.found_listbox.bind("<Double-Button-1>", self.on_double_click)

        # Кнопки
        button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Отмена",
            command=self.cancel,
            fg_color="#F44336",
            hover_color="#D32F2F",
            width=100,
            height=35
        )
        cancel_btn.pack(side=tk.LEFT, padx=(0, 10))

        add_btn = ctk.CTkButton(
            button_frame,
            text="Добавить",
            command=self.add_selected,
            fg_color="#2196F3",
            hover_color="#1976D2",
            width=100,
            height=35
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))

        ok_btn = ctk.CTkButton(
            button_frame,
            text="OK",
            command=self.ok,
            fg_color="#4CAF50",
            hover_color="#45a049",
            width=100,
            height=35
        )
        ok_btn.pack(side=tk.RIGHT)

        # Привязка Escape к отмене
        self.dialog.bind('<Escape>', lambda e: self.cancel())

        # Загружаем все товары при открытии
        self.on_search_change()

    def on_search_change(self, *args):
        """Обработка изменения поиска"""
        search_text = self.search_var.get().strip()

        if not search_text:
            found_products = self.backend.get_all_products()
        else:
            found_products = self.backend.search_products(search_text)

        self.found_listbox.delete(0, tk.END)
        self.filtered_items.clear()

        for i, product in enumerate(found_products):
            article = product.get('article', '???')
            name = product.get('name', 'Без названия')[:40]
            display_text = f"{article} - {name}..."
            self.found_listbox.insert(tk.END, display_text)
            self.filtered_items[i] = product

    def on_double_click(self, event):
        """Обработчик двойного клика - добавляет товар"""
        self.add_selected()

    def add_selected(self):
        """Добавить выбранный товар"""
        selection = self.found_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите товар для добавления", parent=self.dialog)
            return

        index = selection[0]
        if index not in self.filtered_items:
            return

        product = self.filtered_items[index]

        # Временно отключаем колбэк success, чтобы не показывать окно при каждом добавлении
        original_success_callback = self.backend.success_callback
        self.backend.success_callback = None

        if self.backend.add_product_to_order(product):
            self.added_count += 1
            # Обновляем дерево через колбэк
            if self.update_tree_callback:
                self.update_tree_callback()
            # Обновляем статус
            if self.update_status_callback:
                self.update_status_callback(f"Добавлено товаров: {self.added_count}")

        # Восстанавливаем колбэк
        self.backend.success_callback = original_success_callback

    def ok(self):
        """Закрыть окно с результатом True и показать итоговое сообщение"""
        if self.added_count > 0:
            # Показываем итоговое сообщение как при загрузке из JSON
            messagebox.showinfo("Успех", f"Успешно добавлено товаров: {self.added_count}", parent=self.dialog)
        self.result = True
        self.dialog.destroy()

    def cancel(self):
        """Закрыть окно без результата"""
        self.result = None
        self.dialog.destroy()


class CustomQuantityDialog:
    """Кастомный диалог для изменения количества в стиле программы"""

    def __init__(self, parent, title, message, initial_value=1):
        self.result = None
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Центрируем диалог
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))

        # Заголовок
        header_label = ctk.CTkLabel(
            self.dialog,
            text=title,
            font=("Arial", 20, "bold")
        )
        header_label.pack(pady=(20, 10))

        # Сообщение
        message_label = ctk.CTkLabel(
            self.dialog,
            text=message,
            font=("Arial", 16),
            wraplength=300
        )
        message_label.pack(pady=(0, 20))

        # Поле ввода
        self.entry = ctk.CTkEntry(
            self.dialog,
            width=200,
            height=40,
            font=("Arial", 16, "bold"),
            justify="center"
        )
        self.entry.pack(pady=(0, 20))
        self.entry.insert(0, str(initial_value))
        self.entry.select_range(0, tk.END)
        self.entry.focus()

        # Кнопки
        button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Отмена",
            command=self.cancel,
            fg_color="#F44336",
            hover_color="#D32F2F",
            width=100,
            height=35
        )
        cancel_btn.pack(side=tk.LEFT, padx=(0, 10))

        ok_btn = ctk.CTkButton(
            button_frame,
            text="OK",
            command=self.ok,
            fg_color="#4CAF50",
            hover_color="#45a049",
            width=100,
            height=35
        )
        ok_btn.pack(side=tk.RIGHT)

        # Привязка Enter к OK
        self.entry.bind('<Return>', lambda e: self.ok())
        self.dialog.bind('<Escape>', lambda e: self.cancel())

    def ok(self):
        try:
            value = int(self.entry.get())
            if 0 <= value <= 9999:
                self.result = value
                self.dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "Значение должно быть от 0 до 9999")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное число")

    def cancel(self):
        self.result = None
        self.dialog.destroy()


class SupplierSelectorPopup:
    """Всплывающее окно для выбора поставщика"""

    def __init__(self, parent, suppliers, current_supplier, x, y):
        self.result = None
        self.parent = parent

        # Создаем всплывающее окно
        self.popup = ctk.CTkToplevel(parent)
        self.popup.title("Выбор поставщика")

        # Убираем декорации окна
        self.popup.overrideredirect(True)

        # Вычисляем размеры
        width = 250
        height = min(len(suppliers) * 40 + 20, 300)

        # Позиционируем окно рядом с курсором
        # Проверяем границы экрана
        screen_width = self.popup.winfo_screenwidth()
        screen_height = self.popup.winfo_screenheight()

        if x + width > screen_width:
            x = screen_width - width - 10
        if y + height > screen_height:
            y = y - height - 10

        self.popup.geometry(f"{width}x{height}+{x}+{y}")

        # Настраиваем окно
        self.popup.configure(fg_color=("#F8F8F8", "#2B2B2B"))
        self.popup.transient(parent)
        self.popup.grab_set()
        self.popup.focus_set()

        # Поднимаем на передний план
        self.popup.lift()
        self.popup.attributes('-topmost', True)

        # Создаем фрейм для кнопок
        if len(suppliers) > 6:
            container = ctk.CTkScrollableFrame(
                self.popup,
                width=width - 20,
                height=height - 20
            )
            container.pack(fill="both", expand=True, padx=10, pady=10)
        else:
            container = ctk.CTkFrame(self.popup, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=10, pady=10)

        # Добавляем кнопки для каждого поставщика
        for i, supplier in enumerate(suppliers):
            if supplier == current_supplier:
                btn_color = "#2196F3"
                hover_color = "#1976D2"
                text_color = "white"
                font_weight = "bold"
            else:
                if ctk.get_appearance_mode() == "Dark":
                    btn_color = "#404040"
                    hover_color = "#505050"
                    text_color = "#E0E0E0"
                else:
                    btn_color = "#F0F0F0"
                    hover_color = "#E0E0E0"
                    text_color = "#333333"
                font_weight = "normal"

            btn = ctk.CTkButton(
                container,
                text=supplier,
                command=lambda s=supplier: self.select_supplier(s),
                fg_color=btn_color,
                hover_color=hover_color,
                text_color=text_color,
                height=35,
                font=("Arial", 12, font_weight),
                anchor="w"
            )
            btn.pack(fill="x", pady=2)

            if supplier == current_supplier:
                btn.focus_set()

        # Привязываем обработчики событий
        self.popup.bind("<Escape>", self.on_escape)
        self.popup.bind("<FocusOut>", self.on_focus_out)

    def select_supplier(self, supplier):
        """Выбор поставщика"""
        self.result = supplier
        self.close()

    def on_escape(self, event):
        """Обработка нажатия Escape"""
        self.close()

    def on_focus_out(self, event):
        """Обработка потери фокуса"""
        self.close()

    def close(self):
        """Закрытие окна"""
        try:
            if self.popup and self.popup.winfo_exists():
                self.popup.destroy()
        except tk.TclError:
            pass


class PurchaseTableGUI:
    """Главный класс пользовательского интерфейса"""

    def __init__(self, root):
        self.root = root
        self.root.title("Генератор таблиц закупки")
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_w}x{screen_h}+0+0")
        self.root.resizable(True, True)

        # Устанавливаем тему customtkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Переменная для отслеживания текущей темы
        self.current_theme = "dark"

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

        # Загружаем сохранённые пути (если есть)
        self.load_config()

        # Создание интерфейса
        self.create_main_interface()

        # Загрузка данных при старте
        self.backend.load_initial_data()

    def load_config(self):
        """Загрузка сохранённых путей из config.json"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.db_var.set(cfg.get("database_file", self.db_var.get()))
                self.img_var.set(cfg.get("images_dir", self.img_var.get()))
                self.out_var.set(cfg.get("output_dir", self.out_var.get()))
            except Exception as e:
                print(f"Ошибка при загрузке config.json: {e}")

    def save_config(self):
        """Сохранение текущих путей в config.json"""
        cfg = {
            "database_file": self.db_var.get(),
            "images_dir": self.img_var.get(),
            "output_dir": self.out_var.get(),
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка при сохранении config.json: {e}")

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
            if self.current_theme == "dark":
                style.theme_use("clam")
                style.configure("Custom.Treeview",
                                background="#2A2A2A",
                                foreground="white",
                                fieldbackground="#2A2A2A",
                                rowheight=190,
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
                                rowheight=190,  # ИСПРАВЛЕНИЕ: было 28, теперь 190
                                font=("Arial", 11))
                style.configure("Custom.Treeview.Heading",
                                background="#E0E0E0",
                                foreground="black",
                                font=("Arial", 11, "bold"))
                style.map("Custom.Treeview.Heading",
                          background=[('active', '#D0D0D0')])

        update_treeview_style()

    def update_theme_dependent_widgets(self):
        """Обновляет цвета виджетов, зависящих от темы."""
        self.setup_treeview_style()

        if hasattr(self, 'theme_button') and self.theme_button:
            if self.current_theme == "dark":
                self.theme_button.configure(
                    fg_color="#455A64",
                    hover_color="#37474F",
                    text_color="white"
                )
            else:
                self.theme_button.configure(
                    fg_color="#90A4AE",
                    hover_color="#78909C",
                    text_color="white"
                )

        if hasattr(self, 'settings_wrapper') and self.settings_wrapper:
            self.settings_wrapper.destroy()
            self.create_settings_frame_in_main()

    def create_settings_frame_in_main(self):
        """Создание фрейма настроек путей в основном интерфейсе"""
        self.settings_wrapper = ctk.CTkFrame(self.main_top_container, corner_radius=10)
        self.settings_wrapper.pack(side=tk.RIGHT, fill="both", expand=True, padx=(10, 0), pady=0)

        settings_container = ctk.CTkFrame(self.settings_wrapper, fg_color="transparent")
        settings_container.pack(fill="both", expand=True, padx=10, pady=10)

        header_label = ctk.CTkLabel(
            settings_container,
            text="Настройки путей",
            font=("Arial", 12, "bold"),
            text_color=("black", "white")
        )
        header_label.pack(anchor="w", pady=(0, 5))

        settings_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        settings_frame.pack(fill="x")

        self.create_path_setting(settings_frame, "База данных:", self.db_var, self.browse_database)
        self.create_path_setting(settings_frame, "Изображения:", self.img_var, self.browse_images)
        self.create_path_setting(settings_frame, "Выходная папка:", self.out_var, self.browse_output)

    def toggle_theme(self):
        """Переключение темы"""
        if self.current_theme == "light":
            self.current_theme = "dark"
            ctk.set_appearance_mode("dark")
        else:
            self.current_theme = "light"
            ctk.set_appearance_mode("light")

        self.update_theme_dependent_widgets()

    def create_main_interface(self):
        """Создание основного интерфейса на customtkinter"""

        # === Горизонтальный контейнер для кнопок и настроек (3 блока) ===
        self.main_top_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_top_container.pack(fill="x", padx=20, pady=(0, 0))

        # --- Левая часть: Блок основных кнопок ---
        buttons_wrapper = ctk.CTkFrame(self.main_top_container, corner_radius=10)
        buttons_wrapper.pack(side=tk.LEFT, fill="both", expand=False, padx=(0, 10), pady=0)

        buttons_container = ctk.CTkFrame(buttons_wrapper, fg_color="transparent")
        buttons_container.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Кнопка "Тема" (во всю ширину) ---
        self.theme_button = ctk.CTkButton(
            buttons_container,
            text="Тема",
            command=self.toggle_theme,
            fg_color="#455A64" if self.current_theme == "dark" else "#90A4AE",
            hover_color="#37474F" if self.current_theme == "dark" else "#78909C",
            text_color="white",
            corner_radius=8,
            height=40,
            font=("Arial", 13, "bold")
        )
        self.theme_button.pack(fill="x", pady=(0, 10))

        # --- Ряд из двух кнопок: "Лист закупки" и "Генерировать" ---
        row_frame = ctk.CTkFrame(buttons_container, fg_color="transparent")
        row_frame.pack(fill="x", pady=(0, 10))

        row_frame.grid_columnconfigure(0, weight=1, uniform="equal")
        row_frame.grid_columnconfigure(1, weight=1, uniform="equal")

        purchase_btn = ctk.CTkButton(
            row_frame,
            text="Лист закупки",
            command=self.show_purchase_interface,
            fg_color="#2196F3",
            hover_color="#1976D2",
            corner_radius=8,
            height=40,
            font=("Arial", 13, "bold"),
            text_color="white"
        )
        purchase_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        generate_btn = ctk.CTkButton(
            row_frame,
            text="Генерировать",
            command=self.generate_purchase_list,
            fg_color="#FF9800",
            hover_color="#F57C00",
            corner_radius=8,
            height=40,
            font=("Arial", 13, "bold"),
            text_color="white"
        )
        generate_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # --- Кнопка "Лист наличия" (во всю ширину) ---
        availability_btn = ctk.CTkButton(
            buttons_container,
            text="Лист наличия",
            command=self.generate_availability_list,
            fg_color="#4CAF50",
            hover_color="#45a049",
            corner_radius=8,
            height=40,
            font=("Arial", 13, "bold"),
            text_color="white"
        )
        availability_btn.pack(fill="x", pady=(0, 0))

        # --- Центральная часть: Блок операций (без заголовка) ---
        json_wrapper = ctk.CTkFrame(self.main_top_container, corner_radius=10)
        json_wrapper.pack(side=tk.LEFT, fill="both", expand=False, padx=(10, 10), pady=0)

        json_container = ctk.CTkFrame(json_wrapper, fg_color="transparent")
        json_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Кнопка "Поиск"
        search_btn = ctk.CTkButton(
            json_container,
            text="Поиск",
            command=self.open_search_dialog,
            fg_color="#9C27B0",
            hover_color="#7B1FA2",
            corner_radius=8,
            height=40,
            width=150,
            font=("Arial", 13, "bold"),
            text_color="white"
        )
        search_btn.pack(fill="x", pady=(0, 10))

        # Кнопка "Сохранить в JSON"
        save_json_btn = ctk.CTkButton(
            json_container,
            text="Сохранить в JSON",
            command=self.save_to_json,
            fg_color="#546E7A",
            hover_color="#455A64",
            corner_radius=8,
            height=40,
            width=150,
            font = ("Arial", 12, "bold"),
            text_color = "white"
        )
        save_json_btn.pack(fill="x", pady=(0, 10))

        # Кнопка "Загрузить из JSON"
        load_json_btn = ctk.CTkButton(
            json_container,
            text="Загрузить из JSON",
            command=self.load_from_json,
            fg_color="#546E7A",
            hover_color="#455A64",
            corner_radius=8,
            height=40,
            width=150,
            font=("Arial", 12, "bold"),
            text_color="white"
        )
        load_json_btn.pack(fill="x", pady=(0, 0))

        # --- Правая часть: Подложка для настроек путей ---
        settings_wrapper = ctk.CTkFrame(self.main_top_container, corner_radius=10)
        settings_wrapper.pack(side=tk.RIGHT, fill="both", expand=True, padx=(10, 0), pady=0)

        settings_container = ctk.CTkFrame(settings_wrapper, fg_color="transparent")
        settings_container.pack(fill="both", expand=True, padx=10, pady=10)

        header_label = ctk.CTkLabel(
            settings_container,
            text="Настройки путей",
            font=("Arial", 12, "bold"),
            text_color=("black", "white")
        )
        header_label.pack(anchor="w", pady=(0, 5))

        settings_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        settings_frame.pack(fill="x")

        self.create_path_setting(settings_frame, "База данных:", self.db_var, self.browse_database)
        self.create_path_setting(settings_frame, "Изображения:", self.img_var, self.browse_images)
        self.create_path_setting(settings_frame, "Выходная папка:", self.out_var, self.browse_output)

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

    def open_search_dialog(self):
        """Открытие диалогового окна поиска"""
        dialog = SearchDialog(self.root, self.backend, self.update_tree, self.update_status)
        self.root.wait_window(dialog.dialog)
        # После закрытия диалога обновляем дерево
        if hasattr(self, 'tree'):
            self.update_tree()

    def create_path_setting(self, parent, label_text, var, browse_command):
        """Создание поля настройки пути с автообновлением при потере фокуса"""
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
        entry.pack(side=tk.LEFT, padx=10, fill="x", expand=True)

        def on_focus_out(event):
            new_path = var.get()
            self.backend.update_paths(
                database_file=self.db_var.get(),
                images_dir=self.img_var.get(),
                output_dir=self.out_var.get()
            )
            if label_text in ["База данных:", "Изображения:"]:
                self.backend.load_initial_data()

        entry.bind("<FocusOut>", on_focus_out)

        ctk.CTkButton(
            frame,
            text="⋯",
            command=browse_command,
            width=32,
            height=32,
            fg_color=ui_config.BUTTON_COLORS['browse'][0],
            hover_color=ui_config.BUTTON_COLORS['browse'][1],
            corner_radius=6,
            font=("Arial", 14)
        ).pack(side=tk.RIGHT)

    def create_purchase_interface(self):
        """Создание интерфейса для режима закупки"""
        self.purchase_frame = ctk.CTkFrame(self.root, fg_color="transparent")

        # === Основной список товаров (дерево) ===
        self.create_tree_section()

        # === Кнопки управления ===
        self.create_control_buttons()

    def create_tree_section(self):
        """Создание секции дерева товаров с фото в первой колонке"""
        tree_container = ctk.CTkFrame(self.purchase_frame, corner_radius=10)
        tree_container.pack(fill="both", expand=True, padx=0, pady=(20, 0))

        ctk.CTkLabel(
            tree_container,
            text="Список для закупки",
            font=("Arial", 14, "bold"),
            text_color=("black", "white"),
            anchor="w"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        tree_inner_frame = ctk.CTkFrame(tree_container, fg_color="transparent")
        tree_inner_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("Чекбокс", "Артикул", "Наименование", "Цена", "Количество", "Поставщик", "Сумма")
        self.tree = ttk.Treeview(
            tree_inner_frame,
            columns=columns,
            show="tree headings",
            height=15,
            style="Custom.Treeview"
        )

        center_align = "center"

        # Колонка #0 теперь для ФОТО
        self.tree.column("#0", width=190, minwidth=190, anchor=center_align)
        self.tree.heading("#0", text="Фото", anchor=center_align)

        # Остальные колонки
        self.tree.column("Чекбокс", width=60, minwidth=60, anchor=center_align)
        self.tree.column("Артикул", width=150, minwidth=120, anchor=center_align)
        self.tree.column("Наименование", width=200, minwidth=180, anchor=center_align)
        self.tree.column("Цена", width=80, minwidth=70, anchor=center_align)
        self.tree.column("Количество", width=80, minwidth=70, anchor=center_align)
        self.tree.column("Поставщик", width=150, minwidth=120, anchor=center_align)
        self.tree.column("Сумма", width=100, minwidth=90, anchor=center_align)

        # Заголовки
        self.tree.heading("Чекбокс", text="✓", anchor=center_align)
        self.tree.heading("Артикул", text="Артикул", anchor=center_align)
        self.tree.heading("Наименование", text="Наименование", anchor=center_align)
        self.tree.heading("Цена", text="Цена", anchor=center_align)
        self.tree.heading("Количество", text="Кол-во", anchor=center_align)
        self.tree.heading("Поставщик", text="Поставщик", anchor=center_align)
        self.tree.heading("Сумма", text="Сумма", anchor=center_align)

        # === Устанавливаем высоту строки = 190px ===
        style = ttk.Style()
        style.configure("Custom.Treeview", rowheight=190)

        # Scrollbar
        tree_scrollbar = ttk.Scrollbar(tree_inner_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.config(yscrollcommand=tree_scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill="y")

        # Биндинги
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Button-1>", self.on_tree_single_click)

        # Хранилище изображений (чтобы GC не удалил)
        self.tree_images = {}

    def create_control_buttons(self):
        """Создание кнопок управления"""
        control_frame = ctk.CTkFrame(self.purchase_frame, fg_color="transparent")
        control_frame.pack(fill="x", padx=0, pady=(10, 20))

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
        ).pack(side=tk.LEFT, padx=10)

    # === ОБРАБОТЧИКИ СОБЫТИЙ ===

    def browse_database(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл базы данных",
            filetypes=[("Excel файлы", "*.xlsx *.xls"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.db_var.set(file_path)
            self.save_config()

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
        self.purchase_frame.pack(fill="both", expand=True, padx=20, pady=(0, 0))
        self.update_status("Режим составления листа закупки")

    def hide_purchase_interface(self):
        """Скрыть интерфейс закупки"""
        self.purchase_frame.pack_forget()
        self.update_status("Готов к работе")

    def on_tree_double_click(self, event):
        """Обработка двойного клика - изменение количества"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return

        values = self.tree.item(item)['values']
        if not values or len(values) < 5:
            return

        article = values[1]  # Артикул в позиции 1
        try:
            current_qty = int(values[4])  # Количество в позиции 4
        except (ValueError, IndexError):
            current_qty = 1

        dialog = CustomQuantityDialog(
            self.root,
            "Изменить количество",
            f"Введите новое количество для {article}:",
            current_qty
        )

        self.root.wait_window(dialog.dialog)

        if dialog.result is not None:
            if self.backend.update_item_quantity(article, dialog.result):
                self.update_tree()

    def update_tree(self):
        """Обновление дерева товаров с правильным размещением изображений"""
        from utils.image_utils import create_rounded_image, pil_to_photoimage

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_images.clear()

        display_items = self.backend.get_order_items_for_display()

        for item_data in display_items:
            # РЕШЕНИЕ: Используем более крупные эмодзи-символы
            # ✅ и ⬜ визуально намного крупнее чем ☑ и ☐
            checkbox = "✅" if item_data['enabled'] else "⬜"

            photo_image = None
            if item_data['photo']:
                try:
                    rounded_img = create_rounded_image(item_data['photo'], size=(186, 186), corner_radius=15)
                    if rounded_img:
                        photo_image = pil_to_photoimage(rounded_img)
                        self.tree_images[item_data['article']] = photo_image
                except Exception as e:
                    print(f"Ошибка обработки изображения для {item_data['article']}: {e}")

            total_sum = item_data['price'] * item_data['quantity']

            values = (
                checkbox,  # Чекбокс (колонка 1)
                item_data['article'],  # Артикул (колонка 2)
                item_data['name'],  # Наименование (колонка 3)
                f"{item_data['price']:.2f}",  # Цена (колонка 4)
                item_data['quantity'],  # Количество (колонка 5)
                item_data['selected_supplier'],  # Поставщик (колонка 6)
                f"{total_sum:.2f}"  # Сумма (колонка 7)
            )

            # Вставляем элемент БЕЗ тега для сохранения стандартного шрифта
            item_id = self.tree.insert(
                "", tk.END,
                text="",
                values=values,
                tags=(item_data['article'],),
                image=photo_image
            )

    def on_tree_single_click(self, event):
        """Обработчик одинарного клика по дереву с новой структурой колонок"""
        region = self.tree.identify_region(event.x, event.y)
        column = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)

        if not row:
            return

        if region == "cell" and column == "#6":
            self.show_supplier_selector(event, row)
        elif region == "cell" and column == "#1":
            self.toggle_item_checkbox(row)

    def toggle_item_checkbox(self, row):
        """Переключение чекбокса товара"""
        values = self.tree.item(row)['values']
        if values and len(values) > 1:
            article = values[1]  # Артикул теперь в позиции 1
            if self.backend.toggle_item_enabled(article):
                self.update_tree()

    def show_supplier_selector(self, event, row):
        """Показ селектора поставщика с новой структурой"""
        values = self.tree.item(row)['values']
        if not values or len(values) < 2:
            return

        article = values[1]  # Артикул в позиции 1

        display_items = self.backend.get_order_items_for_display()
        target_item = next((item for item in display_items if item['article'] == article), None)
        if not target_item:
            return

        all_suppliers = target_item['all_suppliers']
        if len(all_suppliers) <= 1:
            return

        selector = SupplierSelectorPopup(
            self.root,
            all_suppliers,
            target_item['selected_supplier'],
            event.x_root,
            event.y_root
        )

        self.root.wait_window(selector.popup)

        if selector.result and selector.result != target_item['selected_supplier']:
            if self.backend.update_item_supplier(article, selector.result):
                self.update_tree()

    def generate_purchase_list(self):
        """Генерация листа закупки"""
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


def main():
    """Запуск GUI приложения на customtkinter"""
    root = ctk.CTk()
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    app = PurchaseTableGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()