import sys
import os
import requests
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from scraper import AniScraper

class AnimeCard(QFrame):
    clicked = pyqtSignal(dict)

    def __init__(self, anime_data, parent=None):
        super().__init__(parent)
        self.data = anime_data
        self.setObjectName("AnimeCard")
        self.setFixedSize(220, 340)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Poster com carregamento assíncrono (simulado com requests simples aqui para brevidade)
        self.poster = QLabel()
        self.poster.setFixedSize(200, 280)
        self.poster.setStyleSheet("background-color: #2a2c31; border-radius: 8px;")
        self.poster.setAlignment(Qt.AlignCenter)
        
        if anime_data.get('image'):
            try:
                img_data = requests.get(anime_data['image'], timeout=5).content
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                self.poster.setPixmap(pixmap.scaled(200, 280, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            except:
                self.poster.setText("🎬")
        else:
            self.poster.setText("🎬")
        
        # Título
        self.title_label = QLabel(anime_data['name'])
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignTop)
        self.title_label.setFixedHeight(40)
        
        layout.addWidget(self.poster)
        layout.addWidget(self.title_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self.data)

class MainWindow(QMainWindow):
    # Sinal thread-safe para atualizar UI a partir de threads
    status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.scraper = AniScraper()
        self.setWindowTitle("AniView v1.1 - Premium Anime Player")
        self.resize(1200, 850)
        
        # Carregar Estilos
        if os.path.exists("styles.qss"):
            with open("styles.qss", "r") as f:
                self.setStyleSheet(f.read())

        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        side_layout = QVBoxLayout(sidebar)
        for icon in ["🏠", "🔍", "🔥", "⚙️"]:
            btn = QPushButton(icon)
            btn.setObjectName("NavButton")
            side_layout.addWidget(btn)
        side_layout.addStretch()
        layout.addWidget(sidebar)

        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Search Header
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchBar")
        self.search_input.setPlaceholderText("Pesquisar no AniView...")
        self.search_input.returnPressed.connect(self.search)
        search_layout.addWidget(self.search_input)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #F47521; font-weight: bold;")
        search_layout.addWidget(self.status_label)
        search_layout.addStretch()
        content_layout.addLayout(search_layout)

        # Grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(25)
        self.scroll.setWidget(self.grid_widget)
        
        content_layout.addWidget(self.scroll)
        layout.addWidget(content)

    def search(self):
        query = self.search_input.text()
        if not query: return
        
        print(f"\n[Interface] Iniciando busca por: '{query}'")
        self.status_label.setText("Buscando...")
        QApplication.processEvents()
        
        # Limpar grid
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget: widget.setParent(None)
            
        results = self.scraper.search_anime(query)
        
        if not results:
            print("[Interface] Nenhum resultado para exibir.")
            self.status_label.setText("Nenhum resultado encontrado.")
        else:
            print(f"[Interface] Renderizando {len(results)} cards.")
            self.status_label.setText(f"{len(results)} resultados encontrados.")
            for i, anime in enumerate(results):
                card = AnimeCard(anime)
                card.clicked.connect(self.select_anime)
                self.grid_layout.addWidget(card, i // 4, i % 4)

    def select_anime(self, anime):
        print(f"\n[Interface] Anime selecionado: {anime['name']}")
        ep_num, ok = QInputDialog.getInt(self, "AniView", 
                                        f"Anime: {anime['name']}\nEpisódios: {anime['episodes']}\nAssistir episódio:", 1, 1, 5000)
        if ok:
            print(f"[Interface] Solicitado episódio {ep_num}")
            self.status_label.setText("Extraindo links...")
            QApplication.processEvents()
            links = self.scraper.get_episode_links(anime['id'], ep_num)
            if links:
                print(f"[Interface] {len(links)} link(s) disponíveis. Tentando resolver...")
                self._play_url(links, anime['name'], ep_num)
            else:
                print("[Interface] Falha: Nenhum link retornado pelo scraper.")
                QMessageBox.warning(self, "AniView", "Não encontramos links ativos para este episódio.")
                self.status_label.setText("")

    def _play_url(self, links, title, ep_num):
        """Tenta cada link disponível até encontrar um que funcione"""
        import threading
        self.status_label.setText("Resolvendo links...")
        QApplication.processEvents()

        try:
            self.status_signal.disconnect()
        except: pass
        self.status_signal.connect(self.status_label.setText)

        def _run():
            title_arg = f"{title} - EP {ep_num}"
            vlc = r"C:\Program Files\VideoLAN\VLC\vlc.exe"

            # A anipy-api já retorna links diretos de vídeo (m3u8 ou mp4)
            for link in links:
                name, url = link['name'], link['url']
                print(f"[Player] Tentando {name}: {url[:70]}...")
                self.status_signal.emit(f"Abrindo {name}...")

                for cmd in [
                    ['mpv.exe', url, f'--force-media-title={title_arg}'],
                    ['mpv', url, f'--force-media-title={title_arg}'],
                    [vlc, url, f'--meta-title={title_arg}'],
                ]:
                    try:
                        subprocess.Popen(cmd)
                        print(f"[Player] ✓ Aberto com {cmd[0].split(chr(92))[-1]}: {name}")
                        self.status_signal.emit(f"▶ EP {ep_num} — {name}")
                        return
                    except FileNotFoundError:
                        continue

            # Fallback: copia a melhor URL
            fallback = links[0]['url'] if links else ''
            print(f"[Player] Nenhum player encontrado. URL: {fallback[:80]}")
            self.status_signal.emit("⚠ Instale o VLC ou MPV. URL copiada.")
            QApplication.clipboard().setText(fallback)

        threading.Thread(target=_run, daemon=True).start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
