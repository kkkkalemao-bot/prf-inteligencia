import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="PRF INTELIGÊNCIA", page_icon="🧠", layout="wide")

REQUIRED_COLUMNS = [
    "id_questao", "cargo", "ano", "banca", "disciplina", "assunto",
    "subassunto", "gabarito", "status", "fonte", "validacao"
]

st.title("🧠 PRF INTELIGÊNCIA")
st.caption("MVP de análise de questões — Agente Administrativo da PRF")
st.info(
    "Importante: os dados demonstrativos são fictícios. Não use os exemplos como "
    "estatísticas reais de provas. As conclusões só serão confiáveis quando a base "
    "for preenchida com questões verificadas e fontes identificadas."
)

@st.cache_data
def load_sample():
    return pd.read_csv("data/questoes_exemplo.csv", dtype=str).fillna("")

def normalize(df):
    df = df.copy()
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[REQUIRED_COLUMNS].fillna("").astype(str)

uploaded = st.sidebar.file_uploader("Importar banco de questões (CSV)", type=["csv"])
if uploaded:
    try:
        imported = pd.read_csv(uploaded, dtype=str).fillna("")
        data = normalize(imported)
        st.sidebar.success(f"{len(data)} registros importados para esta sessão.")
        st.sidebar.caption("A importação não substitui nem salva automaticamente a base original.")
    except Exception as e:
        st.sidebar.error(f"Não foi possível ler o CSV: {e}")
        data = normalize(load_sample())
else:
    data = normalize(load_sample())
    st.sidebar.caption("Usando dados fictícios de demonstração.")

with st.sidebar:
    st.header("Filtros")
    cargos = sorted([x for x in data["cargo"].unique() if x])
    cargo_sel = st.selectbox("Cargo", ["Todos"] + cargos)
    disciplinas = sorted([x for x in data["disciplina"].unique() if x])
    disciplina_sel = st.selectbox("Disciplina", ["Todas"] + disciplinas)
    anos = sorted([x for x in data["ano"].unique() if x], reverse=True)
    ano_sel = st.selectbox("Ano", ["Todos"] + anos)
    status_opts = sorted([x for x in data["status"].unique() if x])
    status_sel = st.multiselect("Status da questão", status_opts, default=status_opts)

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

valid = filtered[filtered["status"].str.lower().isin(["válida", "valida"])].copy()
n_total = len(filtered)
n_valid = len(valid)

subjects = filtered["assunto"].replace("", pd.NA).dropna()
subjects = subjects[subjects.str.lower() != "classificação temática pendente"]
n_subjects = subjects.nunique()

sources = filtered["fonte"].replace("", pd.NA).dropna()
n_sources = sources.nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Registros filtrados", n_total)
c2.metric("Questões válidas", n_valid)
c3.metric("Assuntos identificados", int(n_subjects))
c4.metric("Fontes registradas", int(n_sources))

st.subheader("Ranking de assuntos")
if n_valid == 0:
    st.warning("Não há questões válidas nos filtros atuais. Importe dados verificados ou ajuste os filtros.")
else:
    counts = (
        valid.assign(assunto=valid["assunto"].replace("", "(Assunto não informado)"))
        .groupby("assunto", dropna=False)
        .size()
        .reset_index(name="questoes")
        .sort_values("questoes", ascending=False)
    )
    counts["percentual_%"] = (counts["questoes"] / counts["questoes"].sum() * 100).round(1)
    left, right = st.columns([3, 2])
    with left:
        st.bar_chart(counts.set_index("assunto")["questoes"])
    with right:
        st.dataframe(counts, use_container_width=True, hide_index=True)

    st.subheader("Recorrência por prova/ano")
    recurring = valid.copy()
    recurring["assunto"] = recurring["assunto"].replace("", "(Assunto não informado)")
    recurring["prova_ano"] = recurring["banca"].replace("", "Banca não informada") + " — " + recurring["ano"].replace("", "Ano não informado")
    recurrence = recurring.groupby("assunto")["prova_ano"].nunique().reset_index(name="provas_ou_combinacoes_ano")
    recurrence = recurrence.sort_values("provas_ou_combinacoes_ano", ascending=False)
    st.dataframe(recurrence, use_container_width=True, hide_index=True)

st.subheader("Base de questões")
st.caption("Confere a fonte de cada questão antes de usar as estatísticas.")
st.dataframe(filtered, use_container_width=True, hide_index=True)

st.subheader("Registros que precisam de revisão")
required_for_review = ["id_questao", "disciplina", "assunto", "ano", "fonte", "validacao"]
if len(filtered):
    review_mask = pd.Series(False, index=filtered.index)
    for col in required_for_review:
        review_mask |= filtered[col].astype(str).str.strip().eq("")
    review_mask |= filtered["validacao"].str.lower().isin(["pendente", "revisar", "não revisada", "nao revisada"])
    review = filtered[review_mask]
    if len(review):
        st.warning(f"{len(review)} registro(s) precisam de revisão.")
        st.dataframe(review, use_container_width=True, hide_index=True)
    else:
        st.success("Nenhum registro incompleto ou pendente de revisão encontrado nos filtros atuais.")
else:
    st.write("Nenhum registro para revisar.")

st.subheader("Baixar modelo para cadastrar questões")
template = pd.DataFrame(columns=REQUIRED_COLUMNS)
st.download_button(
    "⬇️ Baixar modelo CSV",
    data=template.to_csv(index=False).encode("utf-8-sig"),
    file_name="modelo_questoes_prf.csv",
    mime="text/csv"
)

st.divider()
st.caption("MVP inicial. Ainda não faz leitura automática de PDFs nem classificação automática por IA.")
