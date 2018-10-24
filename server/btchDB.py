from __future__ import print_function
import sqlite3
import os

class btchDB:
    
    BTCH_DB_PATH = "btch.db"
    
    def __init__(self, path=None):
        self.connection = None
        self.cursor = None
        if path == None:
            self.path = BTCH_DB_PATH
        else :
            self.path = path
        if not os.path.exists(self.path):
            self.create()
        

    def startEditing(self):
        if self.connection != None or self.cursor != None:
            print("warning, trying to open a connection to sqlite when previous one was not closed")
        self.connection = sqlite3.connect(self.path)
        self.cursor = self.connection.cursor()
    
    
    def stopEditing(self):
        if self.connection == None or self.cursor == None:
            print("warning, trying to close a connection to sqlite when none was open")
        else :
            self.connection.commit()
            self.connection.close()
            self.connection = None
            self.cursor = None
    
    
    def execute(self, command, params=None):
        if self.connection == None or self.cursor == None:
            print("warning, trying to execute a command without valid sqlite connection")
        elif params != None:
            self.cursor.execute(command, params)
        else :
            self.cursor.execute(command)
            
    
    def create(self):
        self.startEditing()
        # Create table
        self.execute('''CREATE TABLE users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    login TEXT UNIQUE NOT NULL,
                    pass TEXT NOT NULL,
                    signup DATE DEFAULT (DATETIME('now')),
                    active INTEGER DEFAULT 1,
                    email TEXT DEFAULT '')''')

        self.execute('''CREATE TABLE games
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idP1 INTEGER NOT NULL,
                    idP2 INTEGER NOT NULL,
                    start DATE DEFAULT (DATETIME('now')),
                    lastMove DATE,
                    turn INTEGER DEFAULT 1,
                    finished INTEGER DEFAULT 0,
                    FOREIGN KEY(idP1) REFERENCES users(id),
                    FOREIGN KEY(idP2) REFERENCES users(id)
                    )''')

        self.execute('''CREATE TABLE gamestates
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idGame INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    date DATE DEFAULT (DATETIME('now')),
                    FOREIGN KEY(idGame) REFERENCES games(id)
                    )''')

        self.execute('''CREATE TABLE invitations
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idP1 INTEGER,
                    idP2 INTEGER,
                    date DATE DEFAULT (DATETIME('now')),
                    expirationDate DATE DEFAULT (DATETIME('now', '+5 days')),
                    message TEXT DEFAULT '',
                    status INTEGER DEFAULT 0,
                    FOREIGN KEY(idP1) REFERENCES users(id),
                    FOREIGN KEY(idP2) REFERENCES users(id)
                    )''')
        self.stopEditing()


    def clearAll(self):
        self.startEditing()
        self.execute("DELETE FROM users")
        self.execute("DELETE FROM games")
        self.execute("DELETE FROM gamestates")
        self.execute("DELETE FROM invitations")
        self.stopEditing()
        

    def userExists(self, login):
        self.startEditing()
        self.execute('select id from users where login=?', (login,))
        exists = len(self.cursor.fetchall()) != 0
        self.stopEditing()
        return exists


    def newUser(self, login, password, email=None):
        if self.userExists(login):
            return False
        self.startEditing()
        if email == None:
            email = ""
        self.execute("INSERT INTO users (login, pass, email) VALUES ('%s', '%s', '%s')"%(login, password, email))
        self.stopEditing()
        return True

    def checkLogin(self, login, password):
        self.startEditing()
        self.execute('select id, pass from users where login=?', (login,))
        result = self.cursor.fetchall()
        self.stopEditing()
        if len(result) != 1:
            return (False, None)
        elif result[0][1] != password:
            return (False, None)
        else:
            return (True, result[0][0])
        

    def updateUserPassword(self, login, oldPassword, newPassword):
        if len(newPassword) == 0:
            return False
        valid, userId = self.checkLogin(login, oldPassword)
        if not valid:
            return False
        self.startEditing()
        self.execute("UPDATE users SET pass = ? where id = ?", (newPassword, userId)) 
        self.stopEditing()
        return True


    def updateUserEmail(self, login, password, newEmail):
        valid, userId = self.checkLogin(login, oldPassword)
        if not valid:
            return False
        self.startEditing()
        self.execute("UPDATE users SET email = ? where id = ?", (newEmail, userId)) 
        self.stopEditing()
        return True
    
    


#=================== TESTING =======================

import unittest

class TestDB(unittest.TestCase):
    def setUp(self):
        self.testPath = "testDB_1234.sqlite"
        if os.path.exists(self.testPath):
            os.remove(self.testPath)
        self.DB = btchDB(self.testPath)

    def tearDown(self):
        if os.path.exists(self.testPath):
            os.remove(self.testPath)

    def testCreateUser(self):
        self.assertTrue(self.DB.newUser("antoine", "pass", "toto@yop.com"))
        self.assertTrue(self.DB.newUser("leo", "pass", "toto@yop.com"))
        self.assertTrue(self.DB.newUser("pol", "pass"))
        self.assertFalse(self.DB.newUser("antoine", "pass", "toto@yop.com"))
        self.DB.clearAll()
        
    def testUserExists(self):
        self.DB.newUser("antoine", "pass", "toto@yop.com")
        self.DB.newUser("leo", "pass", "toto@yop.com")
        self.assertTrue(self.DB.userExists("antoine"))
        self.assertTrue(self.DB.userExists("leo"))
        self.assertFalse(self.DB.userExists("Pol"))
        self.DB.clearAll()
    
    def testCheckLogin(self):
        self.DB.newUser("antoine", "pass", "toto@yop.com")
        self.DB.newUser("leo", "leoPass", "toto@yop.com")
        validPassword, idUser = self.DB.checkLogin("antoine", "pass")
        self.assertTrue(validPassword)
        validPassword, idUser = self.DB.checkLogin("leo", "leoPass")
        self.assertTrue(validPassword)
        validPassword, idUser = self.DB.checkLogin("antoine", "leoPass")
        self.assertFalse(validPassword)
        self.DB.clearAll()
        
    def testUpdatePassword(self):
        self.DB.newUser("antoine", "pass", "toto@yop.com")
        self.assertTrue(self.DB.checkLogin("antoine", "pass")[0])
        self.assertTrue(self.DB.updateUserPassword("antoine", "pass", "newPass"))
        self.assertFalse(self.DB.checkLogin("antoine", "pass")[0])
        self.assertTrue(self.DB.checkLogin("antoine", "newPass")[0])
        self.DB.clearAll()
        
if __name__ == "__main__":
    unittest.main()
    

