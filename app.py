import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client

# Configuração da página para o celular
st.set_page_config(page_title="Controle de Gastos Compartilhado", page_icon="📊", layout="centered")

# --- CONEXÃO COM O SUPABASE (VIA API) ---
# Substitua com os dados que você copiou do Passo 2
SUPABASE_URL = "https://sfvfxkxwqvbekdtufxby.supabase.co/rest/v1/compras"
SUPABASE_KEY = "sb_publishable_rZebB_4zb2V58wfJ6Vf5sQ_rUmDq1QT"

# Inicializa o cliente do banco de dados
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def salvar_gasto(estabelecimento, valor, tipo, categoria):
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
    dados = {
        "estabelecimento": estabelecimento,
        "valor": float(valor),
        "tipo": tipo,
        "categoria": categoria,
        "data": data_atual
    }
    # Insere diretamente na tabela do Supabase
    supabase.table("compras").insert(dados).execute()

def ler_gastos():
    # Busca todas as linhas da tabela
    resposta = supabase.table("compras").select("*").order("id", desc=True).execute()
    if resposta.data:
        return pd.DataFrame(resposta.data)
    return pd.DataFrame()

# --- INTERFACE DO APLICATIVO ---

st.title("📊 Nosso Gestor Financeiro")
st.markdown("---")

st.subheader("Novo Lançamento")

with st.form(key="formulario_gasto", clear_on_submit=True):
    estabelecimento = st.text_input("Onde foi o gasto?")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    tipo = st.selectbox("Forma de Pagamento", ["Crédito", "Débito", "Pix", "Dinheiro"])
    categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Moradia", "Saúde", "Outros"])
    
    botao_salvar = st.form_submit_button(label="Lançar Gasto")

if botao_salvar:
    if estabelecimento and valor > 0:
        try:
            salvar_gasto(estabelecimento, valor, tipo, categoria)
            st.success("Gasto salvo na nuvem com sucesso!")
            st.rerun()
        except Exception as e:
            st.error("Erro ao salvar! Certifique-se de que a tabela 'compras' foi criada no painel do Supabase.")
    else:
        st.error("Por favor, preencha o estabelecimento e um valor maior que R$ 0,00.")

st.markdown("---")

try:
    dados_salvos = ler_gastos()
except Exception as e:
    dados_salvos = pd.DataFrame()

if dados_salvos.empty:
    st.info("Nenhum gasto guardado ainda! Comece a lançar para ver os gráficos.")
else:
    st.subheader("Total Gasto")
    total_gasto = dados_salvos["valor"].sum()
    st.metric(label="Soma de todas as despesas", value=f"R$ {total_gasto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.markdown("---")

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

    st.subheader("Histórico de Compras")
    dados_exibicao = dados_salvos[["estabelecimento", "valor", "tipo", "categoria", "data"]].rename(columns={
        "estabelecimento": "Estabelecimento",
        "valor": "Valor (R$)",
        "tipo": "Tipo",
        "categoria": "Categoria",
        "data": "Data"
    })
    st.dataframe(dados_exibicao, use_container_width=True, hide_index=True)