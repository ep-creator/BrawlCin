# Como rodar

1. Criar o ambiente virtual (uma vez):

       python -m venv .venv

2. Ativar:

       .venv\Scripts\Activate.ps1      # Windows (PowerShell)
       source .venv/bin/activate       # Linux / macOS

   Se o PowerShell reclamar de permissão, rode antes:

       Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

3. Instalar as dependências:

       pip install -r requirements.txt

4. Rodar:

       python -m brawl

   O jogo é um pacote Python (`brawl/`), então roda com `-m` a partir da raiz
   do repositório. Isso é o que garante que os caminhos de assets funcionem
   independentemente de onde o comando foi chamado.

## Testes

    pip install -r requirements-dev.txt
    python -m pytest

A suíte roda headless (`SDL_VIDEODRIVER=dummy`), sem abrir janela — serve para
terminal e para CI. São ~130 testes em cerca de 3 segundos.

A varredura de navegabilidade do mapa fica fora da rodada padrão por ser mais
pesada. Vale rodá-la sempre que a hitbox dos pés, o mapa ou os spawns mudarem:

    python -m pytest -m lento

## Controles

|            | Mover       | Atirar |
|------------|-------------|--------|
| Player 1   | W A S D     | ESPAÇO |
| Player 2   | setas       | ENTER  |

`ESC` sai. No fim do campeonato, `R` reinicia e `T` volta para a seleção.

## Pendências

- [ ] Melhorar o placar
- [ ] HUD: melhorar a vida; trocar o texto dos bônus de velocidade e dano por ícone com contagem
- [ ] Redesenhar as telas de vitória de rodada e de jogo
- [ ] Avaliar mais vida para alongar a batalha
- [ ] Redesenhar a tela de seleção

O mapa é 960x540 e o mundo é desenhado numa superfície desse tamanho, escalada
uma vez por frame para a janela (`brawl/render/camera.py`). A escala dá x2
exata em 1920x1080, sem barras.

O mapa vive em `assets/mapa.tmx` e é editado no Tiled. Desenho e colisão saem
das mesmas camadas: `agua` bloqueia, `grama` esconde, e `parede` bloqueia
quando existir. Mover a água no Tiled move a colisão junto.

As hitboxes passaram a ser definidas por tamanho absoluto (corpo 24x40, pés
16x12), ancoradas nos pés do sprite, e a borda do mapa passou a bloquear por
código — nenhum mapa precisa mais desenhar a moldura.
