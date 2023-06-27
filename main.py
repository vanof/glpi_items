import os
from glpi_api import GLPI
from dotenv import load_dotenv

load_dotenv()

# GLPI API configuration
base_url = os.getenv("BASE_URL")
app_token = os.getenv("APP_TOKEN")
user_token = os.getenv("USER_TOKEN")

glpi = GLPI(url=base_url, apptoken=app_token, auth=user_token)

peripheral_mapping = {
    'keyboard': 1,
    'mouse': 2,
    'bags': 3,
    'dock_station': 4,
    'external_hdd': 5,
    'usb': 6,
    'headset': 7,
    'external_cd': 8,
    'ups': 9,
    'web': 10,
    'chargers': 11
}


# получение id пользователя
# нужна функция наоборот
def get_user_id_by_username(username):
    users = glpi.get_all_items(itemtype="User")
    found_users = [user for user in users if user['name'] == username]
    if found_users:
        return found_users[0]['id']
    return None


# проверяет, существует ли комп в glpi и добавляет его
# возвращает id компа
def check_computer(computer_name):
    computer = glpi.get_all_items('Computer', searchText={'name':computer_name}, range={"0-1500"})
    deleted_computer = glpi.get_all_items('Computer', searchText={'name':computer_name}, range={"0-1500"}, is_deleted=True)
    # не найден пк
    # if computer == 0 and deleted_computer == 0:

    if deleted_computer:
        # добавить проверку на дубли в deleted
        print(f"Computer '{computer_name}' already exists in deleted in GLPI.")

        #print(deleted_computer[0]['id'])
        #print(deleted_computer[0]['name'])
        #print(deleted_computer[0]['is_deleted'])
        glpi.update('Computer', {'id': deleted_computer[0]['id'], 'comment': 'bot: восстановлен из удаленных, был у '+deleted_computer[0]['contact'], 'is_deleted': '0'})
        #print(f"Computer '{computer_name}' восстановлен")
        return deleted_computer[0]['id']

    if computer:
        print(f"Computer '{computer_name}' already exists in GLPI.")
        # возможно надо перенести в другую функцию
        glpi.update('Computer', {'id': computer[0]['id'], 'comment': 'bot: обновлен, был у ' + computer[0]['contact']})
        return computer[0]['id']

    glpi.add('Computer', {'name': computer_name, 'comment': 'bot: добавлен', 'entities_id': 0})
    print(f"Computer '{computer_name}' added to GLPI.")
    computer = glpi.get_all_items('Computer', searchText={'name': computer_name}, range={"0-1500"})
    return computer[0]['id']


def check_equipment(equipment_type, equipment_name, username):
    if equipment_type not in ['Computer', 'Monitor', 'Peripheral']:
        print(f"Invalid equipment type: {equipment_type}")
        return None

    search_params = {'name': equipment_name}
    equipment = glpi.get_all_items(equipment_type, searchText=search_params, range={"0-1500"})

    for item in equipment:
        if item['contact'] == f"{username}"+os.getenv("DOMAIN"):
            print(f"{equipment_type} '{equipment_name}' already exists in user in GLPI.")
            return item['id']

    deleted_equipment = glpi.get_all_items(equipment_type, searchText=search_params, range={"0-1500"}, is_deleted=True)
    if deleted_equipment:
        print(f"{equipment_type} '{equipment_name}' already exists in deleted in GLPI.")
        glpi.update(equipment_type, {'id': deleted_equipment[0]['id'], 'comment': 'bot: восстановлен из удаленных, был у ' + deleted_equipment[0]['contact'], 'is_deleted': '0'})
        return deleted_equipment[0]['id']

    glpi.add(equipment_type, {'name': equipment_name, 'contact': f"{username}"+os.getenv("DOMAIN"), 'comment': 'bot: добавлен', 'entities_id': 0})
    print(f"{equipment_type} '{equipment_name}' added to GLPI.")
    equipment = glpi.get_all_items(equipment_type, searchText=search_params, range={"0-500"})
    return equipment[0]['id']

    glpi.add(equipment_type, {'name': equipment_name, 'contact': f"{username}" + os.getenv("DOMAIN"), 'comment': 'bot: добавлен', 'entities_id': 0})
    print(f"{equipment_type} '{equipment_name}' added to GLPI.")
    equipment = glpi.get_all_items(equipment_type, searchText=search_params, range={"0-500"})
    return equipment[0]['id']


def link_equipment(equipment_type, username, equipment_name):
    equipment_id = check_equipment(equipment_type, equipment_name, username)

    if equipment_id:
        if equipment_type == 'Computer':
            glpi.update('Computer', {'id': equipment_id, 'contact': f"{username}"+os.getenv("DOMAIN"), 'users_id': get_user_id_by_username(username)})
        elif equipment_type == 'Monitor':
            glpi.update('Monitor', {'id': equipment_id, 'contact': f"{username}"+os.getenv("DOMAIN"), 'users_id': get_user_id_by_username(username)})
        elif equipment_type == 'Peripheral':
            peripheraltypes_id = glpi.get_item('Peripheral', equipment_id).get('peripheraltypes_id')
            #print(glpi.get_item('Peripheral', equipment_id))
            #print(peripheraltypes_id)
            glpi.update('Peripheral', {'id': equipment_id, 'contact': f"{username}"+os.getenv("DOMAIN"), 'users_id': get_user_id_by_username(username), 'peripheraltypes_id': peripheraltypes_id})
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
        'usb': 'Peripheral',
        'headset': 'Peripheral',
        'mouse': 'Peripheral',
        'keyboard': 'Peripheral',
        'dock_station': 'Peripheral',
        'external_hdd': 'Peripheral',
        'external_cd': 'Peripheral',
        'ups': 'Peripheral'
    }

    for equipment_type, glpi_equipment_type in equipment_types.items():
        if missing_items[equipment_type]:
            for equipment_name in missing_items[equipment_type]:
                link_equipment(glpi_equipment_type, username, equipment_name)


