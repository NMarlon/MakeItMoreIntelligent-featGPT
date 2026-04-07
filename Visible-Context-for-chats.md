# Contexto Visivel para Continuacao

## 2026-04-07 - Correcao da animacao STDP em `NeuronAdjustment_lampExample.py`

Foi corrigido um erro de runtime na visualizacao da simulacao STDP em `Planning/Funcoes Detalhadas/NeuronAdjustment_lampExample.py`.

### Problema observado

- A animacao quebrava no primeiro frame com `AttributeError: 'FancyArrowPatch' object has no attribute 'get_color'`.
- A causa era a tentativa de consultar `get_color()` em um `FancyArrowPatch`, mas esse patch do matplotlib aceita `set_color(...)` e nao expoe `get_color()`.

### Correcao aplicada

- Cada aresta passou a armazenar `flash_frames`, que controla por quantos frames a conexao fica destacada depois de um ajuste STDP.
- O codigo deixou de depender da leitura da cor atual do patch para saber quando restaurar a aparencia neutra.
- O reset dos pesos agora tambem restaura largura, cor, alpha e estado visual da seta, evitando divergencia entre peso real e visualizacao.

### Aprendizado reaproveitavel

- Em animacoes do matplotlib, especialmente com `FancyArrowPatch`, e mais seguro controlar estados visuais com variaveis proprias do modelo do que depender de getters graficos que podem nao existir ou retornar formatos diferentes.
- Esse padrao combina com a ideia do projeto: a representacao interna deve guiar a acao/saida visual, e nao o contrario.

## 2026-03-26 - Levantamento da memoria do `MegaIA.py`

Foi feito um levantamento das funcoes ligadas a memoria no arquivo `MegaIA.py`, cruzando o codigo com o arquivo `megaia_memoria.json` e com as definicoes de memoria do projeto em `AGENTS.md` e `AI Instructions/Concepts Definitions and Micro-details.md`.

### Estrutura atual da memoria identificada

- `sensory_memory`: dicionario persistente indexado por `(dx, dy, symbol)` com valor inteiro clampado entre `-200` e `200`.
- `rules`: regras booleanas inferidas do mundo.
- `world_facts`: contagem e historico temporal simples de eventos como morte e recompensa.
- `timeline`: lista cronologica de eventos.
- `identity`: estado identitario simplificado por string.
- `apples_found`: contador acumulado de macas coletadas.

### Funcoes diretamente ligadas a memoria

- `__init__`: inicializa estado e carrega memoria persistida.
- `_default_rules` e `_default_world_facts`: definem a memoria estrutural inicial.
- `_clamp_truth`: limita a intensidade da memoria.
- `_normalize_memory_key`: normaliza chave da memoria sensorial.
- `_parse_sensory_memory`: le memoria antiga/heterogenea e consolida.
- `_serialize_sensory_memory`: transforma memoria em JSON.
- `_reset_runtime_state`: apaga estado em execucao.
- `_carregar_memoria`: carrega memoria persistida.
- `_salvar_memoria`: salva memoria persistida.
- `reset_memory`: reinicia memoria com backup.
- `finalizar_vida`: persiste memoria no fim do ciclo.
- `get_sensory_truth`: consulta memoria sensorial.
- `_apply_sensory_delta`: altera memoria sensorial.
- `update_sensory_truth`: transforma recompensa em ajuste de memoria, mas hoje praticamente nao participa do fluxo principal.
- `learn_from_turn`: principal atualizador de memoria e regras.
- `_record_event`: registra memoria episodica simples.
- `_temporal_risk`: consulta risco recente usando `world_facts`.
- `_safe_route_score`, `_twostep_score` e `_mental_simulate`: usam a memoria para pontuar decisoes.

### Diagnostico objetivo

- A memoria atual e util como prototipo de aprendizado persistente entre execucoes.
- Ela ja consegue armazenar experiencia local por simbolo relativo, regras simples, historico de eventos e uma identidade minima.
- Porem ela ainda nao corresponde ao modelo de memoria desejado no projeto, porque nao guarda entrada/saida por memoria, nao liga memorias entre si, nao representa causalidade explicitamente e nao separa bem curto prazo, longo prazo e memoria estrutural.

### Problemas concretos observados no estado salvo

- `sensory_memory` esta saturando: 11 de 16 registros atuais ja chegaram ao clamp `-200` ou `200`, perdendo nuance.
- A memoria e relativa ao corpo/direcao e nao ao mundo ou contexto; isso limita generalizacao e explicabilidade.
- `timeline` e `world_facts` acumulam contagens, mas quase nao viram conhecimento reutilizavel mais rico.
- `world_facts.turns` tem muitas repeticoes e nao guarda contexto suficiente do evento.
- `identity` ainda e derivada quase so de maca encontrada, ficando pobre para um agente com arbitro e autodomino.
- `update_sensory_truth` parece subutilizada; `learn_from_turn` concentra quase todo aprendizado.
- As regras sao binarias demais; uma unica observacao ja pode cristalizar uma regra como verdade total.
- Nao ha mecanismo de esquecimento inteligente, consolidacao, confianca, contradicao ou revisao causal.

### Direcao sugerida

Evoluir da memoria atual de "score por simbolo em coordenada relativa" para uma arquitetura com camadas:

1. memoria de trabalho para o turno atual
2. memoria episodica com contexto da experiencia
3. memoria semantica/estrutural com regras graduais e confianca
4. memoria causal em grafo ligando percepcao, escolha, acao, resultado e erro

Isso alinha melhor o codigo com a visao do projeto sobre verdade, identidade, atencao, previsao e crescimento sem perder conhecimento util.

## 2026-03-26 - Implementacao inicial da nova arquitetura de memoria

Foi implementada uma `memoria_v2` diretamente dentro do `MegaIA.py`, mantendo compatibilidade com a API publica do `MegaCore` e com o arquivo legado `megaia_memoria.json`.

### O que mudou na pratica

- A memoria agora persiste `turn`, `session_id` e `life_id`, resolvendo a principal inconsistência temporal encontrada antes.
- O agente passou a ter `working_memory`, `episodic_memory`, `semantic_memory`, `rule_memory`, `identity_state` e `causal_graph`.
- `sensory_memory` foi mantida como cache legado/projecao simples para nao quebrar o resto do codigo e para manter inspecao humana rapida.
- `get_sensory_truth` agora le primeiro da memoria semantica e usa um prior leve por simbolo quando a posicao exata ainda nao foi aprendida.
- `_apply_sensory_delta` deixou de ser so um ajuste numerico cru e passou a alimentar a memoria semantica com evidencia graduada.
- `learn_from_turn` agora tambem registra memoria de trabalho, episodio, elo causal e atualiza a identidade por traços.
- `rules` continuam existindo como booleanos, mas agora sao derivadas de `rule_memory`, que guarda evidencia, confianca e score.
- `main_megaia` passou a marcar novas vidas com `begin_life`, para a memoria temporal e episodica fazer sentido entre ciclos.

### Resultado do teste local

- `python -m py_compile MegaIA.py main.py tutorial.py` passou sem erro.
- Um ciclo minimo de teste com `MegaCore(memory_file='megaia_memoria_test_v3.json')` conseguiu:
  - abrir nova vida
  - aprender 1 episodio
  - criar 1 registro semantico
  - salvar memoria no novo formato

### Limitacoes atuais da memoria_v2

- A decisao ainda usa boa parte da politica antiga de score; ela ja consulta a memoria nova por baixo, mas ainda nao explora toda a riqueza episodica/causal.
- `semantic_memory` hoje representa sobretudo valencia por percepto relativo; ainda falta enriquecer contexto de acao/direcao na chave ou em estruturas derivadas.
- `rule_memory` ja e gradual, mas a inferencia ainda e simples e muito guiada por heuristicas codificadas.
- `causal_graph` ainda e compacto e textual; no futuro pode virar grafo mais formal de percepcao -> acao -> resultado -> erro.

### Proximo passo recomendado

Criar uma camada de consolidacao:

1. episodios recentes -> generalizacoes semanticas
2. semantica -> regras/causalidade mais fortes
3. identidade -> modulacao real da politica de escolha

Isso deve aproximar mais a MegaIA da ideia de memoria viva, fractal e ligada a verdade descrita no projeto.

## 2026-03-28 - Girar nao consome turno

Foi implementada uma regra simples no ambiente: apenas `avancar` e `atacar` consomem turno do mundo.

### O que mudou

- Em `main.py`, a `Dungeon.step()` agora calcula `consumes_turn` e so reduz fome, move monstros e avanca respawn quando a acao for `avancar` ou `atacar`.
- `virar_esquerda`, `virar_direita` e `pegar` deixaram de consumir turno do mundo.
- Em `MegaIA.py`, os loops de simulacao agora corrigem `core.turn` para nao avancar em acoes gratuitas.
- Em `tutorial.py`, o tutorial tambem deixou de avancar `core.turn` para acoes que nao consomem turno.

### Validacao local

- `python -m py_compile MegaIA.py main.py tutorial.py` passou.
- Teste manual rapido confirmou:
  - girar manteve a fome igual
  - girar nao moveu monstro
  - avancar continuou reduzindo fome normalmente
