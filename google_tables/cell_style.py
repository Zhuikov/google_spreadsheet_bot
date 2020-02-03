import pygsheets


class CellStyle:

    fields_format = {
        "backgroundColor": (0.80, 0.80, 0.80),
        "fontFamily": "Arial",
        "fontSize": 14,
        "horizontal_alignment": pygsheets.custom_types.HorizontalAlignment.CENTER,
        "borders": {"top": {"style": "SOLID"}, "bottom": {"style": "SOLID"},
                    "left": {"style": "SOLID"}, "right": {"style": "SOLID"}}
    }

    students_names_format = {
        "backgroundColor": (0.90, 0.90, 0.90),
        "fontFamily": "Arial",
        "fontSize": 12,
        "italic": True
    }

    main_table_format = {
        "horizontal_alignment": pygsheets.custom_types.HorizontalAlignment.CENTER,
        "fontFamily": "Arial",
        "fontSize": 12,
        "bold": True,
    }

    fields_format_cell = pygsheets.Cell("A1")
    fields_format_cell.horizontal_alignment = fields_format["horizontal_alignment"]
    fields_format_cell.color = fields_format["backgroundColor"]
    fields_format_cell.borders = fields_format["borders"]
    fields_format_cell.set_text_format("fontFamily", fields_format["fontFamily"])
    fields_format_cell.set_text_format("fontSize", fields_format["fontSize"])

    student_names_format_cell = pygsheets.Cell("A1")
    student_names_format_cell.color = students_names_format["backgroundColor"]
    student_names_format_cell.set_text_format("fontFamily", students_names_format["fontFamily"])
    student_names_format_cell.set_text_format("fontSize", students_names_format["fontSize"])
    student_names_format_cell.set_text_format("italic", students_names_format["italic"])

    main_table_cell = pygsheets.Cell("A1")
    main_table_cell.horizontal_alignment = main_table_format["horizontal_alignment"]
    main_table_cell.set_text_format("fontFamily", main_table_format["fontFamily"])
    main_table_cell.set_text_format("fontSize", main_table_format["fontSize"])
    main_table_cell.set_text_format("bold", main_table_format["bold"])
