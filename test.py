import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish
from datetime import datetime
from threading import Thread
from time import sleep
import mysql.connector
import json
import pytz
import csv
import sys

# global variables
now = datetime.now(pytz.timezone("America/Bogota"))
global_list_ports = []
global_data = [[now, 'null', 0, i, json.dumps({})] for i in range(1, 9)]

class etl_iolink_edge: 
  
    def __init__(
            self, hostname:str, name_table:str, name_database:str,
            user_database:str, pass_database:str, route_log:str='./log_etl_iolink_edge.csv', period:int=5
            ):             
        self._hostname = hostname
        self._index_list = [18, 21]
        self._route_log = route_log
        self._name_table = name_table
        self._user_database = user_database
        self._pass_database = pass_database
        self._name_database = name_database
        self._connection_mariadb = mysql.connector.connect(
            host = self._hostname,
            user = self._user_database,
            password = self._pass_database,
            database = self._name_database
        )
        self._cursor = self._connection_mariadb.cursor()
        self._period = period
        self._colombia_tz = pytz.timezone("America/Bogota")

    def close_connection_mariadb(self):
        """
        Close connection to mariadb database.
        """
        self._cursor.close()
        self._connection_mariadb.close()

    def create_table_mariadb(self):
        """
        Create table 'name_table' in database 'name_database' if it does not exist.

        :param table_definition: Definition for create table with column names.
        """
        table_definition = [
            'id INT AUTO_INCREMENT PRIMARY KEY',
            'timestamp TIMESTAMP NOT NULL',
            'reference VARCHAR(255) NOT NULL', 
            'serial VARCHAR(255) NOT NULL', 
            'port_id INT NOT NULL', 
            'data_json JSON NOT NULL'
            ]
        try:
            query = f"CREATE TABLE {self._name_table} ({', '.join(table_definition)})"
            self._cursor.execute(query)
            print(f'Table {self._name_table} created successfully')
        except mysql.connector.Error as e:
            print(f'Table {self._name_table} already exists.')
            self._log(message=f'Table {self._name_table} already exists. Error:{e}')
        
    def upload_data_mariadb(self, data:list):
        """
        Upload data to MaraDB Database.

        :param data: list of variable data to load according to varnames.
        """
        varnames = ['timestamp', 'reference', 'serial', 'port_id', 'data_json']
        try:
            query = f"INSERT INTO {self._name_table} ({', '.join(varnames)}) VALUES ({', '.join(['%s']*len(varnames))})"
            self._cursor.execute(query, data)
            self._connection_mariadb.commit()
            print('Data uploaded to DataBase successfully')
        except mysql.connector.Error as e:
            self._log(message=f'Error inserting values into the database. Error:{e}')
    
    def _log(self, message):
        """
        Log errors in 'csv' path with timestamp.

        :param message: Error message to log.
        """
        with open(self._route_log, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now(), message])

    def get_data(self):
        global global_list_ports, global_data
        ports = range(1, 9)
        for port in ports:
            #if port not in global_list_ports:
            global_data[port-1] = [datetime.now(self._colombia_tz), 'null', 0, port, json.dumps({})]
            # else para actualizar hora cuando el valor no cambia
        data = global_data
        return data
        

    def run(self):
        self.create_table_mariadb()
        self._log(message='Started execution of ETL_iolink_edge')
        while True:
            data = self.get_data()
            for d in data:
                self.upload_data_mariadb(data=d)
            sleep(self._period)











def main():
    etl = etl_iolink_edge(
        hostname='192.168.17.235',
        name_table = 'data',
        name_database='IO-Link-data',
        user_database='jclondono',
        pass_database='Elico2024-',
        period=5
        )       
    mqtt_subscribe_list_port_thread = Thread(target=mqtt_subscribe_list_port)
    mqtt_subscribe_list_port_thread.start()
    try:
        etl.run()
    finally:
        print('\nDatabase connection closed successfully\n')
        etl.close_connection_mariadb()

def byte_array_to_dict(msg:bytearray):
    try:
        string_bytes = msg.payload
        string_utf8 = string_bytes.decode('utf-8')
        data_dict = json.loads(string_utf8) 
    except UnicodeDecodeError:
        string_utf8 = string_bytes.decode('latin-1')      
        data_dict = json.loads(string_utf8)
    return data_dict

def get_list_port(client, userdata, message):
    global global_list_ports
    pData = byte_array_to_dict(message)
    list_ports = []
    for port, i in zip(pData['ports'], range(1,9)):
        if port['status'] == 'Operational':
            list_ports.append(i)
    global_list_ports = list_ports  

def mqtt_subscribe_list_port():
    subscribe.callback(get_list_port, 'IOLM/clientstatus', hostname='192.168.17.235', userdata={'message_count': 0})

if __name__ == '__main__':
    main()