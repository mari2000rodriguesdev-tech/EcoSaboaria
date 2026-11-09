import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(
    page_title="Gestão EcoSaboaria Artesanal",
    page_icon="🧼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# 1. CONTROLE DE SESSÃO E AUTENTICAÇÃO
# -------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_pin(pin_input: str) -> bool:
    try:
        correct_pin = str(st.secrets.get("ACCESS_PIN", "1234"))
    except FileNotFoundError:
        correct_pin = "1234"
    return pin_input == correct_pin

def login_screen():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("### 🧼 EcoSaboaria Artesanal")
        st.caption("Acesso ao painel administrativo e financeiro")
        with st.form("pin_login_form"):
            pin = st.text_input("PIN de Acesso", type="password", max_chars=8, placeholder="Digite o PIN...")
            if st.form_submit_button("Entrar no Painel", use_container_width=True):
                if check_pin(pin.strip()):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("PIN incorreto. Tente novamente.")

def logout():
    st.session_state.authenticated = False
    st.rerun()

if not st.session_state.authenticated:
    login_screen()
    st.stop()

# -------------------------------------------------------------
# 2. BASE DE DADOS EM MEMÓRIA (PERSISTENTE NA SESSÃO)
# -------------------------------------------------------------
if "pedidos" not in st.session_state:
    hoje = date.today()
    st.session_state.pedidos = pd.DataFrame([
        {"id": 1, "data": hoje - timedelta(days=6), "cliente": "Mariana Souza", "tipo": "Eventos (Casamento)", "linha": "Lavanda & Aveia", "quantidade": 80, "valor_total": 480.00, "custo_total": 210.00, "status": "Entregue"},
        {"id": 2, "data": hoje - timedelta(days=4), "cliente": "Carla Mendes", "tipo": "Varejo / Presente", "linha": "Argila Branca & Mel", "quantidade": 4, "valor_total": 68.00, "custo_total": 26.00, "status": "Entregue"},
        {"id": 3, "data": hoje - timedelta(days=2), "cliente": "Clínica Bem Estar", "tipo": "Eventos (Corporativo)", "linha": "Alecrim & Capim-Limão", "quantidade": 50, "valor_total": 325.00, "custo_total": 140.00, "status": "Em Produção"},
        {"id": 4, "data": hoje - timedelta(days=1), "cliente": "Fernanda Lima", "tipo": "Eventos (Maternidade)", "linha": "Camomila Baby", "quantidade": 35, "valor_total": 245.00, "custo_total": 105.00, "status": "Em Produção"},
        {"id": 5, "data": hoje, "cliente": "Beatriz Rocha", "tipo": "Varejo / Presente", "linha": "Café Esfoliante", "quantidade": 2, "valor_total": 36.00, "custo_total": 13.00, "status": "Pendente"}
    ])

# -------------------------------------------------------------
# 3. BARRA LATERAL: FILTROS DINÂMICOS & AÇÕES
# -------------------------------------------------------------
with st.sidebar:
    st.title("🧼 EcoSaboaria Artesanal")
    st.caption("Filtros de Exibição")

    # Filtro de Período
    datas = st.session_state.pedidos["data"]
    data_inicio = st.date_input("De:", min(datas))
    data_fim = st.date_input("Até:", max(datas))

    # Filtro por Linha e Categoria
    todos_tipos = list(st.session_state.pedidos["tipo"].unique())
    tipos_selecionados = st.multiselect("Categoria de Venda", todos_tipos, default=todos_tipos)

    todos_status = list(st.session_state.pedidos["status"].unique())
    status_selecionados = st.multiselect("Status do Pedido", todos_status, default=todos_status)

    st.divider()
    if st.button("Encerrar Sessão", use_container_width=True):
        logout()

# Aplicação dos filtros sobre a base
df = st.session_state.pedidos.copy()
df = df[
    (df["data"] >= data_inicio) &
    (df["data"] <= data_fim) &
    (df["tipo"].isin(tipos_selecionados)) &
    (df["status"].isin(status_selecionados))
]

# -------------------------------------------------------------
# 4. ABAS PRINCIPAIS DO DASHBOARD
# -------------------------------------------------------------
aba1, aba2, aba3 = st.tabs([
    "📊 Visão Geral & Métricas",
    "📝 Gerenciador de Encomendas",
    "🧮 Calculadora de Custo & Lucro"
])

# -------------------------------------------------------------
# ABA 1: VISÃO GERAL & MÉTRICAS
# -------------------------------------------------------------
with aba1:
    faturamento = df["valor_total"].sum()
    custos = df["custo_total"].sum()
    lucro = faturamento - custos
    margem = (lucro / faturamento * 100) if faturamento > 0 else 0.0
    total_unidades = df["quantidade"].sum()

    # Cartões de Métricas (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Faturamento Filtrado", f"R$ {faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col2.metric("Lucro Bruto", f"R$ {lucro:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), f"{margem:.1f}% margem")
    col3.metric("Unidades Vendidas", f"{total_unidades} un")
    col4.metric("Pedidos Listados", f"{len(df)} pedidos")

    st.markdown("---")

    # Gráficos Dinâmicos
    col_graf1, col_graf2 = st.columns([1.5, 1])

    with col_graf1:
        st.subheader("Receita por Categoria de Venda")
        if not df.empty:
            receita_categoria = df.groupby("tipo")["valor_total"].sum()
            st.bar_chart(receita_categoria, color="#4A7C59")
        else:
            st.info("Nenhum pedido encontrado para os filtros selecionados.")

    with col_graf2:
        st.subheader("Volume por Fragrância / Linha")
        if not df.empty:
            volume_linha = df.groupby("linha")["quantidade"].sum()
            st.bar_chart(volume_linha, horizontal=True)
        else:
            st.info("Sem dados para o período.")

# -------------------------------------------------------------
# ABA 2: GERENCIADOR DE ENCOMENDAS
# -------------------------------------------------------------
with aba2:
    st.subheader("Pedidos e Prazos de Entrega")

    # Exibição interativa da tabela
    st.dataframe(
        df[["data", "cliente", "tipo", "linha", "quantidade", "valor_total", "status"]],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    st.subheader("Cadastrar Novo Pedido")

    with st.form("novo_pedido_form", clear_on_submit=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            nome_cliente = st.text_input("Nome do Cliente")
            tipo_pedido = st.selectbox("Canal de Venda", ["Varejo / Presente", "Eventos (Casamento)", "Eventos (Maternidade)", "Eventos (Corporativo)", "Eventos (Aniversário)"])
        with f_col2:
            linha_sabonete = st.text_input("Aroma / Linha", placeholder="Ex: Alecrim & Argila Verde")
            quantidade = st.number_input("Quantidade (unidades)", min_value=1, value=20, step=1)
        with f_col3:
            valor_venda = st.number_input("Valor Total da Venda (R$)", min_value=0.0, value=120.0, step=5.0)
            custo_estimado = st.number_input("Custo Total de Insumos (R$)", min_value=0.0, value=50.0, step=5.0)

        data_pedido = st.date_input("Data do Registro", date.today())
        status_inicial = st.selectbox("Status", ["Pendente", "Em Produção", "Entregue"])

        if st.form_submit_button("Registrar Pedido", use_container_width=True):
            if nome_cliente and linha_sabonete:
                novo_id = st.session_state.pedidos["id"].max() + 1 if not st.session_state.pedidos.empty else 1
                novo_registro = {
                    "id": novo_id,
                    "data": data_pedido,
                    "cliente": nome_cliente,
                    "tipo": tipo_pedido,
                    "linha": linha_sabonete,
                    "quantidade": quantidade,
                    "valor_total": valor_venda,
                    "custo_total": custo_estimado,
                    "status": status_inicial
                }
                st.session_state.pedidos = pd.concat([st.session_state.pedidos, pd.DataFrame([novo_registro])], ignore_index=True)
                st.success(f"Pedido de {nome_cliente} cadastrado com sucesso!")
                st.rerun()
            else:
                st.warning("Preencha o nome do cliente e a linha do produto.")

# -------------------------------------------------------------
# ABA 3: CALCULADORA DE CUSTO & LUCRO POR LOTE
# -------------------------------------------------------------
with aba3:
    st.subheader("Simulador de Custo Real por Barra")
    st.caption("Descubra o valor mínimo de venda antes de fechar orçamentos de eventos.")

    calc_col1, calc_col2 = st.columns([1.2, 1])

    with calc_col1:
        st.markdown("#### 1. Insumos do Lote")
        rendimento = st.number_input("Quantas barras rende esta receita?", min_value=1, value=10, step=1)
        
        c_base = st.number_input("Custo da Base Glicerinada (R$)", value=38.00, step=1.0)
        c_essencia = st.number_input("Custo Essência + Extratos + Óleos (R$)", value=14.00, step=1.0)
        c_embalagem = st.number_input("Embalagem (Tags, Fitas, Plástico/Caixa) total (R$)", value=12.00, step=1.0)
        c_adicionais = st.number_input("Outros (Corante, álcool, perdas de corte) (R$)", value=4.00, step=1.0)

        st.markdown("#### 2. Mão de Obra e Margem")
        horas_trabalho = st.number_input("Horas dedicadas a este lote", value=2.0, step=0.5)
        valor_hora = st.number_input("Valor da hora de trabalho (R$)", value=15.00, step=1.0)
        margem_desejada = st.slider("Margem de Lucro Desejada (%)", min_value=10, max_value=80, value=45, step=5)

    with calc_col2:
        st.markdown("#### Resultado da Análise")
        
        custo_direto_insumos = c_base + c_essencia + c_embalagem + c_adicionais
        custo_mao_obra = horas_trabalho * valor_hora
        custo_total_lote = custo_direto_insumos + custo_mao_obra
        custo_unitario = custo_total_lote / rendimento

        preco_venda_unitario = custo_unitario / (1 - (margem_desejada / 100))
        preco_total_lote = preco_venda_unitario * rendimento
        lucro_liquido_lote = preco_total_lote - custo_total_lote

        st.metric("Custo Real por Sabonete", f"R$ {custo_unitario:.2f}")
        st.metric("Preço Sugerido por Unidade", f"R$ {preco_venda_unitario:.2f}")
        st.metric("Preço Mínimo do Lote Completo", f"R$ {preco_total_lote:.2f}", f"R$ {lucro_liquido_lote:.2f} de lucro")

        st.info(f"💡 Para um pedido de **50 lembrancinhas** com esta fórmula, o valor do orçamento deve ser de pelo menos **R$ {preco_venda_unitario * 50:.2f}** para manter sua margem de {margem_desejada}%.")