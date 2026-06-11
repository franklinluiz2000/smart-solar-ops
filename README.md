# Smart Solar Ops - Plataforma de Telemetria Preditiva e Otimização Solar

O **Smart Solar Ops** é uma Prova de Conceito (POC) de uma plataforma de Engenharia de Dados e Inteligência Artificial voltada para a gestão inteligente de usinas fotovoltaicas. O objetivo do sistema é ingerir dados de telemetria de inversores solares em tempo real, armazená-los de forma otimizada para séries temporais e aplicar modelos analíticos para manutenção preditiva e eficiência operacional.

---

## 🚀 Arquitetura do Projeto

O pipeline foi desenhado seguindo as melhores práticas de infraestrutura moderna, focado em alta disponibilidade, escalabilidade e baixo custo operacional.

1. **Camada de Ingestão (IoT Simulator):** Microsserviço em Python que simula o comportamento físico de inversores solares, gerando dados de telemetria (tensão, corrente, temperatura e kW/h).
2. **Camada de Armazenamento (Time-Series):** Uso do **TimescaleDB** (baseado em PostgreSQL), otimizado especificamente para dados de sensores e alta concorrência de escrita.
3. **Camada de Inteligência (Analytics/IA):** Algoritmo preditivo para detecção de anomalias em tempo real (como perda de eficiência por sujeira nos painéis ou falhas de hardware).
4. **Camada de Observabilidade:** Painéis analíticos em **Grafana** para monitoramento executivo e técnico do Health Score da usina.

---

## 🛠️ Stack Tecnológica

* **Linguagem:** Python 3.11+
* **Banco de Dados:** TimescaleDB (PostgreSQL 15)
* **Orquestração e Containers:** Docker & Docker Compose
* **Visualização de Dados:** Grafana

---

## 🔧 Como Executar o Ambiente

O projeto foi totalmente containerizado para garantir que suba em qualquer ambiente de produção com um único comando.

### Pré-requisitos
* Docker instalado
* Docker Compose instalado

### Passo a Passo

1. Clone o repositório:
   ```bash
   git clone git@github.com:franklinluiz2000/smart-solar-ops.git
   cd smart-solar-ops