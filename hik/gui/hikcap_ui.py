# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'hikcap_gui.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGraphicsView, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QWidget)

class Ui_HIKCapture(object):
    def setupUi(self, HIKCapture):
        if not HIKCapture.objectName():
            HIKCapture.setObjectName(u"HIKCapture")
        HIKCapture.resize(881, 532)
        self.gridLayout = QGridLayout(HIKCapture)
        self.gridLayout.setObjectName(u"gridLayout")
        self.pushButton_detect = QPushButton(HIKCapture)
        self.pushButton_detect.setObjectName(u"pushButton_detect")

        self.gridLayout.addWidget(self.pushButton_detect, 0, 0, 1, 2)

        self.pushButton_connect = QPushButton(HIKCapture)
        self.pushButton_connect.setObjectName(u"pushButton_connect")

        self.gridLayout.addWidget(self.pushButton_connect, 0, 4, 1, 2)

        self.label_4 = QLabel(HIKCapture)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 1, 0, 1, 1)

        self.comboBox_leftcam = QComboBox(HIKCapture)
        self.comboBox_leftcam.setObjectName(u"comboBox_leftcam")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_leftcam.sizePolicy().hasHeightForWidth())
        self.comboBox_leftcam.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.comboBox_leftcam, 1, 1, 1, 1)

        self.pushButton_swtich = QPushButton(HIKCapture)
        self.pushButton_swtich.setObjectName(u"pushButton_swtich")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pushButton_swtich.sizePolicy().hasHeightForWidth())
        self.pushButton_swtich.setSizePolicy(sizePolicy1)

        self.gridLayout.addWidget(self.pushButton_swtich, 1, 2, 1, 2)

        self.label_5 = QLabel(HIKCapture)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 1, 4, 1, 1)

        self.comboBox_rightcam = QComboBox(HIKCapture)
        self.comboBox_rightcam.setObjectName(u"comboBox_rightcam")
        sizePolicy.setHeightForWidth(self.comboBox_rightcam.sizePolicy().hasHeightForWidth())
        self.comboBox_rightcam.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.comboBox_rightcam, 1, 5, 1, 1)

        self.graphicsView_left = QGraphicsView(HIKCapture)
        self.graphicsView_left.setObjectName(u"graphicsView_left")

        self.gridLayout.addWidget(self.graphicsView_left, 2, 0, 1, 3)

        self.graphicsView_right = QGraphicsView(HIKCapture)
        self.graphicsView_right.setObjectName(u"graphicsView_right")

        self.gridLayout.addWidget(self.graphicsView_right, 2, 3, 1, 3)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(HIKCapture)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.lineEdit_exposure = QLineEdit(HIKCapture)
        self.lineEdit_exposure.setObjectName(u"lineEdit_exposure")

        self.horizontalLayout.addWidget(self.lineEdit_exposure)

        self.label_2 = QLabel(HIKCapture)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)


        self.gridLayout.addLayout(self.horizontalLayout, 3, 0, 1, 2)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_3 = QLabel(HIKCapture)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_2.addWidget(self.label_3)

        self.lineEdit_gain = QLineEdit(HIKCapture)
        self.lineEdit_gain.setObjectName(u"lineEdit_gain")

        self.horizontalLayout_2.addWidget(self.lineEdit_gain)


        self.gridLayout.addLayout(self.horizontalLayout_2, 3, 4, 1, 2)

        self.pushButton_still_mode = QPushButton(HIKCapture)
        self.pushButton_still_mode.setObjectName(u"pushButton_still_mode")

        self.gridLayout.addWidget(self.pushButton_still_mode, 5, 4, 2, 2)

        self.pushButton_capture = QPushButton(HIKCapture)
        self.pushButton_capture.setObjectName(u"pushButton_capture")

        self.gridLayout.addWidget(self.pushButton_capture, 7, 4, 1, 2)

        self.pushButton_stream_mode = QPushButton(HIKCapture)
        self.pushButton_stream_mode.setObjectName(u"pushButton_stream_mode")

        self.gridLayout.addWidget(self.pushButton_stream_mode, 4, 4, 1, 2)

        self.pushButton_save_jpg = QPushButton(HIKCapture)
        self.pushButton_save_jpg.setObjectName(u"pushButton_save_jpg")

        self.gridLayout.addWidget(self.pushButton_save_jpg, 6, 0, 2, 2)

        self.pushButton_save_bmp = QPushButton(HIKCapture)
        self.pushButton_save_bmp.setObjectName(u"pushButton_save_bmp")

        self.gridLayout.addWidget(self.pushButton_save_bmp, 5, 0, 1, 2)

        self.pushButton_setexpparams = QPushButton(HIKCapture)
        self.pushButton_setexpparams.setObjectName(u"pushButton_setexpparams")

        self.gridLayout.addWidget(self.pushButton_setexpparams, 4, 0, 1, 2)


        self.retranslateUi(HIKCapture)

        QMetaObject.connectSlotsByName(HIKCapture)
    # setupUi

    def retranslateUi(self, HIKCapture):
        HIKCapture.setWindowTitle(QCoreApplication.translate("HIKCapture", u"HIKCapture", None))
        self.pushButton_detect.setText(QCoreApplication.translate("HIKCapture", u"Detect Cameras", None))
        self.pushButton_connect.setText(QCoreApplication.translate("HIKCapture", u"Connect Cameras", None))
        self.label_4.setText(QCoreApplication.translate("HIKCapture", u"Left:", None))
        self.pushButton_swtich.setText(QCoreApplication.translate("HIKCapture", u"Switch LR", None))
        self.label_5.setText(QCoreApplication.translate("HIKCapture", u"Right", None))
        self.label.setText(QCoreApplication.translate("HIKCapture", u"Exposure:", None))
        self.label_2.setText(QCoreApplication.translate("HIKCapture", u"ms", None))
        self.label_3.setText(QCoreApplication.translate("HIKCapture", u"Gain:", None))
        self.pushButton_still_mode.setText(QCoreApplication.translate("HIKCapture", u"Still Mode", None))
        self.pushButton_capture.setText(QCoreApplication.translate("HIKCapture", u"Capture", None))
        self.pushButton_stream_mode.setText(QCoreApplication.translate("HIKCapture", u"Stream Mode", None))
        self.pushButton_save_jpg.setText(QCoreApplication.translate("HIKCapture", u"Save as JPG", None))
        self.pushButton_save_bmp.setText(QCoreApplication.translate("HIKCapture", u"Save as BMP", None))
        self.pushButton_setexpparams.setText(QCoreApplication.translate("HIKCapture", u"Set EXP/GAIN", None))
    # retranslateUi

