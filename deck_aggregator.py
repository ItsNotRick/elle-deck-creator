from PyQt5.QtWidgets import QApplication, QFrame, QGroupBox, QFormLayout, QLineEdit, QLayout, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QMainWindow, QListView, QGridLayout, QSizePolicy, QAbstractButton, QScrollArea, QStackedWidget
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem, QIcon, QPainter, QColor
from PyQt5.QtCore import Qt, QSize, QRect, pyqtSignal
from pathlib import Path
import re
import time
import sys
import requests
import json

def parse_media_folder(mediaFolder):
    img_paths = [(pth) for pth in list(mediaFolder.glob('**/*.[pPjJ][nNpP][gG]'))]
    imgs = [(QPixmap(str(img))) for img in img_paths]
    words = [(str(pth.stem)) for pth in img_paths]
    return imgs, words, img_paths

def login(username, password):
    form = {'username': username, 'password': password}
    res = requests.post('https://endlesslearner.com/login', json=form)
    if res.status_code == 200:
        return res.json()['access_token']
    return None


# https://stackoverflow.com/questions/2711033/how-code-a-image-button-in-pyqt
class PicButton(QAbstractButton):
    def __init__(self, pixmap, label=None, path=None, parent=None):
        super(PicButton, self).__init__(parent)
        self.pixmap = pixmap
        self.label = label
        self.path = path
        self.setCheckable(True)
        self.setChecked(False)
        self.toggled.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.isChecked():
            back = QColor(160, 220, 130)
        else:
            back = QColor(240, 205, 255)
        painter.fillRect(QRect(self.pixmap.rect().x(), self.pixmap.rect().y(), self.pixmap.rect().width() + 4, self.pixmap.rect().height() + 24), back)
        painter.drawPixmap(QRect(self.pixmap.rect().x() + 2, self.pixmap.rect().y() + 22, self.pixmap.rect().width(), self.pixmap.rect().height()), self.pixmap)#event.rect(), self.pixmap)
        painter.drawText(QRect(self.pixmap.rect().x() + 2, self.pixmap.rect().y(), self.pixmap.rect().width(), 20), Qt.AlignCenter, self.label)

    def sizeHint(self):
        return QSize(self.pixmap.width() + 4, self.pixmap.height() + 24)


class ImageView(QScrollArea):
    def __init__(self, parent=None):
        super(ImageView, self).__init__(parent)
        self.setWidgetResizable(True)
        inner = QFrame(self)
        grid = QGridLayout()
        grid.setSizeConstraint(QLayout.SetFixedSize)
        self.grid = grid
        inner.setLayout(grid)
        self.setWidget(inner)


        imgs, words, paths = parse_media_folder(Path('./Images'))
        btns = []
        for img, word, path in zip(imgs, words, paths):
            img = img.scaledToHeight(150, mode=Qt.SmoothTransformation)
            rect = img.rect()
            img = img.copy((img.width() - 150)/2, 0, 150, 150)
            btn = PicButton(img, word, path)
            btns.append(btn)
        self.btns = btns
        self.fillGrid()
        self.grid.invalidate()
        #self.resize(grid.sizeHint().width() + 20, self.height())
    
    def sizeHint(self):
        w = self.grid.sizeHint().width()
        return QSize(w + 20, w*1.2)

    def fillGrid(self, filt=None):
        i = 1
        j = 0

        for btn in self.btns:
            if filt is not None:
                if re.search(re.compile(filt, flags=re.IGNORECASE), str(btn.path)) is None:
                    btn.hide()
                    continue
            w = 1
            r = btn.pixmap.rect()
            if r.width() / r.height() > 1.4:
                w = 2
            self.grid.addWidget(btn, i, j, 1, w, Qt.AlignLeft)
            btn.show()
            j += w
            if j >= 3:
                j = 0
                i += 1
    #self.show()

class FilterBar(QWidget):
    def __init__(self, parent=None):
        super(FilterBar, self).__init__(parent)
        layout = QHBoxLayout()
        self.search_lbl = QLabel('Filter:')
        self.search_box = QLineEdit()
        self.done_btn = QPushButton('Done')
        layout.addWidget(self.search_lbl)
        layout.addWidget(self.search_box)
        layout.addWidget(self.done_btn)
        self.setLayout(layout) 

class ImageSelector(QWidget):
    def __init__(self, parent=None):
        super(ImageSelector, self).__init__(parent)
        layout = QVBoxLayout()
        self.top_bar = FilterBar(self)
        layout.addWidget(self.top_bar)
        self.image_view = ImageView(self)
        layout.addWidget(self.image_view)

        self.top_bar.search_box.textChanged.connect(self.filter_imgs)

        self.setLayout(layout)

    def filter_imgs(self, query):
        self.image_view.fillGrid(query)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.resize(300, 200)
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        self.login_screen = LoginWidget(self)
        self.central_widget.addWidget(self.login_screen)
        self.central_widget.setCurrentWidget(self.login_screen)

    def successful_login(self):
        op_select_widget = OpSelectWidget(self)
        op_select_widget.new_deck_btn.clicked.connect(self.new_deck)
        self.load_screen = LoadingScreen(self)
        self.central_widget.addWidget(self.load_screen)
        self.central_widget.addWidget(op_select_widget)
        self.central_widget.setCurrentWidget(op_select_widget)


    def new_deck(self):
        self.central_widget.setCurrentWidget(self.load_screen)
        self.central_widget.repaint()
        self.image_selector = ImageSelector(self)
        self.central_widget.addWidget(self.image_selector)
        self.central_widget.setCurrentWidget(self.image_selector)
        # card_view = ImageView(self)
        # card_view.fillGrid('ch')
        # self.central_widget.addWidget(card_view)
        # self.central_widget.setCurrentWidget(card_view)
        self.resize(self.image_selector.sizeHint())

class LoadingScreen(QWidget):
    def __init__(self, parent=None):
        super(LoadingScreen, self).__init__(parent)
        layout = QHBoxLayout()
        self.loading_lbl = QLabel('Loading Images...')
        layout.addWidget(self.loading_lbl, alignment=Qt.AlignCenter)
        self.setLayout(layout)

class LoginWidget(QWidget):
    logged_in = pyqtSignal([str])
    
    def __init__(self, parent=None):
        super(LoginWidget, self).__init__(parent)
        layout = QFormLayout()
        self.username = QLineEdit()
        layout.addRow('Username', self.username)
        self.password = QLineEdit()
        layout.addRow('Password', self.password)
        self.login_btn = QPushButton('Login')
        layout.addRow(self.login_btn)
        layout.setFormAlignment(Qt.AlignCenter)
        self.layout = layout

        self.login_btn.clicked.connect(self.try_login)
        self.password.returnPressed.connect(self.try_login)
        self.setLayout(layout)

    def try_login(self):
        tok = login(self.username.text(), self.password.text())
        if tok is not None:
            self.logged_in.emit(tok)
        else:
            self.layout.addRow(QLabel('Error'))

class OpSelectWidget(QWidget):
    def __init__(self, parent=None):
        super(OpSelectWidget, self).__init__(parent)
        layout = QVBoxLayout()
        self.new_deck_btn = QPushButton('New Deck')
        self.append_deck_btn = QPushButton('Append to Deck')
        layout.addWidget(self.new_deck_btn)
        layout.addWidget(self.append_deck_btn)
        self.setLayout(layout)
    
if __name__ == '__main__':
    app = QApplication(['ELLE Uploader'])
    app.setApplicationDisplayName('ELLE Uploader')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())