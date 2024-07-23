# ClimRetrieve: A Benchmarking Dataset for Information Retrieval from Corporate Climate Disclosures

This is the GitHub repository for the paper ["ClimRetrieve: A Benchmarking Dataset for Information Retrieval from Corporate Climate Disclosures"](https://arxiv.org/abs/2406.09818). Here, you will find the datasets created in the paper. The paper itself delivers a detailed description of the dataset creation. We upload two datasets and code for the experiments.

## Expert-Annotated Relevant Sources Dataset

The first product of the paper is the expert-annotated dataset. In this dataset, three expert labelers have walked through reports (in the "Reports" folder) and searched for information corresponding to climate change questions.

As a result, they created the "ClimRetrieve_base" dataset with the following form:

- **Document**: Report under investigation. 
- **Question**: Question under investigation. 
- **Relevant**: Full-sentence form question-relevant information. 
- **Context**: Context of the question relevant information (extending the relevant information by a sentence before and afterward). 
- **Page**: Page of the relevant information. 
- **Source From**: Answers whether the relevant information is from text, table, or graph. 
- **Source Relevance Score**: Classifies from 1-3 how relevant the information is for answering the question (see Appendix E for details on the relevance classification). 
- **Unsure Flag**: Flag whether it is unclear if this source is question-relevant. 
- **Addressed directly**: Flag whether the relevant information addresses the question directly or indirectly. 
- **Answer**: Answer to the question based on all retrieved relevant information.
- **Core 16 Question**: Indicator variable that signals whether the question is among the core 16 questions. These are the main questions under investigation. Other questions have also been answered and might be of use to researchers (hence included here).


Furthermore, every of the core 16 questions under investigation was defined by the lablers.

As a result, we created the "Core_Questions_with_Explanations" dataset with the following columns:

- **question**: Question under investigation.
- **Definition**: Initial labler definition.
- **Refined Definition**: Refined definition after labeling.
- **Raw Information Retrieval Background**: Concepts that the question contained (see paper Appendix A).
- **Information Retrieval Background**: Concepts that the question contained (see paper Appendix A). Concepts are classified to be Core (Co) or Latent (La) concepts. Furthermore, they are classified to be very broad (C1), concrete (C2), or very concrete (C3) concepts.
- **Answer Definition Help**: Help to answer the question.

As mentioned in the paper, these concepts and definitions are personal help for the labelers rather than general truths about the question. Thus, they have an explanatory power of the mental model of the labler but do not entirely capture it. Rather, this represents a first approach towards making labler thoughts transparent.

## Report-Level Dataset

The "ClimRetrieve_base" data contains relevant sources extracted from reports. The report-level dataset is a result of parsing the entire report and searching for the content (see Appendix G in the paper).

The "ClimRetrieve_ReportLevel" dataset has the following form:

- paragraph: Paragraph of a given report.
- report: Report under investigation.
- question: Question that was investigated for the report.
- relevant_text: Potentially relevant text for the question.
- relevance: Relevance label from 0-3. Classifies how relevant the information is for answering the question (see Appendix E for details on the relevance classification).
- relevance_text_sim: Similarity of the _relevant_text_ to the _paragraph_. Values range from 0 (not at all similar) to 1 (identical).
- sim_text_relevance: _Relevance_ label of the most similar _relevant_text_. This only has explanatory power if the _relevant_text_ and the _paragraph_ are very similar (i.e., they are the same text). In the paper, we set the similarity threshold to 0.9 to be identical. Then _relevance_ is set to _sim_text_relevance_, otherwise _relevance_ is set to zero.

You will find the code for creating this dataset in the "Report-Level Dataset" folder. A demo run has already been implemented. When using the code, make yourself familiar with the details of implementation (e.g., selected thresholds).

## Experiments

We follow three steps to execute the experiments:
1. Create the new information retrieval background for the embedding search (see "create_embedding_search_queries.py" and folder "Embedding_Search_Queries").
2. Search for the top-k paragraphs with different information retrieval strategies (see "create_embedding_search_results.py" and folder "Embedding_Search_Results").
3. Aggregate model results and create a visualization (see "analyse_results.py").
