import google_tables
from pprint import pprint


def main():

    tables_interface = google_tables.TableInterface("client_secrets.json")
    spreadsheet = tables_interface.create_spreadsheet("AnotherSpreadSheet", "new_folder", "anotherList")
    list = tables_interface.get_spreadsheets("new_folder")
    pprint(list)


main()
