"""
!pip install openai==1.19.0
"""


import pandas as pd
from openai import OpenAI
import random
PROMPT_TEMPLATE = """You are a sustainability report analyst specialising on climate change adaptation and resilience.

You are provided with a <QUESTION> about a sustainability report. Your task is to explain the <QUESTION> in the context of adaptation and resilience. Please first explain the meaning of the <question>, i.e., meaning of the question itself and the concepts mentioned. And then give a list of examples, showing what information from the sustainability report the analyst is looking for by posting this <question>.

The <QUESTION> is:
{0}

Your task is to create a short {1} word explanation for which details the question is asking for.

Start the answer with 'We search for details on'. Don't mention the question itself in the text.
Your answer:
"""
# 'The question "<QUESTION>" is asking for details on'.
# REPLACED: 'We search for details on'. Don't mention the question itself in the text.

PROMPT_TEMPLATE_EXAMPLE = """You are a sustainability report analyst specialising on climate change adaptation and resilience.

You are provided with a <QUESTION> about a sustainability report. Your task is to explain the <QUESTION> in the context of adaptation and resilience. Please first explain the meaning of the <question>, i.e., meaning of the question itself and the concepts mentioned. And then give a list of examples, showing what information from the sustainability report the analyst is looking for by posting this <question>.

The <QUESTION> is:
{0}

Furthermore, you already analysed one report and extracted the following examples of relevant information the question is looking for:
---
{1}
---

Your task is to create a short {2} word explanation for which details the question is asking for.
Make sure to make use of the examples by not directly referencing them but using them to influence the details that might be of help. Be aware that the examples stem from one company from one industry. The final explanation should be applicable to all industries and companies.

Start the answer with 'We search for details on'. Don't mention the question itself in the text.
Your answer:
"""

PROMPT_TEMPLATE_EXAMPLES = """You are a sustainability report analyst specialising on climate change adaptation and resilience.

You are provided with a <QUESTION> about a sustainability report. Your task is to explain the <QUESTION> in the context of adaptation and resilience. Please first explain the meaning of the <question>, i.e., meaning of the question itself and the concepts mentioned. And then give a list of examples, showing what information from the sustainability report the analyst is looking for by posting this <question>.

The <QUESTION> is:
{0}

Furthermore, you already analysed some reports and extracted the following examples of relevant information the question is looking for:
---
{1}
---

Your task is to create a short {2} word explanation for which details the question is asking for.
Make sure to make use of the examples by not directly referencing them but using them to influence the details that might be of help. Be aware that the examples may stem from companies of certain industries. The final explanation should be applicable to all industries and companies.

Start the answer with 'We search for details on'. Don't mention the question itself in the text.
Your answer:
"""

PROMPT_TEMPLATE_ALL = """You are a sustainability report analyst specialising on climate change adaptation and resilience.

You are provided with a <QUESTION> about a sustainability report. Your task is to explain the <QUESTION> in the context of adaptation and resilience. Please first explain the meaning of the <question>, i.e., meaning of the question itself and the concepts mentioned. And then give a list of examples, showing what information from the sustainability report the analyst is looking for by posting this <question>.

The <QUESTION> is:
{0}

Furthermore, you already analysed reports and extracted the following passages of relevant information the question is looking for:
---
{1}
---

Your task is to create a short {2} word explanation for which details the question is asking for.
Make sure to make use of the passages by not directly referencing them but using them to influence the details that might be of help.

Start the answer with 'We search for details on'. Don't mention the question itself in the text.
Your answer:
"""


def processPrompt(CLIENT, MODEL, content):
    completion = CLIENT.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": content}
        ],
        temperature=0
    )

    return completion.choices[0].message.content


# randomly select one, two or three reports
# ensure 3+ examples
def getPromptWithEx(unique_question, q_data, report_num, PROMPT_TEMPLATE_EXAMPLES, LENGTH):
    # get examples
    examples = []
    count = 0

    q_data_sub = q_data[q_data["Question"] == unique_question]

    report_num = report_num
    while ((len(examples) <= 1) and (count < 6)):
        # choose random report
        # from data that has this question
        reports = random.sample(q_data_sub["Document"].unique().tolist(), report_num)
        examples = q_data_sub[
            (q_data_sub["Document"].isin(reports)) & (q_data_sub["Source Relevance Score"] >= 2)].Relevant.to_list()
        count += 1

    if count > 5:
        print("hi")
        return ("NA", "NA", "NA", "NA")

    # create prompt
    rel_str = ""
    for i, r in enumerate(examples):
        rel_str += f"Example {i}: {r}\n"
    prompt = PROMPT_TEMPLATE_EXAMPLES.format(unique_question, rel_str, LENGTH)

    return prompt, examples, reports, report_num


def getPromptWithAll(unique_question, q_data, PROMPT_TEMPLATE, LENGTH):
    # get examples
    passages = []
    count = 0
    q_data_sub = q_data[q_data["Question"] == unique_question]
    all_data = q_data_sub[(q_data_sub["Source Relevance Score"] >= 2)].Relevant.to_list()
    # only those longer than 10 signs
    all_data = [x for x in all_data if len(str(x)) > 5]

    if len(all_data) == 0:
        print("hi")
        return "NA"

    # create prompt
    rel_str = ""
    for i, r in enumerate(examples):
        rel_str += f"Passage {i}: {r}\n"
    prompt = PROMPT_TEMPLATE_EXAMPLES.format(unique_question, rel_str, LENGTH)

    return prompt


LENGTH = 150  # TODO: ADJUST LENGTH
# openai key
CLIENT = OpenAI(api_key="sk-...")  # TODO: CREATE YOUR OWN KEY TO EXECUTE
MODEL = "gpt-4o-mini-2024-07-18"  # "gpt-4-0125-preview" "gpt-4-0125-preview" GPT-4-turbo
TEST_RUN = True # TODO: IF YOU ARE SATISFIED, DON'T RUN AS TEST

# create Answers
q_data = pd.read_excel("../Expert-Annotated Relevant Sources Dataset/ClimRetrieve_base.xlsx", index_col=0)
# transform Source Relevance Score
qs, irs_simple, irs, reports_all, irs_three, reports_threes, irs_all = [], [], [], [], [], [], []

questions = q_data.Question.dropna().unique()
if TEST_RUN:
  questions = questions[:2]

for uq in questions:
    print(uq)
    # prompts
    prompt_simple = PROMPT_TEMPLATE.format(uq, LENGTH)
    report_number = 1
    prompt, examples, reports, report_num = getPromptWithEx(uq, q_data, report_number, PROMPT_TEMPLATE_EXAMPLE, LENGTH)
    report_number = 3
    prompt_three, examples, reports_three, report_num = getPromptWithEx(uq, q_data, report_number,
                                                                        PROMPT_TEMPLATE_EXAMPLES, LENGTH)
    prompt_all = getPromptWithAll(uq, q_data, PROMPT_TEMPLATE_ALL, LENGTH)

    # create IRs
    answer_simple = processPrompt(CLIENT, MODEL, prompt_simple)
    if prompt == "NA":
        answer = "NA"
    else:
        answer = processPrompt(CLIENT, MODEL, prompt)
    if prompt_three == "NA":
        answer_three = "NA"
    else:
        answer_three = processPrompt(CLIENT, MODEL, prompt_three)
    if prompt_all == "NA":
        answer_all = "NA"
    else:
        answer_all = processPrompt(CLIENT, MODEL, prompt_all)

    qs.append(uq)
    irs_simple.append(answer_simple)
    irs.append(answer)
    reports_all.append(reports[0])  # only one report
    irs_three.append(answer_three)
    reports_threes.append(reports_three)  # three reports
    irs_all.append(answer_all)

question_with_IR = pd.DataFrame({"question": qs, "simple_IR": irs_simple, "IR": irs, "report_inspiration": reports_all,
                                 "IR_three": irs_three, "report_three": reports_threes, "IR_all": irs_all})
question_with_IR.to_excel(f"./Intermediate_Steps_Data/question_with_IR_{LENGTH}len_noQ.xlsx")
