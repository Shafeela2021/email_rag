from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, ContextualPrecisionMetric, ContextualRecallMetric, GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval import evaluate
from deepeval.dataset import EvaluationDataset
from deepeval.models import OllamaModel 
import os
import sys

sys.path.append(os.path.abspath(os.path.join('..')))

from app.rag import EmailRAG


# ... (Your existing imports and RAG setup) ...

JUDGE_MODEL = OllamaModel(
        model='llama3.1',
        base_url='http://192.168.1.75:11434')

# --- METRIC-SPECIFIC RULES ---


RULES_CORRECTNESS = """
Score the FACTUAL overlap between ACTUAL and EXPECTED (1-5):
- 5: All core entities (Dates, Times, Locations) match perfectly. 
- 4: The facts are correct, but the phrasing is different.
- 3: One minor detail is missing, but no facts are WRONG.
- 2: There is a factual contradiction (e.g., wrong room or wrong time).
- 1: The answer is completely different from the Gold Answer.

EQUIVALENCY: 'Gym'='Gymnasium', '2/3'='Feb 3rd'. Ignore intro chatter.
"""

RULES_FAITHFULNESS = """
Compare ACTUAL output vs RETRIEVAL CONTEXT.
1. Does the Actual Output contain any info NOT present in the Context?
2. If the LLM claims a date/time/fact that is NOT in the context, score 0.0 (Hallucination).
3. If the LLM says "I don't know" and the info is indeed missing from context, score 1.0.
"""

RULES_RECALL = """
Compare the GOLD ANSWER to the RETRIEVED CONTEXT (Scale 1-5):
- (5) COMPLETE: Every single fact, date, and name in the Gold Answer is present in the Context.
- (3) PARTIAL: Some facts are there, but key details (like a specific time or room number) are missing from the search results.
- (1) FAILED: The context doesn't contain the information needed to answer the question at all.

MISSION: You are grading the SEARCH ENGINE, not the LLM's writing.
"""

RULES_RELEVANCY = """
CRITERIA: Does the answer address the user's intent?
- Score 5: The answer fully provides the requested info.
- Score 5: The info is NOT in the context, and the LLM honestly says "I cannot find that info." (THIS IS RELEVANT).
- Score 1: The LLM gives a generic answer that ignores the specific question.
- Score 1: The LLM makes up an answer (Hallucination).
"""

def get_dataset():
    dataset = EvaluationDataset()
    goldens = dataset.add_goldens_from_json_file(
        file_path="./data/email_goldens.json"
    )
    print(f'goldens : {dataset.goldens}')
    return dataset

def create_testcases():
    rag= EmailRAG()
    dataset = get_dataset()
    test_cases= []

    for golden in dataset.goldens:
        response = rag.ask(golden.input)
        print(f'golden.input : {golden.input}')
        print(f'golden.expected_output : {golden.expected_output}')
        print(f'golden.context : {golden.context}')
        print(f'response : {response}')
        docs = rag.retreive_docs_as_list(golden.input,5)
        print(f'docs from get_relevant_doc :{docs}')
        test_case = LLMTestCase(
            input = golden.input,
            actual_output = response,
            retrieval_context=docs,
            expected_output=golden.expected_output,
            context = golden.context
        )
        test_cases.append(test_case)
    return test_cases

def get_faithfulness_metric():
    """Checks if the answer is derived ONLY from the retrieved context."""
    return FaithfulnessMetric(
        threshold=0.5, 
        model=JUDGE_MODEL, 
        include_reason=True
    )

def get_relevancy_metric():
    """Checks if the answer actually addresses the user's query."""
    return AnswerRelevancyMetric(
        threshold=0.5, 
        model=JUDGE_MODEL, 
        include_reason=True
    )

def get_precision_metric():
    """Checks if the 'Gold' chunks are ranked at the top of retrieval."""
    return ContextualPrecisionMetric(
        threshold=0.5, 
        model=JUDGE_MODEL, 
        include_reason=True
    )

def get_recall_metric():
    """Checks if the retriever actually found the necessary information."""
    return ContextualRecallMetric(
        threshold=0.5, 
        model=JUDGE_MODEL, 
        include_reason=True
    )


def get_faithfulness_geval():
    return GEval(
        name="Faithfulness",
        model=JUDGE_MODEL,
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.RETRIEVAL_CONTEXT],
        criteria=f"MISSION: Is the LLM hallucinating? \n{RULES_FAITHFULNESS}",
        threshold=0.5
    )

def get_recall_geval():
    return GEval(
        name="Contextual Recall",
        model=JUDGE_MODEL,
        evaluation_params=[LLMTestCaseParams.EXPECTED_OUTPUT, LLMTestCaseParams.RETRIEVAL_CONTEXT],
        criteria=f"MISSION: Did the search find the right data? \n{RULES_RECALL}",
        threshold=0.5
    )

def get_relevancy_geval():
    return GEval(
        name="Answer Relevancy",
        model=JUDGE_MODEL,
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        criteria=f"MISSION: Did the LLM answer the user? \n{RULES_RELEVANCY}",
        threshold=0.5
    )

def get_correctness_geval():
    return GEval(
        name="Correctness",
        model=JUDGE_MODEL,
        evaluation_params=[
            LLMTestCaseParams.ACTUAL_OUTPUT, 
            LLMTestCaseParams.EXPECTED_OUTPUT
        ],
        criteria=f"""
        MISSION: Compare the facts in the Actual Output vs the Gold Answer.
        
        {RULES_CORRECTNESS}
        
        STEP 1: Identify the facts in the Gold Answer.
        STEP 2: See if those facts exist in the Actual Output.
        STEP 3: Provide a 1-sentence reason for your score.
        STEP 4: Output the numeric score (1-5).
        """,
        threshold=0.5 # This corresponds to a score of ~3 or higher on the 1-5 scale
    )

# --- EXECUTION ENGINE ---

def run_full_evaluation(test_cases):
    """Executes the standard RAG metrics using the evaluate() helper."""
    metrics = [
        # get_faithfulness_metric(),
        # get_relevancy_metric(),
        # get_precision_metric(),
        get_recall_metric()
    ]
    print("📊 Running RAG Pipeline Metrics...")
    evaluate(test_cases, metrics)

def run_comprehensive_eval(test_cases):
    # This list now contains all your "Layered" GEvals
    metrics = [
        # get_faithfulness_geval(),  
        # get_relevancy_geval(), 
        # get_correctness_geval() ,
        get_recall_geval()  
         
    ]
    print("🚀 Starting Advanced RAG Evaluation Suite...")
    evaluate(test_cases, metrics)

if __name__ =="__main__":
    dataset = get_dataset()
    testcases = create_testcases()

    run_full_evaluation(testcases)
    # run_comprehensive_eval(testcases)