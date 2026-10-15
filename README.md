# Campanha 2026 · Centro de Comando

Painel web para organizar a base de apoiadores de uma campanha eleitoral: lideranças, multiplicadores, bairros, veículos, apoio no dia da eleição e relatórios, tudo lido de uma planilha do Google e atualizado a cada minuto.

**Demonstração ao vivo:** <https://campanha2026.streamlit.app> (dados fictícios · senha `demo2026`)

Desenvolvido por **Lucas Soares** · Análise e Desenvolvimento de Sistemas.

## O que o painel faz

| Aba | Para que serve |
|---|---|
| Lideranças | Ranking de líderes e multiplicadores com meta individual, alerta de quem está parado e botão **Cobrar** que abre o WhatsApp com mensagem pronta. |
| Histórico | Cadastros por semana, total acumulado contra a meta, melhor semana e quem está em ritmo nos últimos 14 dias. |
| Bairros | Apoiadores por bairro e bairros da lista oficial ainda sem cadastro. |
| Perfil | Gênero, pirâmide etária, aniversariantes da semana e qualidade dos dados. |
| Veículos | Frota de apoio para o transporte no dia da eleição. |
| Apoio Extra | Quem topou adesivo, bandeira ou trabalhar no dia da eleição. |
| Duplicatas | Cadastros repetidos, com nível de confiança, para limpar a planilha. |
| Relatórios | Excel e PDF prontos para imprimir ou mandar no grupo. |

Também tem busca geral de apoiador, atalhos para as outras ferramentas da campanha (Carona Amiga, Onde eu voto, Mapa de escolas) e um modo pós-eleição com o balanço da campanha.

## Segurança e privacidade

- Senha guardada como hash PBKDF2-SHA256 (600 mil iterações), nunca em texto.
- Bloqueio por tentativas erradas (por sessão e geral) e saída automática por inatividade.
- CPF, título, nascimento e telefone ficam **mascarados** por padrão, na tela e nos relatórios. Mostrar completo exige ligar uma chave e aparece um aviso.
- A planilha é lida em modo somente leitura por uma conta de serviço do Google.

## Tecnologias

Python 3.12 · Streamlit · pandas · gspread / Google Sheets API · XlsxWriter · ReportLab. Interface própria em HTML/CSS (tema "Azul Vidro"), feita para funcionar bem no celular.

## Rodar no computador

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

Sem configuração nenhuma, o painel abre em **modo demonstração** com dados fictícios (senha `demo2026`).

## Ligar à planilha real (modo planilha)

No Streamlit Cloud, abra **Settings › Secrets** do app (no computador, crie `.streamlit/secrets.toml`, que **não** deve ir para o GitHub) e preencha:

```toml
[app]
modo = "planilha"

[auth]
senha_hash = "pbkdf2_sha256$600000$...$..."   # gere com o comando abaixo

[planilha]
id = "ID_DA_PLANILHA"            # o trecho entre /d/ e /edit no link da planilha
# aba_respostas = "Respostas ao formulário 1"   # só se os nomes das abas forem diferentes
# aba_equipe = "EQUIPE"
# aba_bairros = "BAIRROS"
# aba_secoes = "SECOES"

[gcp_service_account]
# cole aqui os campos do JSON da conta de serviço do Google
```

Para gerar o `senha_hash` (troque `SUA_SENHA`):

```bash
python -c "import hashlib,secrets;s=secrets.token_hex(16);print('pbkdf2_sha256$600000$'+s+'$'+hashlib.pbkdf2_hmac('sha256',b'SUA_SENHA',bytes.fromhex(s),600000).hex())"
```

Depois compartilhe a planilha (somente leitura) com o e-mail da conta de serviço.

## Ajustes rápidos

As regras ficam no topo de `dashboard.py`: meta por multiplicador, data da eleição, dias para considerar alguém parado, tempo de inatividade, autoria mostrada no login da demonstração (`AUTOR`) e a versão.

## Layout

O espaçamento segue uma escala única, como nos sistemas de design do IBM Carbon, Material Design e Shopify Polaris: o mesmo espaço entre todos os cards (`--gap`: 16px no celular e tablet, 20px a partir de 1200px) e 12px entre itens de lista. As colunas se adaptam à largura:

| Largura da tela | Conteúdo + coluna lateral | KPIs |
|---|---|---|
| até 899px (celular e tablet) | empilhados | 2 por linha |
| 900 a 1199px (notebook pequeno) | 3:2 | 4 por linha |
| 1200px ou mais | 2:1 | 4 por linha |
| 1600px ou mais | 2:1, área limitada a 1440px | 4 por linha |

## Cores

A paleta segue a teoria das cores, na proporção 60-30-10, e a regra de que **a mesma coisa tem sempre a mesma cor** em todas as abas:

| Papel | Cor | Uso |
|---|---|---|
| Base (60%) | Azul da marca `#2563EB` sobre azul-marinho | Fundo, botões, aba selecionada |
| Identidade dos dados (30%): análogas ao azul | Céu `#38BDF8` | Cadastros e pessoas (Histórico, Perfil, busca) |
| | Violeta `#A78BFA` | Lideranças e multiplicadores (ranking, barras "por liderança") |
| | Verde-água `#2DD4BF` | Bairros e território (ranking, barras "por bairro", cobertura) |
| Acento (10%): complementar do azul | Âmbar `#FBBF24` | Veículos, apoio extra, 1º lugar e melhor semana |
| Status | Verde `#4ADE80` | Meta batida, tudo certo |
| | Laranja `#FB923C` | Atenção: parado, conferir, líderes diferentes |
| | Coral `#FB7185` | Crítico: zero cadastros, duplicata certa, bairro sem ninguém |
| Gênero | Azul `#3B82F6` e rosa `#EC4899` | Masculino e feminino na aba Perfil |

Cada KPI tem uma faixa no topo e um ícone na cor do seu dado, e cada seção tem um marcador colorido no título. Nos rankings, a barra fica mais intensa quanto maior o valor. Os textos coloridos têm contraste de 7,2:1 a 12,1:1 sobre os cards (WCAG AAA). Como céu × violeta, âmbar × laranja e verde × coral se parecem para quem tem daltonismo, os status sempre vêm com ícone (✓ ou ⚠) e texto. As cores ficam em constantes no topo da seção UI de `dashboard.py` (`COR_CAD`, `COR_MUL`, `COR_BAI`, `COR_VEI`, `COR_OK`, `COR_ATENCAO`, `COR_CRITICO`).

## Estrutura

Todo o painel fica em **um arquivo só**, `dashboard.py`. Para atualizar, basta trocar esse arquivo no GitHub: o Streamlit Cloud publica sozinho. As versões das bibliotecas ficam fixas em `requirements.txt` para uma atualização do Streamlit não mudar o visual sem aviso.
