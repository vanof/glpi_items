import os
from glpi_api import GLPI
from dotenv import load_dotenv

DEBUG = True

load_dotenv()

# GLPI API configuration
base_url = os.getenv("BASE_URL")
app_token = os.getenv("APP_TOKEN")
user_token = os.getenv("USER_TOKEN")

glpi = GLPI(url=base_url, apptoken=app_token, auth=user_token)


# получение id пользователя
# нужна функция наоборот
def get_user_id_by_username(username):
    users = glpi.get_all_items(itemtype="User")
    found_users = [user for user in users if user['name'] == username]
    if found_users:
        return found_users[0]['id']
    return None


# проверяет, существует ли оборудование в GLPI
# восстанавливает из удаленных
# добавляет если не существует
def check_equipment(equipment_type, equipment_name, username, peripheral_type):
    if equipment_type not in ['Computer', 'Monitor', 'Peripheral']:
        print(f"Invalid equipment type: {equipment_type}")
        return None
    print(equipment_name)
    search_params = {'name': equipment_name}
    equipment = glpi.get_all_items(equipment_type, searchText=search_params, range={"0-1500"})
    print((equipment))
    for item in equipment:
        if item['contact'] == f"{username}"+os.getenv("DOMAIN"):
            print(f"{equipment_type} '{equipment_name}' already exists in user in GLPI.")
            return item['id']

    deleted_equipment = glpi.get_all_items(equipment_type, searchText=search_params, range={"0-1500"}, is_deleted=True)
    if deleted_equipment:
        print(f"{equipment_type} '{equipment_name}' already exists in deleted in GLPI.")
        glpi.update(equipment_type, {'id': deleted_equipment[0]['id'], 'comment': 'bot: восстановлен из удаленных, был у ' + deleted_equipment[0]['contact'], 'is_deleted': '0'})
        return deleted_equipment[0]['id']

    # вот тут нужно добавление различных параметров
    if equipment_type == 'Peripheral':
        if peripheral_type is not None:
            glpi.add(equipment_type, {'name': equipment_name, 'contact': f"{username}" + os.getenv("DOMAIN"),
                                      'comment': 'bot: добавлен как периферия',
                                      'peripheraltypes_id': peripheral_type,
                                      'entities_id': 0})
            print(f"{equipment_type} '{equipment_name}' added to peripheral GLPI.")
        #return item['id']

    glpi.add(equipment_type,
             {'name': equipment_name, 'contact': f"{username}" + os.getenv("DOMAIN"), 'comment': 'bot: добавлен',
              'entities_id': 0})
    print(f"{equipment_type} '{equipment_name}' added to GLPI.")
    equipment = glpi.get_all_items(equipment_type, searchText=search_params, range={"0-500"})
    return equipment[0]['id']


# привязывает оборудование к пользователю
# через поля контактое лицо и Пользователь
def link_equipment(equipment_type, username, equipment_name, peripheral_type=None):
    equipment_id = check_equipment(equipment_type, equipment_name, username, peripheral_type)

    if equipment_id:
        if equipment_type == 'Computer':
            glpi.update('Computer', {'id': equipment_id, 'contact': f"{username}"+os.getenv("DOMAIN"), 'users_id': get_user_id_by_username(username)})
        elif equipment_type == 'Monitor':
            glpi.update('Monitor', {'id': equipment_id, 'contact': f"{username}"+os.getenv("DOMAIN"), 'users_id': get_user_id_by_username(username)})
        elif equipment_type == 'Peripheral':
            glpi.update('Peripheral', {'id': equipment_id, 'contact': f"{username}"+os.getenv("DOMAIN"), 'users_id': get_user_id_by_username(username), 'peripheraltypes_id': peripheral_type})
        else:
            print(f"Invalid equipment type: {equipment_type}")
    else:
        print(f"Equipment '{equipment_name}' not found in GLPI.")


def add_equipment_to_glpi_user(missing_items):
    username = missing_items['username']
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

    for equipment_type, glpi_equipment_type in equipment_types.items():
        if missing_items[equipment_type]:
            for equipment_name in missing_items[equipment_type]:

                if glpi_equipment_type == 'Peripheral':
                    peripheral_type = None
                    for key, value in peripheral_mapping.items():
                        if key in missing_items and missing_items[key] and equipment_name in missing_items[key]:
                            peripheral_type = value
                            break

                    #if DEBUG:
                    #    print(peripheral_type, "Вызов в add_equipment_to_glpi_user")

                    if peripheral_type is not None:
                        link_equipment(glpi_equipment_type, username, equipment_name, peripheral_type)
                    else:
                        print(f"Invalid peripheral type: {equipment_name}")

                else:
                    link_equipment(glpi_equipment_type, username, equipment_name)