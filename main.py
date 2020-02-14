import google_tables
from pprint import pprint

class Obj:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def to_string(self):
        return "a = " + str(self.a) + " b = " + str(self.b) + " c = " + str(self.c)


def main():

    mapa = {}
    mapa[1] = Obj(0, 0, 0)
    pprint(mapa[1].to_string())

    mapa[1].a = 1
    mapa[1].b = 2

    pprint(mapa[1].to_string())
    print(mapa[1].c)
    print(mapa[234] is None)
    # tables_interface = google_tables.TableInterface("client_secrets.json")
    # tables_interface.add_date_col("219651041", "GoodTable", ["TEST6", "-", "'+", "-", "-", "'+", "'+"])
    # print(tables_interface.get_students_list("219651041", "GoodTable"))


main()
