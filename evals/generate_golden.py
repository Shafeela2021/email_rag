from deepeval.synthesizer import Synthesizer
from deepeval.models import OllamaModel 
from deepeval.synthesizer.config import StylingConfig
from deepeval.dataset import EvaluationDataset
import sys
import os

sys.path.append(os.path.abspath(os.path.join('..')))

from app.rag import EmailRAG



custom_model = OllamaModel(
    model='llama3.1',
    base_url='http://192.168.1.75:11434'
)



def create_golden_dataset():
    rag = EmailRAG()
    docs = rag.get_random_chunk(num_chunks=5)
    contexts = [[doc[:600]]for doc in docs]
    print(contexts)

    styling_config = StylingConfig(
        task=(
        "Generate a single, direct, and ultra-short question (max 10 words) based on the provided email context. "
        "The question should be simple and specific, such as 'When is the badminton tryout?' or 'Who is the coach?'."
    ),
    input_format=(
        "A simple, one-sentence question ending in a question mark. "
        "Strictly no conversational filler, introductory text, or complex multi-part questions."
    ),
    scenario="A student is quickly asking a school administrator for a specific detail via email."
    )
    synthesizer = Synthesizer(
        model=custom_model,
        styling_config=styling_config
    )

    goldens = synthesizer.generate_goldens_from_contexts(
        contexts = contexts,
        include_expected_output = True,
        max_goldens_per_context = 1
    )

    dataset = EvaluationDataset(goldens=goldens)
    dataset.save_as(file_type="json", directory="./data", file_name="email_goldens_1")
    print(f"✅ Success! Generated {len(goldens)} golden pairs.")

if __name__ =="__main__":
    create_golden_dataset()

