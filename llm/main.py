import logging
import os
from dataclasses import dataclass, field

from google import genai

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@dataclass
class LLMDiplomaConsumer:
    """
    A class to interact with the Gemini API using the Client pattern
    to generate an X post summarizing a Portuguese parliamentary diploma.
    """

    model_name: str = "gemini-2.5-pro"
    client: genai.Client = field(init=False)

    def __post_init__(self):
        try:
            self.client = genai.Client()
            logging.info(
                f"Successfully initialized Gemini Client for model '{self.model_name}'."
            )
        except Exception as e:
            logging.error(
                f"Failed to initialize Gemini Client. Ensure GEMINI_API_KEY is set. Error: {e}"
            )
            raise

    def _prepare_input(
        self, diploma_markdown: str, diploma_context_markdown: str
    ) -> str:
        return f"""
            És um jornalista político cujo objetivo é obter o conteúdo e o contexto dos diplomas recentemente aprovados pelo parlamento português e produzir um X post que consiste num resumo conciso e direto do que foi aprovado. Apenas menciona o conteúdo relevante para um leitor comum, baseado apenas no conteúdo fornecido. O tom não deverá ser euforico nem humoristico mas meramente informativo. Aqui está um exemplo:

            Redução do IRS em 2025 aprovada na generalidade pelo Parlamento.
            A proposta do Governo para a descida do IRS foi aprovada pelo PSD, CHEGA e IL, com abstenção do Livre e do PS. PCP e BE votam contra.

            Conteúdo do diploma aprovado:
            {diploma_markdown}

            Texto original da inicitiva (contexto do diploma):
            {diploma_context_markdown}
        """

    def get_post_content(
        self, diploma_markdown: str, diploma_context_markdown: str
    ) -> str:
        prompt = self._prepare_input(diploma_markdown, diploma_context_markdown)

        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )

            if response.text:
                logging.info("Successfully generated content from the API.")
                return response.text.strip()
            else:
                logging.warning(
                    "API response was empty. This may be due to safety settings."
                )
                return "Error: Could not generate post content. The API returned an empty response."

        except Exception as e:
            logging.error(f"An error occurred while calling the Gemini API: {e}")
            return "Error: An API error occurred while generating the post content."


# --- Example Usage ---
if __name__ == "__main__":
    if "GEMINI_API_KEY" not in os.environ:
        print("ERROR: Please set the GEMINI_API_KEY environment variable.")
    else:
        diploma_content = """
        - Artigo 1: Alteração ao Código do Trabalho
        - O presente diploma procede à segunda alteração à Lei n.º 7/2009.
        - Artigo 2: Aditamento ao Código do Trabalho
        - É aditado o artigo 127.º-A, com a seguinte redação:
        - "Artigo 127.º-A: O trabalhador tem direito a uma folga remunerada no dia do seu aniversário."
        """
        context_text = """
        - Exposição de motivos:
        - A presente iniciativa legislativa visa reforçar os direitos dos trabalhadores,
        - promovendo um melhor equilíbrio entre a vida profissional e pessoal.
        """

        consumer = LLMDiplomaConsumer()

        post = consumer.get_post_content(
            diploma_markdown=diploma_content, diploma_context_markdown=context_text
        )
        print("\n--- Generated X Post ---\n")
        print(post)
        print("\n------------------------\n")
