import telebot
import requests
import sqlite3
from datetime import datetime


class ROMBot(telebot.TeleBot):
    def __init__(self, token, api, url, db, h):
        super().__init__(token)
        self.h = h
        self.api = api
        self.url = url
        self.db = db
        self.item_list = {}
        self.get_item_list()
        print(self.get_me())
        try:
            with sqlite3.connect(self.db) as conn:
                conn.execute('''create table if not exists history 
                (id integer, query text, timestamp integer, 
                primary key (id, query))''')
        except sqlite3.OperationalError:
            pass
        except sqlite3.IntegrityError:
            self.db = None
        finally:
            conn.close()

    def get_help(self):
        return self.h

    def get_item_list(self):
        try:
            response = requests.get(self.api + '/get_item_list',
                                    headers={'Origin': self.url, 'User-Agent': 'rom3810bot'},
                                    timeout=3)
        except requests.exceptions.RequestException:
            return None
        else:
            for item in response.json()['data']['item_list']:
                self.item_list[item['name']] = item['display_name']
            return self.item_list

    def find_item(self, item_name):
        if item_name in self.item_list.keys():
            pass
        elif item_name in self.item_list.values():
            item_name = [x for x, y in self.item_list.items() if y == item_name][0]
        else:
            return None
        try:
            response = requests.get(self.api + '/get_latest_price/' + item_name,
                                    headers={'Origin': self.url, 'User-Agent': 'rom3810bot'},
                                    timeout=3)
        except requests.exceptions.RequestException:
            return None
        else:
            info = f"[{datetime.fromtimestamp(response.json()['data']['data']['timestamp'])}]\n" \
                   f"{self.item_list[item_name]}: "
            if response.json()['data']['data']['price'] > 0:
                info += f"{response.json()['data']['data']['price']:,} z"
            else:
                info += 'нет'
            return info

    def history_item(self, item_name):
        try:
            response = requests.get(self.api + '/get_price_history/' + item_name,
                                    headers={'Origin': self.url, 'User-Agent': 'rom3810bot'},
                                    timeout=3)
        except requests.exceptions.RequestException:
            return None
        else:
            table = ''
            for i, data in enumerate(response.json()['data']['data_list']):
                table += f"[{datetime.fromtimestamp(data['timestamp'])}]\t{data['volume']} шт.\t{data['price']:,} z\n"
                if i > 9:
                    break
            return table

    def auto_fill(self, text):
        lines = []
        for i, item in enumerate(self.item_list.items()):
            if item[0].lower().startswith(text) or item[1].lower().startswith(text):
                lines.append({'id': 'item' + str(i),
                              'title': item[1],
                              'description': item[0],
                              'message_text': '/f ' + item[1]
                              })
        return lines

    def get_query_history(self, user_id):
        try:
            with sqlite3.connect(self.db) as conn:
                c = conn.cursor()
                c.execute('select * from history where id = ? limit 4', (user_id,))
                last = c.fetchall()
                return last
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    def add_query_history(self, user_id, query, timestamp):
        try:
            with sqlite3.connect(self.db) as conn:
                result = conn.execute('insert into history values (?, ?, ?)', (user_id, query, timestamp))
                return result
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
