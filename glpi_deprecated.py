# файл с неиспользуемыми или тестируемыми функциями

from glpi_api import GLPI
from tabulate import tabulate
import os
from dotenv import load_dotenv

load_dotenv()

# GLPI API configuration
base_url = os.getenv("BASE_URL")
app_token = os.getenv("APP_TOKEN")
user_token = os.getenv("USER_TOKEN")

glpi_connect = GLPI(url=base_url, apptoken=app_token, auth=user_token)


def get_user_id_by_username(username):
    users = glpi_connect.get_all_items(itemtype="User", range={"0-1000"})
    found_users = [user for user in users if user['name'] == username]
    if found_users:
        return found_users[0]['id']
    return None


def get_all():
    users = glpi_connect.get_all_items(itemtype="User", range={"0-1000"})
    # Prepare the table data
    table = []
    for index, user in enumerate(users, start=1):
        table_row = [
            index,
            user['id'],
            user['name']
        ]
        table.append(table_row)

    # Print the user data in a table format
    headers = ['Position', 'ID', 'Username']
    print(tabulate(table, headers, tablefmt='grid'))


def get_all_peripheral():
    peripheral_types = glpi_connect.get_all_items('Peripheral', range={"0-500"})
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
    all_computers = glpi_connect.get_all_items('Computer', searchText={'name':'pc-vdi-116'}, range={"0-500"}) #is_deleted=True
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
    computer = glpi_connect.get_all_items('Computer', searchText={'name':name}, range={"0-1500"})
    deleted_computer = glpi_connect.get_all_items('Computer', searchText={'name':name}, range={"0-1500"}, is_deleted=True)
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
            item['users_id'],
            item['is_deleted'],
            item['comment']
        ]
        table.append(table_row)

    # Print the filtered data in a table format
    headers = ['Position', 'id', 'name', 'contact', 'user_id', 'is_deleted', 'comment']
    print(tabulate(table, headers, tablefmt='grid'))


# проверяет, существует ли комп в glpi и добавляет его
# возвращает id компа
def check_computer(computer_name):
    computer = glpi_connect.get_all_items('Computer', searchText={'name':computer_name}, range={"0-1500"})
    deleted_computer = glpi_connect.get_all_items('Computer', searchText={'name':computer_name}, range={"0-1500"}, is_deleted=True)
    # не найден пк
    # if computer == 0 and deleted_computer == 0:

    if deleted_computer:
        # добавить проверку на дубли в deleted
        print(f"Computer '{computer_name}' already exists in deleted in GLPI.")
        #print(deleted_computer[0]['id'])
        #print(deleted_computer[0]['name'])
        #print(deleted_computer[0]['is_deleted'])
        glpi_connect.update('Computer', {'id': deleted_computer[0]['id'], 'comment': 'bot: восстановлен из удаленных, был у '+deleted_computer[0]['contact'], 'is_deleted': '0'})
        #print(f"Computer '{computer_name}' восстановлен")
        return deleted_computer[0]['id']

    if computer:
        print(f"Computer '{computer_name}' already exists in GLPI.")
        # возможно надо перенести в другую функцию
        glpi_connect.update('Computer', {'id': computer[0]['id'], 'comment': 'bot: обновлен, был у ' + computer[0]['contact']})
        return computer[0]['id']

    glpi_connect.add('Computer', {'name': computer_name, 'comment': 'bot: добавлен', 'entities_id': 0})
    print(f"Computer '{computer_name}' added to GLPI.")
    computer = glpi_connect.get_all_items('Computer', searchText={'name': computer_name}, range={"0-1500"})
    return computer[0]['id']


def get_equipment(equipment_name, username):
    search_params = {'name': equipment_name, 'contact': username, 'users_id': get_user_id_by_username(username)} # проверка по имени, имени пользователя, контакту
    computer = glpi_connect.get_all_items('Computer', searchText=search_params, range={"0-1500"})
    deleted_computer = glpi_connect.get_all_items('Computer', searchText=search_params, range={"0-1500"}, is_deleted=True)
    if deleted_computer:
        computer = deleted_computer
        #все тоже самое, но только делаем апдейт из deleted
    # Prepare the table data
    table = []
    for index, item in enumerate(computer, start=1):
        table_row = [
            index,
            item['id'],
            item['name'],
            item['contact'],
            item['users_id'],
            item['is_deleted'],
            item['comment']
        ]
        table.append(table_row)

    # Print the filtered data in a table format
    headers = ['Position', 'id', 'name', 'contact', 'user_id', 'is_deleted', 'comment']
    print(tabulate(table, headers, tablefmt='grid'))

def check_equipment():
    pass

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
            print(f"Invalid equipment type0: {equipment_type}")
    else:
        print(f"Equipment '{equipment_name}' not found in GLPI, when links!")
