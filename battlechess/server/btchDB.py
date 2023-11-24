from __future__ import print_function

import os
import sqlite3


class btchDB:

    BTCH_DB_PATH = "btch.db"
    PENDING = 0
    ACCEPTED = 1
    DECLINED = 2
    MAXINVITE = 5

    def __init__(self, path=None):
        self.connection = None
        self.cursor = None
        if path == None:
            self.path = BTCH_DB_PATH
        else:
            self.path = path
        if not os.path.exists(self.path):
            self.startEditing()
            self.create()
            self.stopEditing()

    def startEditing(self):
        if self.connection == None or self.cursor == None:
            self.connection = sqlite3.connect(self.path)
            self.cursor = self.connection.cursor()

    def stopEditing(self):
        if self.connection == None or self.cursor == None:
            print("warning, trying to close a connection to sqlite when none was open")
        else:
            self.connection.commit()
            self.connection.close()
            self.connection = None
            self.cursor = None

    def execute(self, command, params=None):
        if self.connection == None or self.cursor == None:
            print(
                "warning, trying to execute a command without valid sqlite connection"
            )
        elif params != None:
            self.cursor.execute(command, params)
        else:
            self.cursor.execute(command)

    def create(self):
        # Create table
        self.execute(
            """CREATE TABLE users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    login TEXT UNIQUE NOT NULL,
                    pass TEXT NOT NULL,
                    signup DATE DEFAULT (DATETIME('now')),
                    active INTEGER DEFAULT 1,
                    email TEXT DEFAULT '')"""
        )

        self.execute(
            """CREATE TABLE games
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idP1 INTEGER NOT NULL,
                    idP2 INTEGER NOT NULL,
                    start DATE DEFAULT (DATETIME('now')),
                    lastMove DATE,
                    turn INTEGER DEFAULT 1,
                    finished INTEGER DEFAULT 0,
                    FOREIGN KEY(idP1) REFERENCES users(id),
                    FOREIGN KEY(idP2) REFERENCES users(id)
                    )"""
        )

        self.execute(
            """CREATE TABLE gamestates
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idGame INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    date DATE DEFAULT (DATETIME('now')),
                    FOREIGN KEY(idGame) REFERENCES games(id)
                    )"""
        )

        self.execute(
            """CREATE TABLE invitations
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idP1 INTEGER,
                    idP2 INTEGER,
                    date DATE DEFAULT (DATETIME('now')),
                    expirationDate DATE DEFAULT (DATETIME('now', '+5 days')),
                    message TEXT DEFAULT '',
                    status INTEGER DEFAULT 0,
                    FOREIGN KEY(idP1) REFERENCES users(id),
                    FOREIGN KEY(idP2) REFERENCES users(id)
                    )"""
        )

    def clearAll(self):
        self.execute("DELETE FROM users")
        self.execute("DELETE FROM games")
        self.execute("DELETE FROM gamestates")
        self.execute("DELETE FROM invitations")

    def userExists(self, login):
        self.execute("SELECT id FROM users WHERE login=?", (login,))
        exists = len(self.cursor.fetchall()) != 0
        return exists

    def newUser(self, login, password, email=None):
        if self.userExists(login):
            return False
        if email == None:
            email = ""
        self.execute(
            "INSERT INTO users (login, pass, email) VALUES ('%s', '%s', '%s')"
            % (login, password, email)
        )
        return True

    def getUserId(self, login):
        self.execute("SELECT id FROM users WHERE login=?", (login,))
        result = self.cursor.fetchall()
        if len(result) != 1:
            return None
        else:
            return result[0][0]

    def checkPassword(self, login, password):
        self.execute("SELECT id, pass FROM users WHERE login=?", (login,))
        result = self.cursor.fetchall()
        if len(result) != 1:
            return (False, None)
        elif result[0][1] != password:
            return (False, None)
        else:
            return (True, result[0][0])

    def updateUserPassword(self, login, newPassword):
        userId = self.getUserId(login)
        self.execute("UPDATE users SET pass = ? where id = ?", (newPassword, userId))
        return True

    def updateUserEmail(self, login, newEmail):
        userId = self.getUserId(login)
        self.execute("UPDATE users SET email = ? where id = ?", (newEmail, userId))
        return True

    def getUserEmail(self, login):
        userId = self.getUserId(login)
        self.execute("SELECT email FROM users WHERE id=?", (userId,))
        result = self.cursor.fetchall()
        if len(result) != 1:
            return None
        else:
            return result[0][0]

    def canInvite(self, login, dest):
        currentInvitations = self.getUserCreatedInvites(login, btchDB.PENDING)
        if len(currentInvitations) >= btchDB.MAXINVITE:
            return False
        idP2 = self.getUserId(dest)
        dests = [invite[2] for invite in currentInvitations]
        return idP2 not in dests

    def newInvite(self, login, dest, text):
        if self.canInvite(login, dest):
            idP1 = self.getUserId(login)
            idP2 = self.getUserId(dest)
            if idP1 == None or idP2 == None:
                return False
            self.execute(
                "INSERT INTO invitations (idP1, idP2, message) VALUES ('%s', '%s', '%s')"
                % (idP1, idP2, text)
            )
            return True
        else:
            return False

    def getUserCreatedInvites(self, login, status=None):
        idP1 = self.getUserId(login)
        if status == None:
            self.execute(
                "SELECT id, idP1, idP2, message FROM invitations WHERE idP1=?", (idP1,)
            )
        else:
            self.execute(
                "SELECT id, idP1, idP2, message FROM invitations WHERE idP1=? AND status=?",
                (idP1, status),
            )
        return self.cursor.fetchall()

    def getUserReceivedInvites(self, login, status=None):
        idP2 = self.getUserId(login)
        if status == None:
            self.execute(
                "SELECT id, idP1, idP2, message FROM invitations WHERE idP2=?", (idP2,)
            )
        else:
            self.execute(
                "SELECT id, idP1, idP2, message FROM invitations WHERE idP2=? AND status=?",
                (idP2, status),
            )
        return self.cursor.fetchall()

    def acceptInvite(self, inviteId):
        self.execute(
            "UPDATE invitations SET status=? where id=?", (btchDB.ACCEPTED, inviteId)
        )

    def declineInvite(self, inviteId):
        self.execute(
            "UPDATE invitations SET status=? where id=?", (btchDB.DECLINED, inviteId)
        )


# =================== TESTING =======================

import unittest


class TestDB(unittest.TestCase):
    def setUp(self):
        self.testPath = "testDB_1234.sqlite"
        if os.path.exists(self.testPath):
            os.remove(self.testPath)
        self.DB = btchDB(self.testPath)
        self.DB.startEditing()

    def tearDown(self):
        self.DB.stopEditing()
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
        validPassword, idUser = self.DB.checkPassword("antoine", "pass")
        self.assertTrue(validPassword)
        validPassword, idUser = self.DB.checkPassword("leo", "leoPass")
        self.assertTrue(validPassword)
        validPassword, idUser = self.DB.checkPassword("antoine", "leoPass")
        self.assertFalse(validPassword)
        self.DB.clearAll()

    def testUpdatePassword(self):
        self.DB.newUser("antoine", "pass", "toto@yop.com")
        self.assertTrue(self.DB.checkPassword("antoine", "pass")[0])
        self.assertTrue(self.DB.updateUserPassword("antoine", "newPass"))
        self.assertFalse(self.DB.checkPassword("antoine", "pass")[0])
        self.assertTrue(self.DB.checkPassword("antoine", "newPass")[0])
        self.DB.clearAll()

    def testUpdateEmail(self):
        self.DB.newUser("antoine", "pass", "toto@yop.com")
        self.DB.newUser("leo", "pass")
        self.assertEqual(self.DB.getUserEmail("antoine"), "toto@yop.com")
        self.assertEqual(self.DB.getUserEmail("leo"), "")
        self.DB.updateUserEmail("leo", "new@ema.il")
        self.assertEqual(self.DB.getUserEmail("leo"), "new@ema.il")
        self.DB.clearAll()

    def testgetUserId(self):
        self.DB.newUser("antoine", "pass", "toto@yop.com")
        self.assertNotEqual(self.DB.getUserId("antoine"), None)
        self.assertEqual(self.DB.getUserId("leo"), None)
        self.DB.clearAll()

    def testCreateInvites(self):
        for i in range(btchDB.MAXINVITE + 2):
            self.DB.newUser("p%d" % i, "pass")
        for i in range(btchDB.MAXINVITE):
            self.assertTrue(self.DB.newInvite("p0", "p%d" % (i + 1), "hey"))

        self.assertTrue(self.DB.newInvite("p1", "p0", "hey"))
        self.assertFalse(self.DB.newInvite("p1", "p0", "hey2"))

        for i in range(btchDB.MAXINVITE):
            self.assertEqual(len(self.DB.getUserReceivedInvites("p%d" % (i + 1))), 1)
            self.assertEqual(
                len(self.DB.getUserReceivedInvites("p%d" % (i + 1), btchDB.PENDING)), 1
            )
            self.assertEqual(
                len(self.DB.getUserReceivedInvites("p%d" % (i + 1), btchDB.ACCEPTED)), 0
            )
            self.assertEqual(
                len(self.DB.getUserReceivedInvites("p%d" % (i + 1), btchDB.DECLINED)), 0
            )
        self.assertFalse(self.DB.newInvite("p0", "p%d" % (btchDB.MAXINVITE + 1), "hey"))
        self.assertEqual(
            len(self.DB.getUserCreatedInvites("p0", btchDB.PENDING)), btchDB.MAXINVITE
        )
        self.assertEqual(len(self.DB.getUserCreatedInvites("p0", btchDB.ACCEPTED)), 0)
        self.assertEqual(len(self.DB.getUserCreatedInvites("p0", btchDB.DECLINED)), 0)
        self.assertEqual(len(self.DB.getUserCreatedInvites("p0")), btchDB.MAXINVITE)
        self.assertEqual(len(self.DB.getUserCreatedInvites("p1")), 1)
        self.assertEqual(len(self.DB.getUserCreatedInvites("p2")), 0)
        self.DB.clearAll()

    def testUpdateInvites(self):
        for i in range(4):
            self.DB.newUser("p%d" % i, "pass")
        self.DB.newInvite("p0", "p1", "hey")
        self.DB.newInvite("p0", "p2", "hey")
        self.DB.newInvite("p0", "p3", "hey")
        for i in range(1, 4):
            self.assertEqual(len(self.DB.getUserReceivedInvites("p%d" % i)), 1)
            self.assertEqual(
                len(self.DB.getUserReceivedInvites("p%d" % i, btchDB.PENDING)), 1
            )
            self.assertEqual(
                len(self.DB.getUserReceivedInvites("p%d" % i, btchDB.ACCEPTED)), 0
            )
            self.assertEqual(
                len(self.DB.getUserReceivedInvites("p%d" % i, btchDB.DECLINED)), 0
            )

        inviteId = self.DB.getUserReceivedInvites("p1")[0]
        self.DB.acceptInvite(inviteId[0])
        inviteId = self.DB.getUserReceivedInvites("p2")[0]
        self.DB.declineInvite(inviteId[0])

        self.assertEqual(len(self.DB.getUserReceivedInvites("p1", btchDB.ACCEPTED)), 1)
        self.assertEqual(len(self.DB.getUserReceivedInvites("p2", btchDB.DECLINED)), 1)
        self.assertEqual(len(self.DB.getUserReceivedInvites("p1", btchDB.PENDING)), 0)
        self.assertEqual(len(self.DB.getUserReceivedInvites("p2", btchDB.PENDING)), 0)
        self.assertEqual(len(self.DB.getUserCreatedInvites("p0", btchDB.PENDING)), 1)
        self.assertEqual(len(self.DB.getUserCreatedInvites("p0", btchDB.ACCEPTED)), 1)
        self.assertEqual(len(self.DB.getUserCreatedInvites("p0", btchDB.DECLINED)), 1)
        self.DB.clearAll()


if __name__ == "__main__":
    unittest.main()
