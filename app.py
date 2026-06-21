import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da página para o celular
st.set_page_config(page_title="Controle de Gastos Pro", page_icon="📊", layout="centered")

# --- FUNÇÕES DO BANCO DE DADOS (SQLite) ---
def conectar_banco():
    conn = sqlite3.connect("gastos.db")
    cursor = conn.cursor()
    # ATUALIZAÇÃO: Agora a tabela também salva a 'categoria'
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estabelecimento TEXT,
            valor REAL,
            tipo TEXT,
            categoria TEXT,
            data TEXT
        )
    """)
    conn.commit()
    return conn

def salvar_gasto(estabelecimento, valor, tipo, categoria):
    conn = conectar_banco()
    cursor = conn.cursor()
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute(
        "INSERT INTO compras (estabelecimento, valor, tipo, categoria, data) VALUES (?, ?, ?, ?, ?)",
        (estabelecimento, valor, tipo, categoria, data_atual)
    )
    conn.commit()
    conn.close()

def ler_gastos():
    conn = conectar_banco()
    df = pd.read_sql_query("SELECT estabelecimento, valor, tipo, categoria, data FROM compras ORDER BY id DESC", conn)
    conn.close()
    return df

# --- INTERFACE DO APLICATIVO ---

st.title("📊 Gestor Financeiro Inteligente")
st.markdown("---")

# --- Bloco 1: Formulário de Lançamento ---
st.subheader("Novo Lançamento")

with st.form(key="formulario_gasto", clear_on_submit=True):
    estabelecimento = st.text_input("Onde você gastou? (Ex: Supermercado)")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    tipo = st.selectbox("Forma de Pagamento", ["Crédito", "Débito"])
    
    # Nova caixinha para selecionar a categoria do gasto
    categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Moradia", "Saúde", "Outros"])
    
    botao_salvar = st.form_submit_button(label="Lançar Gasto")

if botao_salvar:
    if estabelecimento and valor > 0:
        salvar_gasto(estabelecimento, valor, tipo, categoria)
        st.success("Gasto categorizado e salvo!")
    else:
        st.error("Por favor, preencha o estabelecimento e um valor maior que R$ 0,00.")

st.markdown("---")

# Busca os dados atualizados do banco
dados_salvos = ler_gastos()

# Se o banco de dados estiver vazio, não mostra gráficos nem totais
if dados_salvos.empty:
    st.info("Nenhum gasto guardado ainda! Comece a lançar para ver os gráficos.")
else:
    # --- Bloco 2: Painel de Total ---
    st.subheader("Total Gasto")
    total_gasto = dados_salvos["valor"].sum()
    st.metric(label="Soma de todas as despesas", value=f"R$ {total_gasto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.markdown("---")

    # --- NOVO Bloco 3: Gráfico de Pizza por Categoria ---
    st.subheader("Resumo por Categorias")
    
    # Agrupa os valores gastos por categoria para gerar o gráfico
    df_categorias = dados_salvos.groupby("categoria")["valor"].sum().reset_index()
    
    # Cria o gráfico de pizza interativo do Plotly
    fig = px.pie(
        df_categorias, 
        values="valor", 
        names="categoria", 
        hole=0.4, # Deixa o gráfico em formato de "Donut" (mais moderno)
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Melhora o visual do gráfico na tela
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