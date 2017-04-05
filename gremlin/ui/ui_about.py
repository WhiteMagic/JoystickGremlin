# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_about.ui'
#
# Created: Sat Jan 24 13:16:31 2015
#      by: PyQt5 UI code generator 5.3.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_About(object):
    def setupUi(self, About):
        About.setObjectName("About")
        About.setWindowModality(QtCore.Qt.WindowModal)
        About.resize(400, 300)
        self.horizontalLayout = QtWidgets.QHBoxLayout(About)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tabWidget = QtWidgets.QTabWidget(About)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.tab)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.about = QtWidgets.QTextBrowser(self.tab)
        self.about.setObjectName("about")
        self.horizontalLayout_4.addWidget(self.about)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.tab_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.jg_license = QtWidgets.QTextBrowser(self.tab_2)
        self.jg_license.setOpenExternalLinks(True)
        self.jg_license.setObjectName("jg_license")
        self.horizontalLayout_2.addWidget(self.jg_license)
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.tab_3)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.third_party_licenses = QtWidgets.QTextBrowser(self.tab_3)
        self.third_party_licenses.setOpenExternalLinks(True)
        self.third_party_licenses.setObjectName("third_party_licenses")
        self.horizontalLayout_3.addWidget(self.third_party_licenses)
        self.tabWidget.addTab(self.tab_3, "")
        self.horizontalLayout.addWidget(self.tabWidget)

        self.retranslateUi(About)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(About)

    def retranslateUi(self, About):
        _translate = QtCore.QCoreApplication.translate
        About.setWindowTitle(_translate("About", "About JoystickGremlin"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("About", "About"))
        self.jg_license.setHtml(_translate("About", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("About", "License"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("About", "3rd Party Licenses"))

