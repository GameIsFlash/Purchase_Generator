import logging
from pathlib import Path
from collections import defaultdict
from config import ERROR_MESSAGES
from data_reader import DataReader
from excel_generator import ExcelGenerator
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_purchase_tables(
        images_dir: str,
        database_file: str,
        order_dict: dict,
        output_dir: str = "output"
):
    """Генерация таблиц закупки по списку заказов"""
    generated_files = []
    errors = []

    try:
        if not order_dict:
            errors.append(ERROR_MESSAGES['EMPTY_ORDER'])
            return generated_files, errors

        data_reader = DataReader(database_file, images_dir)
        excel_generator = ExcelGenerator(output_dir)

        if not data_reader.load_database():
            errors.append("Не удалось загрузить базу данных")
            return generated_files, errors

        suppliers_data = defaultdict(list)

        for article, quantity in order_dict.items():
            try:
                if not isinstance(quantity, int) or quantity <= 0:
                    errors.append(ERROR_MESSAGES['INVALID_QUANTITY'].format(article, quantity))
                    continue

                product_info = data_reader.get_product_info(article)
                if not product_info:
                    errors.append(ERROR_MESSAGES['PRODUCT_NOT_FOUND'].format(article))
                    continue

                processed_image = data_reader.process_image(product_info['article'])

                item_data = {
                    'article': product_info['article'],
                    'name': product_info['name'],
                    'price': product_info['price'],
                    'quantity': quantity,
                    'supplier': product_info['supplier'],
                    'processed_image': processed_image
                }

                suppliers_data[product_info['supplier']].append(item_data)

            except Exception as e:
                error_msg = f"Ошибка обработки артикула {article}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        for supplier, items in suppliers_data.items():
            try:
                supplier_data = {
                    'supplier': supplier,
                    'items': items
                }

                file_path = excel_generator.generate_table(supplier_data)
                generated_files.append(file_path)

                logger.info(f"Успешно создана таблица для {supplier}: {len(items)} позиций")

            except Exception as e:
                error_msg = f"Ошибка генерации Excel для поставщика {supplier}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        logger.info(f"Готово. Всего файлов: {len(generated_files)}, ошибок: {len(errors)}")

    except Exception as e:
        error_msg = f"Фатальная ошибка: {str(e)}"
        errors.append(error_msg)
        logger.error(error_msg)

    return generated_files, errors


def generate_general_table(
        images_dir: str,
        database_file: str,
        output_dir: str = "output"
):
    """Генерация общей таблицы всех товаров из БД"""
    generated_files = []
    errors = []

    try:
        data_reader = DataReader(database_file, images_dir)
        excel_generator = ExcelGenerator(output_dir)

        if not data_reader.load_database():
            errors.append("Не удалось загрузить базу данных")
            return generated_files, errors

        # Получаем все товары из базы данных
        all_products = data_reader.get_all_products()
        if not all_products:
            errors.append("База данных пуста или не удалось загрузить товары")
            return generated_files, errors

        suppliers_data = defaultdict(list)

        for product_info in all_products:
            try:
                processed_image = data_reader.process_image(product_info['article'])

                item_data = {
                    'article': product_info['article'],
                    'name': product_info['name'],
                    'price': product_info['price'],
                    'quantity': 1,  # Для общей таблицы ставим количество 1
                    'supplier': product_info['supplier'],
                    'processed_image': processed_image
                }

                suppliers_data[product_info['supplier']].append(item_data)

            except Exception as e:
                error_msg = f"Ошибка обработки товара {product_info.get('article', 'неизвестно')}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        for supplier, items in suppliers_data.items():
            try:
                supplier_data = {
                    'supplier': supplier,
                    'items': items
                }

                file_path = excel_generator.generate_general_table(supplier_data)
                generated_files.append(file_path)

                logger.info(f"Успешно создана общая таблица для {supplier}: {len(items)} позиций")

            except Exception as e:
                error_msg = f"Ошибка генерации общей таблицы для поставщика {supplier}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        logger.info(f"Готово. Всего файлов: {len(generated_files)}, ошибок: {len(errors)}")

    except Exception as e:
        error_msg = f"Фатальная ошибка: {str(e)}"
        errors.append(error_msg)
        logger.error(error_msg)

    return generated_files, errors


def choose_mode():
    """Выбор режима работы программы"""
    print("\n" + "=" * 50)
    print("ГЕНЕРАТОР ТАБЛИЦ ЗАКУПКИ")
    print("=" * 50)
    print("Выберите режим работы:")
    print("1. Общая таблица (все товары из БД)")
    print("2. Таблица закупки по заказу (из JSON)")
    print("3. Графический интерфейс (GUI)")
    print("=" * 50)

    while True:
        try:
            choice = input("\nВведите номер режима (1, 2 или 3): ").strip()
            if choice == "1":
                return "general"
            elif choice == "2":
                return "order"
            elif choice == "3":
                return "gui"
            else:
                print("Ошибка: введите 1, 2 или 3")
        except KeyboardInterrupt:
            print("\n\nПрограмма прервана пользователем")
            exit(0)


def main():
    """Главная функция программы"""
    mode = choose_mode()

    if mode == "gui":
        print("\n🖥️  Запуск графического интерфейса...")
        try:
            from UI import main as gui_main
            gui_main()
        except ImportError:
            print("❌ Ошибка: не найден модуль UI.py")
            print("Убедитесь, что файл UI.py находится в той же папке")
            input("Нажмите Enter для выхода...")
        except Exception as e:
            print(f"❌ Ошибка запуска GUI: {e}")
            input("Нажмите Enter для выхода...")
        return

    # Настройки по умолчанию для консольных режимов
    images_dir = "data/images"
    database_file = "data/table/database.xlsx"
    output_dir = "output"

    if mode == "general":
        print(f"\n📊 Запуск режима: Общая таблица")
        print(f"База данных: {database_file}")
        print(f"Папка с изображениями: {images_dir}")
        print(f"Выходная папка: {output_dir}")
        print("\nГенерация общих таблиц...")

        files, errors = generate_general_table(
            images_dir=images_dir,
            database_file=database_file,
            output_dir=output_dir
        )

    elif mode == "order":
        print(f"\n🛒 Запуск режима: Таблица закупки по заказу")

        # JSON с заказом (можно вынести в отдельный файл или сделать ввод)
        order = {
            "vl-cronier-ployka-cr-2018": 10
        }

        print(f"База данных: {database_file}")
        print(f"Папка с изображениями: {images_dir}")
        print(f"Выходная папка: {output_dir}")
        print(f"Количество позиций в заказе: {len(order)}")
        print("\nГенерация таблиц закупки...")

        files, errors = generate_purchase_tables(
            images_dir=images_dir,
            database_file=database_file,
            order_dict=order,
            output_dir=output_dir
        )

    # Вывод результатов для консольных режимов
    print(f"\n{'=' * 50}")
    print("РЕЗУЛЬТАТЫ ГЕНЕРАЦИИ")
    print(f"{'=' * 50}")

    if files:
        print(f"✅ Успешно создано файлов: {len(files)}")
        for i, file_path in enumerate(files, 1):
            print(f"   {i}. {Path(file_path).name}")
    else:
        print("❌ Файлы не созданы")

    if errors:
        print(f"\n⚠️  Обнаружено ошибок: {len(errors)}")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
    else:
        print("\n✅ Ошибок не обнаружено")

    print(f"\n{'=' * 50}")
    print("Программа завершена")
    input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()