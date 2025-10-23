# 🚀 LEIA-ME PRIMEIRO - Guia de Início Rápido

**Bem-vindo ao ANBIMA Data Scraper!** Este guia vai te ajudar a começar em 5 minutos.

---

## ⚡ Início Ultrarrápido (Para Quem Tem Pressa)

```bash
# 1. Instalar dependências
pip3 install -r requirements.txt

# 2. Executar
python3 main.py

# 3. Pronto! Verifique o arquivo output_*.xlsx
```

**Funcionou?** Parabéns! 🎉  
**Deu erro?** Continue lendo abaixo. ⬇️

---

## 📋 O Que Este Projeto Faz?

Extrai automaticamente dados de fundos de investimento do site da ANBIMA:

**ENTRADA** → Lista de CNPJs (Excel)  
**PROCESSAMENTO** → Scraping automático do site  
**SAÍDA** → Dados históricos (Excel)

### Dados Extraídos

✅ **CNPJ**  
✅ **Nome do Fundo**  
✅ **Data da cotação** (últimos 22 dias úteis)  
✅ **Valor da cota**

---

## 🎯 Para Quem É Este Projeto?

- ✅ Analistas financeiros que precisam de dados periódicos de fundos
- ✅ Gestores que querem automatizar coleta de informações
- ✅ Desenvolvedores que precisam integrar dados da ANBIMA
- ✅ Pesquisadores que estudam mercado de fundos

---

## 📚 Qual Documentação Devo Ler?

### 👤 Você É...

#### 🔰 **Iniciante / Primeiro Uso**
1. Este arquivo (você está aqui) ✓
2. [README.md](README.md) - Seções: Instalação e Guia de Uso
3. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Se der algum erro

#### 👨‍💼 **Usuário Regular**
1. [README.md](README.md) - Leia completo
2. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Marque como referência

#### 👨‍💻 **Desenvolvedor**
1. [README.md](README.md) - Visão geral
2. [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitetura detalhada
3. [CONTRIBUTING.md](CONTRIBUTING.md) - Como contribuir

#### 🏢 **Gestor / Tomador de Decisão**
1. [README.md](README.md) - Seções: Visão Geral e Limitações
2. [LICENSE.md](LICENSE.md) - Termos legais
3. [ARCHITECTURE.md](ARCHITECTURE.md) - Seção: Performance e Roadmap

---

## 🛠️ Instalação Detalhada

### Pré-requisitos

✅ **Python 3.9+** instalado  
✅ **Google Chrome** instalado  
✅ **Conexão com internet**

### Passo a Passo

**1. Verificar Python**
```bash
python3 --version
# Deve mostrar: Python 3.9.x ou superior
```

**2. Instalar Dependências**
```bash
pip3 install -r requirements.txt
```

**O que será instalado:**
- `selenium` - Automação do navegador
- `pandas` - Manipulação de dados
- `openpyxl` - Leitura/escrita de Excel
- `webdriver-manager` - Gerencia ChromeDriver automaticamente
- `tqdm` - Barra de progresso

**3. Preparar Arquivo de Entrada**

O projeto já vem com `input_cnpjs.xlsx` contendo 2 CNPJs de exemplo.

Para usar seus próprios CNPJs:
- Abra `input_cnpjs.xlsx` no Excel
- Substitua os CNPJs pelos seus
- Salve o arquivo

**Formato esperado:**

| CNPJ |
|------|
| 48.330.198/0001-06 |
| 34.780.531/0001-66 |

**4. Executar o Scraper**
```bash
python3 main.py
```

**5. Aguardar Conclusão**

Você verá algo como:
```
✓ Found 2 CNPJ(s) to process
✓ Web scraper initialized successfully

🔍 Scraping data for 2 fund(s)...
Progress: 100%|████████████| 2/2 [01:40<00:00, 50.19s/fund]

✓ Results saved to: output_anbima_data_20251023_110804.xlsx
```

**6. Verificar Resultado**

Abra o arquivo `output_anbima_data_*.xlsx` gerado.

---

## 🎮 Comandos Básicos

### Modo Padrão (Navegador Invisível)
```bash
python3 main.py
```

### Modo Visível (Para Ver o que Está Acontecendo)
```bash
python3 main.py --no-headless
```

### Especificar Arquivo de Entrada
```bash
python3 main.py -i meus_cnpjs.xlsx
```

### Especificar Arquivo de Saída
```bash
python3 main.py -o resultados.xlsx
```

### Combinar Opções
```bash
python3 main.py -i meus_cnpjs.xlsx -o resultados_outubro.xlsx --no-headless
```

---

## ❓ Problemas Comuns e Soluções Rápidas

### ❌ `ModuleNotFoundError: No module named 'selenium'`

**Solução:**
```bash
pip3 install -r requirements.txt
```

---

### ❌ `Failed to initialize WebDriver`

**Solução:**
1. Verifique se Google Chrome está instalado
2. Limpe cache do webdriver:
```bash
rm -rf ~/.wdm/
python3 main.py
```

---

### ❌ `No CNPJs found in input file`

**Solução:**
1. Verifique se o arquivo Excel tem uma coluna chamada exatamente **"CNPJ"**
2. Verifique se há CNPJs na coluna (não vazia)

---

### ❌ `Timeout: Page took too long to load`

**Solução:**
1. Verifique sua conexão com internet
2. Tente executar novamente (pode ser instabilidade temporária)
3. Se persistir, aumente timeouts em `config.py`:
```python
PAGE_LOAD_TIMEOUT = 60  # Era 30
```

---

### ❌ Outros Problemas?

Consulte o **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** completo com +30 problemas documentados e suas soluções.

---

## 📊 O Que Esperar

### Performance
- ⏱️ **Tempo**: ~50 segundos por fundo
- 📊 **Dados**: 22 dias úteis de histórico por fundo
- ✅ **Taxa de sucesso**: >95% em condições normais

### Exemplo de Resultado

```
CNPJ                Nome do Fundo               Data           Valor cota    Status
48.330.198/0001-06  CLASSE ÚNICA DE INVESTI...  19/09/2025    R$ 1,569379   Success
48.330.198/0001-06  CLASSE ÚNICA DE INVESTI...  22/09/2025    R$ 1,570331   Success
48.330.198/0001-06  CLASSE ÚNICA DE INVESTI...  23/09/2025    R$ 1,571226   Success
...
```

---

## 🔧 Configurações Opcionais

### Ajustar Timeouts (Se Conexão Lenta)

Edite `config.py`:
```python
PAGE_LOAD_TIMEOUT = 60  # Aumentar se sua internet for lenta
EXPLICIT_WAIT_LONG = 40
```

### Processar Lote Grande de CNPJs

Para +50 CNPJs, divida em múltiplos arquivos para evitar bloqueios:
```bash
python3 main.py -i lote1.xlsx
python3 main.py -i lote2.xlsx
python3 main.py -i lote3.xlsx
```

---

## 📁 Estrutura de Arquivos

```
Eduardo Scrapping/
├── 📘 README.md              ← Documentação completa (leia depois)
├── 🚀 LEIA-ME_PRIMEIRO.md    ← Este arquivo
├── 📋 CHANGELOG.md           ← Histórico de versões
├── 🏗️  ARCHITECTURE.md       ← Arquitetura técnica (dev)
├── 🔧 TROUBLESHOOTING.md     ← Solução de problemas
├── 🤝 CONTRIBUTING.md        ← Como contribuir
├── 📄 LICENSE.md             ← Licença MIT
├── 
├── 💻 main.py                ← Script principal
├── 💻 anbima_scraper.py      ← Motor de scraping
├── 💻 data_processor.py      ← Processamento de dados
├── ⚙️  config.py             ← Configurações
├── 📦 requirements.txt       ← Dependências Python
├── 
├── 📊 input_cnpjs.xlsx       ← Seu arquivo de entrada
├── 📊 output_*.xlsx          ← Arquivos de saída gerados
└── 📁 logs/                  ← Logs de execução
```

---

## 🎯 Próximos Passos

### ✅ Instalou e Executou com Sucesso?

**Parabéns!** Agora você pode:

1. **Usar regularmente**
   - Atualize `input_cnpjs.xlsx` com seus CNPJs
   - Execute `python3 main.py` quando precisar
   - Analise os resultados em Excel

2. **Aprender mais**
   - Leia o [README.md](README.md) completo
   - Explore opções avançadas de configuração
   - Veja o [CHANGELOG.md](CHANGELOG.md) para novidades

3. **Automatizar**
   - Agende execuções periódicas (cron/Task Scheduler)
   - Integre com seus sistemas
   - Consulte [README.md](README.md) seção "Uso Recorrente"

### 📚 Quer Entender Melhor?

- **Como funciona?** → [ARCHITECTURE.md](ARCHITECTURE.md)
- **Como contribuir?** → [CONTRIBUTING.md](CONTRIBUTING.md)
- **Histórico do projeto?** → [CHANGELOG.md](CHANGELOG.md)

---

## 💡 Dicas Úteis

### ✅ Boas Práticas

1. **Execute com `--no-headless` na primeira vez** para ver o que acontece
2. **Verifique logs/** se algo der errado
3. **Faça backup dos arquivos output_*.xlsx** importantes
4. **Processe CNPJs em lotes** se tiver muitos (máximo 50 por vez)
5. **Aguarde 2-3 segundos entre execuções** para não sobrecarregar o site

### ❌ Evite

1. ❌ Executar múltiplas instâncias simultaneamente
2. ❌ Processar centenas de CNPJs de uma vez
3. ❌ Modificar código sem entender (leia ARCHITECTURE.md primeiro)
4. ❌ Compartilhar dados extraídos sem autorização apropriada

---

## 📞 Precisa de Ajuda?

### 1️⃣ **Primeiro**: Verifique este guia e [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### 2️⃣ **Segundo**: Verifique os logs em `logs/`
```bash
# Ver último log
cat logs/scraper_*.log | tail -50
```

### 3️⃣ **Terceiro**: Execute com `--no-headless` para ver o que está acontecendo
```bash
python3 main.py --no-headless
```

### 4️⃣ **Ainda com problemas?** Abra uma issue incluindo:
- Versão do Python (`python3 --version`)
- Sistema operacional
- Mensagem de erro completa
- Últimas 50 linhas do log
- O que você já tentou

---

## 🎉 Pronto para Começar!

```bash
# Execute agora mesmo:
python3 main.py
```

**Boa sorte e bom scraping!** 🚀

---

## 📖 Índice Completo da Documentação

Para navegar por toda a documentação disponível, consulte:
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - Índice completo com guias por perfil de usuário

---

**Versão**: 1.0  
**Última Atualização**: 23 de Outubro de 2025  
**Tempo de Leitura**: 5-10 minutos

