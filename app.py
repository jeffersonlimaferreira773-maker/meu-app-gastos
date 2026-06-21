import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from sqlalchemy import create_engine, text

# Configuração da página para o celular
st.set_page_config(page_title="Controle de Gastos Compartilhado", page_icon="📊", layout="centered")

# --- CONEXÃO COM O BANCO DE DADOS (SUPABASE VIA SQLALCHEMY) ---
# Mudamos o início para 'postgresql+pg8000://' e usamos a porta pooler 6543
DB_URI = "postgresql+pg8000://postgres:joh0703201404061994@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"

# Cria o motor de conexão
engine = create_engine(DB_URI, pool_pre_ping=True)

# Cria a tabela na nuvem se ela ainda não existir
def criar_tabela():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS compras (
                id SERIAL PRIMARY KEY,
                estabelecimento TEXT,
                valor REAL,
                tipo TEXT,
                categoria TEXT,
                data TEXT
            )
        """))

# Executa a criação da tabela logo na abertura do app
criar_tabela()

def salvar_gasto(estabelecimento, valor, tipo, categoria):
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO compras (estabelecimento, valor, tipo, categoria, data) VALUES (:est, :val, :tipo, :cat, :data)"),
            {"est": estabelecimento, "val": valor, "tipo": tipo, "cat": categoria, "data": data_atual}
        )

def ler_gastos():
    with engine.connect() as conn:
        df = pd.read_sql_query(text("SELECT estabelecimento, valor, tipo, categoria, data FROM compras ORDER BY id DESC"), conn)
    return df
# --- INTERFACE DO APLICATIVO ---

st.title("📊 Nosso Gestor Financeiro")
st.markdown("---")

# --- Bloco 1: Formulário de Lançamento ---
st.subheader("Novo Lançamento")

with st.form(key="formulario_gasto", clear_on_submit=True):
    estabelecimento = st.text_input("Onde foi o gasto?")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    tipo = st.selectbox("Forma de Pagamento", ["Crédito", "Débito", "Pix", "Dinheiro"])
    categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Moradia", "Saúde", "Outros"])
    
    botao_salvar = st.form_submit_button(label="Lançar Gasto")

if botao_salvar:
    if estabelecimento and valor > 0:
        salvar_gasto(estabelecimento, valor, tipo, categoria)
        st.success("Gasto salvo na nuvem com sucesso!")
        st.rerun()
    else:
        st.error("Por favor, preencha o estabelecimento e um valor maior que R$ 0,00.")

st.markdown("---")

# Busca os dados atualizados do banco na nuvem
try:
    dados_salvos = ler_gastos()
except Exception as e:
    dados_salvos = pd.DataFrame()

if dados_salvos.empty:
    st.info("Nenhum gasto guardado ainda! Comece a lançar para ver os gráficos.")
else:
    # --- Bloco 2: Painel de Total ---
    st.subheader("Total Gasto")
    total_gasto = dados_salvos["valor"].sum()
    st.metric(label="Soma de todas as despesas", value=f"R$ {total_gasto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.markdown("---")

    # --- Bloco 3: Gráfico de Pizza por Categoria ---
    st.subheader("Resumo por Categorias")
    df_categorias = dados_salvos.groupby("categoria")["valor"].sum().reset_index()
    
    fig = px.pie(
        df_categorias, 
        values="valor", 
        names="categoria", 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # --- Bloco 4: Histórico ---
    st.subheader("Histórico de Compras")
    dados_exibicao = dados_salvos.rename(columns={
        "estabelecimento": "Estabelecimento",
        "valor": "Valor (R$)",
        "tipo": "Tipo",
        "categoria": "Categoria",
        "data": "Data"
    })
    st.dataframe(dados_exibicao, use_container_width=True, hide_index=True)