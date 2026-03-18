# GowCounter 🚦

Uma aplicação web inteligente para processamento de vídeo e contagem analítica de veículos (carros) e pedestres (pessoas, bicicletas). Construída com **Streamlit** no frontend e motor de IA baseado em **YOLOv8** e **ByteTrack**.

## Funcionalidades Principais
- **Processamento de Vídeo Local com IA**: Upload de vídeos através do painel com inferência automatizada.
- **Rastreamento Analítico e Persistente (ByteTrack)**: Lógica com memória temporal que impede contagens falsas geradas por pequenos erros visuais.
- **Leis Dinâmicas de Inteligência**: 
  - *Carros* possuem lei de contagem rígida com alta confiança e persistência (8 frames).
  - *Pessoas e Bicicletas* são contabilizadas mais rapidamente (3 a 4 frames) preservando a exatidão mesmo com menor tamanho ou oclusão alta. 
- **Dashboard Analítico Automatizado**:
  - Geração de gráficos Plotly (Linha Horária e Fatiamento de Pizza) filtrados por Data.
  - Indicadores automáticos divididos por Classe de Objeto (Carro, Pessoa, Bicicleta).
- **Banco de Dados Embutido (SQLite)**: As contagens são persistidas internamente e cruzadas em tempo real na aba de relatório.

## Arquitetura do Sistema
O sistema possui 3 pilares de código:
1. `app.py`: Interface web limpa e moderna operada pelo Streamlit e abas de navegação.
2. `video_processor.py`: Módulo responsável pela leitura de frames de vídeo, orquestração do tracker YOLOv8 e configurações do `custom_bytetrack.yaml`.
3. `database.py`: Driver leve de armazenamento e formatação (`gowcounter.db`).

## Como Instalar e Rodar

1. Clone o repositório ou baixe os arquivos fonte do Github em uma pasta local.
2. Abra o terminal nesta pasta do projeto.
3. Instale todas as dependências requeridas predefinidas executando:
   ```bash
   pip install -r requirements.txt
   ```
4. Inicie a plataforma:
   ```bash
   streamlit run app.py
   ```
5. O painel web abrirá automaticamente no seu navegador pelo link local (o padrão é `http://localhost:8501`).

## Uso do Sistema
- Comece navegando no menu para **Processamento de Vídeo**. Insira um vídeo MP4/AVI e estipule de que horas o vídeo se trata para geração estatística (Início e Fim originais). Clique para processar e aguarde a barra finalizar aos 100%.
- Após o processing da IA, navegue para a aba **Dashboard de Resultados**, localize a data que você selecionou no passo anterior e confira todas as métricas renderizadas.

---
**Nota para Desenvolvedores**: Na primeira vez em que a aplicação identificar e processar um vídeo submetido, fará o auto-download oficial do componente `yolov8n.pt` para o raiz. Este arquivo será excluído das comitadas futuras via regras do `.gitignore`.
