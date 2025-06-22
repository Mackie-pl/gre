"""
Recommendation engine module using LangChain and LangGraph.
Handles the core recommendation logic.
"""
import os
from typing import List, Dict, Any, Optional
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from vector_store import GameVectorStore

class GameRecommendationEngine:
    def __init__(
        self,
        vector_store: Optional[GameVectorStore] = None,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize the game recommendation engine.
        
        Args:
            vector_store: GameVectorStore instance.
            openai_api_key: OpenAI API key.
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize vector store if not provided
        if vector_store is None:
            self.vector_store = GameVectorStore()
            self.vector_store.create_collection()
        else:
            self.vector_store = vector_store
            
        # Initialize LLM
        self.llm = ChatOpenAI(
                openai_api_base="https://openrouter.ai/api/v1",
                openai_api_key="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",
                temperature=0.7,
                model_name="deepseek/deepseek-chat-v3-0324:free"
        )
        
        # Setup templates
        self.setup_templates()
        
        # Build the graph
        self.build_graph()
        
    def setup_templates(self):
        """Set up prompt templates for the recommendation engine."""
        # Template for query enhancement
        self.query_enhancement_template = PromptTemplate(
            input_variables=["user_query"],
            template="""
            You are an AI assistant helping users find mobile games based on their descriptions.
            Convert the user's query into a detailed search query that will help find relevant games.
            Extract key elements like visual style, gameplay mechanics, mood, and theme.
            
            User query: {user_query}
            
            Enhanced search query:
            """
        )
        
        # Template for formatting results
        self.result_formatting_template = PromptTemplate(
            input_variables=["user_query", "search_results"],
            template="""
            You are an AI assistant helping users find mobile games based on their descriptions.
            The user is looking for: {user_query}
            
            Based on this query, here are the search results:
            {search_results}
            
            Analyze these results and provide a helpful recommendation to the user.
            For each recommended game, explain why it matches what they're looking for.
            Focus particularly on how the game's visuals and gameplay relate to their query.
            If the results don't seem to match the query well, please acknowledge that and suggest 
            refining the search.
            
            Your game recommendations:
            """
        )
        
    def build_graph(self):
        """Build the LangGraph for the recommendation flow."""
        # Define state
        class State(dict):
            """State for the recommendation flow."""
            user_query: str
            enhanced_query: str
            search_results: List[Dict[str, Any]]
            final_recommendation: str
    
        # Define graph nodes
        def enhance_query(state: State) -> State:
            """Enhance the user's query to improve search results."""
            prompt = self.query_enhancement_template.format(user_query=state["user_query"])
            enhanced_query = self.llm.invoke(prompt)
            return {"enhanced_query": enhanced_query}
            
        def search_games(state: State) -> State:
            """Search for games based on the enhanced query."""
            search_results = self.vector_store.search_games(
                query=state["enhanced_query"].content,
                limit=5,
                score_threshold=0.6
            )
            return {"search_results": search_results}
            
        def format_results(state: State) -> State:
            """Format the search results into a user-friendly recommendation."""
            results_text = ""
            for i, result in enumerate(state["search_results"], 1):
                results_text += f"{i}. {result['app_name']} (Score: {result.get('similarity_score', 0):.2f})\n"
                results_text += f"   Category: {result.get('app_category', 'Unknown')}\n"
                
                # Add screenshot captions if available
                captions = result.get('screenshot_captions', [])
                if captions:
                    results_text += "   Screenshots show:\n"
                    for caption in captions[:2]:  # Limit to first 2 captions
                        results_text += f"     - {caption}\n"
                        
                # Add truncated description
                description = result.get('app_description', '')[:200]
                if description:
                    results_text += f"   Description: {description}...\n\n"
            
            prompt = self.result_formatting_template.format(
                user_query=state["user_query"],
                search_results=results_text
            )
            final_recommendation = self.llm.invoke(prompt)
            
            return {"final_recommendation": final_recommendation}
        
        # Build the graph
        workflow = StateGraph(State)
        
        # Add nodes
        workflow.add_node("enhance_query", enhance_query)
        workflow.add_node("search_games", search_games)
        workflow.add_node("format_results", format_results)
        
        # Add edges
        workflow.add_edge("enhance_query", "search_games")
        workflow.add_edge("search_games", "format_results")
        workflow.add_edge("format_results", END)
        
        # Set entry point
        workflow.set_entry_point("enhance_query")
        
        # Compile the graph
        self.graph = workflow.compile()
        
    def recommend_games(self, user_query: str) -> Dict[str, Any]:
        """
        Generate game recommendations based on the user's query.
        
        Args:
            user_query: User's query string.
            
        Returns:
            Dictionary with recommendation results.
        """
        # Initialize state with user query
        initial_state = {"user_query": user_query}
        
        # Execute the graph
        result = self.graph.invoke(initial_state)
        
        return {
            "user_query": result["user_query"],
            "enhanced_query": result["enhanced_query"],
            "recommendations": result["search_results"],
            "recommendation_text": result["final_recommendation"].content
        }

if __name__ == "__main__":
    # Example usage
    engine = GameRecommendationEngine()
    
    # Test recommendation
    result = engine.recommend_games("colorful games with cute characters similar to Candy Crush")
    
    print("User Query:", result["user_query"])
    print("Enhanced Query:", result["enhanced_query"])
    print("\nRecommendation:")
    print(result["recommendation_text"])
