import os
from glpi_api import GLPI
from dotenv import load_dotenv

load_dotenv()

# GLPI API configuration
base_url = os.getenv("BASE_URL")
app_token = os.getenv("APP_TOKEN")
user_token = os.getenv("USER_TOKEN")

glpi_connect = GLPI(url=base_url, apptoken=app_token, auth=user_token)


def initialize_equipment_data():
    return {
        'username': None,
        'type': None,
        'pc': [],
        'laptops': [],
        'bags': [],
        'chargers': [],
        'web': [],
        'usb_key': [],
        'headset': [],
        'monitors': [],
        'mouse': [],
        'keyboard': [],
        'dock_station': [],
        'external_hdd': [],
        'external_cd': [],
        'ups': [],
        'usb': [],
    }


# получение id пользователя
def get_user_id_by_username(username):
    users = glpi_connect.get_all_items(itemtype="User", range={"0-1000"})
    found_users = [user for user in users if user['name'] == username]
    if found_users:
        return found_users[0]['id']
    return None


def get_user_items(username):
    equipment_data = initialize_equipment_data()

    peripheral_mapping = {
        1: 'keyboard',
        2: 'mouse',
        3: 'bags',
        4: 'dock_station',
        5: 'external_hdd',
        6: 'usb_key',
        7: 'headset',
        8: 'external_cd',
        9: 'ups',
        10: 'web',
        11: 'chargers',
        12: 'usb'
    }

    try:
        username = username.strip()
        user_id = get_user_id_by_username(username)

        if user_id:
            equipment_data['username'] = username

            all_computers = glpi_connect.get_all_items(itemtype="Computer", range={"0-1500"})
            monitors = glpi_connect.get_all_items(itemtype="Monitor", range={"0-500"})
            all_peripherals = glpi_connect.get_all_items(itemtype="Peripheral", range={"0-2500"})

            for computer in all_computers:
                if computer['name'].startswith((os.getenv("PC_MASK"), os.getenv("NB_MASK"))) and computer[
                    'users_id'] == user_id:
                    if computer['name'].startswith(os.getenv("PC_MASK")):
                        equipment_data['pc'].append(computer['name'])
                    elif computer['name'].startswith(os.getenv("NB_MASK")):
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
                # print(response)
            else:
                print(f"No assets found for user '{username}'.")
        else:
            print(f"No user found with the username '{username}'.")

        return equipment_data

    except Exception as e:
        print(f"GLPI API error: {str(e)}")


'''
проверяет, существует ли оборудование в GLPI
может быть несколько случаев:
1) полное совпадение поиского запроса с именем, контактом, ид пользователя - проверка не нужна, выполняается ранее
2) совпадение по имени и контакту
3) совпадение по имени и ид пользователя - проверка не нужна, выполняается ранее
4) совпадение только по имени оборудования
5) отсутствие оборудование и его добавление.
# При таком запросе возвращает "имя оборудование + (копия)", нужен фильтр
'''


def check_equipment(equipment_type, username, equipment_name, peripheral_type):
    if equipment_type not in ['Computer', 'Monitor', 'Peripheral']:
        print(f"Invalid equipment type: {equipment_type}")
        return None

    search_params = {'name': equipment_name, 'contact': username}
    equipment = glpi_connect.get_all_items(equipment_type, searchText=search_params, range={"0-1500"})
    deleted_equipment = glpi_connect.get_all_items(equipment_type, searchText=search_params, range={"0-1500"}, is_deleted=True)

    if equipment:
        print(f"{equipment_type} '{equipment_name}' already exists with correct contact in GLPI.")
        return equipment[0]['id']
    elif deleted_equipment:
        print(f"{equipment_type} '{equipment_name}' already exists with correct contact in deleted items in GLPI. Restoring...")
        glpi_connect.update(equipment_type, {'id': deleted_equipment[0]['id'],
                                             'comment': 'bot: восстановлен из удаленных, был у ' + username,
                                             'is_deleted': '0'})
        return deleted_equipment[0]['id']

    search_params = {'name': equipment_name}
    equipment = glpi_connect.get_all_items(equipment_type, searchText=search_params, range={"0-1500"})
    deleted_equipment = glpi_connect.get_all_items(equipment_type, searchText=search_params, range={"0-1500"}, is_deleted=True)

    if equipment:
        print(f"{equipment_type} '{equipment_name}' already exists in GLPI.")
        return equipment[0]['id']
    elif deleted_equipment:
        print(f"{equipment_type} '{equipment_name}' already exists in deleted items in GLPI.")
        glpi_connect.update(equipment_type, {'id': deleted_equipment[0]['id'],
                                             'comment': 'bot: восстановлен из удаленных, был у ' + username,
                                             'is_deleted': '0'})
        return deleted_equipment[0]['id']

    if equipment_type == 'Peripheral' and peripheral_type is not None:
        res = glpi_connect.add(equipment_type, {'name': equipment_name, 'contact': f"{username}" + os.getenv("DOMAIN"),
                                                'comment': 'bot: добавлен как периферия',
                                                'peripheraltypes_id': peripheral_type,
                                                'entities_id': 0})
        print(f"{equipment_type} '{equipment_name}' peripheral added to GLPI.")
        return res[0]['id']
    else:
        res = glpi_connect.add(equipment_type, {'name': equipment_name, 'contact': f"{username}" + os.getenv("DOMAIN"),
                                                'comment': 'bot: добавлен', 'entities_id': 0})
        print(f"{equipment_type} '{equipment_name}' added to GLPI.")
        return res[0]['id']


def check_equipment_unlink(equipment_type, username, equipment_name, peripheral_type):
    if equipment_type not in ['Computer', 'Monitor', 'Peripheral']:
        print(f"Invalid equipment type: {equipment_type}")
        return None

    search_params = {'name': equipment_name, 'contact': username, 'users_id': get_user_id_by_username(username)}
    equipment = glpi_connect.get_all_items(equipment_type, searchText=search_params, range={"0-1500"})

    for item in equipment:
        print(f"{equipment_type} '{equipment_name}' already exists in user in GLPI.")
        return item['id']


# привязывает оборудование к пользователю
# через поля контактое лицо и Пользователь
# link_equipment(glpi_equipment_type, username, equipment_name)
def link_equipment(equipment_type, username, equipment_name, peripheral_type=None):
    equipment_id = check_equipment(equipment_type, username, equipment_name, peripheral_type)
    if equipment_id:
        if equipment_type == 'Computer':
            glpi_connect.update('Computer', {'id': equipment_id, 'contact': f"{username}" + os.getenv("DOMAIN"),
                                             'users_id': get_user_id_by_username(username)})
        elif equipment_type == 'Monitor':
            glpi_connect.update('Monitor', {'id': equipment_id, 'contact': f"{username}" + os.getenv("DOMAIN"),
                                            'users_id': get_user_id_by_username(username)})
        elif equipment_type == 'Peripheral':
            glpi_connect.update('Peripheral', {'id': equipment_id, 'contact': f"{username}" + os.getenv("DOMAIN"),
                                               'users_id': get_user_id_by_username(username),
                                               'peripheraltypes_id': peripheral_type})
        else:
            print(f"Invalid equipment type: {equipment_type}")
    else:
        print(f"Equipment '{equipment_name}' not found in GLPI, when links!")


def unlink_equipment(equipment_type, username, equipment_name, peripheral_type=None):
    equipment_id = check_equipment_unlink(equipment_type, username, equipment_name, peripheral_type)

    if equipment_id:
        if equipment_type == 'Computer':
            glpi_connect.update('Computer', {'id': equipment_id, 'contact': '', 'users_id': '0',
                                             'comment': 'bot: откреплен от ' + username})
        elif equipment_type == 'Monitor':
            glpi_connect.update('Monitor', {'id': equipment_id, 'contact': '', 'users_id': '0',
                                            'comment': 'bot: откреплен от ' + username})
        elif equipment_type == 'Peripheral':
            glpi_connect.update('Peripheral', {'id': equipment_id, 'contact': '', 'users_id': '0',
                                               'comment': 'bot: откреплен от ' + username})
        else:
            print(f"Invalid equipment type: {equipment_type}")
    else:
        print(f"Equipment '{equipment_name}' not found in GLPI, when unlinks!")


def update_equipment(missing_items):
    username = missing_items['username']
    type = missing_items['type']

    equipment_types = {
        'pc': 'Computer',
        'laptops': 'Computer',
        'monitors': 'Monitor',
        'bags': 'Peripheral',
        'chargers': 'Peripheral',
        'web': 'Peripheral',
        'usb_key': 'Peripheral',
        'headset': 'Peripheral',
        'mouse': 'Peripheral',
        'keyboard': 'Peripheral',
        'dock_station': 'Peripheral',
        'external_hdd': 'Peripheral',
        'external_cd': 'Peripheral',
        'ups': 'Peripheral',
        'usb': 'Peripheral'
    }

    peripheral_mapping = {
        'keyboard': 1,
        'mouse': 2,
        'bags': 3,
        'dock_station': 4,
        'external_hdd': 5,
        'usb_key': 6,
        'headset': 7,
        'external_cd': 8,
        'ups': 9,
        'web': 10,
        'chargers': 11,
        'usb': 12,
    }

    if type == 1:
        for equipment_type, glpi_equipment_type in equipment_types.items():
            if missing_items[equipment_type]:
                for equipment_name in missing_items[equipment_type]:
                    if glpi_equipment_type == 'Peripheral':
                        peripheral_type = None
                        for key, value in peripheral_mapping.items():
                            if key in missing_items and missing_items[key] and equipment_name in missing_items[key]:
                                peripheral_type = value
                                break

                        if peripheral_type is not None:
                            link_equipment(glpi_equipment_type, username, equipment_name, peripheral_type)
                        else:
                            print(f"Invalid peripheral type: {equipment_name}")

                    else:
                        link_equipment(glpi_equipment_type, username, equipment_name)
    else:
        for equipment_type, glpi_equipment_type in equipment_types.items():
            if missing_items[equipment_type]:
                for equipment_name in missing_items[equipment_type]:
                    unlink_equipment(glpi_equipment_type, username, equipment_name)
