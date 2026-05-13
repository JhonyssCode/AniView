# AniView 🎌

Um player de animes para desktop com interface moderna em PyQt5 e motor de scraping focado em extração direta de links de vídeo. O AniView resolve links de streaming do AllAnime e reproduz os episódios diretamente no seu player de vídeo local (VLC ou MPV), ignorando anúncios e pop-ups de navegadores.

## ✨ Funcionalidades

- **Interface Premium**: Design "Dark Anime" utilizando PyQt5 e QSS com suporte a capas de animes via Jikan API (MyAnimeList).
- **Extração Direta**: Descriptografa blobs AES-256-CTR para extrair links diretos de vídeo (`.mp4`, `.m3u8`).
- **Reprodução Local**: Assista diretamente pelo VLC Media Player ou MPV sem abrir o navegador.
- **Auto-Fallback**: Testa múltiplos providers de vídeo automaticamente até encontrar um link funcional.

## 🚀 Como instalar

1. **Pré-requisitos**:
   - [Python 3.9+](https://www.python.org/downloads/)
   - [VLC Media Player](https://www.videolan.org/vlc/) instalado na máquina.
   - [Git](https://git-scm.com/downloads) (Opcional, para clonar)

2. **Clone ou baixe este repositório**:
   ```bash
   git clone https://github.com/JhonyssCode/AniView.git
   cd AniView
   ```

3. **Instale as dependências Python**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Dependências principais: `PyQt5`, `requests`, `pycryptodome`, `yt-dlp`)*

## 🎬 Como rodar

Basta executar o arquivo principal:

```bash
python main.py
```

1. Digite o nome do anime na barra de busca (ex: "Jujutsu Kaisen").
2. Clique no anime desejado.
3. Escolha o número do episódio e clique em "Assistir".
4. O VLC abrirá automaticamente com o vídeo!

## ⚠️ Aviso Legal
Este projeto foi construído para fins estritamente **educacionais** de estudo de web scraping e descriptografia de tráfego de rede. O AniView não hospeda nenhum conteúdo de vídeo protegido por direitos autorais, apenas atua como um buscador de links públicos.
