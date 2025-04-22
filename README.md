# PromptOS v1.0 - Gerador de Patches Genérico

## Descrição

Uma ferramenta web que utiliza a API Gemini do Google para gerar patches `.diff` para repositórios GitHub com base em instruções em linguagem natural.

## Tecnologias

- FastAPI
- Python
- Docker
- Gemini API
- GitPython
- HTML/CSS/JS

## Como Usar

1. Acesse a URL da aplicação implantada.
2. Preencha o nome do repositório GitHub (formato `owner/repo`).
3. Descreva detalhadamente a mudança desejada no campo de instruções.
4. Selecione o modelo Gemini desejado.
5. Clique em "Gerar Patch".
6. Aguarde o processamento. O patch `.diff` gerado aparecerá na área de texto.
7. Use o botão "Copiar" e aplique o patch manualmente ao seu repositório local (`git apply patch.diff`).

## Setup Local

1. Clone este repositório.
2. Crie um ambiente virtual (`python -m venv .venv && source .venv/bin/activate`).
3. Instale as dependências (`pip install -r backend/requirements.txt`).
4. Copie `.env.example` para `.env` e preencha com suas chaves (`GEMINI_API_KEY`, opcionalmente `GITHUB_PAT`).
5. Rode o backend (`cd backend && python app/main.py` ou `uvicorn app.main:app --reload --port 8000`).
6. Abra o `frontend/index.html` no navegador (ou acesse `http://localhost:8000` se servido pelo FastAPI).

## Deploy (Railway)

1. Faça o push do código para um repositório GitHub/GitLab.
2. Crie um novo projeto no Railway e conecte ao seu repositório.
3. O Railway deve detectar o `Dockerfile` (ou `railway.toml` apontando para ele).
4. Configure as **Variáveis de Ambiente** no painel do Railway (essencial: `GEMINI_API_KEY`, opcional: `GITHUB_PAT`). **NÃO coloque segredos no `railway.toml`.
5. Aguarde o build e o deploy.

## Variáveis de Ambiente Necessárias

- `GEMINI_API_KEY`: Obrigatória. Chave da API Google Gemini.
- `GITHUB_PAT`: Opcional, mas recomendada. Personal Access Token do GitHub para clonar repositórios privados e evitar rate limits.
- `LOG_LEVEL`: Opcional. Padrão `INFO`.

## Considerações de Segurança

- **NUNCA** comite seu arquivo `.env` ou chaves de API no Git.
- Use variáveis de ambiente seguras para todas as credenciais.
- Restrinja as origens CORS (`allow_origins`) em produção para o domínio específico do seu frontend.
- Esteja ciente dos custos associados ao uso da API Gemini.

## Limitações Atuais

- A aplicação do patch é manual.
- A qualidade do patch depende da capacidade da Gemini e da clareza das instruções.
- Não há testes automatizados (importante para evoluções).
- Não há gerenciamento de usuários ou histórico.

## Próximos Passos / Futuro

- Implementar aplicação automática de patches (via GitPython ou gerando PRs).
- Adicionar testes unitários e de integração.
- Melhorar a validação do patch gerado.
- Interface para visualizar a estrutura de arquivos do repo clonado.
- Histórico de gerações.
