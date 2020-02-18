import google_tables
from pprint import pprint


def main():

    style = google_tables.TableStyle(["1", "2", "3", "4"])

    tables_interface = google_tables.TableInterface("client_secrets.json")
    # tables_interface.create_spreadsheet("try2", "219651041", "New_title", ["1", "2", "3", "4"],
    #                                     ["newname", "new", "wewe", "zeze", "aLast"])
    tables_interface.add_worksheet("1luCAsy00wNJXDJRG5p2ym-QcVWrisnPEnRM1CuDkJD0", "NEWNEWNEW",
                                   style,
                                   ["newname", "new", "wewe", "zeze", "aLast"])
    # pprint(tables_interface.get_spreadsheets("219651041"))
    # tables_interface.add_date_col("219651041", "GoodTable", ["TEST6", "-", "'+", "-", "-", "'+", "'+"])
    # print(tables_interface.get_students_list("219651041", "GoodTable"))


main()
