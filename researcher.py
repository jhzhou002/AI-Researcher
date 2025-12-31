import arxiv
from openai import OpenAI
import os

class Paper:
    def __init__(self, title, authors, summary, url, published):
        self.title = title
        self.authors = authors
        self.summary = summary
        self.url = url
        self.published = published

    def __str__(self):
        return f"{self.title} - {', '.join(self.authors)}"

def search_arxiv(query, max_results=10):
    """
    Search ArXiv for papers based on a query.
    """
    if not query:
        return []

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    results = []
    try:
        for r in client.results(search):
            paper = Paper(
                title=r.title,
                authors=[a.name for a in r.authors],
                summary=r.summary,
                url=r.pdf_url,
                published=r.published.strftime("%Y-%m-%d")
            )
            results.append(paper)
    except Exception as e:
        print(f"Error searching ArXiv: {e}")
        
    return results

def generate_review(papers, api_key, topic):
    """
    Generate a literature review using OpenAI API based on the summaries of the papers.
    """
    if not papers:
        return "No papers found to review."
    
    if not api_key:
        return "Please provide an OpenAI API Key to generate the review."

    client = OpenAI(api_key=api_key)
    
    # Prepare the context from papers
    context = ""
    for i, p in enumerate(papers):
        context += f"Paper {i+1}:\nTitle: {p.title}\nAuthors: {', '.join(p.authors)}\nPublished: {p.published}\nAbstract: {p.summary}\n\n"

    prompt = f"""
    You are an expert academic researcher. 
    I need a comprehensive literature review on the topic: "{topic}".
    
    Below are the abstracts of relevant papers found on ArXiv.
    Please write a structured literature review synthesizing these papers.
    Categorize the approaches if possible, highlight common themes, and identify gaps if evident.
    Quote heavily from the provided abstracts to support your points.
    
    Papers:
    {context}
    
    Output Format in Markdown.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Or gpt-3.5-turbo if cost is a concern, but 4o is better for reasoning
            messages=[
                {"role": "system", "content": "You are a helpful research assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating review: {e}"
