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

        print(f"Создано всплывающее окно в позиции {x}, {y}, размер {width}x{height}")

        # Создаем фрейм для кнопок
        if len(suppliers) > 6:
            # Если много поставщиков, используем скроллируемый фрейм
            container = ctk.CTkScrollableFrame(
                self.popup,
                width=width - 20,
                height=height - 20
            )
            container.pack(fill="both", expand=True, padx=10, pady=10)
        else:
            # Если мало поставщиков, обычный фрейм
            container = ctk.CTkFrame(self.popup, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=10, pady=10)

        # Добавляем кнопки для каждого поставщика
        for i, supplier in enumerate(suppliers):
            if supplier == current_supplier:
                # Выделяем текущего поставщика
                btn_color = "#2196F3"
                hover_color = "#1976D2"
                text_color = "white"
                font_weight = "bold"
            else:
                # Обычные поставщики
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

            # Устанавливаем фокус на текущий поставщик
            if supplier == current_supplier:
                btn.focus_set()

        # Привязываем обработчики событий
        self.popup.bind("<Escape>", self.on_escape)
        self.popup.bind("<FocusOut>", self.on_focus_out)

        print(f"Добавлено {len(suppliers)} кнопок поставщиков")

    def select_supplier(self, supplier):
        """Выбор поставщика"""
        self.result = supplier
        print(f"Выбран поставщик: {supplier}")
        self.close()

    def on_escape(self, event):
        """Обработка нажатия Escape"""
        print("Нажат Escape, закрываем селектор")
        self.close()

    def on_focus_out(self, event):
        """Обработка потери фокуса"""
        print("Потеря фокуса, закрываем селектор")
        self.close()

    def close(self):
        """Закрытие окна"""
        try:
            if self.popup and self.popup.winfo_exists():
                self.popup.destroy()
                print("Всплывающее окно закрыто")
        except tk.TclError:
            pass


class PurchaseTableGUI:
    """Главный класс пользовательского интерфейса"""

    def __init__(self, root):
        self.root = root
        self.root.title("Генератор таблиц закупки")
        # Добавляем автоматическое разворачивание на весь экран
        # Надёжное разворачивание во весь экран:
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
                                rowheight=28,
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
        # Обновляем Treeview
        self.setup_treeview_style()
        # Обновляем Listbox
        self.update_listbox_colors()

        # Обновляем кнопку переключения темы (если она существует)
        if hasattr(self, 'theme_button') and self.theme_button:
            if self.current_theme == "dark":
                self.theme_button.configure(fg_color="gray20", hover_color="#F2F7F2", text_color="white")
            else:
                self.theme_button.configure(fg_color="#F2F7F2", hover_color="gray20", text_color="gray20")

        if hasattr(self, 'settings_wrapper') and self.settings_wrapper:
            self.settings_wrapper.destroy()
            self.create_settings_frame_in_main()

    def create_settings_frame_in_main(self):
        """Создание фрейма настроек путей в основном интерфейсе (для возможности пересоздания)."""
        # Правая часть: Подложка для настроек путей
        self.settings_wrapper = ctk.CTkFrame(self.main_top_container, corner_radius=10)
        self.settings_wrapper.pack(side=tk.RIGHT, fill="both", expand=True, padx=(10, 0), pady=0)

        # Внутренний контейнер с отступами 10px
        settings_container = ctk.CTkFrame(self.settings_wrapper, fg_color="transparent")
        settings_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Заголовок "Настройки путей"
        header_label = ctk.CTkLabel(
            settings_container,
            text="Настройки путей",
            font=("Arial", 12, "bold"),
            text_color=("black", "white")
        )
        header_label.pack(anchor="w", pady=(0, 5))  # Отступ снизу 5px

        # Внутренний контейнер для полей ввода
        settings_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        settings_frame.pack(fill="x")

        # === База данных ===
        self.create_path_setting(settings_frame, "База данных:", self.db_var, self.browse_database)

        # === Папка изображений ===
        self.create_path_setting(settings_frame, "Изображения:", self.img_var, self.browse_images)
        # === Выходная папка ===
        self.create_path_setting(settings_frame, "Выходная папка:", self.out_var, self.browse_output)

    def toggle_theme(self):
        """Переключение темы"""
        if self.current_theme == "light":
            self.current_theme = "dark"
            ctk.set_appearance_mode("dark")
        else:
            self.current_theme = "light"
            ctk.set_appearance_mode("light")

        # Обновляем стили и виджеты
        self.update_theme_dependent_widgets()

    def create_main_interface(self):
        """Создание основного интерфейса на customtkinter (обновлённая версия)"""

        # === Горизонтальный контейнер для кнопок и настроек (3 блока) ===
        self.main_top_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_top_container.pack(fill="x", padx=20, pady=(0, 0))

        # --- Левая часть: Блок основных кнопок ---
        buttons_wrapper = ctk.CTkFrame(self.main_top_container, corner_radius=10)
        buttons_wrapper.pack(side=tk.LEFT, fill="both", expand=False, padx=(0, 10), pady=0)

        # Внутренний контейнер с отступами
        buttons_container = ctk.CTkFrame(buttons_wrapper, fg_color="transparent")
        buttons_container.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Кнопка "Тема" (во всю ширину) ---
        theme_btn = ctk.CTkButton(
            buttons_container,
            text="Тема",
            command=self.toggle_theme,
            fg_color="gray" if self.current_theme == "dark" else "gray20",
            hover_color="gray" if self.current_theme == "dark" else "gray20",
            corner_radius=8,
            height=40
        )
        theme_btn.pack(fill="x", pady=(0, 10))

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
            height=40
        )
        purchase_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        generate_btn = ctk.CTkButton(
            row_frame,
            text="Генерировать",
            command=self.generate_purchase_list,
            fg_color="#FF9800",
            hover_color="#F57C00",
            corner_radius=8,
            height=40
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
            height=40
        )
        availability_btn.pack(fill="x", pady=(0, 0))

        # --- Центральная часть: Блок JSON кнопок ---
        json_wrapper = ctk.CTkFrame(self.main_top_container, corner_radius=10)
        json_wrapper.pack(side=tk.LEFT, fill="both", expand=False, padx=(10, 10), pady=0)

        # Внутренний контейнер с отступами
        json_container = ctk.CTkFrame(json_wrapper, fg_color="transparent")
        json_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Заголовок "JSON операции"
        json_header_label = ctk.CTkLabel(
            json_container,
            text="JSON операции",
            font=("Arial", 12, "bold"),
            text_color=("black", "white")
        )
        json_header_label.pack(anchor="w", pady=(0, 5))

        # Кнопка "Сохранить в JSON"
        save_json_btn = ctk.CTkButton(
            json_container,
            text="Сохранить в JSON",
            command=self.save_to_json,
            fg_color="#607D8B",
            hover_color="#455A64",
            corner_radius=8,
            height=40,
            width=150
        )
        save_json_btn.pack(fill="x", pady=(0, 10))

        # Кнопка "Загрузить из JSON"
        load_json_btn = ctk.CTkButton(
            json_container,
            text="Загрузить из JSON",
            command=self.load_from_json,
            fg_color="#9E9E9E",
            hover_color="#757575",
            corner_radius=8,
            height=40,
            width=150
        )
        load_json_btn.pack(fill="x", pady=(0, 0))

        # --- Правая часть: Подложка для настроек путей ---
        settings_wrapper = ctk.CTkFrame(self.main_top_container, corner_radius=10)
        settings_wrapper.pack(side=tk.RIGHT, fill="both", expand=True, padx=(10, 0), pady=0)

        # Внутренний контейнер с отступами 10px
        settings_container = ctk.CTkFrame(settings_wrapper, fg_color="transparent")
        settings_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Заголовок "Настройки путей"
        header_label = ctk.CTkLabel(
            settings_container,
            text="Настройки путей",
            font=("Arial", 12, "bold"),
            text_color=("black", "white")
        )
        header_label.pack(anchor="w", pady=(0, 5))  # Отступ снизу 5px

        # Внутренний контейнер для полей ввода
        settings_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        settings_frame.pack(fill="x")

        # === База данных ===
        self.create_path_setting(settings_frame, "База данных:", self.db_var, self.browse_database)

        # === Папка изображений ===
        self.create_path_setting(settings_frame, "Изображения:", self.img_var, self.browse_images)

        # === Выходная папка ===
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

    def create_button(self, parent, text, command,
                      width=180, height=45,
                      fg_color="#3B8ED0", hover_color="#367CBA",
                      text_color="white", corner_radius=10,
                      side=tk.LEFT, padx=(0, 0), pady=0,
                      font=("Arial", 12, "bold"),
                      anchor="center"):  # <-- Добавлен параметр anchor
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
        btn.pack(side=side, padx=padx, pady=pady, anchor=anchor)  # <-- Добавлен anchor в pack
        return btn

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

        # Определяем, какой путь обновлять в зависимости от метки
        def on_focus_out(event):
            # Получаем текущее значение из поля
            new_path = var.get()
            # Обновляем ВСЕ пути в backend (чтобы не терять остальные)
            self.backend.update_paths(
                database_file=self.db_var.get(),
                images_dir=self.img_var.get(),
                output_dir=self.out_var.get()
            )
            # Если это поле базы данных — перезагружаем данные
            if label_text == "База данных:":
                self.backend.load_initial_data()

        # Привязываем событие потери фокуса
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

        def on_focus_out(event):
            new_path = var.get()
            self.backend.update_paths(
                database_file=self.db_var.get(),
                images_dir=self.img_var.get(),
                output_dir=self.out_var.get()
            )
            # Перезагружаем данные, если изменилась база ИЛИ папка изображений
            if label_text in ["База данных:", "Изображения:"]:
                self.backend.load_initial_data()

    def create_purchase_interface(self):
        """Создание интерфейса для режима закупки (исправленные отступы и центрирование)"""
        # purchase_frame уже создан в create_main_interface, но мы убедимся:
        self.purchase_frame = ctk.CTkFrame(self.root, fg_color="transparent")

        # === Единая панель поиска и найденных товаров ===
        # search_container имеет верхний внешний отступ 20px (между блоком путей и этим блоком)
        search_container = ctk.CTkFrame(self.purchase_frame, corner_radius=10)
        search_container.pack(fill="both", expand=False, padx=0, pady=(20, 0))

        # Верхняя строка: используем pack для top_row_frame, а внутри него grid для трёх колонок
        top_row_frame = ctk.CTkFrame(search_container, fg_color="transparent")
        top_row_frame.pack(fill="x", padx=0, pady=(0, 0))

        # Настраиваем 3 равных колонки: поиск | заголовок (центр) | кнопка
        top_row_frame.grid_columnconfigure(0, weight=1)
        top_row_frame.grid_columnconfigure(1, weight=1)
        top_row_frame.grid_columnconfigure(2, weight=1)

        # ---- Поиск (левая колонка) ----
        search_frame = ctk.CTkFrame(top_row_frame, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        ctk.CTkLabel(search_frame, text="Поиск по артикулу:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(0, 8))
        self.search_var.trace('w', self.on_search_change)
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Введите артикул...",
            font=("Arial", 12),
            height=32,
            width=280
        )
        search_entry.pack(side=tk.LEFT)

        # ---- Заголовок (центральная колонка) ----
        header_label = ctk.CTkLabel(
            top_row_frame,
            text="Найденные товары",
            font=("Arial", 14, "bold"),
            text_color=("black", "white")
        )
        header_label.grid(row=0, column=1, sticky="nsew")

        # ---- Кнопка (правая колонка) ----
        add_btn = ctk.CTkButton(
            top_row_frame,
            text="Добавить выбранный",
            command=self.add_selected_item,
            fg_color="#4CAF50",
            hover_color="#45a049",
            text_color="white",
            corner_radius=8,
            font=("Arial", 12, "bold"),
            height=32
        )
        add_btn.grid(row=0, column=2, sticky="e", padx=10, pady=10)

        # === Блок найденных (нижняя часть search_container) ===
        found_inner_frame = ctk.CTkFrame(search_container, fg_color="transparent")
        # внутренние отступы блока — 10px
        found_inner_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # listbox с правильными цветами
        self.update_listbox_colors_vars()
        self.found_listbox = tk.Listbox(
            found_inner_frame,
            height=6,
            font=("Arial", 11),
            bg=self.listbox_bg,
            fg=self.listbox_fg,
            selectbackground="#2196F3",
            selectforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.listbox_highlight_bg,
            highlightcolor="#2196F3"
        )
        found_scrollbar = ttk.Scrollbar(found_inner_frame, orient=tk.VERTICAL, command=self.found_listbox.yview)
        self.found_listbox.config(yscrollcommand=found_scrollbar.set)
        self.found_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        found_scrollbar.pack(side=tk.RIGHT, fill="y")

        # Добавляем обработчик двойного клика для найденных товаров
        self.found_listbox.bind("<Double-Button-1>", self.on_found_item_double_click)

        # === Основной список товаров (дерево) ===
        # используем отдельную функцию (ниже) — она тоже приведена внизу
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
        self.update_listbox_colors_vars()

        self.found_listbox = tk.Listbox(
            found_inner_frame,
            height=4,
            font=("Arial", 11),
            bg=self.listbox_bg,
            fg=self.listbox_fg,
            selectbackground="#2196F3",
            selectforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.listbox_highlight_bg,
            highlightcolor="#2196F3"
        )
        found_scrollbar = ttk.Scrollbar(found_inner_frame, orient=tk.VERTICAL, command=self.found_listbox.yview)
        self.found_listbox.config(yscrollcommand=found_scrollbar.set)
        self.found_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        found_scrollbar.pack(side=tk.RIGHT, fill="y")

    def update_listbox_colors_vars(self):
        """Обновляем переменные цветов для listbox"""
        if self.current_theme == "dark":
            self.listbox_bg = "#333333"
            self.listbox_fg = "#FFFFFF"
            self.listbox_highlight_bg = "#555555"
        else:
            self.listbox_bg = "#F5F5F5"
            self.listbox_fg = "#000000"
            self.listbox_highlight_bg = "#D0D0D0"

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

        # ИСПРАВЛЕНИЕ: Изменяем структуру колонок - фото будет в колонке #0
        columns = ("Чекбокс", "Артикул", "Наименование", "Цена", "Количество", "Поставщик", "Сумма")
        self.tree = ttk.Treeview(
            tree_inner_frame,
            columns=columns,
            show="tree headings",
            height=15,
            style="Custom.Treeview"
        )

        # === Настройка стилей и выравнивания ===
        center_align = "center"

        # Колонка #0 теперь для ФОТО
        self.tree.column("#0", width=190, minwidth=190, anchor=center_align)
        self.tree.heading("#0", text="Фото", anchor=center_align)

        # Остальные колонки
        self.tree.column("Чекбокс", width=50, minwidth=50, anchor=center_align)
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
        """Создание кнопок управления (убрана кнопка Назад и JSON кнопки)"""
        control_frame = ctk.CTkFrame(self.purchase_frame, fg_color="transparent")
        # верхний отступ 10, нижний 20 (внешний: отделяет дерево от кнопок)
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

    def on_found_item_double_click(self, event):
        """Обработчик двойного клика по найденным товарам - добавляет товар в список закупки"""
        selection = self.found_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index not in self.filtered_items:
            return

        product = self.filtered_items[index]
        if self.backend.add_product_to_order(product):
            self.update_tree()

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
        # Пакуем фрейм с внешними 20px по бокам, без верхнего padding (между блоками 20 реализовано в search_container)
        self.purchase_frame.pack(fill="both", expand=True, padx=20, pady=(0, 0))
        self.update_status("Режим составления листа закупки")

    def hide_purchase_interface(self):
        """Скрыть интерфейс закупки"""
        self.purchase_frame.pack_forget()
        self.update_status("Готов к работе")

    def on_search_change(self, *args):
        """Обработка изменения поиска - теперь показывает все товары, но фильтрует при поиске"""
        search_text = self.search_var.get().strip()

        # Если поиск пустой, показываем все товары
        if not search_text:
            found_products = self.backend.get_all_products()  # Новый метод для получения всех товаров
        else:
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
        if not values or len(values) < 5:
            return

        article = values[1]  # Артикул в позиции 1
        try:
            current_qty = int(values[4])  # Количество в позиции 4
        except (ValueError, IndexError):
            current_qty = 1

        # Используем кастомный диалог
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
        # Добавляем импорт функций для обработки изображений
        from utils.image_utils import create_rounded_image, pil_to_photoimage

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_images.clear()

        display_items = self.backend.get_order_items_for_display()

        for item_data in display_items:
            checkbox = "☑" if item_data['enabled'] else "☐"

            # Обрабатываем изображение с закруглением углов
            photo_image = None
            if item_data['photo']:
                try:
                    # ИСПРАВЛЕНИЕ: Создаем скругленное изображение
                    rounded_img = create_rounded_image(item_data['photo'], size=(186, 186), corner_radius=15)
                    if rounded_img:
                        photo_image = pil_to_photoimage(rounded_img)
                        # Сохраняем ссылку на изображение
                        self.tree_images[item_data['article']] = photo_image
                except Exception as e:
                    print(f"Ошибка обработки изображения для {item_data['article']}: {e}")

            # Рассчитываем сумму
            total_sum = item_data['price'] * item_data['quantity']

            # ИСПРАВЛЕНИЕ: Новая структура значений для колонок
            values = (
                checkbox,  # Чекбокс (колонка 1)
                item_data['article'],  # Артикул (колонка 2)
                item_data['name'],  # Наименование (колонка 3)
                f"{item_data['price']:.2f}",  # Цена (колонка 4)
                item_data['quantity'],  # Количество (колонка 5)
                item_data['selected_supplier'],  # Поставщик (колонка 6)
                f"{total_sum:.2f}"  # Сумма (колонка 7)
            )

            # ИСПРАВЛЕНИЕ: Вставляем строку с изображением в колонке #0
            item_id = self.tree.insert(
                "", tk.END,
                text="",  # Пустой текст, так как изображение будет отображаться
                values=values,
                tags=(item_data['article'],),
                image=photo_image  # Изображение устанавливается сразу при создании
            )

    def on_tree_single_click(self, event):
        """Обработчик одинарного клика по дереву с новой структурой колонок"""
        region = self.tree.identify_region(event.x, event.y)
        column = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)

        if not row:
            return

        # Новая структура колонок:
        # #0 - фото
        # #1 - чекбокс
        # #2 - артикул
        # #3 - наименование
        # #4 - цена
        # #5 - количество
        # #6 - поставщик
        # #7 - сумма

        # Если кликнули по колонке "Поставщик" (#6)
        if region == "cell" and column == "#6":
            self.show_supplier_selector(event, row)
        # Если кликнули по колонке с чекбоксом (#1)
        elif region == "cell" and column == "#1":
            self.toggle_item_checkbox(row)

    def toggle_item_checkbox(self, row):
        """Переключение чекбокса товара"""
        values = self.tree.item(row)['values']
        if values and len(values) > 1:
            article = values[1]  # Артикул теперь в позиции 1 (второй элемент values)
            if self.backend.toggle_item_enabled(article):
                self.update_tree()

    def show_supplier_selector(self, event, row):
        """Показ селектора поставщика с новой структурой"""
        values = self.tree.item(row)['values']
        if not values or len(values) < 2:
            return

        article = values[1]  # Артикул в позиции 1

        # Получаем список всех поставщиков для этого артикула из backend
        display_items = self.backend.get_order_items_for_display()
        target_item = next((item for item in display_items if item['article'] == article), None)
        if not target_item:
            return

        all_suppliers = target_item['all_suppliers']
        if len(all_suppliers) <= 1:
            return

        # Создаем селектор как всплывающее окно
        selector = SupplierSelectorPopup(
            self.root,
            all_suppliers,
            target_item['selected_supplier'],
            event.x_root,
            event.y_root
        )

        # Ждем результат
        self.root.wait_window(selector.popup)

        # Проверяем результат и обновляем
        if selector.result and selector.result != target_item['selected_supplier']:
            if self.backend.update_item_supplier(article, selector.result):
                self.update_tree()

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
        self.update_listbox_colors_vars()
        if hasattr(self, 'found_listbox'):
            self.found_listbox.configure(
                bg=self.listbox_bg,
                fg=self.listbox_fg,
                highlightbackground=self.listbox_highlight_bg
            )


def main():
    """Запуск GUI приложения на customtkinter"""
    # Создаём главное окно CTk
    root = ctk.CTk()

    # Устанавливаем тему и цветовую схему
    ctk.set_appearance_mode("light")  # "light", "dark", "system"
    ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

    # Создаём приложение
    app = PurchaseTableGUI(root)

    # Запускаем главный цикл
    root.mainloop()


if __name__ == "__main__":
    main()