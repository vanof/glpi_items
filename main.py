from glpi_api import GLPI
import re
from tabulate import tabulate
import os
from dotenv import load_dotenv

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


# не используется, шаблон данных
def get_user_items(username):
    equipment_data = {
        'username': None,
        'pc': [],
        'laptops': [],
        'bags': [],
        'chargers': [],
        'web': [],
        'usb': [],
        'headphones': None,
        'monitors': [],
        'mouse': None,
        'keyboard': None
    }


# прототип для тестирования API
def add_computer_to_glpi(glpi):
    computer_name = 'pc-apx-004'

    # Check if the computer already exists
    existing_computers = glpi.get_all_items(itemtype='Computer', search={'contact': 'pc-vdi-110'}, range={"0-500"})
    print(existing_computers)
    if existing_computers:
        #print(f"Computer '{computer_name}' already exists in GLPI.")
        return

    # Computer data
    computer_data = {'name': computer_name, 'entities_id': 0}

    # Add the computer to GLPI
    glpi.add('Computer', computer_data)
    #print(f"Computer '{computer_name}' added to GLPI.")


def get_all_peripheral():
    peripheral_types = glpi.get_all_items('Peripheral', range={"0-500"})
    # Prepare the table data
    table = []
    for index, item in enumerate(peripheral_types, start=1):
        table_row = [
            index,
            item['id'],
            item['name'],
            item['peripheraltypes_id'],
            item['contact']
        ]
        table.append(table_row)

    # Print the filtered data in a table format
    headers = ['Position', 'id', 'name', 'peripheraltypes_id', 'contact']
    print(tabulate(table, headers, tablefmt='grid'))


def get_all_computers():
    all_computers = glpi.get_all_items('Computer', searchText={'name':'pc-vdi-116'}, range={"0-500"}) #is_deleted=True
    # Prepare the table data
    table = []
    for index, item in enumerate(all_computers, start=1):
        table_row = [
            index,
            item['id'],
            item['name'],
            item['contact']
        ]
        table.append(table_row)

    # Print the filtered data in a table format
    headers = ['Position', 'id', 'name', 'contact']
    print(tabulate(table, headers, tablefmt='grid'))


def get_computer(name):
    computer = glpi.get_all_items('Computer', searchText={'name':name}, range={"0-1500"})
    deleted_computer = glpi.get_all_items('Computer', searchText={'name':name}, range={"0-1500"}, is_deleted=True)
    if deleted_computer:
        computer = deleted_computer
    # Prepare the table data
    table = []
    for index, item in enumerate(computer, start=1):
        table_row = [
            index,
            item['id'],
            item['name'],
            item['contact'],
            item['is_deleted']
        ]
        table.append(table_row)

    # Print the filtered data in a table format
    headers = ['Position', 'id', 'name', 'contact', 'is_deleted']
    print(tabulate(table, headers, tablefmt='grid'))

def check_peripheral(peripheral_name):
    peripheral = glpi.get_all_items('Peripheral', searchText={'name':peripheral_name}, range={"0-500"})
    deleted_peripheral = glpi.get_all_items('Peripheral', searchText={'name':peripheral_name}, range={"0-500"}, is_deleted=True)
    # не найден пк
    # if computer == 0 and deleted_computer == 0:

    if deleted_peripheral:
        # добавить проверку на дубли в deleted
        print(f"peripheral '{peripheral_name}' already exists in deleted in GLPI.")

        glpi.update('Peripheral', {'id': deleted_peripheral[0]['id'], 'comment': 'bot: восстановлен из удаленных, был у '+deleted_peripheral[0]['contact'], 'is_deleted': '0'})
        return deleted_peripheral[0]['id']

    if peripheral:
        print(f"peripheral '{peripheral_name}' already exists in GLPI.")
        # возможно надо перенести в другую функцию
        #glpi.update('Peripheral', {'id': peripheral[0]['id'], 'comment': 'bot: обновлен, был у ' + peripheral[0]['contact']})
        glpi.update('Peripheral', {'id': peripheral[0]['id'], 'comment': 'bot: обновлен'})
        return peripheral[0]['id']

    glpi.add('Peripheral', {'name': peripheral_name, 'comment': 'bot: добавлен', 'entities_id': 0})
    print(f"peripheral '{peripheral_name}' added to GLPI.")
    peripheral = glpi.get_all_items('Peripheral', searchText={'name': peripheral_name}, range={"0-500"})
    return peripheral[0]['id']


def link_peripheral_to_user(username, peripheral_name):
    # добавить проверку не привязан  к другому пользователю или к этому.
    glpi.update('Peripheral', {'id': check_peripheral(peripheral_name), 'contact': username + '@ESSDEV', 'users_id': get_user_id_by_username(username)})


def check_equipment(equipment_type, equipment_name, username):
    if equipment_type not in ['Computer', 'Monitor', 'Peripheral']:
        print(f"Invalid equipment type: {equipment_type}")
        return None

    search_params = {'name': equipment_name}
    equipment = glpi.get_all_items(equipment_type, searchText=search_params, range={"0-500"})

    for item in equipment:
        if item['contact'] == f"{username}@ESSDEV":
            print(f"{equipment_type} '{equipment_name}' already exists in GLPI.")
            return item['id']

    glpi.add(equipment_type, {'name': equipment_name, 'contact': f"{username}@ESSDEV", 'comment': 'bot: добавлен', 'entities_id': 0})
    print(f"{equipment_type} '{equipment_name}' added to GLPI.")
    equipment = glpi.get_all_items(equipment_type, searchText=search_params, range={"0-500"})
    return equipment[0]['id']


def link_equipment(equipment_type, username, equipment_name):
    equipment_id = check_equipment(equipment_type, equipment_name, username)
    if equipment_id:
        if equipment_type == 'Computer':
            glpi.update('Computer', {'id': equipment_id, 'contact': f"{username}@ESSDEV", 'users_id': get_user_id_by_username(username)})
        elif equipment_type == 'Monitor':
            glpi.update('Monitor', {'id': equipment_id, 'contact': f"{username}@ESSDEV", 'users_id': get_user_id_by_username(username)})
        elif equipment_type == 'Peripheral':
            glpi.update('Peripheral', {'id': equipment_id, 'contact': f"{username}@ESSDEV", 'users_id': get_user_id_by_username(username)})
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
                # Move the equipment_id check inside the loop


