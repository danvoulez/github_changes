import os
import tempfile
import shutil
from pathlib import Path
from git import Repo, GitCommandError
from loguru import logger

def clone_repo_and_get_path(repo_url: str, branch: str = "main") -> Path | None:
    """
    Clona um repositório para um diretório temporário seguro.

    Args:
        repo_url: URL completa do repositório (ex: https://github.com/owner/repo.git).
        branch: Nome da branch a ser clonada.

    Returns:
        O Path para o diretório clonado ou None em caso de erro.
        O chamador é responsável por remover o diretório após o uso.
    """
    temp_dir = None
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="promptos_clone_"))
        logger.info(f"Clonando {repo_url} (branch: {branch}) para {temp_dir}")
        Repo.clone_from(repo_url, temp_dir, branch=branch, depth=1) # depth=1 para clone mais rápido
        logger.info(f"Repositório clonado com sucesso.")
        return temp_dir
    except GitCommandError as e:
        logger.error(f"Erro ao clonar repositório {repo_url}: {e.stderr}")
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir) # Limpa em caso de erro
        return None
    except Exception as e:
        logger.error(f"Erro inesperado durante a clonagem: {e}")
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir) # Limpa em caso de erro
        return None

def safe_remove_dir(dir_path: Path | None):
    """Remove um diretório de forma segura."""
    if dir_path and dir_path.exists() and dir_path.is_dir():
        try:
            shutil.rmtree(dir_path)
            logger.debug(f"Diretório temporário {dir_path} removido.")
        except Exception as e:
            logger.error(f"Falha ao remover diretório temporário {dir_path}: {e}")
