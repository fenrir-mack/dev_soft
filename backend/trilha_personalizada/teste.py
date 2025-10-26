import google.generativeai as genai
from prompt import build_prompt
import json
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("models/gemini-2.5-flash")

# Tema de teste
tema = "Quero aprender a criar um site de estudo de nanomateriais"

# Gerar prompt
prompt = build_prompt(tema, "iniciante")

# Chamar IA
response = model.generate_content(prompt)

# Mostrar resposta bruta
print("🧠 Resposta bruta da IA:\n", response.text)


raw_text = response.text
try:
    trilha_data = json.loads(raw_text)
    print("✅ JSON convertido com sucesso!")
except json.JSONDecodeError as e:
    print("❌ Erro ao converter JSON:", e)

# Tentar converter em dict Python
try:
    trilha_data = json.loads(response.text)
    print("\n✅ JSON convertido com sucesso!")
    print("Título da trilha:", trilha_data["trilha"]["titulo"])
    print("Número de etapas:", len(trilha_data["etapas"]))
    print("Número de projetos:", len(trilha_data["projetos"]))
except json.JSONDecodeError:
    print("\n❌ A resposta da IA não é um JSON válido")


def mostrar_trilha(json_str):
    trilha = json.loads(json_str)

    print(f"TÍTULO DA TRILHA: {trilha['trilha']['titulo']}")
    print(f"Descrição: {trilha['trilha']['descricao']}")
    print(f"Categoria: {trilha['trilha']['categoria']}")
    print(f"Dificuldade: {trilha['trilha']['dificuldade']}\n")

    print("ETAPAS:")
    for etapa in sorted(trilha['etapas'], key=lambda x: x['ordem']):
        print(f"  {etapa['ordem']}. {etapa['titulo']}")
        for topico in sorted(etapa['topicos'], key=lambda x: x['ordem']):
            print(f"     {topico['ordem']}. {topico['texto']}")

    print("\nPROJETOS:")
    for projeto in sorted(trilha['projetos'], key=lambda x: x['ordem']):
        print(f"  {projeto['ordem']}. {projeto['titulo']}")
        print(f"     {projeto['descricao']}")

mostrar_trilha(response.text)