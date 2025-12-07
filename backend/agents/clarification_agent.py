from backend.services.text_service import query_groq_text
from backend.agents.agri_agent_base import AgriAgentBase

class ClarificationAgent(AgriAgentBase):
    """
    ClarificationAgent
    
    Before sending the farmer to a specialist (Pest/Crop/Irrigation),
    this agent makes sure we actually understand what they need.
    
    It handles:
    - Vague queries: "My plant is sick" -> "What crop? What symptoms?"
    - Greetings: "Hi" -> "Hello! How can I help?"
    - Gibberish: "???" -> "I didn't quite get that. Could you rephrase?"
    """

    name = "ClarificationAgent"
    
    
    GREETINGS = {"hi", "hello", "hey", "hola", "good morning", "good afternoon", "good evening, hii"}
    THANKS = {"thanks", "thank you", "thx", "ty", "appreciate it"}
    GOODBYES = {"bye", "goodbye", "see you", "later", "cya"}

    def handle_query(self, query: str = None, image_path: str = None, chat_history: str = None) -> str:
        
        if not query or not query.strip():
            return "Hello! I'm AgriGPT, your farming assistant. What crop or issue would you like help with today?"

        clean_query = query.strip()
        lower_query = clean_query.lower()
        
        if lower_query in self.GREETINGS:
            return "Hello! I'm AgriGPT, your farming assistant. What crop or issue can I help you with today?"
        
        if lower_query in self.THANKS:
            return "You're welcome! Let me know if you have any more questions."
        

        if lower_query in self.GOODBYES:
            return "Goodbye! Feel free to come back anytime. Happy farming!"
        
        if len(clean_query) < 2:
            return "I didn't quite catch that. Could you tell me more about what you need help with?"

        has_image = "Yes (the user uploaded an image)" if image_path else "No"

        prompt = f"""
You are AgriGPT's friendly Clarification Assistant.
Your job is to make sure we understand the farmer's question BEFORE we try to answer it.

=== CONTEXT ===
Previous Chat: {chat_history if chat_history else "None (this is the first message)."}
Image Uploaded: {has_image}

=== USER'S MESSAGE ===
"{clean_query}"

=== YOUR INSTRUCTIONS ===

1. **If the message is a GREETING** (Hi, Hello, Hey, Good morning, etc.):
   - Reply warmly and ask how you can help.
   - Example: "Hello! I'm AgriGPT. What crop or farming question can I help you with today?"

2. **If the message is a THANK YOU or GOODBYE** (Thanks, Bye, See you):
   - Reply politely.
   - Example: "You're welcome! Feel free to come back anytime."

3. **If the message is VAGUE** (missing crop name or specific issue):
   - Ask ONE simple clarifying question.
   - Example: User says "It's dying" -> You ask "I'm sorry to hear that! What crop is it, and what symptoms are you seeing?"
   - Example: User says "Yellow leaves" -> You ask "Which crop has yellow leaves?"

4. **If an IMAGE was uploaded but the message is vague**:
   - Acknowledge the image and ask for context.
   - Example: "I see you've uploaded an image. Could you tell me what crop this is so I can give you accurate advice?"

5. **If the message + history is CLEAR** (you know the crop AND the issue):
   - Just output the word: PASS
   - This tells the system to route to the expert agents.
   - Example: "How do I treat aphids on tomatoes?" -> PASS
   - Example: "How do I water them?" (History mentions tomatoes) -> PASS

=== OUTPUT ===
Either:
- A friendly clarifying question or greeting (1-2 sentences max)
- OR the word "PASS" if the query is clear enough for experts
"""

        try:
            response = query_groq_text(prompt)
            response = response.strip()
        except Exception:
            return "I'm having a bit of trouble. Could you tell me more about the crop and issue you're facing?"

        
        if response.upper() == "PASS":
            return "Got it! Let me connect you with the right expert. If you don't get a helpful answer, try rephrasing your question with more details."
            
        return self.respond_and_record(clean_query, response, image_path)
