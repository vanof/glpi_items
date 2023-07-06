import re
import glpi
import os
import logging
from dotenv import load_dotenv
from deepdiff import DeepDiff

load_dotenv('env.env')

# для локального тестирования
# input_message_1 = os.getenv("INPUT_1")
# input_message_2 = os.getenv("INPUT_2")


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

    return equipment_name


def sortr(dict):
    for key in dict:
        if isinstance(dict[key], list):
            if all(isinstance(item, str) for item in dict[key]):
                dict[key].sort()
            else:
                dict[key].sort(key=lambda x: str(x))
    return dict


def compare_equipment_data(parsed_equipment, user_equipment):
    missing_items = glpi.initialize_equipment_data()
    missing_items['username'] = parsed_equipment['username']
    missing_items['type'] = parsed_equipment['type']
    # keys_to_skip = ['username', 'type']
    diff = DeepDiff(sortr(parsed_equipment), sortr(user_equipment))
    item_removed = diff.get('iterable_item_removed', {})
    field_mapping = {
        "root['headset']": 'headset',
        "root['monitors']": 'monitors',
        "root['pc']": 'pc',
        "root['laptops']": 'laptops',
        "root['bags']": 'bags',
        "root['chargers']": 'chargers',
        "root['web']": 'web',
        "root['usb_key']": 'usb_key',
        "root['mouse']": 'mouse',
        "root['keyboard']": 'keyboard',
        "root['dock_station']": 'dock_station',
        "root['external_hdd']": 'external_hdd',
        "root['external_cd']": 'external_cd',
        "root['ups']": 'ups',
        "root['usb']": 'usb',
        "root['printers']": 'printers'
    }

    for key, value in item_removed.items():
        for prefix, field in field_mapping.items():
            if key.startswith(prefix):
                missing_items[field].append(value)
                break

    return missing_items

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
        missing_items = compare_equipment_data(parsed_equipment, user_equipment)
        log_print("не хватает:")
        log_print(missing_items)

        # Обновление оборудования
        glpi.update_equipment(missing_items)

        user_equipment = glpi.get_user_items(username)
        log_print("после обновления:")
        log_print(user_equipment)
        log_print("==================================================================================================================================================================================")
