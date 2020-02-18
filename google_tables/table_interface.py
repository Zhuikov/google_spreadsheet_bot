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
    # Returns new spreadsheet's link and id
    def create_spreadsheet(self, spreadsheet_title, spreadsheet_folder_title, worksheet_title,
                           table_style, group_list):

        style = gt.TableStyle(table_style)
        spreadsheet_template = {
            "properties": {
                "title": spreadsheet_title,
                "locale": "ru_RU"
            }
        }

        spreadsheet_folder_id = self.__get_folder_id(spreadsheet_folder_title)
        print("ID FOLDER =", spreadsheet_folder_id)

        if spreadsheet_folder_id is None:
            spreadsheet_folder_id = self.__create_folder(spreadsheet_folder_title)

        spreadsheet = self.client.create(spreadsheet_title, spreadsheet_template, spreadsheet_folder_id)

        # create new worksheet in new spreadsheet
        res = self.add_worksheet(spreadsheet.id, worksheet_title, table_style, group_list)
        if not res:
            print("Error while worksheet creating")
            return None

        # remove standard sheet1
        spreadsheet.del_worksheet(spreadsheet.sheet1)

        return {"link": spreadsheet.url, "id": spreadsheet.id, "worksheets": self.__get_worksheets(spreadsheet.id)}

    # Returns table's url
    def share_table(self, spreadsheet_id, user_mail, role):
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        share_role = "reader" if role == "r" else "writer"
        spreadsheet.share(user_mail, share_role)

        return spreadsheet.url

    # Adds new worksheet in spreadsheet with specified id
    # Fills worksheet with fields table_style and students group_list
    def add_worksheet(self, spreadsheet_id, worksheet_title, table_style, group_list):

        style = gt.TableStyle(table_style)
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        spreadsheet.add_worksheet(worksheet_title, rows=len(group_list) + 1, cols=len(style.fields))

        new_worksheet = spreadsheet.worksheet("title", worksheet_title)

        # init table fields and students' names
        new_worksheet.update_row(1, [style.fields])
        new_worksheet.update_col(1, [group_list], row_offset=1)

        # format students' names column
        first_col = new_worksheet.get_col(1, returnas='range')
        first_col.apply_format(gt.CellStyle.student_names_format_cell)

        # format table field
        first_row = new_worksheet.get_row(1, returnas='range')
        first_row.apply_format(gt.CellStyle.fields_format_cell)

        new_worksheet.adjust_column_width(0, new_worksheet.cols)

        # set format of main table (with marks)
        main_field = new_worksheet.get_values(
            (2, 2), (new_worksheet.rows, new_worksheet.cols), returnas='range',
            include_tailing_empty_rows=True)
        main_field.apply_format(gt.CellStyle.main_table_cell)

        return True

    # Returns all spreadsheets {name, link, id} in folder_name directory
    def get_spreadsheets(self, folder_name: str):
        folder_id = self.__get_folder_id(folder_name)

        if folder_name is None or folder_id is None:
            return None

        files = self.drive.ListFile({"q": "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"}) \
            .GetList()

        files_info = [{"name": o["title"], "link": o["alternateLink"], "id": o["id"],
                       "worksheets": self.__get_worksheets(o["id"])}
                      for o in filter(lambda elem: elem["parents"][0]["id"] == folder_id, files)]

        return files_info

    # Returns list of students first name and second name
    # Students must be in A2:An column
    def get_students_list(self, spreadsheet_id, worksheet_name):
        worksheet = self.client.open_by_key(spreadsheet_id).worksheet("title", worksheet_name)
        students_range = worksheet.range("A2:A" + str(worksheet.rows), returnas='cell')
        students_list = [cell.value for cells in students_range for cell in cells]
        return students_list

    # Deletes table by spreadsheet_id
    def del_spreadsheet(self, spreadsheet_id):
        self.client.drive.delete(spreadsheet_id)

    # Creates new column with attendance content
    # content[0] -- col name, content[1:n] -- attendance of student (+/-)
    def add_date_col(self, spreadsheet_id, worksheet_name, content):

        insert_index = self.__find_date_col_index(spreadsheet_id)
        print(insert_index)

        worksheet = self.client.open_by_key(spreadsheet_id).worksheet("title", worksheet_name)
        worksheet.insert_cols(insert_index, values=content, inherit=True)
        worksheet.adjust_column_width(insert_index)

        now = datetime.datetime.now()
        pprint(worksheet.cell(addr=(1, insert_index + 1)))
        added_field_cell = worksheet.cell((1, insert_index + 1))
        added_field_cell.note = str(now.day) + "." + str(now.month) + "." + str(now.year)

        new_col_content = worksheet.get_values(
            (2, insert_index + 1), (worksheet.rows, insert_index + 1), returnas='range',
            include_tailing_empty_rows=True)
        new_col_content.apply_format(gt.CellStyle.main_table_cell)

        return True

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

    def __get_worksheets(self, spreadsheet_id):
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        return [o.title for o in spreadsheet.worksheets()]

    def __find_date_col_index(self, spreadsheet_id):
        worksheet = self.client.open_by_key(spreadsheet_id).sheet1
        fields = worksheet.get_row(1, returnas='cell')

        index = None
        for i in range(len(fields)):
            if fullmatch("\d{1,2}\.\d{1,2}\.\d{4}", str(fields[i].note)):
                print(str(fields[i].note))
                index = i

        return 1 if index is None else index + 1

