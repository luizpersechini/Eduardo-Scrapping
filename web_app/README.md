# 🌐 ANBIMA Data Scraper - Web Application

Interface web moderna para extração automatizada de dados de fundos da ANBIMA.

---

## ✨ Recursos

- 📤 **Upload de Arquivos Excel** - Faça upload de planilhas com CNPJs para scraping
- ⚡ **Processamento Paralelo** - Configure de 1 a 4 workers paralelos
- 📊 **Monitoramento em Tempo Real** - Acompanhe o progresso ao vivo com Socket.IO
- 💾 **Histórico de Jobs** - Visualize todos os jobs executados
- 🔄 **Retry Automático** - Tente novamente CNPJs que falharam
- 📥 **Download de Resultados** - Baixe os dados extraídos em formato Excel
- 🎨 **Interface Moderna** - UI limpa e responsiva
- 📱 **Mobile-Friendly** - Funciona perfeitamente em dispositivos móveis

---

## 🚀 Como Usar

### 1. Instalação

Certifique-se de que todas as dependências estão instaladas:

```bash
# Do diretório raiz do projeto
pip3 install -r requirements.txt
```

### 2. Iniciar o Servidor

**Opção A: Script automatizado (recomendado)**

```bash
# Do diretório raiz do projeto
./start_web_app.sh
```

**Opção B: Manualmente**

```bash
cd web_app
python3 app.py
```

### 3. Acessar a Aplicação

Abra seu navegador e acesse:

```
http://localhost:5000
```

---

## 📖 Guia de Uso

### Criando um Novo Job

1. **Upload do Arquivo**
   - Clique em "Selecione o arquivo Excel com CNPJs"
   - Escolha um arquivo `.xlsx` ou `.xls`
   - O arquivo deve ter uma coluna com CNPJs

2. **Configurar Workers**
   - Ajuste o número de workers paralelos (1-4)
   - Recomendado: 4 workers (validado cientificamente)

3. **Criar Job**
   - Clique em "Upload e Criar Job"
   - Confirme se deseja iniciar o job imediatamente

### Monitorando o Progresso

Ao iniciar um job, você verá:

- **Barra de Progresso** - Visualização do progresso geral
- **Estatísticas em Tempo Real** - CNPJs processados, sucessos e falhas
- **Log ao Vivo** - Cada CNPJ sendo processado em tempo real
- **Fases do Processo**
  - Pré-inicialização do ChromeDriver
  - Teste de workers
  - Scraping
  - Finalização

### Resultados

Quando o job é concluído:

1. **Download** - Baixe o arquivo Excel com os resultados
2. **Visualizar Detalhes** - Clique em um job para ver detalhes completos
3. **Retry** - Se houver falhas, tente novamente apenas os CNPJs que falharam

---

## 🗄️ Banco de Dados

A aplicação usa **SQLite** para armazenar:

- **Jobs** - Informações de cada job de scraping
- **CNPJs** - Status individual de cada CNPJ
- **Dados Extraídos** - Valores históricos de cotas

**Localização do banco de dados:**
```
web_app/anbima_scraper.db
```

### Tabelas

#### `scraping_jobs`
- `id` - ID único do job
- `filename` - Nome do arquivo original
- `status` - pending, running, completed, failed
- `total_cnpjs` - Total de CNPJs no job
- `successful_cnpjs` - CNPJs processados com sucesso
- `failed_cnpjs` - CNPJs que falharam
- `workers` - Número de workers usados
- `created_at` - Data de criação
- `started_at` - Data de início
- `completed_at` - Data de conclusão
- `output_file` - Caminho do arquivo de saída

#### `cnpjs`
- `id` - ID único
- `job_id` - Referência ao job
- `cnpj` - Número do CNPJ
- `fund_name` - Nome do fundo
- `status` - pending, processing, success, failed, not_found
- `error_message` - Mensagem de erro (se aplicável)
- `retry_count` - Número de tentativas
- `data_count` - Quantidade de registros históricos extraídos
- `scraped_at` - Data/hora da extração

#### `scraped_data`
- `id` - ID único
- `cnpj_id` - Referência ao CNPJ
- `cnpj` - Número do CNPJ
- `fund_name` - Nome do fundo
- `date` - Data da cotação
- `value` - Valor da cota
- `created_at` - Data de criação do registro

---

## 🔌 API Endpoints

### Jobs

- `GET /api/jobs` - Lista todos os jobs
- `GET /api/jobs/<job_id>` - Detalhes de um job específico
- `GET /api/jobs/<job_id>/failed` - Lista CNPJs que falharam
- `POST /api/jobs/<job_id>/start` - Inicia um job
- `POST /api/jobs/<job_id>/retry` - Tenta novamente CNPJs que falharam
- `GET /api/jobs/<job_id>/download` - Download dos resultados

### Upload

- `POST /api/upload` - Upload de arquivo Excel com CNPJs

### Estatísticas

- `GET /api/stats` - Estatísticas gerais da aplicação

---

## 🔄 Socket.IO Events

### Client → Server

- `connect` - Conecta ao servidor
- `disconnect` - Desconecta do servidor

### Server → Client

- `connected` - Confirmação de conexão
- `job_update` - Atualização de progresso do job
  ```json
  {
    "job_id": 1,
    "status": "running",
    "progress": 45.5,
    "successful": 50,
    "failed": 5,
    "message": "Processando...",
    "timestamp": "2024-10-31T12:00:00"
  }
  ```

- `cnpj_update` - Atualização de status de um CNPJ
  ```json
  {
    "job_id": 1,
    "cnpj": "12.345.678/0001-90",
    "status": "success",
    "timestamp": "2024-10-31T12:00:00"
  }
  ```

---

## 🎨 Interface

### Seções Principais

1. **Header com Estatísticas**
   - Total de jobs
   - Jobs completados
   - Jobs em andamento
   - CNPJs extraídos

2. **Novo Job**
   - Upload de arquivo
   - Configuração de workers
   - Botão de criação

3. **Job em Andamento**
   - Progresso em tempo real
   - Estatísticas de sucesso/falha
   - Log ao vivo

4. **Histórico de Jobs**
   - Lista de todos os jobs
   - Ações por job (iniciar, download, retry)
   - Visualização de detalhes

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Flask** - Framework web
- **Flask-SQLAlchemy** - ORM para banco de dados
- **Flask-SocketIO** - Comunicação em tempo real
- **SQLite** - Banco de dados
- **Selenium** - Web scraping
- **Pandas** - Processamento de dados

### Frontend
- **HTML5** - Estrutura
- **CSS3** - Estilização moderna
- **JavaScript (ES6+)** - Lógica e interações
- **Socket.IO Client** - Comunicação em tempo real
- **Font Awesome** - Ícones

---

## 📁 Estrutura de Arquivos

```
web_app/
├── app.py                      # Aplicação Flask principal
├── models.py                   # Modelos de banco de dados
├── scraper_service.py          # Serviço de scraping integrado
├── anbima_scraper.db           # Banco de dados SQLite (criado automaticamente)
├── templates/
│   └── index.html             # Página principal
├── static/
│   ├── css/
│   │   └── style.css          # Estilos
│   └── js/
│       └── main.js            # JavaScript principal
├── uploads/                    # Arquivos Excel enviados (criado automaticamente)
└── outputs/                    # Resultados gerados (criado automaticamente)
```

---

## 🔒 Segurança

- ✅ Limite de tamanho de arquivo (16MB)
- ✅ Validação de tipo de arquivo (apenas Excel)
- ✅ Sanitização de nomes de arquivo
- ✅ Isolamento de uploads e outputs

---

## 🚀 Deploy (Futuro)

Para deploy em produção, considere:

1. **Usar um servidor WSGI** (Gunicorn, uWSGI)
2. **Proxy reverso** (Nginx, Apache)
3. **Banco de dados robusto** (PostgreSQL)
4. **Variáveis de ambiente** para configurações sensíveis
5. **HTTPS** para comunicação segura
6. **Autenticação** para acesso restrito

---

## 🐛 Troubleshooting

### Problema: Porta 5000 já em uso

**Solução:** Mude a porta em `app.py`:

```python
socketio.run(app, host='0.0.0.0', port=5001, debug=True)
```

### Problema: Erro ao conectar ao ChromeDriver

**Solução:** A aplicação pré-inicializa o ChromeDriver. Se persistir:

1. Limpe o cache do ChromeDriver
2. Reduza o número de workers
3. Verifique a memória do sistema

### Problema: Jobs não aparecem

**Solução:** 
- Recarregue a página
- Verifique o console do navegador (F12)
- Verifique os logs do servidor

---

## 📝 Logs

Os logs são salvos em:

```
logs/scraper_parallel_YYYYMMDD_HHMMSS.log
```

---

## 🎯 Próximas Funcionalidades

- [ ] Autenticação de usuários
- [ ] Agendamento de jobs
- [ ] Notificações por email
- [ ] Dashboard de analytics
- [ ] Exportação em múltiplos formatos
- [ ] API REST completa
- [ ] Temas claro/escuro
- [ ] Comparação de resultados

---

## 💡 Dicas

1. **Performance**: Use 4 workers para melhor performance/estabilidade
2. **CNPJs Grandes**: Para listas muito grandes (500+), considere dividir em jobs menores
3. **Retry**: Sempre tente novamente os CNPJs que falharam - pode ser problema temporário do site
4. **Backup**: Faça backup do banco de dados periodicamente
5. **Limpeza**: Remova jobs e dados antigos periodicamente

---

## 📞 Suporte

Para problemas ou sugestões, consulte a documentação principal do projeto.

---

**Status:** ✅ **PRODUCTION READY**  
**Versão:** 1.0.0  
**Data:** Novembro 2024







