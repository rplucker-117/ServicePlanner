from tkinter import *
from tkinter import ttk
from configs.settings import *
from logzero import logger
from pco_plan import PcoPlan
from re import search

class SelectService:
    """Class to select a service type & service and pass it along to another part of the app.

    :param send_to: where to send the details to. This should contain a method called receive_plan_details.
    See code below.
    """

    def __init__(self, send_to=None):
        logger.debug('Starting SelectService class instance')

        self.service_type_id: int
        self.service_id: int

        self.send_to = send_to
        self.pco_plan = PcoPlan()

        self.current_buttons = []

        self.root = Tk()
        self.root.geometry('450x800')
        self.root.configure(bg=bg_color)

        self.controls_frame = Frame(self.root, bg=bg_color)
        self.controls_frame.pack(pady=20)

        Label(self.controls_frame, text='Search:', bg=bg_color, fg=text_color, font=(font, other_text_size-2)).grid(row=0, column=0)

        self.search_box_entry = StringVar(self.controls_frame)
        self.search_box_entry.trace_add('write', self._on_search_box_changed)

        self.search_box = Entry(self.controls_frame, textvariable=self.search_box_entry)
        self.search_box.grid(row=0, column=1)

        self.back_button = Button(self.controls_frame, text='Back', command=self._build_service_types_buttons,
                                  bg=bg_color, fg=text_color, font=(font, other_text_size-2), bd=1)

        # -----I don't really know how stuff below works. Recommend not touching it.-------
        # https://www.youtube.com/watch?v=0WafQCaok6g&ab_channel=Codemy.com

        # Create main frame to hold everything that scrolls
        self.canvas_holder_frame = Frame(self.root, bg=bg_color)
        self.canvas_holder_frame.pack(fill=BOTH, expand=1)

        # create canvas inside of main frame
        self.container_canvas = Canvas(self.canvas_holder_frame, bg=bg_color)
        self.container_canvas.pack(side=LEFT, fill=BOTH, expand=1)

        # add scrollbar to canvas
        self.scrollbar = Scrollbar(self.canvas_holder_frame, orient=VERTICAL, command=self.container_canvas.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        # configure canvas and set scrollbar binding
        self.container_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.container_canvas.bind('<Configure>', lambda e: self.container_canvas.
                                   configure(scrollregion=self.container_canvas.bbox('all')))
        self.container_canvas.bind_all('<MouseWheel>', self._on_mouse_wheel)

        # Create another frame inside of canvas. All scroll-able content goes in this frame
        self.primary_button_content_frame = Frame(self.container_canvas, bg=bg_color)

        # add above frame to new window inside of canvas
        self.container_canvas.create_window((0,0), window=self.primary_button_content_frame, anchor='nw')

    def _on_mouse_wheel(self, event):
        """Mouse scroll event handler"""
        self.container_canvas.yview_scroll(-1*int((event.delta/120)), 'units')

    def _on_search_box_changed(self, var, index, mode) -> None:
        """This performs the search function"""

        # "forget" and repack all button, so they come back in the correct order
        for button in self.current_buttons:
            button.pack_forget()
            button.pack()

        # convert to lowercase so case doesn't matter when searching
        text_entry = self.search_box_entry.get()
        text_entry_lowercase = text_entry.lower()

        # remove buttons that don't apply to search string
        for button in self.current_buttons:
            if not search(text_entry_lowercase, button.cget('text').lower()):
                button.pack_forget()

    def ask_service_info(self) -> None:
        """Outside entry point for this class. Call this method to get things started."""
        self._build_service_types_buttons()
        self.root.mainloop()

    def _build_service_types_buttons(self) -> None:
        if len(self.current_buttons) != 0:
            for button in self.current_buttons:
                button.destroy()
            self.current_buttons.clear()

        # delete what's in the search box. This is here for if user clicks "back" button
        self.search_box.delete(first=0, last=len(self.search_box.get()))

        for service_type in self.pco_plan.get_service_types():
            self.current_buttons.append(
                Button(self.primary_button_content_frame, text=service_type['name'],
                       command=lambda service_type=service_type: self.build_services_buttons(
                           service_type_id=service_type['id']
                       ), bg=bg_color, fg=text_color, font=(font, other_text_size-2), bd=1, width=55)
            )
        for button in self.current_buttons:
            button.pack()

        self.back_button.grid_forget()

    def build_services_buttons(self, service_type_id: int) -> None:
        self.service_type_id = service_type_id
        self.pco_plan.service_type = self.service_type_id

        # delete what's in the search box when user advance to the next step
        self.search_box.delete(first=0, last=len(self.search_box.get()))

        for button in self.current_buttons:
            button.destroy()
        self.current_buttons.clear()

        for service in self.pco_plan.get_services_from_service_type():
            if service['title'] is not None:
                title = f'{service["date"]} | {service["title"]}'
            else:
                title = service['date']

            self.current_buttons.append(
                Button(self.primary_button_content_frame, text=title,
                       command=lambda service = service: self._update_values(service_id=service['id']),
                       bg=bg_color, fg=text_color, font=(font, other_text_size-2), bd=1, width=55)
            )

        for button in self.current_buttons:
            button.pack()

        self.back_button.grid(row=0, column=2, padx=20)

    def _update_values(self, service_id: int) -> None:
        """sends final service_type_id and service_id values to receiving class, destroys ui"""
        self.service_id = service_id

        logger.debug(f'SelectService: service_type_id {self.service_type_id} and service_id {self.service_id} selected.')

        self.root.destroy()

        if self.send_to is not None:
            logger.debug(f'SelectService: sending details (service_type_id {self.service_type_id}'
                         f' and service_id {self.service_id}) to class {self.send_to.__class__.__name__}')
            self.send_to.receive_plan_details(service_type_id=self.service_type_id, service_id=self.service_id)


if __name__ == '__main__':
    class TestClass:
        def __init__(self):
            pass

        def receive_plan_details(self, service_type_id, service_id):
            print('got plan details.')
            print(service_type_id)
            print(service_id)

    test = TestClass()

    s = SelectService(send_to=test)
    s.ask_service_info()