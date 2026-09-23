# Car Wiki

Site de pesquisa de carros em estilo wiki, feito em Python com Streamlit.

- **Buscar carros:** anúncios de vários sites, com endereço, filtros (ano, preço, km, estado, cidade, câmbio, combustível) e comparação do preço com a FIPE.
- **Wiki do carro:** ficha técnica em formato de verbete, montada pela IA a partir de sites de ficha técnica.
- **Comparar:** fichas técnicas lado a lado, com o melhor valor de cada linha destacado e uma análise escrita pela IA.
- **Tabela FIPE:** preço por marca, modelo e ano, com gráfico do preço por ano.

## Publicar na web (Streamlit Community Cloud, grátis)

O Streamlit Cloud instala tudo sozinho a partir do `requirements.txt`. **Não precisa de `venv`.**

1. Crie um repositório no GitHub e suba o conteúdo desta pasta (o `.gitignore` já deixa `venv/` e segredos de fora).
2. Entre em <https://share.streamlit.io> com a conta do GitHub e clique em **Create app**.
3. Escolha o repositório, a branch `main` e o arquivo principal `app.py`.
4. Em **Advanced settings > Secrets**, cole:
   ```toml
   ANTHROPIC_API_KEY = "sua-chave"
   ```
5. Clique em **Deploy**. Em alguns minutos o site fica online, com link para compartilhar.

A chave da API é criada em <https://console.anthropic.com> e é separada da assinatura do Claude.ai. Sem ela o site funciona, mas sem ficha técnica organizada e sem comparação.

## Rodar no computador

```
pip install -r requirements.txt
streamlit run app.py
```

Para usar a IA localmente, copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml` e ponha a chave.

## Como o projeto está organizado

```
app.py                  navegação entre as páginas
views/                  as 4 páginas (buscar, wiki, comparar, tabela_fipe)
carwiki/config.py       lista de sites e campos da ficha técnica
carwiki/search.py       pesquisa nos sites (anúncios e fichas)
carwiki/fipe.py         Tabela FIPE
carwiki/ai.py           módulo de IA (extrai ficha e compara)
carwiki/wiki.py         junta pesquisa e IA para montar a ficha de um carro
carwiki/ui.py           cartões, infobox, tabela de comparação, CSS
```

Para incluir outro site, adicione uma linha em `FONTES` no `carwiki/config.py`. Use `papel: "anuncios"` para entrar na busca de carros ou `papel: "ficha"` para servir de fonte da ficha técnica.

## Limitações

- **Os sites mudam e podem bloquear robôs.** A busca usa o DuckDuckGo com `site:` e lê os dados públicos da página (título, foto, JSON-LD). Se um site passar a bloquear, o card aparece sem foto ou endereço e um aviso é exibido. Cada site pode exigir um ajuste em `search.py`.
- **Confira os termos de uso** de cada site antes de divulgar o seu. Alguns proíbem coleta automática. O site sempre leva o usuário ao anúncio original e guarda resultados em cache para fazer poucas requisições.
- **A FIPE vem de uma API aberta** (`fipe.parallelum.com.br`), porque o site oficial não tem API. Sem token são 500 consultas por dia. Para mais, crie um token gratuito e ponha em `FIPE_TOKEN`.
- **A IA pode errar.** Ela só usa o texto das páginas lidas e deixa em branco o que não achar, mas a ficha deve ser conferida nas fontes listadas.
- **O endereço** só aparece quando o anúncio informa (cidade e estado, ou endereço completo da loja). Não é geocodificado, e não há mapa.
