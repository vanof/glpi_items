import re
import glpi
import os
from dotenv import load_dotenv

load_dotenv('env.env')

input_message_1 = os.getenv("INPUT_1")
input_message_2 = os.getenv("INPUT_2")
input = ''

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
        'Внешний CD-ROM': ('external_cd', False),
        'ИБП': ('ups', False),
        'USB концентратор': ('usb', False)
    }

    username_start_index = message_text.find('"') + 1
    username_end_index = message_text.find('"', username_start_index)
    username = message_text[username_start_index:username_end_index]
    equipment_data['username'] = username.strip()

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
            parsed_items = set(item_list) if item_list is not None else set()

            if user_items is not None:
                user_items = set(user_items)
                missing = list(parsed_items - user_items)
                if missing:
                    missing_items[item_type] = missing

    equipment_data['username'] = user_equipment.get('username')
    equipment_data.update(missing_items)

    return equipment_data

DEBUG = False
if DEBUG:
    Delete = True
    # Парсинг сообщения
    parsed_equipment = parse_equipment_message(input_message_2 if Delete else input_message_1)
    username = parsed_equipment['username']
    print("парсинг сообщения")
    print(parsed_equipment)

    # Получение данных пользователя
    user_equipment = glpi.get_user_items(username)
    print("У пользователя:")
    print(user_equipment)

    if Delete:
        # Удаление
        glpi.update_equipment(parsed_equipment)

        user_equipment = glpi.get_user_items(username)
        print("после удаления:")
        print(user_equipment)
    else:
        # Сравнение данных и вывод разницы
        missing_items = compare_equipment_data(user_equipment, parsed_equipment)
        print("не хватает:")
        print(missing_items)

        # Обновление оборудования
        glpi.update_equipment(compare_equipment_data(user_equipment, parsed_equipment))

        user_equipment = glpi.get_user_items(username)
        print("после обновления:")
        print(user_equipment)
