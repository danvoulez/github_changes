# backend/app/main.py
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from loguru import logger
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env APENAS em desenvolvimento local
# Em produção (Railway), as variáveis são injetadas diretamente
if os.getenv("RAILWAY_ENVIRONMENT") != "production":
    load_dotenv()

# Importa funções e clientes
from app.tools.client_gemini import generate_via_gemini
from app.tools.utils import clone_repo_and_get_path, safe_remove_dir

# --- Configuração do Logging ---
log_level = os.getenv("LOG_LEVEL", "INFO")
# logger.add("logs/backend_{time}.log", rotation="1 day", level=log_level) # Opcional: log para arquivo
logger.add(lambda msg: print(msg, end=""), level=log_level, colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")


# --- Ciclo de Vida da Aplicação (Opcional, mas bom para inicialização/limpeza) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando PromptOS Backend Service...")
    # Coloque aqui código de inicialização (ex: conectar ao DB, Redis)
    yield
    logger.info("Encerrando PromptOS Backend Service...")
    # Coloque aqui código de limpeza (ex: fechar conexões)


# --- Inicialização do FastAPI ---
app = FastAPI(
    title="PromptOS Backend API v1.0",
    description="API para gerar patches de código usando Gemini.",
    version="1.0.0",
    lifespan=lifespan # Usa o gerenciador de ciclo de vida
)

# --- Middlewares ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja para o domínio do seu frontend!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modelos Pydantic (Requisições e Respostas) ---
class PatchRequest(BaseModel):
    repo: str = Field(..., description="Repositório no formato 'owner/repo'")
    instructions: str = Field(..., description="Instruções detalhadas para a geração do patch")
    model: str = Field(default="gemini-pro", description="Modelo Gemini a ser usado")
    # Removido: github_token, branch, file_paths

class PatchResponse(BaseModel):
    patch: str | None = Field(description="O patch .diff gerado ou None em caso de falha")
    message: str = Field(description="Mensagem de status")

# --- Endpoints da API ---

@app.post("/promptos/patch", response_model=PatchResponse)
async def make_generic_patch(req: PatchRequest):
    """
    Endpoint principal para gerar um patch .diff para um repositório GitHub.
    1. Constrói a URL de clone (usando GITHUB_PAT do env se disponível).
    2. Clona o repositório para um diretório temporário.
    3. Monta um prompt detalhado para a Gemini com as instruções.
    4. Chama a API Gemini para gerar o patch.
    5. Retorna o patch ou uma mensagem de erro.
    6. Limpa o diretório temporário.
    """
    logger.info(f"Recebida requisição de patch para repo: {req.repo} com modelo {req.model}")

    github_token = os.getenv("GITHUB_PAT")
    # Constrói a URL de clone segura
    if github_token:
        clone_url = f"https://oauth2:{github_token}@github.com/{req.repo}.git"
        logger.debug("Usando GITHUB_PAT para clonar.")
    else:
        clone_url = f"https://github.com/{req.repo}.git"
        logger.warning("GITHUB_PAT não encontrado no ambiente. Clonando repo público.")

    cloned_repo_path: Path | None = None
    try:
        # 1. Clonar o repositório
        cloned_repo_path = clone_repo_and_get_path(clone_url) # Branch padrão é 'main'
        if not cloned_repo_path:
            raise HTTPException(status_code=400, detail=f"Não foi possível clonar o repositório '{req.repo}'. Verifique a URL e as permissões (GITHUB_PAT).")

        # 2. Montar o prompt para Gemini
        #    (Não lemos arquivos aqui, confiamos nas instruções e na inferência da Gemini)
        #    Podemos opcionalmente listar a estrutura de arquivos para dar contexto
        file_structure = []
        try:
            for item in sorted(cloned_repo_path.rglob('*')):
                 if item.is_file() and '.git' not in item.parts: # Ignora o .git
                      relative_path = str(item.relative_to(cloned_repo_path))
                      file_structure.append(relative_path)
        except Exception as e:
             logger.warning(f"Não foi possível listar a estrutura de arquivos: {e}")


        prompt = (
            f"Você é um assistente de programação especialista em gerar patches Git.\n"
            f"Analise as instruções abaixo para o repositório '{req.repo}'.\n"
            f"Considere a seguinte estrutura de arquivos (pode estar incompleta):\n"
            f"{chr(10).join(file_structure) if file_structure else 'Estrutura de arquivos não disponível.'}\n\n"
            f"INSTRUÇÕES DO USUÁRIO:\n"
            f"----------------------\n"
            f"{req.instructions}\n"
            f"----------------------\n\n"
            f"Gere APENAS um patch válido no formato unified diff (`.diff`) que implemente EXATAMENTE as instruções fornecidas.\n"
            f"O patch deve ser aplicável com `git apply patch.diff` na raiz do repositório.\n"
            f"Certifique-se que os caminhos dos arquivos no patch (ex: `--- a/path/to/file.py`, `+++ b/path/to/file.py`) estão corretos relativamente à raiz do repositório.\n"
            f"Se as instruções não forem claras ou não puderem ser implementadas como um patch, retorne apenas a palavra 'IMPOSSÍVEL'."
        )
        logger.debug(f"Prompt enviado para Gemini (primeiros 500 chars): {prompt[:500]}...")

        # 3. Chamar Gemini
        generated_text = generate_via_gemini(prompt, model_name=req.model)

        if not generated_text:
            raise HTTPException(status_code=500, detail="Falha ao gerar texto com a API Gemini.")
        if "IMPOSSÍVEL" in generated_text:
             raise HTTPException(status_code=400, detail="Gemini indicou que não é possível gerar um patch com as instruções fornecidas.")
        # Uma validação básica se parece com um diff
        if not ("--- a/" in generated_text and "+++ b/" in generated_text):
             logger.warning("Texto gerado pela Gemini não parece um patch .diff válido.")
             # Poderia tentar tratar ou apenas retornar como está
             # raise HTTPException(status_code=500, detail="A resposta da Gemini não parece ser um patch .diff válido.")


        logger.info("Patch gerado com sucesso.")
        return PatchResponse(patch=generated_text, message="Patch gerado com sucesso!")

    except HTTPException as http_exc:
        # Re-lança exceções HTTP para serem tratadas pelo FastAPI
        logger.error(f"Erro HTTP: {http_exc.status_code} - {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception("Erro inesperado no endpoint /promptos/patch:") # Loga o traceback completo
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {e}")
    finally:
        # 4. Limpeza SEMPRE garante a remoção do diretório temporário
        safe_remove_dir(cloned_repo_path)


# --- Servir Arquivos Estáticos (Frontend) ---
# Certifique-se que o diretório 'frontend' está no nível correto relativo a este arquivo
try:
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    if frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
        logger.info(f"Servindo frontend estático de: {frontend_dir}")
    else:
        logger.warning(f"Diretório frontend não encontrado em {frontend_dir}. O frontend não será servido.")
except Exception as e:
    logger.error(f"Erro ao tentar montar diretório estático: {e}")


# --- Tratador Global de Exceções (Opcional) ---
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Log genérico para qualquer exceção não tratada especificamente
    logger.exception(f"Erro não tratado durante requisição para {request.url}:")
    return JSONResponse(
        status_code=500,
        content={"message": "Ocorreu um erro interno inesperado no servidor."},
    )

# --- Ponto de Entrada (se executado diretamente, para debug local) ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Executando em modo de debug local com Uvicorn.")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

