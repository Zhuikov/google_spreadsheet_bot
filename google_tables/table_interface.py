import pygsheets
import google_tables as gt


class TableInterface:

    def __init__(self, credentials_file):
        self.client = pygsheets.authorize(credentials_file)

    # table_style_file -- path to style file
    # group_list_file -- path to group list file
    def create_spreadsheet(self, spreadsheet_title, spreadsheet_folder, worksheet_title,
                           table_style_file, group_list_file):
        style = gt.TableStyle(table_style_file)
        with open(group_list_file) as input:
            lines = input.read().splitlines()
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

        # init table fields and students' names
        spreadsheet = self.client.create(spreadsheet_title, spreadsheet_template, spreadsheet_folder)
        spreadsheet.sheet1.update_row(1, [style.fields])
        spreadsheet.sheet1.update_col(1, [lines], row_offset=1)

        # format students' names column
        first_col = spreadsheet.sheet1.get_col(1, returnas='range')
        first_col.apply_format(gt.CellStyle.student_names_format_cell)
        spreadsheet.sheet1.adjust_column_width(0)

        # format table fields
        first_row = spreadsheet.sheet1.get_row(1, returnas='range')
        first_row.apply_format(gt.CellStyle.fields_format_cell)

        # set format of main table (with marks)
        main_field = spreadsheet.sheet1.get_values(
            (2, 2), (spreadsheet.sheet1.rows, spreadsheet.sheet1.cols), returnas='range',
            include_tailing_empty_rows=True)
        main_field.apply_format(gt.CellStyle.main_table_cell)

        # TODO: remove it
        return spreadsheet.sheet1