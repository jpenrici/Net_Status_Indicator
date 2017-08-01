# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

'''
  No pacote psutil o método utilizado:
  psutil.network_io_counters(pernic=True) ou novo
  psutil.net_io_counters(pernic=True) retorna:
  {'interface': iostat(bytes_sent=0, bytes_recv=0, packets_sent=0,
      packets_recv=0, errin=0, errout=0, dropin=0, dropout=0),
  'outras interfaces...'}
  sendo utilizado neste aplicativo: bytes_sent, bytes_recv.
'''

# Módulos padrão
import sys
import time
import os.path
import gtk
import gobject
import pynotify
from threading import Thread

# Checar Módulo AppIndicator (python-appidicator)
try:
    import appindicator
    print ("import appindicator ok...")
except ImportError:
    print (('Error: Module appindicator needs to be installed!', sys.stderr))
    sys.exit(1)

# Checar Módulo Psutil (python-psutil)
try:
    import psutil
    print ("import psutil ok...")
except ImportError:
    print (('Error: psutil module needs to be installed!', sys.stderr))
    sys.exit(1)

# Variáveis globais
wlan_label = 'wlan0'  # identificação genérica
#wlan_label = 'wlx0015afa3ed5c'  # exemplo específico
eth_label = 'eth0'
ppp_label = 'ppp0'
local_label = 'lo'
thread_reader = None
interface = {'Wireless': [wlan_label , 0, 0],  # {'Rótulo': ['interface',
             'Ethernet': [eth_label, 0, 0],  # bytes_enviados_total,
             'Modem3G': [ppp_label, 0, 0],  # bytes_recebidos_total]}
             'Local': [local_label, 0, 0]}

# Constantes
APP_PATH = os.path.dirname(os.path.realpath(__file__))
RESOURCES_PATH = APP_PATH + "/resources/"


# Classe Indicador
class Indicador():

    # Inicializa a construção do menu indicator
    def __init__(self):
        ui = gtk.Builder()
        ui.add_from_file("menu-indicator.xml")
        ui.connect_signals({"swap_interface": self.swap_interface,
                            "reset_counting": self.reset_counting,
                            "inform": self.inform,
                            "exit": self.exit})

        menu = ui.get_object("menu")
        self.interface_current = ui.get_object("interface_current")
        self.icon_interface_current = ui.get_object("icon_interface_current")
        self.interface1 = ui.get_object("interface1")
        self.interface2 = ui.get_object("interface2")
        self.downUp = ui.get_object("downUp")
        self.icon_downUp = ui.get_object("icon_downUp")
        self.total_net = ui.get_object("total_net")
        self.icon_total_net = ui.get_object("icon_total_net")
        self.total_down = ui.get_object("total_down")
        self.icon_total_down = ui.get_object("icon_total_down")
        self.total_up = ui.get_object("total_up")
        self.icon_total_up = ui.get_object("icon_total_up")
        self.reset_counting = ui.get_object("reset_counting")
        self.inform = ui.get_object("inform")
        self.icon_inform = ui.get_object("icon_inform")
        self.icon_notify = ui.get_object("icon_notify")
        self.exit = ui.get_object("exit")
        self.icon_exit = ui.get_object("icon_exit")

        list_interface = (list(interface.keys()))
        self.interface_current.set_label(list_interface[0])
        self.interface1.set_label(list_interface[1])
        self.interface2.set_label(list_interface[2])

        self.ind = appindicator.Indicator("app_indicator",
            "distributor-logo", appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)

        if os.path.exists(RESOURCES_PATH):
            self.ind.set_icon_theme_path(RESOURCES_PATH)
            self.ind.set_icon(self.interface_current.get_label())
            self.icon_interface_current.set_from_file(RESOURCES_PATH +
                                                           			"swap.svg")
            self.icon_total_net.set_from_file(RESOURCES_PATH + "total_net.svg")
            self.icon_downUp.set_from_file(RESOURCES_PATH + 
            						self.interface_current.get_label() + ".svg")
            self.icon_total_down.set_from_file(RESOURCES_PATH + "total_down.svg")
            self.icon_total_up .set_from_file(RESOURCES_PATH + "total_up.svg")
            self.icon_inform.set_from_file(RESOURCES_PATH + "inform.svg")
            self.icon_exit.set_from_file(RESOURCES_PATH + "exit.svg")

        self.ind.set_label("Down : Up")
        self.ind.set_menu(menu)
        menu.show_all()
        print("indicador started...")

    # Pynotify
    def notify(self, s="Inform", m="Message", i=gtk.STOCK_INFO):
        print ("notify...")
        pynotify.init("Notification")
        i = RESOURCES_PATH + "notify.svg"
        notify = pynotify.Notification(summary=s, message=m, icon=i)
        notify.show()

    # Evento Trocar Interface
    def swap_interface(self, widget):
        new_interface = widget.get_label()
        if (self.interface1.get_label() == new_interface):
            self.interface1.set_label(self.interface_current.get_label())
        else:
            self.interface2.set_label(self.interface_current.get_label())

        if os.path.exists(RESOURCES_PATH):
            self.ind.set_icon(new_interface)

        self.interface_current.set_label(new_interface)
        print(("new_interface: %s" % new_interface))

        self.notify(s="Interface changed!", m=new_interface)

    # Evento Zerar Contador
    def reset_counting(self, *argv):
        i = self.interface_current.get_label()
        interface[i][1] = 0
        interface[i][2] = 0
        self.notify(s="Counter Zero!", m=("Network interface: %s" % i))
        print ("Counter Zero!...")

    # Evento informar
    def inform(self, *argv):
        self.notify(s="Network measurement.",
                m=("Received (Down) : Sent (Upload)" +
                "\nMeasurement in kilobits/second.\nNetwork interface: %s"
                % self.interface_current.get_label()))

    # Evento Fechar Aplicativo
    def exit(self, *argv):
        self.stop_reading()
        self.notify(s="Attention:", m="Application terminated!")
        print ("application terminated!...")
        gtk.main_quit()

    # Método utilizado na Thread
    def read_psutil(self):
        bytes_sent = 0
        bytes_received = 0
        bytes_sent_total = 0
        bytes_received_total = 0

        try:
            # Loop de leitura do psutil
            while thread_reader.ativo:

				# Atenção biblioteca psutil atualizada
				# Antigo: psutil.network_io_counters(pernic=True)
                read_anterior = psutil.net_io_counters(pernic=True)
                time.sleep(1)  # pausa de 1 segundo
                read_current = psutil.net_io_counters(pernic=True)

                for l in (list(interface.keys())):
                    i = interface[l][0]
                    if (i in read_current):
                        bytes_sent = (read_current[i][0]
                                        - read_anterior[i][0])
                        bytes_received = (read_current[i][1]
                                        - read_anterior[i][1])
                    else:
                        bytes_sent = 0
                        bytes_received = 0

                    bytes_sent_total = interface[l][1] + bytes_sent
                    interface[l][1] = bytes_sent_total
                    bytes_received_total = interface[l][2] + bytes_received
                    interface[l][2] = bytes_received_total

                    # Enviar dados para atualizar label do indicador
                    # da interface escolhida
                    if (l == self.interface_current.get_label()):
                        gobject.idle_add(self.update_indicador,
                                    bytes_received, bytes_sent,
                                    bytes_received_total, bytes_sent_total)
                #print (interface)

        except:
            print ('Unexpected error!')
            #self.notify(s="Unexpected error!", m="Reactivating the reading.")
            time.sleep(1)
            self.start_reading()

    # Método de atualização do indicador
    def update_indicador(self, bytes_received, bytes_sent,
                            bytes_received_total, bytes_sent_total):
        # Cálculos
        kbits_received = ((float(bytes_received) * 8) / 1024)
        kbits_sent = ((float(bytes_sent) * 8) / 1024)
        mbytes_received_total = ((float(bytes_received_total) / 1024) / 1024)
        mbytes_sent_total = ((float(bytes_sent_total) / 1024) / 1024)
        mbytes_total_net = mbytes_received_total + mbytes_sent_total

        # Atualizando label
        #self.ind.set_label(str('%.2f' % kbits_received) + " : "
        #            + str('%.2f' % kbits_sent))
        self.downUp.set_label(str('%.2f' % kbits_received) + " : "
                    + str('%.2f Kb/s' % kbits_sent ))
        self.total_down.set_label(str('%.2f' % mbytes_received_total) + " MB")
        self.total_up.set_label(str('%.2f' % mbytes_sent_total) + " MB")
        self.total_net.set_label(str('%.2f' % mbytes_total_net) + " MB")

        # Atualizando icon
        if os.path.exists(RESOURCES_PATH):
        	update_icon = self.interface_current.get_label();
            if (kbits_received > kbits_sent):
            	self.ind.set_icon(RESOURCES_PATH + "net_down.svg")            
            if (kbits_received < kbits_sent):
            	self.ind.set_icon(RESOURCES_PATH + "net_up.svg")
            if (kbits_received == kbits_sent):
            	self.ind.set_icon(update_icon)


    # Inicia a Thread
    def start_reading(self, *args):
        global thread_reader
        thread_reader = Thread(target=self.read_psutil)
        thread_reader.ativo = True  # Ativar loop de leitura
        thread_reader.start()
        print ("thread_reader activating...")

    # Encerra a Thread
    def stop_reading(self, *args):
        global thread_reader
        thread_reader.ativo = False  # Parar loop de leitura
        print ("thread_reader shutting down...")


# Método Principal
def main():
    print ("launching application...")
    app = Indicador()
    app.start_reading()
    gtk.gdk.threads_init()
    gtk.main()
    return 0

if __name__ == "__main__":
    main()