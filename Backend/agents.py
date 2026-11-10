import re
from typing import TypedDict

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
import os

from tools import web_search, scrape_url

load_dotenv()




llm = ChatOpenAI(
    model="openrouter/free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
    
)


#1st agent 
search_agent = create_agent(
    model=llm,
    tools=[web_search]
)
#2nd agent 

reader_agent = create_agent(
    model=llm,
    tools=[scrape_url]
)



#writer chain 

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional.
SOURCE AND CITATION RULES:

1. Use only sources provided in the research data.
2. Never invent report titles, authors, organizations, URLs,
   statistics, or publication dates.
3. Every source must include its original URL.
4. Attach citations to relevant claims in the report.
5. If a claim cannot be verified from the retrieved sources,
   explicitly identify it as unverified.
6. Do not include sources that were not actually retrieved.



REVISION MODE:

You are revising an existing research report.

Previous Report:
{previous_report}

Critic Feedback:
{feedback}

Research Evidence:
{research}

Your task:

1. Identify every weakness mentioned by the Critic.
2. Create a concrete improvement for each weakness.
3. Replace weak or outdated statistics with better-supported
   evidence from the retrieved research.
4. Prioritize official reports, regulatory publications,
   exchange data, and peer-reviewed research.
5. Remove unsupported statistics rather than guessing.
6. Include a detailed methodology and limitations section.
7. Add critical analysis, not just descriptive summaries.
8. Preserve accurate information from the previous report.

IMPORTANT:
Do not simply rewrite the previous report with different words.
Every revision must address the Critic's specific feedback.
Never invent sources, statistics, or URLs.



"""),
])

writer_chain = writer_prompt | llm | StrOutputParser()

#critic_chain 


critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a strict research-report evaluator.
Evaluate factual accuracy, source quality, depth,
critical analysis, organization, and citation quality.

Always return a genuine report evaluation.
Never return a safety classification, moderation
label, or unrelated metadata.

Your first line MUST be exactly:
Score: X/10

Then include:
Strengths:
- At least two specific points

Areas to Improve:
- At least two specific points

One line verdict:
A concise evaluation of the report.

Use a score from 0 to 10. Be consistent and honest."""
    ),
    (
        "human",
        """Research topic: {topic}

Evaluate this report:
{report}"""
    ),
])


critic_chain = critic_prompt | llm | StrOutputParser()


#state
class ResearchState(TypedDict):
    topic: str
    search_results: list
    documents: list
    research: str
    report: str
    critic_feedback: str
    critic_score: float
    retrieval_attempts: int
    revision_count: int

MAX_RETRIEVAL_ATTEMPTS= 2
MAX_REVISIONS = 2
PASS_SCORE = 7.0

#nodes

def search_node(state: ResearchState):
    """Search the web for relevant sources."""
    print("🔎 SEARCH NODE")
    print("Attempt:", state.get("retrieval_attempts", 0) + 1)

    response=search_agent.invoke({
        "messages":[
            {
                "role": "user",
                "content": (
                    f"Research this topic: {state['topic']}. "
                    "Find relevant, credible sources. "
                    "Return the source URLs and key findings."
                ),
                
            }
        ]
    })

    answer = response["messages"][-1].content

    return {
        "search_results": state.get("search_results", []) + [answer],
        "retrieval_attempts": state.get("retrieval_attempts", 0) + 1,
    }

 

import re

def read_node(state: ResearchState):

    print("📖 READ NODE")

    search_text = state["search_results"][-1]

    response = reader_agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Topic: {state['topic']}\n\n"
                    f"Search results:\n{search_text}\n\n"
                    "Use scrape_url to read the relevant URLs.\n\n"
                    "Instructions:\n"
                    "1. Extract useful information relevant to the topic.\n"
                    "2. Preserve the exact original source URLs.\n"
                    "3. Include important facts, statistics, and evidence.\n"
                    "4. Associate every finding with its source URL.\n"
                    "5. Never invent facts or citations.\n"
                    "6. Clearly mention when information cannot be verified.\n"
                ),
            }
        ]
    })

    answer = response["messages"][-1].content

    # Extract original URLs directly from search results.
    urls = list(dict.fromkeys(
        re.findall(r"https?://[^\s<>\"']+", search_text)
    ))

    # Preserve URLs independently of the Reader's response.
    source_list = "\n".join(
        f"- {url}" for url in urls
    )

    document = (
        f"TOPIC: {state['topic']}\n\n"
        f"READER FINDINGS:\n{answer}\n\n"
        f"ORIGINAL SOURCE URLS:\n{source_list}"
    )

    previous = state.get("documents", [])

    updated_documents = previous + [document]

    return {
        "documents": updated_documents,
        "research": "\n\n".join(updated_documents),
    }

def evaluate_retrieval(state: ResearchState):
    """Check whether useful research was gathered."""

    research = state.get("research", "").strip()

    insufficient = (
        len(research) < 300
        or "no relevant sources found" in research.lower()
    )

    if insufficient:
        return {
            "critic_feedback": (
                "Retrieved information appears insufficient. "
                "Try a more specific search query and find "
                "additional relevant sources."
            )
        }

    return {"critic_feedback": ""}

def route_retrieval(
    state: ResearchState,
) -> str:
    research = state.get("research", "").strip()
    feedback = state.get("critic_feedback", "")

    insufficient = (
        len(research) < 300
        or bool(feedback.strip())
    )

    if (
        insufficient
        and state["retrieval_attempts"] < MAX_RETRIEVAL_ATTEMPTS
    ):
        return "search"

    return "writer"

def writer_node(state: ResearchState):
    """Generate or revise the research report."""
    print("✍️ WRITER NODE")
    print("Draft/revision:", state.get("revision_count", 0) + 1)

    

    report = writer_chain.invoke({
        "topic": state["topic"],
        "research": state.get("research", ""),
        "feedback": state.get("critic_feedback", ""),
        "previous_report":state.get("report","")
    })

    return {
        "report": report,
        "revision_count": state.get("revision_count", 0) + 1,
    }



def critic_node(state: ResearchState):
    """Evaluate the report and validate the critic's response."""

    print("\n🧐 CRITIC NODE")

    feedback = critic_chain.invoke({
        "topic": state["topic"],
        "report": state["report"],
    })

    print("\n--- RAW CRITIC RESPONSE ---")
    print(repr(feedback))
    print("---------------------------")

    match = re.search(
        r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10",
        feedback,
        re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            "Critic returned an invalid evaluation. "
            f"Expected 'Score: X/10', received: {feedback!r}"
        )

    score = float(match.group(1))

    if not 0 <= score <= 10:
        raise ValueError(f"Critic score out of range: {score}")

    print(f"📊 Critic score: {score}/10")

    return {
        "critic_feedback": feedback,
        "critic_score": score,
    }



def route_critic(state: ResearchState) -> str:
    score = state["critic_score"]
    revisions = state["revision_count"]

    if score < PASS_SCORE and revisions < MAX_REVISIONS + 1:
        print(f"↩️ Revising report: score={score}/10")
        return "writer"

    print(f"✅ Ending graph: score={score}/10")
    return "end"


#graph

Graph = StateGraph(ResearchState)

Graph.add_node("search", search_node)
Graph.add_node("read", read_node)
Graph.add_node("evaluate_retrieval", evaluate_retrieval)
Graph.add_node("writer", writer_node)
Graph.add_node("critic", critic_node)

Graph.add_edge(START, "search")
Graph.add_edge("search", "read")
Graph.add_edge("read", "evaluate_retrieval")

Graph.add_conditional_edges(
    "evaluate_retrieval",
    route_retrieval,
    {
        "search": "search",
        "writer": "writer",
    },
)

Graph.add_edge("writer", "critic")

Graph.add_conditional_edges(
    "critic",
    route_critic,
    {
        "writer": "writer",
        "end": END,
    },
)

research_graph = Graph.compile()


if __name__ == "__main__":
    print("\n🔬 ResearchMind — LangGraph Runner\n")

    topic = input("Enter research topic: ").strip()

    if not topic:
        print("❌ Research topic cannot be empty.")
    else:
        initial_state = {
            "topic": topic,
            "search_results": [],
            "documents": [],
            "research": "",
            "report": "",
            "critic_feedback": "",
            "critic_score": 0.0,
            "retrieval_attempts": 0,
            "revision_count": 0,
        }

        print("\n🚀 Starting research workflow...\n")

        try:
            result = research_graph.invoke(initial_state)

            print("\n" + "=" * 60)
            print("📄 FINAL RESEARCH REPORT")
            print("=" * 60)
            print(result.get("report", ""))

            print("\n" + "=" * 60)
            print("🧐 CRITIC FEEDBACK")
            print("=" * 60)
            print(result.get("critic_feedback", ""))
            print(f"\nFinal score: {result.get('critic_score', 0)}/10")

            print("\n✅ Research workflow completed!")

        except Exception as e:
            print(f"\n❌ Research workflow failed: {e}")
