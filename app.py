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
    Path("data/prf_inteligencia_base_v03_corrigida_provisoria.csv"),
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
    status_sel = st.multiselect("Status do registro", statuses, default=statuses)
    mostrar_todos = st.checkbox("Mostrar todos os registros, inclusive provisórios", value=True)

filtered = data.copy()
if cargo_sel != "Todos":
    filtered = filtered[filtered["cargo"] == cargo_sel]
if disciplina_sel != "Todas":
    filtered = filtered[filtered["disciplina"] == disciplina_sel]
if ano_sel != "Todos":
    filtered = filtered[filtered["ano"] == ano_sel]
if status_sel:
    filtered = filtered[filtered["status"].isin(status_sel)]
else:
    filtered = filtered.iloc[0:0]

confirmed = filtered[filtered["_ranking_confirmado"]].copy()
n_total = len(filtered)
n_confirmed = len(confirmed)
n_provisional = n_total - n_confirmed
n_subjects = filtered.loc[filtered["assunto"].str.strip().ne(""), "assunto"].nunique()
n_sources = filtered.loc[filtered["fonte"].str.strip().ne(""), "fonte"].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Registros filtrados", n_total)
c2.metric("Liberados para ranking confirmado", n_confirmed)
c3.metric("Registros provisórios/pendentes", n_provisional)
c4.metric("Fontes registradas", n_sources)

st.subheader("Ranking de incidência confirmada")
if confirmed.empty:
    st.info(
        "Ainda não há questões liberadas para o ranking confirmado. Isso é intencional: "
        "a base atual tem classificações provisórias e gabaritos pendentes de conferência oficial."
    )
else:
    ranking = (
        confirmed.assign(assunto=confirmed["assunto"].replace("", "(Assunto não informado)"))
        .groupby("assunto").size().reset_index(name="questoes_confirmadas")
        .sort_values("questoes_confirmadas", ascending=False)
    )
    ranking["percentual_%"] = (
        ranking["questoes_confirmadas"] / ranking["questoes_confirmadas"].sum() * 100
    ).round(1)
    left, right = st.columns([3, 2])
    with left:
        st.bar_chart(ranking.set_index("assunto")["questoes_confirmadas"])
    with right:
        st.dataframe(ranking, use_container_width=True, hide_index=True)

st.subheader("Distribuição provisória dos registros")
st.caption(
    "Esta seção mostra apenas como os registros atuais estão classificados. "
    "Não representa incidência oficial nem deve orientar conclusões definitivas."
)
provisional = filtered.copy()
provisional["assunto_exibicao"] = provisional["assunto"].replace("", "(Assunto não informado)")
provisional["assunto_exibicao"] = provisional["assunto_exibicao"].replace(
    "Classificação temática pendente", "(Classificação temática pendente)"
)
if not provisional.empty:
    counts = (
        provisional.groupby("disciplina", dropna=False).size()
        .reset_index(name="registros_provisórios")
        .sort_values("registros_provisórios", ascending=False)
    )
    left, right = st.columns([2, 3])
    with left:
        st.bar_chart(counts.set_index("disciplina")["registros_provisórios"])
    with right:
        st.dataframe(counts, use_container_width=True, hide_index=True)

    topic_counts = (
        provisional.groupby(["disciplina", "assunto_exibicao"], dropna=False)
        .size().reset_index(name="registros")
        .sort_values(["disciplina", "registros"], ascending=[True, False])
    )
    st.dataframe(topic_counts, use_container_width=True, hide_index=True)
else:
    st.write("Nenhum registro para os filtros selecionados.")

st.subheader("Auditoria e pendências")
if not filtered.empty:
    audit_cols = [
        "id_questao", "disciplina", "assunto", "gabarito",
        "status_gabarito", "status_classificacao", "status_enunciado",
        "pode_contar_no_ranking", "prioridade_revisao", "fonte_gabarito",
        "fonte", "validacao"
    ]
    st.dataframe(filtered[audit_cols], use_container_width=True, hide_index=True)
    pending_mask = (
        ~filtered["_ranking_confirmado"]
        | filtered["enunciado"].str.strip().eq("")
        | filtered["fonte"].str.strip().eq("")
    )
    pending = filtered[pending_mask]
    if len(pending):
        st.warning(f"{len(pending)} registro(s) ainda precisam de revisão.")
        st.dataframe(
            pending[["id_questao", "disciplina", "assunto", "status_gabarito",
                     "status_classificacao", "status_enunciado", "prioridade_revisao"]],
            use_container_width=True, hide_index=True
        )
else:
    st.write("Nenhum registro para revisar.")

st.subheader("Base de questões")
display_cols = [c for c in ALL_COLUMNS if c in filtered.columns]
if not mostrar_todos:
    filtered_display = filtered[filtered["_ranking_confirmado"]]
else:
    filtered_display = filtered
st.dataframe(filtered_display[display_cols], use_container_width=True, hide_index=True)

st.subheader("Exportar modelo para cadastrar questões")
template = pd.DataFrame(columns=ALL_COLUMNS)
st.download_button(
    "⬇️ Baixar modelo CSV",
    data=template.to_csv(index=False).encode("utf-8-sig"),
    file_name="modelo_questoes_prf_com_auditoria.csv",
    mime="text/csv",
)

