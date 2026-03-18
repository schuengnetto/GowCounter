import streamlit as st
import datetime
import tempfile
import os
import pandas as pd
import plotly.express as px
from database import init_db, get_all_detections
from video_processor import process_video_generator

st.set_page_config(page_title="GowCounter", layout="wide", page_icon="🚦")

def local_css():
    st.markdown("""
    <style>
    .metric-card {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        text-align: center;
        margin-bottom: 20px;
        color: white;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4CAF50;
    }
    .metric-label {
        font-size: 1.2rem;
        color: #BDBDBD;
        text-transform: uppercase;
        font-weight: 500;
    }
    
    div[data-testid="stSidebarNav"] {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    local_css()
    st.sidebar.title("🚦 GowCounter")
    pagina = st.sidebar.radio("Navegação", ["Processamento de Vídeo", "Dashboard de Resultados"])
    
    init_db()
    
    if pagina == "Processamento de Vídeo":
        show_processing_page()
    else:
        show_dashboard_page()

def show_processing_page():
    st.title("Processamento Automático de Veículos e Pessoas")
    st.markdown("Faça o upload do vídeo da rua/estrada e defina o período de gravação exato do vídeo. O GowCounter fará a contagem e interpolação do horário de cada item detectado.")
    
    with st.form("upload_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Início da Gravação")
            start_date = st.date_input("Data de Início", datetime.date.today())
            start_time_input = st.time_input("Hora de Início", datetime.time(8, 0))
        with col2:
            st.subheader("Fim da Gravação")
            end_date = st.date_input("Data de Fim", datetime.date.today())
            end_time_input = st.time_input("Hora de Fim", datetime.time(9, 0))
            
        uploaded_file = st.file_uploader("Escolha um arquivo de vídeo (MP4, AVI, MOV)", type=["mp4", "avi", "mov", "mkv"])
        
        submit_button = st.form_submit_button("Iniciar Processamento", use_container_width=True)

    start_dt = datetime.datetime.combine(start_date, start_time_input)
    end_dt = datetime.datetime.combine(end_date, end_time_input)

    if submit_button:
        if end_dt <= start_dt:
            st.error("ERRO: A Data/Hora de fim deve ser posterior à Data/Hora de Início.")
            return

        if uploaded_file is None:
            st.error("ERRO: Faça o upload de um vídeo antes de processar.")
            return

        st.info("Vídeo carregado. Iniciando processamento em tempo real com IA...")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
            tfile.write(uploaded_file.read())
            tmp_path = tfile.name
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        frame_window = st.empty()
        
        try:
            for frame, f_idx, t_frames in process_video_generator(tmp_path, uploaded_file.name, start_dt, end_dt):
                if t_frames > 0:
                    progress = min(max(f_idx / t_frames, 0.0), 1.0)
                    progress_bar.progress(progress)
                status_text.text(f"Processando frame {f_idx} de {t_frames}...")
                frame_window.image(frame, channels="RGB", use_container_width=True)
                
            st.success("Processamento concluído e dados salvos no banco de dados!")
        except Exception as e:
            st.error(f"Erro durante o processamento: {e}")
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass

def render_metric_card(label, value):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def show_dashboard_page():
    st.title("Dashboard Estratégico de Contagem")
    
    df = get_all_detections()
    if df.empty:
        st.warning("Nenhum dado processado ainda. Vá para a tela de Processamento e suba um vídeo!")
        return
        
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    min_date = df['timestamp'].dt.date.min()
    max_date = df['timestamp'].dt.date.max()
    
    st.sidebar.subheader("Filtros Dashboard")
    selected_date = st.sidebar.date_input("Selecione o Dia para Análise", max_date, min_value=min_date, max_value=max_date)
    
    mask = df['timestamp'].dt.date == selected_date
    filtered_df = df[mask].copy()
    
    if filtered_df.empty:
        st.info(f"Nenhum registro encontrado para a data {selected_date.strftime('%d/%m/%Y')}.")
        return
        
    st.subheader(f"Visão Geral: {selected_date.strftime('%d/%m/%Y')}")
    
    pessoas_count = len(filtered_df[filtered_df['class_name'] == 'Pessoa'])
    carros_count = len(filtered_df[filtered_df['class_name'] == 'Automóvel'])
    bikes_count = len(filtered_df[filtered_df['class_name'] == 'Bicicleta'])
    
    col1, col2, col3 = st.columns(3)
    with col1: render_metric_card("Automóveis", carros_count)
    with col2: render_metric_card("Pessoas", pessoas_count)
    with col3: render_metric_card("Bicicletas", bikes_count)
    
    st.markdown("---")
    
    filtered_df['hour'] = filtered_df['timestamp'].dt.hour
    hourly_counts = filtered_df.groupby(['hour', 'class_name']).size().reset_index(name='contagem')
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("### Tráfego por Hora")
        if not hourly_counts.empty:
            fig_line = px.line(hourly_counts, x='hour', y='contagem', color='class_name', markers=True,
                               labels={'hour': 'Hora do Dia', 'contagem': 'Quantidade Detectada', 'class_name': 'Tipo'})
            fig_line.update_xaxes(dtick=1)
            fig_line.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                   legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.write("Sem dados suficientes para gerar o gráfico de hora.")
            
    with col_chart2:
        st.markdown("### Distribuição Total no Dia")
        class_counts = filtered_df['class_name'].value_counts().reset_index()
        class_counts.columns = ['class_name', 'contagem']
        if not class_counts.empty:
            fig_pie = px.pie(class_counts, values='contagem', names='class_name', hole=0.5,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_pie, use_container_width=True)
            
if __name__ == "__main__":
    main()
