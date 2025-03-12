"""
Recommended installations:
!pip install llama_index==0.10.29
!pip install spacy
"""


import pandas as pd
import glob
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
import spacy
from difflib import SequenceMatcher



def reportToParagraphs(REPORT, CHUNK_SIZE, CHUNK_OVERLAP):
    # report to text
    documents = SimpleDirectoryReader(input_files=[REPORT]).load_data()
    parser = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)  # tries to keep sentences together
    nodes = parser.get_nodes_from_documents(documents)

    paragraphs = []
    for i in nodes:
        text = i.get_content().replace("\n", "")
        paragraphs.append(text)

    return paragraphs


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


# returns count > 0 if match is found
def findmatch(annotated, retrieved, nlp):
    retrieved = str(retrieved)
    annotated = str(annotated)
    # try simple matching first
    if (len(str(annotated)) > 15) & (str(annotated) in str(retrieved)):
        return 1

    # else split both annotated and retrieved into sentences
    doc1 = nlp(str(annotated))
    doc2 = nlp(str(retrieved))
    sent_a = []
    for sent in doc1.sents:
        sent_a.append(sent.text)
    sent_r = []
    for sent in doc2.sents:
        sent_r.append(sent.text)

    # sent_a = nltk.sent_tokenize(str(annotated))
    # sent_r = nltk.sent_tokenize(str(retrieved))
    dict_out = {}
    for a in sent_a:
        if (len(a) > 15) and (a in retrieved):
            return 1
        row = []
        for r in sent_r:
            row.append(similar(a, r))
        dict_out[a] = row

    # create df that is similarity matrix
    simmat = pd.DataFrame(dict_out).T
    simmat.columns = sent_r

    # values above threshold
    # values_above_t = simmat[simmat > threshold]
    # count = values_above_t.count().sum()

    # find max value
    max_value = simmat.max().max()

    # return simmat
    return max_value


"""
Function that chunks up reports and creates report-level a dataset using LlamaIndex
"""


def chunking(base_data, test_run=False):
    # hyperparams
    CHUNK_SIZE = 350
    CHUNK_OVERLAP = 50
    reports = glob.glob("../Reports/*")
    if test_run:
        reports = reports[:2]

    final_data = []
    for r in reports:
        r_name = r.split("\\")[-1].split("/")[-1]
        print(r_name)
        report_data = base_data[
            base_data["Document"].apply(lambda x: True if r_name in str(x) else False)].copy()
        # get paragraphs and questions
        paras = reportToParagraphs(r, CHUNK_SIZE, CHUNK_OVERLAP)
        questions_in_report = report_data.Question.unique()
        for q in questions_in_report:
            df = pd.DataFrame({"paragraph": paras})
            df["report"] = r_name
            df["question"] = q
            final_data.append(df)

    out = pd.concat(final_data)
    if test_run:
        out.to_csv(f"./Intermediate_Steps_Data/report_level_data_test.csv")
    return out


"""
Function that calculates the most similar sentence and assign the relevance by threshold
"""
def relevance_calculation(base_data, report_paragraph, nlp, test_run=False):
    report_paragraph["relevant_text"] = "NA"
    report_paragraph["relevant_paragraph_sim"] = 0
    report_paragraph["relevance"] = 0
    # go through every report
    dfs_report_question_data = []
    reports = report_paragraph.report.unique()
    if test_run:
        reports = reports[:1]
    for r in reports:
        print(r)
        report_data = report_paragraph[report_paragraph["report"] == r].copy()
        # go through every question
        questions = report_data.question.unique()
        for q in questions:
            print(q)
            report_question_data = report_data[report_data["question"] == q].copy()
            relevant_parts = base_data[(base_data["Document"] == r) & (base_data["Question"] == q)].copy()
            for row in relevant_parts.iterrows():
                relevant_text = row[1]["Relevant"]
                relevance = row[1]["Source Relevance Score"]
                # find this relevant text in the report
                sim_scores_paragraphs = report_question_data.paragraph.apply(
                    lambda retrieved: findmatch(relevant_text, retrieved, nlp))
                # compare pairwise
                current_rps = report_question_data.relevant_paragraph_sim.to_list()
                current_rts = report_question_data.relevant_text.to_list()
                current_rels = report_question_data.relevance.to_list()
                new_rt, new_rps, new_rel = [], [], []
                for i, ssp in enumerate(sim_scores_paragraphs):
                    if ssp > current_rps[i]:
                        new_rt.append(relevant_text)
                        new_rps.append(ssp)
                        new_rel.append(relevance)
                    else:
                        new_rt.append(current_rts[i])
                        new_rps.append(current_rps[i])
                        new_rel.append(current_rels[i])
                report_question_data["relevant_text"] = new_rt
                report_question_data["relevant_paragraph_sim"] = new_rps
                report_question_data["relevance"] = new_rel
            # save the report_question_data data again to fully build up new dataset finally
            dfs_report_question_data.append(report_question_data)
            out = pd.concat(dfs_report_question_data)
            #out.to_csv("./Intermediate_Steps_Data/report_level_data_final_test.csv")

    out = pd.concat(dfs_report_question_data)
    # transform everything to numeric
    out["relevance"] = out["relevance"].apply(
        lambda x: 1 if "1" in str(x) else 2 if "2" in str(x) else 3 if "3" in str(x) else x)
    # transfer relevance threshold 0.9
    out["relevance_threshold0.9"] = out.apply(
        lambda row: 0 if (row["relevant_paragraph_sim"] < 0.9) or (len(str(row["relevant_text"])) < 5) else row[
            "relevance"], axis=1)
    save = out.copy()
    save.rename(columns={'relevant_paragraph_sim': 'relevant_text_sim'}, inplace=True)
    save.rename(columns={'relevance': 'sim_text_relevance'}, inplace=True)
    save.rename(columns={'relevance_threshold0.9': 'relevance'}, inplace=True)
    save = save[['paragraph', 'report', 'question', 'relevant_text', 'relevance',
       'relevant_text_sim', 'sim_text_relevance']].copy()
    if test_run:
        save.to_csv("./Intermediate_Steps_Data/report_level_data_final_test.csv")
    return save

def main():
    # load base data
    base_data = pd.read_excel("../Expert-Annotated Relevant Sources Dataset/ClimRetrieve_base.xlsx", index_col=0)
    # test_run variable to quickly see functionality
    test_run = False
    # chunk up the reports
    print("Chunk up reports")
    report_paragraph = chunking(base_data, test_run=test_run)  # saved in Intermediate_Steps_Data
    nlp = spacy.load('en_core_web_sm')
    # final dataset
    print("Find annotated sentences")
    final = relevance_calculation(base_data, report_paragraph, nlp, test_run=test_run)
    final.to_csv("ClimRetrieve_ReportLevel_V1.csv")

if __name__ == '__main__':
    main()
