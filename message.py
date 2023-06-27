import re
import main
import os
from dotenv import load_dotenv
from glpi_api import GLPI

load_dotenv()

# GLPI API configuration
base_url = os.getenv("BASE_URL")
app_token = os.getenv("APP_TOKEN")
user_token = os.getenv("USER_TOKEN")

glpi = GLPI(url=base_url, apptoken=app_token, auth=user_token)

input_message_1 = os.getenv("INPUT_1")

input_message_2 = os.getenv("INPUT_2")


# добавить usb концентраторы и debug
def parse_equipment_message(message_text):
    equipment_data = {
        'username': None,
        'pc': [],
        'laptops': [],
        'bags': [],
        'chargers': [],
        'web': [],
        'usb': [],
        'headset': [],
        'monitors': [],
        'mouse': [],
        'keyboard': [],
        'dock_station': [],
        'external_hdd': [],
        'external_cd': [],
        'ups': []
    }

    # преобразование-обрезка полей
    field_patterns = {
        'Системный блок': ('pc', True),
        'Ноутбук': ('laptops', True),
        'Сумка': ('bags', False),
        'Зарядное устройство': ('chargers', False),
        'Веб-камера': ('web', False),
        'USB ключ': ('usb', False),
        'Гарнитура': ('headset', False),
        'Монитор': ('monitors', True),
        'Мышка': ('mouse', False),
        'Клавиатура': ('keyboard', False),
        'Док-станция': ('dock_station', False),
        'Внешний диск': ('external_hdd', False),
        'Внешний CD-ROM': ('external_cd', False),
        'ИБП': ('ups', False)
    }

    username_start_index = message_text.find('"') + 1
    username_end_index = message_text.find('"', username_start_index)
    username = message_text[username_start_index:username_end_index]
    equipment_data['username'] = username.strip()

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


def get_user_id_by_username(username):
    users = glpi.get_all_items(itemtype="User")
    found_users = [user for user in users if user['name'] == username]
    if found_users:
        return found_users[0]['id']
    return None


def get_user_items(username):
    equipment_data = {
        'username': None,
        'pc': [],
        'laptops': [],
        'bags': [],
        'chargers': [],
        'web': [],
        'usb': [],
        'headset': [],
        'monitors': [],
        'mouse': [],
        'keyboard': [],
        'dock_station': [],
        'external_hdd': [],
        'external_cd': [],
        'ups': []
    }

    peripheral_mapping = {
        1: 'keyboard',
        2: 'mouse',
        3: 'bags',
        4: 'dock_station',
        5: 'external_hdd',
        6: 'usb',
        7: 'headset',
        8: 'external_cd',
        9: 'ups',
        10: 'web',
        11: 'chargers'
    }

    try:
        username = username.strip()
        user_id = get_user_id_by_username(username)

        if user_id:
            equipment_data['username'] = username

            all_computers = glpi.get_all_items(itemtype="Computer", range={"0-1500"})
            monitors = glpi.get_all_items(itemtype="Monitor", range={"0-500"})
            all_peripherals = glpi.get_all_items(itemtype="Peripheral", range={"0-2500"})

            for computer in all_computers:
                if computer['name'].startswith(('pc-apx-', 'nb-apx-')) and computer['users_id'] == user_id:
                    if computer['name'].startswith('pc-apx-'):
                        equipment_data['pc'].append(computer['name'])
                    elif computer['name'].startswith('nb-apx-'):
                        equipment_data['laptops'].append(computer['name'])

            user_monitors = [monitor['name'] for monitor in monitors if monitor['users_id'] == user_id]
            equipment_data['monitors'] = user_monitors

            for peripheral in all_peripherals:
                peripheraltypes_id = peripheral['peripheraltypes_id']
                if peripheraltypes_id in peripheral_mapping and peripheral['users_id'] == user_id:
                    key = peripheral_mapping[peripheraltypes_id]
                    equipment_data[key].append(peripheral['name'])

            if equipment_data:
                response = f"User ID: {user_id}\n"
                response += f"Assets for user '{username}':\n{equipment_data}"
                #print(response)
            else:
                print(f"No assets found for user '{username}'.")
        else:
            print(f"No user found with the username '{username}'.")

        return equipment_data

    except Exception as e:
        print(f"GLPI API error: {str(e)}")


def compare_equipment_data(user_equipment, parsed_equipment):
    equipment_data = {
        'username': None,
        'pc': [],
        'laptops': [],
        'bags': [],
        'chargers': [],
        'web': [],
        'usb': [],
        'headset': [],
        'monitors': [],
        'mouse': [],
        'keyboard': [],
        'dock_station': [],
        'external_hdd': [],
        'external_cd': [],
        'ups': []
    }

    missing_items = {}

    # Compare each item type in parsed_equipment
    for item_type, item_list in parsed_equipment.items():
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


# добавление всего оборудования
def add_equipment_to_glpi_user(missing_items):
    if missing_items['pc']:
        main.link_computer_to_user(missing_items['username'], missing_items['pc'][0])
    #else:
    #    print("No computers to add.")

    if missing_items['laptops']:
        main.link_computer_to_user(missing_items['username'], missing_items['laptops'][0])

    if missing_items['monitors']:
        main.link_monitor_to_user(missing_items['username'], missing_items['monitors'][0])

    # print(f"Equipment data added to user '{equipment_data['username']}' in GLPI.")


parsed_equipment = parse_equipment_message(input_message_1)
username = parsed_equipment['username']

# Получение данных пользователя
user_equipment = get_user_items(username)
print("У пользователя:")
print(user_equipment)
#print("парсинг сообщения")
#print(parsed_equipment)
# Сравнение данных и вывод разницы

print("не хватает:")
print(compare_equipment_data(user_equipment, parsed_equipment))

missing_items = compare_equipment_data(user_equipment, parsed_equipment)
#print(missing_items)
main.add_equipment_to_glpi_user(missing_items)

user_equipment = get_user_items(username)
print("после добавления:")
print(user_equipment)

