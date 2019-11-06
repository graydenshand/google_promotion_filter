from db import Db
from config import * 
import json, csv

class Sender():
    """
    Sender
        * domain
        * name
        * insert
        * get_by_domain
        * json
    """

    def __init__(self, data=None):
        if data == None:
            self._domain = ''
            self._name = ''
        else:
            self._domain = data['domain']
            self._name = data['name']

    def __repr__(self):
        return f'Sender: {self.domain()} - {self.name()}'

    def domain(self):
        return self._domain

    def name(self):
        return self._name

    def insert(self, verbose=False):
        db = Db()
        sql = 'INSERT INTO sender (domain, name) VALUES (%s, %s);'
        data = [self.domain(), self.name()]
        db.query(sql, data, verbose)

    def get_by_domain(self, domain):
        db = Db()
        sql = 'SELECT * FROM sender WHERE domain = %s;'
        data = [domain]
        result = db.query(sql, data)
        if result is not None:
            self._domain, self._name = result['domain'], result['name']

    def json(self):
        data = {'domain': self.domain(), 'name': self.name()}
        return json.dumps(data)

if __name__=='__main__':
    pass
    """ 
    # Creating GoldList from CSV
    fn = "/Users/grayden/Downloads/Gold list for google promo - for Grayden.csv"
    with open(fn, 'r') as f:
        reader = csv.DictReader(f)
        domains = []
        for i, row in enumerate(reader):
            if row['domain'] not in domains:
                data = {'domain': row['domain'], 'name': row['name']}
                s = Sender(data)
                s.insert(True)
                domains.append(s.domain())
    """

    # get_by_domain
    #s = Sender()
    #s.get_by_domain('sethgodin.com')
    #print(s)




