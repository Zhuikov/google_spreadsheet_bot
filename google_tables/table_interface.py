import pygsheets
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

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

    # table_style_file -- path to style file
    # group_list_file -- path to group list file
    def create_spreadsheet(self, spreadsheet_title, spreadsheet_folder, worksheet_title):
        style = gt.TableStyle("temp_files/temp_table_style")
        with open("temp_files/temp_group_list") as input:
            lines = input.read().splitlines()
            input.close()
        spreadsheet_template = {
            "properties": {
                "title": spreadsheet_title,
                "locale": "ru_RU"
            },
            "sheets": [{
                "properties": {
                    "title": worksheet_title,
                    "gridProperties": {
                        "rowCount": len(lines) + 1,   # 1 is fields
                        "columnCount": len(style.fields),
                    }
                }
            }]
        }

        # # init table fields and students' names
        # spreadsheet = self.client.create(spreadsheet_title, spreadsheet_template, "1rIhyXRdy77AKFLvWJqoyGsDAmD-6JZVH")
        # spreadsheet.sheet1.update_row(1, [style.fields])
        # spreadsheet.sheet1.update_col(1, [lines], row_offset=1)

        # self.client.open_by_key("1wweVJX0tDh17C-ZrdehShAUXHJqtUlLbQ-uDm7jo7R0").delete()
        # folder = self.drive.CreateFile({"title": "my_folder", "mimeType": "application/vnd.google-apps.folder"})
        # folder.Upload()
        # pprint(self.client.drive.list(fields="files(name,id)"))
        list = self.drive.ListFile({}).GetList()
        for file in list:
            pprint(file["title"])
            pprint(file["id"])
            pprint(file["parents"])
            print()

        # # format students' names column
        # first_col = spreadsheet.sheet1.get_col(1, returnas='range')
        # first_col.apply_format(gt.CellStyle.student_names_format_cell)
        # spreadsheet.sheet1.adjust_column_width(0)
        #
        # # format table fields
        # first_row = spreadsheet.sheet1.get_row(1, returnas='range')
        # first_row.apply_format(gt.CellStyle.fields_format_cell)
        #
        # # set format of main table (with marks)
        # main_field = spreadsheet.sheet1.get_values(
        #     (2, 2), (spreadsheet.sheet1.rows, spreadsheet.sheet1.cols), returnas='range',
        #     include_tailing_empty_rows=True)
        # main_field.apply_format(gt.CellStyle.main_table_cell)

        # return spreadsheet.url