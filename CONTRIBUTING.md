# 🤝 Guia de Contribuição

Obrigado por considerar contribuir para o **ANBIMA Data Scraper**! Este documento fornece diretrizes para contribuir com o projeto.

---

## 📋 Índice

1. [Código de Conduta](#código-de-conduta)
2. [Como Posso Contribuir?](#como-posso-contribuir)
3. [Configuração do Ambiente](#configuração-do-ambiente)
4. [Processo de Desenvolvimento](#processo-de-desenvolvimento)
5. [Padrões de Código](#padrões-de-código)
6. [Commits e Mensagens](#commits-e-mensagens)
7. [Pull Requests](#pull-requests)
8. [Reportando Bugs](#reportando-bugs)
9. [Sugerindo Melhorias](#sugerindo-melhorias)

---

## 📜 Código de Conduta

### Nossos Compromissos

- Ser respeitoso e inclusivo com todos os colaboradores
- Aceitar críticas construtivas de forma profissional
- Focar no que é melhor para a comunidade
- Demonstrar empatia com outros membros da comunidade

### Comportamentos Inaceitáveis

- Uso de linguagem ou imagens sexualizadas
- Trolling, insultos ou comentários depreciativos
- Assédio público ou privado
- Publicação de informações privadas de terceiros

---

## 🚀 Como Posso Contribuir?

### 1. Reportando Bugs

Bugs são rastreados como issues. Ao reportar um bug, inclua:

- **Título claro e descritivo**
- **Passos para reproduzir** o problema
- **Comportamento esperado** vs. comportamento atual
- **Screenshots** (se aplicável)
- **Informações do ambiente** (OS, Python version, etc.)
- **Logs relevantes** da pasta `logs/`

**Template de Bug Report:**

```markdown
## Descrição do Bug
[Descrição clara do problema]

## Passos para Reproduzir
1. Execute '...'
2. Observe '...'
3. Veja erro

## Comportamento Esperado
[O que deveria acontecer]

## Comportamento Atual
[O que está acontecendo]

## Ambiente
- OS: [Windows 10 / macOS 12 / Ubuntu 20.04]
- Python: [3.9.7]
- Selenium: [4.15.2]

## Logs
```
[Cole logs relevantes aqui]
```

## Screenshots
[Se aplicável]
```

### 2. Sugerindo Melhorias

Sugestões são bem-vindas! Ao sugerir uma melhoria:

- **Use um título claro** e descritivo
- **Forneça uma descrição detalhada** da melhoria sugerida
- **Explique por que** essa melhoria seria útil
- **Liste exemplos** de como seria usada
- **Inclua mockups** ou exemplos de código (se aplicável)

**Template de Feature Request:**

```markdown
## Descrição da Funcionalidade
[Descrição clara da funcionalidade proposta]

## Problema que Resolve
[Qual problema essa funcionalidade resolve?]

## Solução Proposta
[Como você imagina que isso deveria funcionar?]

## Alternativas Consideradas
[Outras soluções que você considerou]

## Contexto Adicional
[Qualquer outra informação relevante]
```

### 3. Contribuindo com Código

Contribuições de código são muito apreciadas! Áreas onde você pode ajudar:

#### 🐛 Correção de Bugs
- Corrigir bugs listados nas issues
- Melhorar tratamento de erros
- Aumentar robustez do scraper

#### ✨ Novas Funcionalidades
- Implementar features do roadmap
- Adicionar suporte para novos formatos de saída
- Melhorar performance

#### 📚 Documentação
- Melhorar documentação existente
- Adicionar exemplos de uso
- Traduzir documentação
- Corrigir erros de digitação

#### 🧪 Testes
- Adicionar testes automatizados
- Melhorar cobertura de testes
- Criar testes de integração

#### 🎨 Interface
- Melhorar mensagens de erro
- Adicionar interface web
- Melhorar relatórios de saída

---

## 🔧 Configuração do Ambiente

### 1. Fork o Repositório

Clique no botão "Fork" no topo da página do repositório.

### 2. Clone seu Fork

```bash
git clone https://github.com/seu-usuario/eduardo-scrapping.git
cd eduardo-scrapping
```

### 3. Configure o Upstream

```bash
git remote add upstream https://github.com/original-usuario/eduardo-scrapping.git
```

### 4. Crie um Ambiente Virtual

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows
```

### 5. Instale Dependências

```bash
pip install -r requirements.txt
```

### 6. Instale Dependências de Desenvolvimento (quando disponíveis)

```bash
pip install -r requirements-dev.txt  # Quando criado
```

### 7. Configure Pre-commit Hooks (quando disponíveis)

```bash
pre-commit install
```

---

## 💻 Processo de Desenvolvimento

### 1. Crie uma Branch

```bash
git checkout -b tipo/descricao-curta
```

**Tipos de branches:**
- `feature/` - Nova funcionalidade
- `bugfix/` - Correção de bug
- `hotfix/` - Correção urgente
- `docs/` - Documentação
- `refactor/` - Refatoração de código
- `test/` - Adição de testes

**Exemplos:**
```bash
git checkout -b feature/adicionar-exportacao-csv
git checkout -b bugfix/corrigir-timeout-scraper
git checkout -b docs/melhorar-readme
```

### 2. Faça suas Alterações

- Escreva código limpo e legível
- Siga os padrões de código do projeto
- Adicione comentários quando necessário
- Atualize documentação se aplicável

### 3. Teste suas Alterações

```bash
# Teste manualmente
python3 main.py --no-headless

# Execute testes automatizados (quando disponíveis)
pytest

# Verifique linting
flake8 .
black --check .
```

### 4. Commit suas Alterações

```bash
git add .
git commit -m "tipo: descrição curta"
```

### 5. Push para seu Fork

```bash
git push origin tipo/descricao-curta
```

### 6. Abra um Pull Request

- Vá para seu fork no GitHub
- Clique em "Compare & pull request"
- Preencha o template de PR
- Aguarde revisão

---

## 📝 Padrões de Código

### Estilo Python

Seguimos o **PEP 8** com algumas adaptações:

#### Formatação
- **Indentação**: 4 espaços (sem tabs)
- **Comprimento de linha**: Máximo 100 caracteres
- **Encoding**: UTF-8
- **Quebras de linha**: Unix style (`\n`)

#### Nomenclatura
```python
# Classes: PascalCase
class ANBIMAScraper:
    pass

# Funções e variáveis: snake_case
def extract_periodic_data():
    fund_name = "Exemplo"

# Constantes: UPPER_SNAKE_CASE
MAX_RETRIES = 3
ANBIMA_BASE_URL = "https://..."

# Privado: prefixo com _
def _internal_method():
    pass
```

#### Imports
```python
# 1. Biblioteca padrão
import os
import time
from typing import List, Dict

# 2. Bibliotecas de terceiros
import pandas as pd
from selenium import webdriver

# 3. Módulos locais
from config import ANBIMA_BASE_URL
from data_processor import DataProcessor
```

#### Documentação
```python
def extract_data(cnpj: str) -> Dict:
    """
    Extrai dados de um fundo dado seu CNPJ.
    
    Args:
        cnpj: CNPJ do fundo no formato XX.XXX.XXX/XXXX-XX
        
    Returns:
        Dict contendo os dados extraídos
        
    Raises:
        ValueError: Se CNPJ for inválido
        TimeoutError: Se requisição exceder timeout
        
    Example:
        >>> data = extract_data("48.330.198/0001-06")
        >>> print(data['Nome do Fundo'])
    """
    pass
```

#### Type Hints
```python
from typing import List, Dict, Optional, Tuple

def process_data(cnpjs: List[str]) -> Tuple[bool, Optional[Dict]]:
    """Use type hints sempre que possível"""
    pass
```

#### Error Handling
```python
# BOM - Específico e informativo
try:
    data = extract_data(cnpj)
except TimeoutError as e:
    logger.error(f"Timeout ao extrair {cnpj}: {e}")
    return None
except ValueError as e:
    logger.error(f"CNPJ inválido {cnpj}: {e}")
    return None

# RUIM - Genérico demais
try:
    data = extract_data(cnpj)
except Exception as e:
    pass
```

### Ferramentas de Qualidade de Código

#### Black (Code Formatter)
```bash
# Formatar código
black .

# Verificar sem modificar
black --check .
```

#### Flake8 (Linter)
```bash
# Verificar código
flake8 .

# Com configuração
flake8 --max-line-length=100 --exclude=venv,__pycache__
```

#### isort (Import Sorter)
```bash
# Organizar imports
isort .

# Verificar sem modificar
isort --check-only .
```

---

## 💬 Commits e Mensagens

### Formato de Commit

Usamos **Conventional Commits**:

```
tipo(escopo): descrição curta

[corpo opcional]

[rodapé opcional]
```

### Tipos de Commit

- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Alterações na documentação
- `style`: Formatação, ponto e vírgula, etc (sem mudança de código)
- `refactor`: Refatoração de código
- `perf`: Melhoria de performance
- `test`: Adição ou correção de testes
- `build`: Mudanças no sistema de build ou dependências
- `ci`: Mudanças em arquivos de CI
- `chore`: Outras mudanças que não modificam src ou test

### Exemplos de Commits

```bash
# Feature
git commit -m "feat(scraper): adicionar suporte para exportação CSV"

# Bug fix
git commit -m "fix(scraper): corrigir timeout ao carregar dados periódicos"

# Documentação
git commit -m "docs(readme): adicionar seção de troubleshooting"

# Refactoring
git commit -m "refactor(processor): simplificar lógica de processamento de dados"

# Performance
git commit -m "perf(scraper): otimizar seletores CSS para reduzir tempo de busca"

# Com corpo e rodapé
git commit -m "feat(api): adicionar endpoint REST para scraping

Implementa endpoints:
- POST /api/scrape
- GET /api/results/{id}

Closes #123"
```

### Boas Práticas

✅ **BOM:**
- Use imperativo ("adicionar" não "adicionado")
- Primeira linha com no máximo 50 caracteres
- Corpo com no máximo 72 caracteres por linha
- Separe assunto do corpo com linha em branco
- Use corpo para explicar "o que" e "por que", não "como"

❌ **EVITE:**
- Mensagens genéricas ("atualização", "correções")
- Commits muito grandes (quebre em commits menores)
- Misturar diferentes tipos de mudanças em um commit
- Commits sem contexto suficiente

---

## 🔀 Pull Requests

### Antes de Criar um PR

1. ✅ Certifique-se que seu código passa em todos os testes
2. ✅ Atualize documentação se necessário
3. ✅ Adicione testes para novas funcionalidades
4. ✅ Verifique que não há conflitos com main
5. ✅ Execute formatters e linters

### Template de Pull Request

```markdown
## Tipo de Mudança

- [ ] Bug fix (mudança que corrige um problema)
- [ ] Nova funcionalidade (mudança que adiciona funcionalidade)
- [ ] Breaking change (fix ou feature que quebra funcionalidade existente)
- [ ] Documentação (mudança apenas em documentação)

## Descrição

[Descrição clara do que foi alterado e por quê]

## Problema Relacionado

Closes #[número da issue]

## Como Foi Testado?

[Descreva os testes realizados]

## Checklist

- [ ] Meu código segue os padrões do projeto
- [ ] Revisei meu próprio código
- [ ] Comentei código em áreas complexas
- [ ] Atualizei a documentação
- [ ] Minhas mudanças não geram novos warnings
- [ ] Adicionei testes que provam que meu fix funciona
- [ ] Testes unitários novos e existentes passam localmente
- [ ] Mudanças dependentes foram merged

## Screenshots (se aplicável)

[Adicione screenshots se relevante]
```

### Processo de Revisão

1. **Automático**: CI/CD executa testes e linters
2. **Revisão de Código**: Pelo menos 1 aprovação necessária
3. **Discussão**: Responda comentários e faça ajustes
4. **Aprovação**: Após aprovação, será merged
5. **Merge**: Squash and merge ou merge commit

---

## 🐞 Reportando Bugs

### Antes de Reportar

1. **Verifique se já foi reportado** nas issues existentes
2. **Reproduza o bug** com a versão mais recente
3. **Colete informações** do ambiente e logs

### Informações Necessárias

```markdown
**Versão:**
- Python: 
- Selenium: 
- Sistema Operacional: 

**Descrição:**
[Descrição clara e concisa do bug]

**Reprodução:**
1. Execute '...'
2. Observe '...'
3. Veja erro '...'

**Esperado:**
[O que deveria acontecer]

**Atual:**
[O que está acontecendo]

**Logs:**
```
[Cole logs aqui]
```

**Screenshots:**
[Se aplicável]

**Contexto Adicional:**
[Qualquer informação adicional]
```

---

## 💡 Sugerindo Melhorias

### Áreas para Melhorias

- **Performance**: Otimizações de velocidade ou memória
- **Usabilidade**: Melhorias na experiência do usuário
- **Funcionalidades**: Novas features
- **Documentação**: Melhorias na docs
- **Testes**: Aumento de cobertura
- **DevOps**: CI/CD, Docker, etc.

### Como Sugerir

1. **Abra uma issue** com o label "enhancement"
2. **Descreva o problema** que a melhoria resolve
3. **Proponha uma solução** detalhada
4. **Discuta alternativas** que considerou
5. **Aguarde feedback** da comunidade

---

## 🎯 Prioridades do Projeto

### Alta Prioridade
1. Correção de bugs críticos
2. Problemas de segurança
3. Melhorias de estabilidade

### Média Prioridade
1. Novas funcionalidades do roadmap
2. Melhorias de performance
3. Expansão de testes

### Baixa Prioridade
1. Melhorias cosméticas
2. Refatorações não-críticas
3. Features experimentais

---

## 📚 Recursos Adicionais

### Documentação
- [README.md](README.md) - Documentação principal
- [CHANGELOG.md](CHANGELOG.md) - Histórico de mudanças

### Aprendizado
- [PEP 8](https://pep8.org/) - Guia de estilo Python
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

### Ferramentas
- [Black](https://black.readthedocs.io/) - Code formatter
- [Flake8](https://flake8.pycqa.org/) - Linter
- [isort](https://pycqa.github.io/isort/) - Import sorter
- [Pytest](https://pytest.org/) - Testing framework

---

## 🙏 Agradecimentos

Obrigado por contribuir para o ANBIMA Data Scraper! Sua ajuda torna este projeto melhor para todos.

---

**Dúvidas?** Abra uma issue ou entre em contato através das issues do projeto.

