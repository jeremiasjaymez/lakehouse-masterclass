import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "ai"))

from rag_utils import ask_ollama, build_rag_prompt, embed_text, rank_chunks
from utils import get_spark_with_nessie

parser = argparse.ArgumentParser()
parser.add_argument("question")
parser.add_argument("--top-k", type=int, default=3)
args = parser.parse_args()

spark = get_spark_with_nessie("rag-answer")

question_embedding = embed_text(args.question)
rows = spark.table("nessie.gold.knowledge_chunks").collect()
top_chunks = rank_chunks(question_embedding, rows, top_k=args.top_k)
answer = ask_ollama(build_rag_prompt(args.question, top_chunks))

print("Pregunta:")
print(args.question)
print("\nRespuesta:")
print(answer)
print("\nFuentes recuperadas:")
for index, chunk in enumerate(top_chunks, start=1):
    print(
        f"{index}. {chunk['source_path']} :: {chunk['section_title']} "
        f"(score={chunk['score']:.3f})"
    )

spark.stop()
