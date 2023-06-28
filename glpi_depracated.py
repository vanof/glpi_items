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

glpi = GLPI(url=base_url, apptoken=app_token, auth=user_token)


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
            item['users_id'],
            item['is_deleted'],
            item['comment']
        ]
        table.append(table_row)

    # Print the filtered data in a table format
    headers = ['Position', 'id', 'name', 'contact', 'user_id', 'is_deleted', 'comment']
    print(tabulate(table, headers, tablefmt='grid'))

get_computer('pc-apx-004')

# прототип для тестирования API
def add_computer_to_glpi(glpi):
    computer_name = 'pc-apx-004'

    # Check if the computer already exists
    # добавить в .env маски имен
    existing_computers = glpi.get_all_items(itemtype='Computer', search={'contact': 'pc-vdi-110'}, range={"0-500"})
    print(existing_computers)
    if existing_computers:
        # print(f"Computer '{computer_name}' already exists in GLPI.")
        return

    # Computer data
    computer_data = {'name': computer_name, 'entities_id': 0}

    # Add the computer to GLPI
    glpi.add('Computer', computer_data)
    # print(f"Computer '{computer_name}' added to GLPI.")


'''
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
'''


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
