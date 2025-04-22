import os
import google.generativeai as genai
from loguru import logger

# Configura a API Key da Gemini a partir das variáveis de ambiente
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.warning("Variável de ambiente GEMINI_API_KEY não definida.")
        # Você pode querer lançar um erro aqui se a chave for estritamente necessária
    else:
        genai.configure(api_key=gemini_api_key)
except Exception as e:
    logger.error(f"Erro ao configurar a API Gemini: {e}")


def generate_via_gemini(prompt: str, model_name: str = "gemini-pro") -> str | None:
    """
    Gera texto (patch, código, etc.) usando a API Gemini.

    Args:
        prompt: O prompt de entrada para o modelo.
        model_name: O nome do modelo Gemini a ser usado (ex: "gemini-pro").

    Returns:
        O texto gerado pela Gemini ou None em caso de erro.
    """
    if not gemini_api_key:
         logger.error("API Key da Gemini não configurada. Não é possível gerar texto.")
         return None
    try:
        logger.info(f"Chamando Gemini com modelo {model_name}...")
        # Remova 'model/' do nome se presente (API espera 'gemini-pro', não 'models/gemini-pro')
        clean_model_name = model_name.replace("models/", "")
        model = genai.GenerativeModel(clean_model_name)

        # Ajuste os parâmetros conforme necessário
        generation_config = genai.types.GenerationConfig(
            # candidate_count=1, # Geralmente 1 é suficiente
            # stop_sequences=['...'], # Se precisar parar em palavras específicas
            # max_output_tokens=2048, # Ajuste conforme a necessidade
            temperature=0.7,      # Ajuste para mais ou menos criatividade (0.0 a 1.0)
            # top_p=1.0,          # Ajuste se necessário
            # top_k=1             # Ajuste se necessário
        )

        # TODO: Adicionar configurações de segurança (safety_settings) se necessário
        # safety_settings = [...]

        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            # safety_settings=safety_settings
            )

        # Verifica se a resposta tem o texto esperado
        if response.parts:
             generated_text = "".join(part.text for part in response.parts)
             logger.info(f"Gemini retornou {len(generated_text)} caracteres.")
             return generated_text
        elif response.prompt_feedback and response.prompt_feedback.block_reason:
             logger.error(f"Geração bloqueada pela Gemini. Razão: {response.prompt_feedback.block_reason}")
             logger.error(f"Detalhes: {response.prompt_feedback.safety_ratings}")
             return None # Ou lançar um erro específico
        else:
             logger.warning("Resposta da Gemini não contém texto ou foi bloqueada sem razão explícita.")
             logger.debug(f"Resposta completa da Gemini: {response}")
             return None


    except Exception as e:
        logger.error(f"Erro durante a chamada à API Gemini ({model_name}): {e}")
        # Você pode querer analisar tipos específicos de erros da API aqui
        return None
