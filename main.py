import google_tables
from pprint import pprint


def main():

    tables_interface = google_tables.TableInterface("client_secrets.json")
    # spreadsheet = tables_interface.create_spreadsheet("SpreadSheetAnotherDir", "new_folder2", "anotherList")
    # tables_interface.add_date_col("219651041", "GoodTable", ["TEST6", "-", "'+", "-", "-", "'+", "'+"])
    print(tables_interface.get_students_list("219651041", "GoodTable"))


main()
