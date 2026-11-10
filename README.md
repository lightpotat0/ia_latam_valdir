# ✈️ IA LATAM — Valdir

**Valdir** é um assistente virtual inteligente desenvolvido para auxiliar no atendimento e na consulta de informações relacionadas à LATAM Airlines e ao programa LATAM Pass.

O projeto utiliza Inteligência Artificial Generativa (LLM) combinada com técnicas de **RAG (Retrieval-Augmented Generation)**, permitindo que o assistente consulte uma base de conhecimento antes de formular suas respostas.

Além do atendimento conversacional, o sistema oferece ferramentas para auxiliar nas atividades operacionais e na elaboração de respostas para clientes.

## 🌐 Demonstração

- **Aplicação:** https://ia-latam-valdir.vercel.app
- **API:** https://ia-latam-valdir.onrender.com
- **Documentação da API:** https://ia-latam-valdir.onrender.com/docs

## 🚀 Funcionalidades

- **Chat inteligente:** responde dúvidas sobre LATAM Airlines, LATAM Pass, milhas, bagagens, check-in, benefícios e procedimentos.
- **RAG (Retrieval-Augmented Generation):** recupera informações de uma base de conhecimento para contextualizar as respostas.
- **Histórico de conversação:** utiliza mensagens anteriores para compreender perguntas de continuidade.
- **Geração de macros:** cria respostas prontas para atendimento nos canais E-mail, Chat e WhatsApp.
- **Personalização de respostas:** permite selecionar o tom da comunicação (cordial, formal ou direto).
- **Calculadora de milhas:** consulta tabelas de resgate de acordo com a cabine e os trechos selecionados.
- **Referências:** retorna fontes utilizadas na elaboração das respostas, quando disponíveis.

## 🧠 Tecnologias utilizadas

| Tecnologia | Aplicação |
|---|---|
| Python 3.11 | Linguagem principal |
| FastAPI | Desenvolvimento da API |
| LangChain | Integração e gerenciamento dos componentes de IA |
| Groq | Inferência do modelo de linguagem |
| ChromaDB | Banco de dados vetorial |
| Hugging Face | Modelos de embeddings |
| Sentence Transformers | Representação semântica dos textos |
| Pydantic | Validação dos dados da API |
| Docker | Containerização e implantação |
| Vercel | Hospedagem da interface |
| Render | Hospedagem do backend |

## 🏗️ Arquitetura

O projeto é dividido em interface e backend, com comunicação por meio de uma API REST.

**Fluxo simplificado:**

1. O usuário envia uma pergunta pela interface.
2. A API recebe e valida a solicitação.
3. O sistema realiza buscas na base vetorial e por palavras-chave.
4. Os conteúdos recuperados são enviados como contexto ao modelo de linguagem.
5. O modelo gera uma resposta contextualizada.
6. A API retorna a resposta e as fontes disponíveis para a interface.

## 📡 Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/` | Disponibiliza a interface web |
| GET | `/health` | Verifica o estado da API |
| POST | `/chat` | Envia perguntas ao assistente |
| POST | `/macro` | Gera respostas prontas para atendimento |
| GET | `/opcoes` | Retorna opções disponíveis para a calculadora |
| POST | `/calcular` | Calcula milhas por cabine e trechos |

### Exemplo de requisição — Chat

`POST /chat`

```json
{
  "pergunta": "Como transfiro milhas para outra pessoa?",
  "historico": []
}
```

### Exemplo de requisição — Geração de macro

`POST /macro`

```json
{
  "situacao": "Cliente deseja informações sobre bagagem despachada.",
  "canal": "email",
  "tom": "cordial",
  "nome_cliente": "João"
}
```

### Exemplo de requisição — Calculadora

`POST /calcular`

```json
{
  "cabine": "Classe Econômica",
  "trechos": [
    {
      "origem": "Oceania",
      "destino": "Europa"
    }
  ]
}
```

## ⚙️ Executando localmente

### 1. Clone o repositório

```bash
git clone https://github.com/lightpotat0/ia_latam_valdir.git
```

### 2. Acesse o diretório do backend

```bash
cd ia_latam_valdir/src
```

### 3. Crie um ambiente virtual

```bash
python -m venv venv
```

Ative o ambiente:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux:**
```bash
source venv/bin/activate
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Configure as variáveis de ambiente

Crie um arquivo `.env` no diretório `src`:

```env
GROQ_API_KEY=sua_chave_groq
```

### 6. Execute a aplicação

```bash
uvicorn api:app --reload
```

A aplicação estará disponível em:

- Interface/API: http://localhost:8000
- Documentação Swagger: http://localhost:8000/docs

**Observação:** para utilizar o chat, também é necessário disponibilizar a base vetorial `chroma_db` compatível com o projeto.

## 🔐 Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `GROQ_API_KEY` | Chave de autenticação da API Groq |
| `GROQ_MODEL` | Modelo de linguagem utilizado |
| `CHROMA_DIR` | Diretório do banco vetorial |
| `ALLOWED_ORIGINS` | Origens autorizadas para requisições CORS |

## 📁 Estrutura do projeto

```text
ia_latam_valdir/
│
├── src/
│   ├── api.py
│   ├── main.py
│   ├── dados_user.py
│   ├── diaguinostico.py
│   ├── site_leitor.py
│   ├── tabela_fixa.py
│   ├── timer.py
│   ├── cabines.json
│   ├── requirements.txt
│   ├── Dockerfile
│   │
│   ├── latam-chat/
│   │   └── index.html
│   │
│   └── chroma_db/
│
└── README.md
```

## 🎯 Objetivo do projeto

O IA LATAM nasceu com a proposta de explorar aplicações práticas de Inteligência Artificial no contexto de atendimento ao cliente.

A ideia é utilizar modelos de linguagem e recuperação de informações para tornar consultas mais rápidas, facilitar o acesso a procedimentos e auxiliar profissionais na elaboração de respostas.

Mais do que um chatbot convencional, o Valdir busca integrar diferentes ferramentas em uma única aplicação, combinando IA generativa, processamento de informações e automação de tarefas.

## 👨‍💻 Desenvolvedor

**Danillo Vaz**

- GitHub: [@lightpotat0](https://github.com/lightpotat0)
- LinkedIn: [Danillo Vaz](https://www.linkedin.com/in/danillo-vaz/)

---

*Projeto independente desenvolvido para fins de estudo, experimentação e aplicação de Inteligência Artificial. Não é um produto oficial da LATAM Airlines.*
