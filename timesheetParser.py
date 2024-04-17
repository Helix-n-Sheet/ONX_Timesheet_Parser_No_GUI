import sys, datetime, pandas as pd

from datetime import timedelta
from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QmlElement
from PySide6.QtQuickControls2 import QQuickStyle

QML_IMPORT_NAME = "io.qt.textproperties"
QML_IMPORT_MAJOR_VERSION = 1

class Player(object):
    def __init__(self, name):
        self.name = name
        self.loggedIn = False
        self.loggedTime = datetime.timedelta(0)
        self.logins = []
        self.logouts = []

@QmlElement
class Timesheet(QObject):
    def __init__(self):
        super().__init__()
        self.timesheetString = ""
        self.displayedPlayers = []

    @Slot(str)
    def loadCSV(self, file):
        self.timesheetString = ""
        self.displayedPlayers = []
        xls = pd.ExcelFile(file)
        timezone = xls.parse('Actions', index_col=3, )
        df = xls.parse('Actions', skiprows=3, skipcolumns=1)
        self.players : Player = []
        registered = []
        for name in df.Name:
            if name not in registered:
                registered.append(name)
                self.players.append(Player(name))

        for i in range(0, len(df.Action)):
            for player in self.players:
                if df.Name[i] == player.name:
                    if df.Action[i] == 'Check In' and player.loggedIn == False:
                        player.logins.append(df.Time[i] + timedelta(hours=self.timezone))
                        player.loggedIn = True
                        break
                    if df.Action[i] == 'Check Out' and player.loggedIn == True:
                        player.logouts.append(df.Time[i]+ timedelta(hours=self.timezone))
                        player.loggedIn = False
                        break

        for player in self.players:
            for i in range(0, min(len(player.logins),len(player.logouts))):
                player.loggedTime = player.loggedTime + (player.logouts[i] - player.logins[i])

        self.players.sort(key=lambda x: x.loggedTime, reverse=True)
        for player in self.players:
            if player.loggedTime > datetime.timedelta(0):
                self.timesheetString +=  "{}     {}".format(str(player.loggedTime).rjust(17),player.name) + '\n'
                self.displayedPlayers.append(player.name)
        self.displayedPlayers.sort()
        self.displayedPlayers.insert(0, "Overview")

    @Slot(str)
    def setTimezone(self, timezone):
        self.timezone = int(timezone[-6:-3])

    @Slot(result=str)
    def getTimesheet(self):
        return self.timesheetString

    @Slot(result=list)
    def getPlayers(self):
        return self.displayedPlayers

    @Slot(str, result=str)
    def getPlayerData(self, playerSelection):
        if playerSelection == 'Overview':
            return self.timesheetString
        else:
            output = ""
            for player in self.players:
                if player.name == playerSelection:
                    output += "{} - clocked time: {}".format(player.name, str(player.loggedTime).rjust(17)) + '\n\n'
                    output += f"UTC{self.timezone}" + '\n'
                    for i in range(0, min(len(player.logins),len(player.logouts))):
                        output +=  "in: {}  -  out: {}".format(str(player.logins[i]),str(player.logouts[i])) + '\n'
            return output

    
if __name__ == '__main__':
    app = QGuiApplication(sys.argv)
    QQuickStyle.setStyle("Material")
    engine = QQmlApplicationEngine()

    qml_file = 'gui.qml'
    engine.load(qml_file)

    sys.exit(app.exec())