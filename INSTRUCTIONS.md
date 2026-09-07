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

O mundo agora é desenhado numa superfície do tamanho nativo do mapa e escalado
uma vez por frame para a janela (`brawl/render/camera.py`). O mapa atual
(791x500) fica com barras de 106 px nas laterais; quando ele for refeito em
960x540 a escala dá inteira (x2) e preenche a tela sem barras.

Em aberto e já diagnosticado: a `hitbox_entidade` tem largura negativa
(40 - 53 = -13), o que deixa a hitbox efetiva em 13x30 e quebra a regra de
50% de cobertura dos arbustos.
