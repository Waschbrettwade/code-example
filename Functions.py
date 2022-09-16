import fitz
import glob
import os
import shutil
from fuzzywuzzy import fuzz


def get_texts_from_old_pdf(pdf_name):
    texts_new = []
    pdf_doc_old = glob.glob(pdf_name)

    for filename in pdf_doc_old:
        doc = fitz.open(filename)
        for page in doc:
            texts_new += page.get_text("blocks")
    doc.close()

    return texts_new


def get_texts_from_new_pdf(pdf_name):
    texts_old = []
    pdf_doc_old = glob.glob(pdf_name)

    for filename in pdf_doc_old:
        doc = fitz.open(filename)
        for page in doc:
            texts_old.append(page.get_text("blocks"))
    doc.close()

    return texts_old


def sort_texts_according_to_page_no(texts):
    texts_newly_arranged = []
    for page in range(len(texts)):
        texts_newly_arranged.append([textbox[0:5] for textbox in texts[page]])
    texts_new = texts_newly_arranged

    return texts_new


def check_boxes(texts_old, texts_new):
    blacklist = {' ', '\n'}
    # textbox Bsp: (2142, 674, 2466, 712, 'Hi\n')
    diff_count = 0
    different_boxes = []
    texts_old.sort()

    rounded_texts_old, string_texts_old, rounded_texts_new = round_coordinates(texts_old, texts_new)

    print("Different textboxes: \n")
    for page_no in range(len(rounded_texts_new)):
        for textbox_no in range(len(rounded_texts_new[page_no])):
            not_similar = 1
            if (rounded_texts_new[page_no][textbox_no] not in rounded_texts_old) and \
                    (set(rounded_texts_new[page_no][textbox_no][4]) != blacklist):
                stringbox_new = str(rounded_texts_new[page_no][textbox_no])
                for old_box in string_texts_old:
                    similarity = fuzz.ratio(old_box, stringbox_new)

                    if similarity > 97:
                        print("Similarity:", similarity, stringbox_new)
                        not_similar = 0
                        break

                if not_similar == 1:
                    print("Page:", page_no, "box:", textbox_no, "\n", rounded_texts_new[page_no][textbox_no], "\n")
                    diff_count += 1
                    different_boxes.append([page_no, textbox_no])

    print("Amount of different textboxes:", diff_count)

    return different_boxes


def round_coordinates(texts_old, texts_new):
    rounded_texts_old = [(int(textbox[0]), int(textbox[1]), int(textbox[2]), int(textbox[3]), textbox[4]) for textbox in texts_old]
    string_texts_old = [str(textbox) for textbox in rounded_texts_old]

    rounded_texts_new = []
    for page in range(len(texts_new)):
        rounded_texts_new.append([(int(textbox[0]), int(textbox[1]), int(textbox[2]), int(textbox[3]), textbox[4]) for textbox in
                         texts_new[page]])

    return rounded_texts_old, string_texts_old, rounded_texts_new


def convert_textboxes_to_coordinates(textboxes, box_indices):
    coordinates = []
    for k in range(len(box_indices)):
        # z.B.: box_index[k] = [1, 45]
        coord_temp = [box_indices[k][0]] + list(textboxes[box_indices[k][0]][box_indices[k][1]][0:4])
        # z.B. coord_temp = [4, 34.1234, 123.1234, 35.234, 456.12345]
        coordinates.append(coordinate_list_to_dict(coord_temp))

    return coordinates


def coordinate_list_to_dict(liste):
    dic = {}
    coordinates = ["pageno", "x1", "y1", "x2", "y2"]
    for i in range(len(coordinates)):
        dic[coordinates[i]] = liste[i]

    return dic


def get_filled_button_coordinates_and_unfilled_widgets(pdf):
    amount_of_pages = len(pdf)
    unfilled_widgets = []
    filled_buttons = []

    for page_no in range(amount_of_pages):
        widgets_temp = []
        buttons_temp = []
        for widget in pdf[page_no].widgets():
            if ("CheckBox" == widget.field_type_string) and (widget.field_value != ""):
                buttons_temp.append(widget.rect)
            elif ("Text" == widget.field_type_string) and (widget.field_value == ""):
                widgets_temp.append(widget.rect)

        unfilled_widgets.append(widgets_temp)
        filled_buttons.append(buttons_temp)

    return filled_buttons, unfilled_widgets


def highlighter(pdf, coordinates, use_case):

    if use_case == "new_text":
        for coordinate in coordinates:
            page = pdf[coordinate["pageno"]]
            highlight = page.add_highlight_annot(fitz.Rect(coordinate["x1"], coordinate["y1"], coordinate["x2"], coordinate["y2"]))
            highlight.setColors({"stroke": (0, 0, 1)})
            highlight.update()
    else:
        for page_no in range(len(coordinates)):
            page = pdf[page_no]
            for rect in coordinates[page_no]:
                if use_case == "button":
                    rect += fitz.Rect(-3, -3, 3, 3)
                    highlight = page.add_highlight_annot(rect)
                    highlight.setColors({"stroke": (0, 1, 0)})
                elif use_case == "widget":
                    highlight = page.add_highlight_annot(rect)
                    highlight.setColors({"stroke": (1, 0, 0)})
                highlight.update()

    return pdf


def save_pdf(pdf, folder_path):
    os.mkdir("Output/" + folder_path.split("\\")[1])
    pdf.save("Output/" + folder_path.split("\\")[1] + "/highlighted.pdf")
    pdf.close()


def delete_input_folder(folder_path):
    shutil.rmtree(folder_path)
