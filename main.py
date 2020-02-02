import google_tables


def main():

    tables_interface = google_tables.TableInterface("client_secret.json")
    list1 = tables_interface.create_spreadsheet("NewSpreadSheet", None, "ListList1", "content-files/style1",
                                        "content-files/grouplist1")


main()
