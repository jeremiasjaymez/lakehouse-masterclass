import argparse

from rag_utils import ask_ollama


def build_prompt(question):
    return (
        "Respondé la siguiente pregunta sobre una masterclass de Data Lakehouse. "
        "No tenés acceso a la documentación del repo, así que respondé solo con lo que sepas.\n\n"
        f"Pregunta:\n{question}\n\n"
        "Respuesta:"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    args = parser.parse_args()

    print("Pregunta:")
    print(args.question)
    print("\nRespuesta sin RAG:")
    print(ask_ollama(build_prompt(args.question)))
