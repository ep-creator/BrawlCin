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

- [ ] Velocidade da diagonal está ~41% maior que a dos eixos
- [ ] Mapa (791x500) é desenhado sem escala numa janela de 1920x1080
- [ ] Melhorar o placar
- [ ] HUD: melhorar a vida; trocar o texto dos bônus de velocidade e dano por ícone com contagem
- [ ] Redesenhar as telas de vitória de rodada e de jogo
- [ ] Avaliar mais vida para alongar a batalha
- [ ] Redesenhar a tela de seleção

O plano de refactor que endereça as duas primeiras está em `design-alvo.md`
(no projeto do Claude), passos 3 e 4.
