import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import Functions
import fitz


class OnMyWatch:
    # Set the directory on watch
    watchDirectory = "Input"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.watchDirectory, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()


class Handler(FileSystemEventHandler):

    folder_path = ""
    interrupt = 0
    event_counter = 0

    def on_any_event(self, event):

        if event.is_directory:
            if self.folder_path == event.src_path:
                self.interrupt = 1
            else:
                self.folder_path = event.src_path
                self.interrupt = 0

        elif event.event_type == "created" and self.interrupt == 0:
            self.event_counter += 1
            if self.event_counter == 2:

                # Event is created, you can process it now
                print("Watchdog received created event - % s." % event.src_path)
                print("Folder path:", self.folder_path)
                pdf_names = os.listdir(self.folder_path)

                for pdf_name in pdf_names:

                    if pdf_name[-7:-4] == "new":
                        texts_new = Functions.get_texts_from_new_pdf(self.folder_path + "/" + pdf_name)
                        texts_new = Functions.sort_texts_according_to_page_no(texts_new)
                        pdf_new = fitz.open(self.folder_path + "/" + pdf_name)
                        #print(pdf_new[0].mediabox)
                    else:
                        texts_old = Functions.get_texts_from_old_pdf(self.folder_path + "/" + pdf_name)
                        texts_old = [textbox[0:5] for textbox in texts_old]

                changed_boxes = Functions.check_boxes(texts_old, texts_new)
                coordinates_changed_text = Functions.convert_textboxes_to_coordinates(texts_new, changed_boxes)
                filled_button_coordinates, unfilled_widget_coordinates = Functions.get_filled_button_coordinates_and_unfilled_widgets(pdf_new)

                pdf_new = Functions.highlighter(pdf_new, coordinates_changed_text, use_case="new_text")
                pdf_new = Functions.highlighter(pdf_new, filled_button_coordinates, use_case="button")
                pdf_new = Functions.highlighter(pdf_new, unfilled_widget_coordinates, use_case="widget")
                Functions.save_pdf(pdf_new, self.folder_path)
                Functions.delete_input_folder(self.folder_path)

                self.event_counter = 0


watch = OnMyWatch()
watch.run()


# Warnung kommt von fuzzy:
# C:\Users\larsw\anaconda3\envs\gitlaw\lib\site-packages\fuzzywuzzy\fuzz.py:11: UserWarning: Using slow pure-python SequenceMatcher. Install python-Levenshtein to remove this warning
#   warnings.warn('Using slow pure-python SequenceMatcher. Install python-Levenshtein to remove this warning')