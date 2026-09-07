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

### Mapa e arte

- [ ] **Arte dos tiles de chão e água** — hoje são cores chapadas de 20x20.
      Trocar por arte de verdade só exige substituir os PNGs.
- [ ] **Arte da vegetação, alta** — a grama precisa de um tileset próprio com
      `tilewidth="20" tileheight="60"`: moitas da altura do personagem. O código
      já está pronto — a faixa acompanha a altura do desenho, a moita fica
      ancorada na base da célula e cresce para cima, e a profundidade continua
      sendo a base da CÉLULA. Ao desenhar:
      - o que não for folhagem precisa ser transparente, senão a moita vira bloco;
      - medido: 20px cobre 9% do sprite, 40px ~30%, 60px ~41%; acima de 60px não
        cobre mais, porque as faixas mais abaixo já não alcançam o boneco;
      - o desenho sobe, mas a REGRA de esconderijo continua vindo da célula
        pintada. Uma moita alta numa célula só vai parecer cobrir três células
        sem que as duas de cima contem como esconderijo — se incomodar, pinte a
        área toda de grama e deixe a arte um pouco mais baixa.
- [ ] **Camada `parede`** — o mapa ainda não tem nada sólido além da água. Basta
      criar uma camada de tiles com esse nome no Tiled; o código já a lê.
- [ ] **Novos sprites** — os atuais são PNGs de 376x664 reduzidos para 40x60. Ao
      trocar, conferir `TAMANHO_FRAME_JOGADOR` e as duas hitboxes junto.

### Telas e animação

- [ ] **Ajustar e criar menu** — hoje a abertura vai direto para a seleção. Não
      há menu de verdade: nem opções, nem sair, nem créditos.
- [ ] **Animação de seleção** + redesenhar a tela de seleção.
- [ ] **Animação de vitória / fim de round** + redesenhar as duas telas. Já são
      cenas separadas (`cenas/sobreposicao.py`), dá para animá-las sem tocar na
      partida.
- [ ] Melhorar o placar.
- [ ] HUD: melhorar a vida; trocar o texto dos bônus por ícone com contagem.
      Hoje usa fontes de 12 a 20 px herdadas de uma janela bem menor, desenhadas
      em 1920x1080 — fica minúsculo.

### Gameplay

- [ ] **Melhorar a gameplay** — guarda-chuva. Itens concretos já levantados:
  - [ ] Avaliar mais vida para alongar a batalha.
  - [ ] Itens não deveriam nascer colados nos spawns: o sorteio só evita
        obstáculo e outros itens, então um orbe pode aparecer ao lado do jogador
        e virar coleta grátis no início da rodada (visto na prévia do mapa novo).
  - [ ] Personagens com stats próprios: `Personagem` já tem `vida_maxima`,
        `velocidade` e `dano_base`, hoje iguais para todos.
  - [ ] `agua` hoje se comporta igual a parede; separar (lentidão? atravessar
        atirando?).
  - [ ] Sentir o `PROJETIL_ALCANCE_MAXIMO`, que subiu de 315 para 380 junto com
        o mapa novo.

### Código (continuação do refactor)

- [ ] Projétil guarda quem atirou, em vez de identificar o alvo por cor RGB (D4).
- [ ] Jogadores viram lista e `Jogador1`/`Jogador2` deixam de ser subclasses (D5).
- [ ] `Campeonato` separado da cena de partida; estado nos donos certos (D7).
- [ ] Movimento por segundo em vez de por frame (D8) — exige rebalancear.
- [ ] README com GIF e capturas, e licença. `docs/previa-*.png` são o começo.

## Já resolvido nesta rodada de refactor

- O jogo não executava (imports, APIs divergentes, caminhos de asset).
- Três laços principais viraram um só, com pilha de cenas.
- Velocidade da diagonal: era 1,414x a dos eixos, agora é igual.
- Mapa desenhado sem escala numa janela 1920x1080.
- Itens nasciam fora da arena em ~81% dos sorteios.
- Hitbox com largura negativa (-13 px) e a regra dos 50% dos arbustos, que
  qualquer encostada satisfazia.
- Borda do mapa por código, dispensando o cinturão de paredes desenhado à mão.
- Suíte de testes headless com 150 testes.
- Mapa novo 960x540 em tiles, com desenho e colisão na mesma fonte.
- Vegetação e entidades desenhadas por profundidade.
