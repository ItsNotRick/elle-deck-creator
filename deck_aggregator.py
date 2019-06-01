from PyQt5.QtWidgets import QApplication, QFrame, QGroupBox, QFormLayout, QComboBox, QLineEdit, QLayout, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QMainWindow, QListView, QGridLayout, QSizePolicy, QAbstractButton, QScrollArea, QStackedWidget
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem, QIcon, QPainter, QColor
from PyQt5.QtCore import Qt, QSize, QRect, pyqtSignal
from pathlib import Path
import re
import time
import sys
import requests
import json

APIURL = 'https://endlesslearner.com'
#APIURL = 'http://localhost:5000'

def parse_image_folder(imageFolder):
    img_paths = [(pth) for pth in list(imageFolder.glob('**/*.[pPjJ][nNpP][gG]'))]
    imgs = [(QPixmap(str(img))) for img in img_paths]
    words = [(str(pth.stem)) for pth in img_paths]
    return imgs, words, img_paths

def parse_sound_folder(soundFolder):
    snd_paths = [(pth) for pth in list(soundFolder.glob('**/*.ogg'))]
    words = [(str(pth.stem)) for pth in snd_paths]
    snd_dict = {}
    print(snd_paths)
    print(words)
    for pth, wrd in zip(snd_paths, words):
        snd_dict[wrd] = pth
    print(snd_dict)
    return snd_dict

def login(username, password):
    form = {'username': username, 'password': password}
    res = requests.post(APIURL + '/login', json=form)
    print(res.status_code)
    if res.status_code == 200:
        return res.json()['access_token']
    return None

def gather_deck_names(token):
    head = {'Authorization': 'Bearer ' + str(token)}
    res = requests.get(APIURL + '/decks', headers=head)
    if res.status_code == 200:
        return res.json()
    else:
        return None

def post_new_deck(token, name, ltype):
    head = {'Authorization': 'Bearer ' + str(token)}
    data = {'deckName': name, 'ttype': ltype}
    res = requests.post(APIURL + '/deck', json=data, headers=head)
    if res.status_code == 201:
        return res.json()['deckID']
    return -1

def post_card(token, deck_id, card):
    print(str(token) + ' : ' + str(deck_id) + ' : ' + str(card))
    head = {'Authorization': 'Bearer ' + str(token)}
    data = {'front': card.source.text(), 'back': card.dest.text(), 'cardName': card.source.text(), 'difficulty': 1}
    res_card = requests.post(APIURL + '/card/' + str(deck_id), json=data, headers=head)
    print(res_card.status_code)
    if res_card.status_code == 201:
        img_data = {'file': open(card.c.path, 'rb')}
        res_img = requests.post(APIURL + '/card/image/' + str(res_card.json()['cardID']), files=img_data, headers=head)
        if (card.sound_file.text() != ''):
            snd_data = {'file': open(card.sound_file.text(), 'rb')}
            res_ind = requests.post(APIURL + '/card/sound/' + str(res_card.json()['cardID']), files=snd_data, headers=head)


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
            back = QColor(120, 220, 100)
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


        imgs, words, paths = parse_image_folder(Path('./Images'))
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

class FilterBar(QWidget):
    def __init__(self, parent=None):
        super(FilterBar, self).__init__(parent)
        layout = QHBoxLayout()
        self.search_lbl = QLabel('Filter:')
        self.search_box = QLineEdit()
        self.done_btn = QPushButton('Next')
        layout.addWidget(self.search_lbl)
        layout.addWidget(self.search_box)
        layout.addWidget(self.done_btn)
        self.setLayout(layout) 

class ImageSelector(QWidget):
    done_selecting = pyqtSignal([list])

    def __init__(self, parent=None):
        super(ImageSelector, self).__init__(parent)
        layout = QVBoxLayout()
        self.top_bar = FilterBar(self)
        layout.addWidget(self.top_bar)
        self.image_view = ImageView(self)
        layout.addWidget(self.image_view)

        self.top_bar.search_box.textChanged.connect(self.filter_imgs)
        self.top_bar.done_btn.clicked.connect(self.done)

        self.setLayout(layout)

    def filter_imgs(self, query):
        self.image_view.fillGrid(query)

    def done(self):
        sel = [(btn) for btn in self.image_view.btns if btn.isChecked()]
        if sel is not None:
            self.done_selecting.emit(sel)

class Card(QWidget):
    def __init__(self, parent=None, c=None):
        super(Card, self).__init__(parent)
        cform = QFormLayout()
        self.c = c
        self.source = QLineEdit(c.label)
        self.dest = QLineEdit()
        self.sound_file = QLineEdit()
        cform.addRow(QLabel('Source:'), self.source)
        cform.addRow(QLabel('Destination:'), self.dest)
        cform.addRow(QLabel('Sound File:'), self.sound_file)
        cform.setVerticalSpacing(15)
        self.setLayout(cform)

class CardView(QScrollArea):
    def __init__(self, parent=None, cards=None):
        super(CardView, self).__init__(parent)
        self.setWidgetResizable(True)
        inner = QFrame(self)
        layout = QFormLayout()
        #layout.setSizeConstraint(QLayout.SetFixedSize)
        self.card_data = []
        for c in cards:
            lbl = QLabel()
            lbl.setPixmap(c.pixmap)
            cont = Card(self, c)
            self.card_data.append(cont)
            layout.addRow(lbl, cont)
        inner.setLayout(layout)
        self.setWidget(inner)

class NewDeckBar(QWidget):
    def __init__(self, parent=None):
        super(NewDeckBar, self).__init__(parent)
        layout = QHBoxLayout()
        self.deck_name_lbl = QLabel('Deck Name:')
        self.deck_name_box = QLineEdit()
        self.deck_language_lbl = QLabel('Deck Language:')
        self.deck_language_box = QLineEdit()
        self.sound_search_btn = QPushButton('Populate Sounds')
        self.submit_btn = QPushButton('Submit')
        layout.addWidget(self.deck_name_lbl)
        layout.addWidget(self.deck_name_box)
        layout.addWidget(self.deck_language_lbl)
        layout.addWidget(self.deck_language_box)
        layout.addWidget(self.sound_search_btn)
        layout.addWidget(self.submit_btn)
        self.setLayout(layout)

class TranslationPhase(QWidget):
    def __init__(self, parent=None, cards=None):
        super(TranslationPhase, self).__init__(parent)
        layout = QVBoxLayout()
        self.deck_bar = NewDeckBar(self)
        layout.addWidget(self.deck_bar)
        self.card_view = CardView(self, cards)
        layout.addWidget(self.card_view)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.resize(300, 200)
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        self.login_screen = LoginWidget(self)
        self.central_widget.addWidget(self.login_screen)
        self.central_widget.setCurrentWidget(self.login_screen)
        self.login_screen.logged_in.connect(self.successful_login)

    def submit_deck(self):
        if self.deck_id == -1:
            print("SUBMIT DECK")
            deck_name = self.translation_phase.deck_bar.deck_name_box.text()
            deck_language = self.translation_phase.deck_bar.deck_language_box.text()
            self.deck_id = post_new_deck(self.token, deck_name, deck_language)
        if self.deck_id != -1:
            print("SUBMIT CARDS")
            for card in self.translation_phase.card_view.card_data:
                post_card(self.token, self.deck_id, card)

    def sound_search(self):
        language = self.translation_phase.deck_bar.deck_language_box.text()
        snd_dict = parse_sound_folder(Path('./Sounds/' + language))
        for card in self.translation_phase.card_view.card_data:
            card.sound_file.setText(str(snd_dict.get(card.source.text(), str(Path('Sounds/invalid_game_mode.ogg')))))


    def successful_login(self, token):
        self.token = token
        self.op_select_widget = OpSelectWidget(token, parent=self)
        self.op_select_widget.new_deck_btn.clicked.connect(self.new_deck)
        self.op_select_widget.append_deck_btn.clicked.connect(self.append_deck)
        self.load_screen = LoadingScreen(self)
        self.central_widget.addWidget(self.load_screen)
        self.central_widget.addWidget(self.op_select_widget)
        self.central_widget.setCurrentWidget(self.op_select_widget)

    def to_translation_phase(self, cards):
        self.translation_phase = TranslationPhase(self, cards)
        self.central_widget.addWidget(self.translation_phase)
        self.central_widget.setCurrentWidget(self.translation_phase)
        self.translation_phase.deck_bar.submit_btn.clicked.connect(self.submit_deck)
        self.translation_phase.deck_bar.sound_search_btn.clicked.connect(self.sound_search)

    def add_cards(self):
        self.central_widget.setCurrentWidget(self.load_screen)
        self.central_widget.repaint()
        self.image_selector = ImageSelector(self)
        self.central_widget.addWidget(self.image_selector)
        self.central_widget.setCurrentWidget(self.image_selector)
        self.image_selector.done_selecting.connect(self.to_translation_phase)
        self.resize(self.image_selector.sizeHint())

    def append_deck(self):
        ind = self.op_select_widget.decks_combo.currentIndex()
        self.deck_id = self.op_select_widget.decks['ids'][ind]
        self.add_cards()

    def new_deck(self):
        self.deck_id = -1
        self.add_cards()

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
        layout.setVerticalSpacing(20)
        self.username = QLineEdit()
        layout.addRow('Username', self.username)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
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
    def __init__(self, token, parent=None):
        super(OpSelectWidget, self).__init__(parent)
        layout = QFormLayout()
        layout.setVerticalSpacing(60)
        self.decks = gather_deck_names(token)
        self.new_deck_btn = QPushButton('Create New Deck')
        self.decks_combo = QComboBox()
        self.decks_combo.addItems(self.decks['names'])
        self.append_deck_btn = QPushButton('Append to Deck')
        layout.addRow(self.new_deck_btn)
        layout.addRow(self.decks_combo, self.append_deck_btn)
        self.setLayout(layout)
    
if __name__ == '__main__':
    app = QApplication(['ELLE Uploader'])
    app.setApplicationDisplayName('ELLE Uploader')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())