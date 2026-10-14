# PRF INTELIGÊNCIA — MVP 0.1

Painel inicial para organizar e analisar questões do concurso de Agente Administrativo da PRF.

## O que esta versão faz
- Lê um arquivo CSV com questões.
- Filtra por cargo, disciplina, ano e status.
- Mostra ranking de assuntos por quantidade e percentual.
- Mostra uma medida simples de recorrência entre combinações de banca/ano.
- Exibe a base importada e sinaliza campos ausentes ou revisões pendentes.
- Permite baixar um modelo CSV para cadastrar questões.

## Importante
`data/questoes_exemplo.csv` contém **dados fictícios de demonstração**, não estatísticas oficiais de provas da PRF.
A versão 0.1 não extrai questões de PDFs e não classifica questões automaticamente por IA.

## Como executar
1. Instale Python 3.10 ou superior.
2. Abra o terminal na pasta do projeto.
3. Instale as dependências:
   `pip install -r requirements.txt`
4. Inicie o painel:
   `streamlit run app.py`

## Como usar pelo Android
A opção mais simples é abrir um ambiente de desenvolvimento em nuvem pelo navegador e colocar os arquivos deste projeto em um repositório GitHub. Depois, publique o `app.py` em um serviço compatível com Streamlit. O fluxo exato pode mudar conforme o serviço e suas regras atuais.

## Colunas do CSV
- `id_questao`: identificador único criado por nós.
- `cargo`: ex. Agente Administrativo.
- `ano`: ano da prova.
- `banca`: banca organizadora.
- `disciplina`: disciplina da questão.
- `assunto`: assunto principal.
- `subassunto`: tópico específico.
- `gabarito`: alternativa ou resposta oficial.
- `status`: `válida`, `anulada` ou `a confirmar`.
- `fonte`: URL pública ou referência do documento.
- `validacao`: `validada`, `pendente` ou `revisar`.

## Regras para uma base confiável
1. Registrar a origem documental de cada questão.
2. Não tratar dados demonstrativos como dados reais.
3. Conferir gabaritos e questões anuladas com fontes oficiais.
4. Rever manualmente classificações incertas.
5. Deduplicar questões repetidas antes de contar.
6. Guardar cópia dos documentos de origem e da base tratada.
