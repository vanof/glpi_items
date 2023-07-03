import re
import glpi
import os
import logging
from dotenv import load_dotenv

load_dotenv('env.env')

# для локального тестирования
#input_message_1 = os.getenv("INPUT_1")
#input_message_2 = os.getenv("INPUT_2")


def log_print(*args, **kwargs):
    message = ' '.join(map(str, args))
    logging.info(f'{message}')
    print(message, **kwargs)


def capitalize_name(name):
    capitalized_parts = [part.capitalize() for part in name.split(".")]
    return ".".join(capitalized_parts)


def parse_equipment_message(message_text):
    equipment_data = glpi.initialize_equipment_data()

    # преобразование-обрезка полей
    field_patterns = {
        'Системный блок': ('pc', True),
        'Ноутбук': ('laptops', True),
        'Сумка': ('bags', False),
        'Зарядное устройство': ('chargers', False),
        'Веб-камера': ('web', False),
        'USB ключ': ('usb_key', False),
        'Гарнитура': ('headset', False),
        'Монитор': ('monitors', True),
        'Мышка': ('mouse', False),
        'Клавиатура': ('keyboard', False),
        'Док-станция': ('dock_station', False),
        'Внешний диск': ('external_hdd', False),
        'CD-ROM': ('external_cd', False),
        'ИБП': ('ups', False),
        'USB концентратор': ('usb', False),
        'Принтер': ('printers', False),
    }

    username_start_index = message_text.find('"') + 1
    username_end_index = message_text.find('"', username_start_index)
    username = message_text[username_start_index:username_end_index]
    equipment_data['username'] = capitalize_name(username.strip())

    if 'получил' in message_text or 'выдано' in message_text:
        equipment_data['type'] = 1
    elif 'сдал' in message_text:
        equipment_data['type'] = 0

    for field, (data_key, requires_transform) in field_patterns.items():
        pattern = rf'{field} (.+)'
        matches = re.findall(pattern, message_text)
        if matches:
            if requires_transform:
                cleaned_matches = [match.strip() for match in matches]
            else:
                cleaned_matches = [f'{field} {match.strip()}' for match in matches]
            equipment_data[data_key] = cleaned_matches

    if 'monitors' in equipment_data:
        monitors = equipment_data['monitors']
        equipment_data['monitors'] = [extract_monitor_brand(monitor) for monitor in monitors]

    return equipment_data


# проверка для benq
def extract_monitor_brand(equipment_name):
    brand_match = re.search(r'Benq', equipment_name)
    if brand_match:
        brand_string = brand_match.group(0)
        brand_string = brand_string[:-1] + brand_string[-1:].upper()

        content_in_parentheses = re.search(r'\((.*?)\)', equipment_name)
        if content_in_parentheses:
            additional_info = content_in_parentheses.group(1)
            additional_info = additional_info[:-2]
            brand_string += ' ' + additional_info.strip()

        return brand_string

    return ''


def compare_equipment_data(user_equipment, parsed_equipment):
    equipment_data = glpi.initialize_equipment_data()
    missing_items = {}

    # Compare each item type in parsed_equipment
    for item_type, item_list in parsed_equipment.items():
        if isinstance(item_list, int):
            if item_type == 'type':
                equipment_data['type'] = item_list
            continue  # Пропустить поле, если тип данных является int
        if item_type not in user_equipment:
            missing_items[item_type] = item_list
        else:
            user_items = user_equipment.get(item_type)
            parsed_items = item_list if item_list is not None else []

            if user_items is not None:
                missing = [item for item in parsed_items if item not in user_items]
                if missing:
                    missing_items[item_type] = missing

            if isinstance(parsed_items, list) and isinstance(user_items, list):
                parsed_dict = {}
                user_dict = {}
                for item in parsed_items:
                    parsed_dict[item] = parsed_dict.get(item, 0) + 1
                for item in user_items:
                    user_dict[item] = user_dict.get(item, 0) + 1

                missing_items_list = [
                    item for item, count in parsed_dict.items() if item not in user_dict or user_dict[item] < count
                ]
                if missing_items_list:
                    missing_items[item_type] = missing_items_list

    equipment_data['username'] = user_equipment.get('username')
    equipment_data.update(missing_items)

    return equipment_data


def message_handler(input_message):
    # Парсинг сообщения
    parsed_equipment = parse_equipment_message(input_message)
    username = parsed_equipment['username']
    type = parsed_equipment['type']
    log_print("==================================================================================================================================================================================")
    log_print("парсинг сообщения:")
    log_print(parsed_equipment)

    # Получение данных пользователя
    user_equipment = glpi.get_user_items(username)
    log_print("У пользователя:")
    log_print(user_equipment)

    if type == None:
        # Удаление
        glpi.update_equipment(parsed_equipment)

        user_equipment = glpi.get_user_items(username)
        log_print("после удаления:")
        log_print(user_equipment)
        log_print("==================================================================================================================================================================================")
    else:
        # Сравнение данных и вывод разницы
        missing_items = compare_equipment_data(user_equipment, parsed_equipment)
        log_print("не хватает:")
        log_print(missing_items)

        # Обновление оборудования
        glpi.update_equipment(missing_items)

        user_equipment = glpi.get_user_items(username)
        log_print("после обновления:")
        log_print(user_equipment)
        log_print("==================================================================================================================================================================================")
