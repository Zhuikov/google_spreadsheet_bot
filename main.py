import google_tables
from pprint import pprint


def main():

    tables_interface = google_tables.TableInterface("client_secrets.json")
    # spreadsheet = tables_interface.create_spreadsheet("SpreadSheetAnotherDir", "new_folder2", "anotherList")
    list = tables_interface.get_spreadsheets("new_folder2")
    pprint(list)
    pprint(tables_interface.del_spreadsheet("new_folder2", "SpreadSheetAnotherDir"))
    # list = tables_interface.get_spreadsheets("new_folder2")
    # pprint(list)


main()
