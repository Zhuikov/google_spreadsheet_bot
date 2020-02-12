import pygsheets
import datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from re import fullmatch

import google_tables as gt

from pprint import pprint


class TableInterface:

    def __init__(self, credentials):
        self.client = pygsheets.authorize(credentials)
        g_auth = GoogleAuth()

        g_auth.LoadCredentialsFile("drive_creds.json")
        if g_auth.credentials is None:
            g_auth.LocalWebserverAuth()
        elif g_auth.access_token_expired:
            g_auth.Refresh()
        else:
            g_auth.Authorize()
        g_auth.SaveCredentialsFile("drive_creds.json")

        self.drive = GoogleDrive(g_auth)

    # table_style  -- list of table fields
    # group_list -- list of students
    # Returns new spreadsheet's url
    def create_spreadsheet(self, spreadsheet_title, spreadsheet_folder_title, worksheet_title,
                           table_style, group_list):
        print("Table_style in create_ssheet", table_style)
        style = gt.TableStyle(table_style)
        print("style_fields:", style.fields)
        spreadsheet_template = {
            "properties": {
                "title": spreadsheet_title,
                "locale": "ru_RU"
            },
            "sheets": [{
                "properties": {
                    "title": worksheet_title,
                    "gridProperties": {
                        "rowCount": len(group_list) + 1,   # 1 is fields
                        "columnCount": len(style.fields),
                    }
                }
            }]
        }

        spreadsheet_folder_id = self.__get_folder_id(spreadsheet_folder_title)
        print("ID FOLDER =", spreadsheet_folder_id)

        if spreadsheet_folder_id is None:
            spreadsheet_folder_id = self.__create_folder(spreadsheet_folder_title)

        # init table fields and students' names
        spreadsheet = self.client.create(spreadsheet_title, spreadsheet_template, spreadsheet_folder_id)
        spreadsheet.sheet1.update_row(1, [style.fields])
        spreadsheet.sheet1.update_col(1, [group_list], row_offset=1)

        # format students' names column
        first_col = spreadsheet.sheet1.get_col(1, returnas='range')
        first_col.apply_format(gt.CellStyle.student_names_format_cell)

        # format table fields
        # TODO wrap strategy
        first_row = spreadsheet.sheet1.get_row(1, returnas='range')
        first_row.apply_format(gt.CellStyle.fields_format_cell)

        spreadsheet.sheet1.adjust_column_width(0, spreadsheet.sheet1.cols)

        # set format of main table (with marks)
        main_field = spreadsheet.sheet1.get_values(
            (2, 2), (spreadsheet.sheet1.rows, spreadsheet.sheet1.cols), returnas='range',
            include_tailing_empty_rows=True)
        main_field.apply_format(gt.CellStyle.main_table_cell)

        return spreadsheet.url

    def share_table(self, spreadsheet_id, user_mail, role):
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        spreadsheet.share()

    # Returns all spreadsheets {name, link, id} in folder_name directory
    def get_spreadsheets(self, folder_name: str):
        folder_id = self.__get_folder_id(folder_name)

        if folder_name is None or folder_id is None:
            return None

        files = self.drive.ListFile({"q": "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"}) \
            .GetList()

        files_name_id = [{"name": o["title"], "link": o["alternateLink"], "id": o["id"]}
                         for o in filter(lambda elem: elem["parents"][0]["id"] == folder_id, files)]

        return files_name_id

    # Returns list of students first name and second name
    # Students must be in A column
    # If there is no folder_name or spreadsheet_name returns None
    # If there are several spreadsheet_name documents also returns None
    def get_students_list(self, folder_name, spreadsheet_name):
        all_spreadsheet_list = self.get_spreadsheets(folder_name)

        if all_spreadsheet_list is None:
            return None

        spreadsheets_with_name = list(filter(lambda elem: elem["name"] == spreadsheet_name, all_spreadsheet_list))

        if len(spreadsheets_with_name) == 0:
            return None

        if len(spreadsheets_with_name) == 1:
            worksheet = self.client.open_by_key(spreadsheets_with_name[0]["id"]).sheet1
            students_range = worksheet.range("A2:A" + str(worksheet.rows), returnas='cell')
            students_list = [cell.value for cells in students_range for cell in cells]
            return students_list

        if len(spreadsheets_with_name) > 1:
            return None

    # Deletes spreadsheet_name from folder_name directory
    # if there is one spreadsheet with spreadsheet_name in folder_name, returns empty list
    # if there are several spreadsheets with spreadsheet_name then returns them in list {name, link, id}
    # if spreadsheet_name not found in folder_name, returns None
    def del_spreadsheet(self, folder_name: str, spreadsheet_name: str):
        all_spreadsheet_list = self.get_spreadsheets(folder_name)

        if all_spreadsheet_list is None:
            return None

        spreadsheets_with_name = list(filter(lambda elem: elem["name"] == spreadsheet_name, all_spreadsheet_list))

        if len(spreadsheets_with_name) == 0:
            return None

        if len(spreadsheets_with_name) == 1:
            self.client.drive.delete(spreadsheets_with_name[0]["id"])
            return []

        return spreadsheets_with_name

    # Deletes table by spreadsheet_id
    def del_spreadsheet_by_id(self, spreadsheet_id):
        self.client.drive.delete(spreadsheet_id)

    # Creates new column with attendance content
    # content[0] -- col name, content[n] -- attendance of student (+/-)
    def add_date_col(self, folder_name, spreadsheet_name, content):
        all_spreadsheet_list = self.get_spreadsheets(folder_name)

        if all_spreadsheet_list is None:
            return None

        spreadsheets_with_name = list(filter(lambda elem: elem["name"] == spreadsheet_name, all_spreadsheet_list))

        if len(spreadsheets_with_name) == 0:
            return None

        if len(spreadsheets_with_name) == 1:
            spreadsheet_id = spreadsheets_with_name[0]["id"]
            insert_index = self.__find_date_col_index(spreadsheet_id)
            print(insert_index)

            spreadsheet = self.client.open_by_key(spreadsheet_id)
            spreadsheet.sheet1.insert_cols(insert_index, values=content, inherit=True)
            spreadsheet.sheet1.adjust_column_width(insert_index)

            now = datetime.datetime.now()
            pprint(spreadsheet.sheet1.cell(addr=(1, insert_index + 1)))
            added_field_cell = spreadsheet.sheet1.cell((1, insert_index + 1))
            added_field_cell.note = str(now.day) + "." + str(now.month) + "." + str(now.year)

            new_col_content = spreadsheet.sheet1.get_values(
                (2, insert_index + 1), (spreadsheet.sheet1.rows, insert_index + 1), returnas='range',
                include_tailing_empty_rows=True)
            new_col_content.apply_format(gt.CellStyle.main_table_cell)

            return True

        if len(spreadsheets_with_name) > 1:
            return False

    # Returns folder's id if directory consists.
    # Else returns None
    def __get_folder_id(self, folder_name: str):
        if folder_name is None:
            return None

        dirs = self.drive.ListFile({"q": "mimeType='application/vnd.google-apps.folder' and trashed=false"})\
            .GetList()
        dir_titles = [o["title"] for o in dirs]

        if str(folder_name) not in dir_titles:
            return None

        for elem in dirs:
            if elem["title"] == str(folder_name):
                return elem["id"]

    # Returns new folder's id
    def __create_folder(self, folder_name):
        new_dir = self.drive.CreateFile({"title": folder_name, "mimeType": "application/vnd.google-apps.folder"})
        new_dir.Upload()
        return new_dir["id"]

    def __find_date_col_index(self, spreadsheet_id):
        worksheet = self.client.open_by_key(spreadsheet_id).sheet1
        fields = worksheet.get_row(1, returnas='cell')

        index = None
        for i in range(len(fields)):
            if fullmatch("\d{1,2}\.\d{1,2}\.\d{4}", str(fields[i].note)):
                print(str(fields[i].note))
                index = i

        return 1 if index is None else index + 1

