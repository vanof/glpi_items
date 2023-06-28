import re
import glpi
import os
from dotenv import load_dotenv

load_dotenv()

DEBUG = True

input_message_1 = os.getenv("INPUT_1")
input_message_2 = os.getenv("INPUT_2")


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

    if 'получил' in message_text:
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

    return equipment_data


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


if DEBUG:
    # Парсинг сообщения
    parsed_equipment = parse_equipment_message(input_message_2)
    username = parsed_equipment['username']
    print("парсинг сообщения")
    print(parsed_equipment)

    # Получение данных пользователя
    user_equipment = glpi.get_user_items(username)
    print("У пользователя:")
    print(user_equipment)


    # Сравнение данных и вывод разницы
    missing_items = compare_equipment_data(user_equipment, parsed_equipment)
    print("не хватает:")
    print(missing_items)

    # Обновление оборудования
    #glpi.update_equipment(missing_items)

    glpi.update_equipment(parsed_equipment)

    user_equipment = glpi.get_user_items(username)
    print("после обновления:")
    print(user_equipment)




