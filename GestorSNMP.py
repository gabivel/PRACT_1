import os
import json
import rrdtool
import time
import threading
from reportlab.pdfgen import canvas
from pysnmp.hlapi import *
from getSNMP_1 import consultaSNMP

def createRRD(host):
    ret = rrdtool.create("reporte" + host + ".rrd",
                     "--start",'N',
                     "--step",'60',
                     "DS:inucast:COUNTER:120:U:U",
                     "DS:ipinreceives:COUNTER:120:U:U",
                     "DS:icmpoutechos:COUNTER:120:U:U",
                     "DS:tcpinsegs:COUNTER:120:U:U",
                     "DS:udpindtgrams:COUNTER:120:U:U",
                     "RRA:AVERAGE:0.5:1:15",
                     "RRA:AVERAGE:0.5:1:15",
                     "RRA:AVERAGE:0.5:1:15",
                     "RRA:AVERAGE:0.5:1:15",
                     "RRA:AVERAGE:0.5:1:15")

    if ret:
        print (rrdtool.error())


def consultas(comunidad,host):
    while 1:
        total_ucast_pkts = int(
            consultaSNMP(comunidad,host,
                         '1.3.6.1.2.1.2.2.1.11.2'))
        ip_in_receives = int(
            consultaSNMP(comunidad,host,
                         '1.3.6.1.2.1.4.3.0'))
        icmp_out_echos = int(
            consultaSNMP(comunidad,host,
                         '1.3.6.1.2.1.5.21.0'))
        tcp_in_segs = int(
            consultaSNMP(comunidad,host,
                         '1.3.6.1.2.1.6.10.0'))
        udp_in_dtgrams = int(
            consultaSNMP(comunidad,host,
                         '1.3.6.1.2.1.7.1.0'))

        valor = "N:" + str(total_ucast_pkts) + ':' + str(ip_in_receives) + ':' + str(icmp_out_echos) + ':' + str(tcp_in_segs) + ':' + str(udp_in_dtgrams)
        #print (valor)
        rrdtool.update("reporte" + host + ".rrd", valor)
        rrdtool.dump("reporte" + host + ".rrd","reporte" + host + ".xml")
        time.sleep(1)

def agregarDispositivo():
    host = input("Ingrese el nombre del host o la dirección IP: ")
    v_SNMP = input("Version de SNMP: ")
    comunidad =  input("Nombre de la comunidad: ")
    port = input("Puerto: ")

    dispositivos = []
    dispositivo = [host,v_SNMP,comunidad,port]
    if os.stat("matriz.txt").st_size == 0:
        dispositivos = [dispositivo]
        print(dispositivos)
        with open('matriz.txt', 'w') as temp_op:
            json.dump(dispositivos, temp_op)
    else:
        with open('matriz.txt', 'r') as filehandle:
            devices = json.load(filehandle)
            devices.append(dispositivo)
            print(devices)
        with open('matriz.txt', 'w') as indevice:
            json.dump(devices, indevice)
    hilo = threading.Thread(name='hilo%s' %host, 
                               target=consultas,args=(item[2],item[0],),
                               daemon=True)
    hilo.start()



def deleteDispositivo():
    host = input("Ingrese el nombre del host o la dirección IP a eliminar: ")
    d_temp = []
    with open('matriz.txt', 'r') as filehandle:
        devices = json.load(filehandle)
        for item in devices:
            if host in item:
                devices.remove(item)
                #os.remove("reporte" + item[0] + ".rrd")
                
        print(devices)

    with open('matriz.txt', 'w') as indevice:
        json.dump(devices, indevice)

def generaGraph(host):
    with open('matriz.txt', 'r') as file:
        devices = json.load(file)
        print(host)
        print(devices)
        for item in devices:
            if host in item:
                tiempo_actual = int(time.time())
                #Grafica desde el tiempo actual menos diez minutos
                tiempo_inicial = tiempo_actual - 600

                ifInUcast = rrdtool.graph( "ifInUcast.png",
                                     "--start",str(tiempo_inicial),
                                     "--end","N",
                                     "--title=Paquetes unicast recibidos por interfaz",
                                     "DEF:PktIn=reporte" + host + ".rrd:inucast:AVERAGE",
                                     "LINE3:PktIn#FF336B:Paquetes unicast")

                ipInReceives = rrdtool.graph( "ipInreceives.png",
                                     "--start",str(tiempo_inicial),
                                     "--end","N",
                                     "--title=Datagramas recibidos, incluidos los erroneos",
                                     "DEF:ipIn=reporte" + host + ".rrd:ipinreceives:AVERAGE",
                                     "LINE3:ipIn#D871F9:Paquetes ipv4")

                icmpOutEchos = rrdtool.graph( "icmpOutEchos.png",
                                     "--start",str(tiempo_inicial),
                                     "--end","N",
                                     "--title=Mensages ICMP echo enviados",
                                     "DEF:icmpOut=reporte" + host + ".rrd:icmpoutechos:AVERAGE",
                                     "LINE3:icmpOut#8C71F9:Echos ICMP")

                tcpInSegs = rrdtool.graph( "tcpInSegs.png",
                                     "--start",str(tiempo_inicial),
                                     "--end","N",
                                     "--title=Segmentos TCP recibidos, incluidos los erroneos",
                                     "DEF:segsIn=reporte" + host + ".rrd:tcpinsegs:AVERAGE",
                                     "LINE3:segsIn#64D564:Segmentos TCP")

                udpInDtgrams = rrdtool.graph( "udpInDtgrams.png",
                                     "--start",str(tiempo_inicial),
                                     "--end","N",
                                     "--title=Datagramas entregados a usuarios UDP",
                                     "DEF:dtgramsIn=reporte" + host + ".rrd:udpindtgrams:AVERAGE",
                                     "LINE3:dtgramsIn#E27723:Datagramas UDP")

                generaPDF(host,item[2])

        else:
            print("El dispositivo ingresado no existe")

def generaPDF(host,comunidad):
    c = canvas.Canvas('reporte.pdf')
    if host == "localhost":
        c.drawImage('Logo-Ubuntu.png', 430, 720, 100, 100)
    else:
        c.drawImage('Logo-Windows.png', 430, 720, 100, 100)
    sysName = consultaSNMP(comunidad,host,
                           '1.3.6.1.2.1.1.5.0')
    c.setFont('Helvetica', 20)
    # Dibujamos texto: (X,Y,Texto)
    c.drawString(25,800,"Nombre del sistema: %s" %sysName)
    sysLocation = consultaSNMP(comunidad,host,
                           '1.3.6.1.2.1.1.6.0')
    c.setFont('Helvetica', 15)
    # Dibujamos texto: (X,Y,Texto)
    c.drawString(25,780,"Locación: %s" %sysLocation)
    ifNumber = consultaSNMP(comunidad,host,
                           '1.3.6.1.2.1.2.1.0')
    c.setFont('Helvetica', 15)
    # Dibujamos texto: (X,Y,Texto)
    c.drawString(25,760,"Numero de interfaces %s" %ifNumber)
    sysUpTime = consultaSNMP(comunidad,host,
                           '1.3.6.1.2.1.1.3.0')
    c.setFont('Helvetica', 15)
    # Dibujamos texto: (X,Y,Texto)
    c.drawString(25,740,"Tiempo de actividad desde el ultimo reinicio %s" %sysUpTime)
    #c.setFont('Helvetica', 15)
    # Dibujamos texto: (X,Y,Texto)
    c.drawString(25,720,"Agente: %s Nombre de comunidad %s" %(host,comunidad))
    # Dibujamos una imagen (IMAGEN, X,Y, WIDTH, HEIGH)
    c.drawImage('ifInUcast.png', 50, 420, 480, 270)
    c.drawImage('ipInreceives.png', 50, 100, 480, 270)
    c.showPage()
    c.drawImage('icmpOutEchos.png', 50, 450, 480, 270)
    c.drawImage('tcpInSegs.png', 50, 100, 480, 270)
    c.showPage()
    c.drawImage('udpInDtgrams.png', 50, 450, 480, 270)
    # Guardar
    c.save()

def hexadecimal(if_descr):
    try:
        int(if_descr,16)
        return True
    except ValueError:
        return False

def decodificar(if_descr):
    hexa = if_descr[2:]
    bytes_object = bytes.fromhex(hexa)
    cadena_ascii = bytes_object.decode("ASCII")
    return cadena_ascii


if os.stat("matriz.txt").st_size == 0:
    print("esta vacio")
with open('matriz.txt', 'r') as file:
    devices = json.load(file)

    print("Dispositivos en monitoreo: " + str(len(devices)))
    for item in devices:
        if os.path.isfile("reporte"+item[0]+".rrd"):
            print("\n")
        else:
            createRRD(item[0])
        hilo = threading.Thread(name='hilo%s' %item[0], 
                               target=consultas,args=(item[2],item[0],),
                               daemon=True)
        hilo.start()


        print("\n----------- Agente: %s ------------" % item[0])
        if os.system("ping -c 1 " + item[0] + " > /dev/null 2>&1") == 0:
            print ("%s estado UP" % item[0])
        else:
            print ("%s estado DOWN" % item[0])

        n_interfaces = consultaSNMP(item[2],item[0],
                           '1.3.6.1.2.1.2.1.0')
        N_interfaces = "Numero de interfaces del agente " + item[0] + " = " + n_interfaces
        print (N_interfaces)
        print("\nEstado administrativo y Descripcion de cada interfaz se muestra como:")
        print("NoInterfaz = AS:valor D:valor")      
        for interface in range(1,int(n_interfaces)+1):
            admin_status = consultaSNMP(item[2],item[0],
                                     '1.3.6.1.2.1.2.2.1.7.'+ str(interface))

            if_descr = consultaSNMP(item[2],item[0],
                                     '1.3.6.1.2.1.2.2.1.2.'+ str(interface))
            if hexadecimal(if_descr):
                decodificado = decodificar(if_descr)
                descripcion = str(interface) +" = AS:" + str(admin_status) + " D:" + str(decodificado)
                print(descripcion) 
            else:
                descripcion = str(interface) +" = AS:" + str(admin_status) + " D:" + str(if_descr) 
                print (descripcion)

while True:
    opcion = input("A: Agregar un dispositivo\nB: Eliminar dispositivo\nC: Reporte de información de dispositivo\n")
    opcion = opcion.strip()
    if opcion.upper() == "A":
        agregarDispositivo()

    elif opcion.upper() == "B":
        deleteDispositivo()


    elif opcion.upper() == "C":
        host = input("Nombre o IP del dispositivo:\n")
        generaGraph(host)
        
    
    