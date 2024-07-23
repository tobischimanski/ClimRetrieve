import numpy as np
import pandas as pd
import glob
import matplotlib.pyplot as plt

from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score


def findlen(name):
    result = "150len_noQ" if "150len_noQ" in name else "150len" if "150len" in name else "60len_noQ" if "60len_noQ" in name else "60len"
    return result


def allMetrics_allThreholds(data, name_pred):
    com = data.copy()
    com = com.dropna(subset=name_pred).copy()
    results = {}
    # for all three threshold: 1, 2, 3
    for i in [1, 2, 3]:
        com["num_relevance"] = com.relevance.apply(lambda x: 1 if int(x) >= i else 0)
        acc = accuracy_score(com["num_relevance"], com[name_pred])
        prec = precision_score(com["num_relevance"], com[name_pred])
        rec = recall_score(com["num_relevance"], com[name_pred])
        f1 = f1_score(com["num_relevance"], com[name_pred])
        temp_d = {"acc": acc, "precision": prec, "recall": rec, "f1": f1}
        results[i] = temp_d
    return results


def getMetrics(option, alternative, update_relevance):
    result_docs = glob.glob("./Embedding_Search_Results/*")
    outs = []
    for r in result_docs:
        topk = int(r.split("__")[-1].split(".")[0])
        embedding = r.split("\\")[-1].split("/")[-1].split("__")[0]
        temp = pd.read_csv(r, index_col=0)
        # overwrite relevance with new relevance:
        # print(temp[temp["relevance"] > 0].shape)
        temp["relevance"] = update_relevance["relevance"]
        # print(temp[temp["relevance"] > 0].shape)

        columns = ['question__question_with_IR_150len', 'simple_IR__question_with_IR_150len',
                   'IR__question_with_IR_150len', 'IR_three__question_with_IR_150len',
                   'IR_all__question_with_IR_150len', 'question__question_with_IR_150len_noQ',
                   'simple_IR__question_with_IR_150len_noQ', 'IR__question_with_IR_150len_noQ',
                   'IR_three__question_with_IR_150len_noQ', 'IR_all__question_with_IR_150len_noQ',
                   'question__question_with_IR_60len', 'simple_IR__question_with_IR_60len',
                   'IR__question_with_IR_60len', 'IR_three__question_with_IR_60len', 'IR_all__question_with_IR_60len',
                   'question__question_with_IR_60len_noQ', 'simple_IR__question_with_IR_60len_noQ',
                   'IR__question_with_IR_60len_noQ', 'IR_three__question_with_IR_60len_noQ',
                   'IR_all__question_with_IR_60len_noQ',
                   'Refined Definition__Questions_with_Explanations_V2',
                   'Raw Information Retrieval Background__Questions_with_Explanations_V2']

        embs, topks, lens, no_irs, sim_irs, ir1s, ir3s, iralls, defs, concs = [], [], [], [], [], [], [], [], [], []

        for c in columns:
            len_here = findlen(c)
            if len_here not in lens:
                lens.append(len_here)
                topks.append(topk)
                embs.append(embedding)
            cat = c.split("__")[0]
            # print(cat)
            results = allMetrics_allThreholds(temp, c)
            if cat == "question":
                no_irs.append(results[alternative][option])
            if cat == "simple_IR":
                sim_irs.append(results[alternative][option])
            if cat == "IR":
                ir1s.append(results[alternative][option])
            if cat == "IR_three":
                ir3s.append(results[alternative][option])
            if cat == "IR_all":
                iralls.append(results[alternative][option])
            if cat == "Raw Information Retrieval Background":
                concs.append(results[alternative][option])
                concs.append(results[alternative][option])
                concs.append(results[alternative][option])
                concs.append(results[alternative][option])
            if cat == "Refined Definition":
                defs.append(results[alternative][option])
                defs.append(results[alternative][option])
                defs.append(results[alternative][option])
                defs.append(results[alternative][option])

        t_out = pd.DataFrame({"embedding": embs, "topk": topks, "len": lens, "no_IR": no_irs, "simple_IR": sim_irs,
                              "IR-1": ir1s, "IR-3": ir3s, "IR-all": iralls, "definition": defs, "concepts": concs})
        outs.append(t_out)

    out = pd.concat(outs)
    return out


def visualize(embeddings, mets):
    df = mets[mets["embedding"] == embeddings].copy()
    df = df.sort_values(by="topk")

    # Plotting with larger x- and y-axis labels
    fig, axs = plt.subplots(1, 3, figsize=(18, 6), sharey=True)

    # Filter columns for plotting
    columns_to_plot = ['no_IR', 'simple_IR', 'IR-1', 'IR-3', 'IR-all']
    columns_to_plot = ['no_IR', 'simple_IR', 'IR-3', 'IR-all']
    columns_to_show = ['question', 'generic', 'inf_3', 'inf_all']
    lens_legend = ["long_Q", "long_noQ", "short_Q", "short_noQ"]

    topk_values = df['topk'].unique()

    for i, topk in enumerate(topk_values):
        subset = df[df['topk'] == topk]
        count = 0
        for index, row in subset.iterrows():
            axs[i].plot(columns_to_plot, row[columns_to_plot], marker='o', linestyle='--',
                        label=lens_legend[count])  # row['len'])
            count += 1
        axs[i].set_title(f'Top-K = {topk}', fontsize=18)
        # axs[i].set_xlabel('IR Setups', fontsize=12)
        axs[i].set_xticks(range(len(columns_to_plot)))
        axs[i].set_xticklabels(columns_to_show, fontsize=18)
        axs[i].tick_params(axis='y', labelsize=18)
        axs[i].grid(True)
        if i == 0:
            axs[i].set_ylabel('Values', fontsize=18)
        axs[i].legend(fontsize=18)

    plt.tight_layout()
    plt.show()


# base dataset
base_data = pd.read_csv("../Report-Level Dataset/ClimRetrieve_ReportLevel.csv", index_col=0)
# metric to calculate
option = "recall" # "precision", "recall", "f1"
# what is the relevance threshold
alternative = 2  # 1, 2,  3
mets_hri = getMetrics(option, alternative, base_data)
print(mets_hri.sort_values(by="topk"))

embeddings = "text-embedding-3-large"  # "text-embedding-3-small"
visualize(embeddings, mets_hri)
