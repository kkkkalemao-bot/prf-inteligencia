import io
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="PRF INTELIGÊNCIA", page_icon="🧠", layout="wide")

BASE_COLUMNS = [
    "id_questao", "cargo", "ano", "banca", "disciplina", "assunto",
    "subassunto", "gabarito", "status", "fonte", "validacao"
]
AUDIT_COLUMNS = [
    "status_gabarito", "status_classificacao", "status_enunciado",
    "pode_contar_no_ranking", "prioridade_revisao", "fonte_gabarito"
]
ALL_COLUMNS = BASE_COLUMNS + [
    "enunciado", "alternativas", "resumo_tema", "confianca_gabarito",
    "observacoes"
] + AUDIT_COLUMNS

st.title("🧠 PRF INTELIGÊNCIA")
st.caption("Painel de análise de questões — PRF Agente Administrativo")

st.warning(
    "Base em fase de auditoria. A classificação temática é provisória e os "
    "gabaritos ainda precisam ser conferidos em fonte oficial. Os registros "
    "provisórios NÃO entram no ranking de incidência confirmada."
)

def normalize(df):
    df = df.copy()
    for col in ALL_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[ALL_COLUMNS].fillna("").astype(str)

@st.cache_data
def load_csv(path, modified_time):
    return pd.read_csv(path, dtype=str).fillna("")

def find_default_csv():
    candidates = [
        Path("data/prf_inteligencia_base_v03_auditoria.csv"),
        Path("prf_inteligencia_base_v03_auditoria.csv"),
        Path("data/prf_inteligencia_base_2014_60_questoes_classificacao_provisoria.csv"),
        Path("data/prf_inteligencia_base_2014_60_questoes_organizada.csv"),
        Path("data/prf_inteligencia_base_2014_60_questoes.csv"),
    ]
    for path in candidates:
        if path.exists():
            return path
    return None

uploaded = st.sidebar.file_uploader("Importar banco de questões (CSV)", type=["csv"])
default_path = find_default_csv()

if uploaded is not None:
    try:
        imported = pd.read_csv(uploaded, dtype=str).fillna("")
        data = normalize(imported)
        st.sidebar.success(f"{len(data)} registros importados nesta sessão.")
        st.sidebar.caption("A importação não altera o arquivo no GitHub.")
    except Exception as exc:
        st.sidebar.error(f"Não foi possível ler o CSV: {exc}")
        data = pd.DataFrame(columns=ALL_COLUMNS)
elif default_path is not None:
    try:
        data = normalize(load_csv(str(default_path), default_path.stat().st_mtime))
        st.sidebar.success(f"Base carregada: {default_path.name}")
    except Exception as exc:
        st.error(f"Erro ao carregar a base: {exc}")
        st.stop()
else:
    st.error(
        "Não encontrei um CSV de questões. Coloque a base v0.3 em "
        "`data/prf_inteligencia_base_v03_auditoria.csv` ou importe um CSV na barra lateral."
    )
    st.stop()

# Auditoria explícita: só registros marcados como liberados podem alimentar ranking confirmado.
ranking_flag = data["pode_contar_no_ranking"].str.strip().str.lower()
gabarito_status = data["status_gabarito"].str.strip().str.lower()
class_status = data["status_classificacao"].str.strip().str.lower()
ranking_released = ranking_flag.isin(["sim", "yes", "true", "1"])
official_key = gabarito_status.str.contains("oficial|confirmado|verificado", regex=True)
classification_confirmed = class_status.str.contains("confirmad|validada|validado", regex=True)
data["_ranking_confirmado"] = ranking_released & official_key & classification_confirmed

with st.sidebar:
    st.header("Filtros")
    cargos = sorted(x for x in data["cargo"].unique() if x.strip())
    cargo_sel = st.selectbox("Cargo", ["Todos"] + cargos)
    disciplinas = sorted(x for x in data["disciplina"].unique() if x.strip())
    disciplina_sel = st.selectbox("Disciplina", ["Todas"] + disciplinas)
    anos = sorted((x for x in data["ano"].unique() if x.strip()), reverse=True)
    ano_sel = st.selectbox("Ano", ["Todos"] + anos)
    statuses = sorted(x for x in data["status"].unique() if x.strip())
