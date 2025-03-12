"""
!pip install llama_index==0.10.29
!pip install openai==1.19.0
"""

import numpy as np
import pandas as pd

from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

from llama_index.core.schema import TextNode
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
import openai

import matplotlib.pyplot as plt


# function that takes the report and creates the retriever (with indexes etc.)
def createRetriever(paragraphs, TOP_K, EMBED_MODEL):
    # load in document
    nodes = []
    for i, p in enumerate(paragraphs):
        tn = TextNode(text=p, id_=i)
        nodes.append(tn)

    # build indexes
    index = VectorStoreIndex(
        nodes,
        embed_model=EMBED_MODEL
    )

    # configure retriever
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=TOP_K,
    )
    return retriever

def createEmbeddingsScores(embeddings, TOP_K, base_data, test_run=False):
    # tryout
    openai.api_key = "sk-.."  # TODO: CREATE YOUR OPENAI KEY
    EMBED_MODEL = OpenAIEmbedding(
        model=embeddings)  # "text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"
    TOP_K = TOP_K
    name_setup = embeddings + "__" + str(TOP_K)

    reports = base_data.report.unique()
    if test_run:
        reports = [reports[0]] # TODO: delete
    final_datasets = []


    for r in reports:
        print(r)
        report_data = base_data[base_data["report"] == r].copy()
        unique_paragraphs = report_data.paragraph.unique()

        retriever = createRetriever(unique_paragraphs, TOP_K, EMBED_MODEL)

        # retrieval
        questions = report_data.question.unique()
        for q in questions:
            IR_background_datasets = ["./Embedding_Search_Queries/question_with_IR_150len.xlsx", "./Embedding_Search_Queries/question_with_IR_150len_noQ.xlsx",
                                      "./Embedding_Search_Queries/question_with_IR_60len.xlsx", "./Embedding_Search_Queries/question_with_IR_60len_noQ.xlsx",
                                      "../Expert-Annotated Relevant Sources Dataset/Core_Questions_with_Explanations.xlsx"]
            report_question_data = report_data[report_data["question"] == q].copy()
            for irbd in IR_background_datasets:
                print(irbd)
                # if irbd != "question_with_IR_60len_noQ.xlsx":
                # continue
                # print(irbd)
                irb = pd.read_excel(irbd, index_col=0)
                searched_cols = ['question', 'simple_IR', 'IR', 'IR_three', 'IR_all']
                # in case, we have the human-defined version
                if irbd == "../Expert-Annotated Relevant Sources Dataset/Core_Questions_with_Explanations.xlsx":
                    searched_cols = ["Refined Definition", "Raw Information Retrieval Background"]

                for col in searched_cols:
                    IRB = irb[irb["question"] == q][col].iloc[0]
                    if str(IRB) == "nan":
                        print(f"Failed for: {col}")
                        continue
                    retrieved_nodes = retriever.retrieve(IRB)

                    sources = []
                    for i in retrieved_nodes:
                        # remove "\n" from the sources
                        source = i.get_content()
                        sources.append(source)

                    # search
                    name_setup = col + "__" + irbds.split("/")[-1].split(".")[0]
                    report_question_data[name_setup] = 0
                    report_question_data.loc[
                        report_question_data.paragraph.apply(lambda x: x in sources), name_setup] = 1

            final_datasets.append(report_question_data)

    # create final output
    out = pd.concat(final_datasets)
    return out


base_data = pd.read_csv("../Report-Level Dataset/Old_data/ClimRetrieve_ReportLevel_V0.csv", index_col=0)
TEST_RUN = True # TODO: adjust this if you want to have the full run

embs = ["text-embedding-3-large", "text-embedding-3-small"]  # , "text-embedding-3-large", "text-embedding-ada-002"
TOP_Ks = [5, 10, 15]

if TEST_RUN:
    embs = ["text-embedding-3-small"]  # , "text-embedding-3-large", "text-embedding-ada-002"
    TOP_Ks = [5]

for embeddings in embs:
    print()
    print("EMBEDDINGS")
    print(embeddings)
    print()
    for TOP_K in TOP_Ks:
        print()
        print("TOK_K")
        print(TOP_K)
        print()
        out = createEmbeddingsScores(embeddings, TOP_K, base_data, TEST_RUN)
        out.to_csv(f"./Intermediate_Steps_Data/{embeddings}__{TOP_K}.csv")