import google_tables


def main():

    tables_interface = google_tables.TableInterface("client_secrets.json")
    list1 = tables_interface.create_spreadsheet("NewSpreadSheet", None, "ListList1")


main()
