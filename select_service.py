from tkinter import *
from tkinter import messagebox
from settings import *
import time
from logzero import logger, logfile
from pco_plan import PcoPlan
from pco_live import PcoLive
from tkinter import ttk



class SelectService:
    def __init__(self, send_to):
        self.service_type_id = None
        self.service_id = None

        self.service_types_menu = Tk()
        self.services_menu = Tk()
        self.services_menu.withdraw()
        self.pco_plan = PcoPlan()

        self.send_to = send_to

    def ask_service_info(self):
        self.__build_service_types_menu()

    def __build_service_types_menu(self):
        self.service_types_menu.title('Pick service folder')
        self.service_types_menu.configure(bg=bg_color)

        # Create button for each service type, call build_service_types_menu when clicked
        for service_type in self.pco_plan.get_service_types()[1]:
            Button(self.service_types_menu, text=service_type['name'],
                   command=lambda
                 service_type=service_type: self.__build_services_menu(
                 service_type_id=service_type['id']),
                   bg=bg_color, fg=text_color, font=(font, other_text_size), bd=1, width=50,
                   pady=3).pack()
        self.service_types_menu.mainloop()

    def __build_services_menu(self, service_type_id):
        self.service_types_menu.destroy()

        self.service_type_id = service_type_id
        self.services_menu.deiconify()

        self.services_menu.title('Pick Service')
        self.services_menu.configure(bg=bg_color)
        self.pco_plan = PcoPlan(service_type=service_type_id)

        #Create button for each service within service type, call build_plan_window + destroy root when clicked
        for service in self.pco_plan.get_services_from_service_type()[1]:
            Button(self.services_menu, text=service['date'], command=lambda service=service: self.__update_values(id=service['id']),
                   bg=bg_color, fg=text_color, font=(font, other_text_size), bd=1, width=50,
                   pady=3, ).pack()


    def __update_values(self, id):
        self.services_menu.destroy()
        self.service_id = id
        logger.debug('SelectService: service_type_id: %s, service_id: %s', self.service_type_id, self.service_id)
        if self.send_to is not None:
            self.send_to.receive_plan_details(service_type_id=self.service_type_id, service_id=self.service_id)
        else:
            return self.service_type_id, self.service_id
