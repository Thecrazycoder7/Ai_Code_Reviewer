


# from dotenv import load_dotenv
# import os
# from langchain_groq import ChatGroq
# from langchain_core.messages import HumanMessage

# # Load .env file
load_dotenv()

# # Verify key is loaded
# api_key = os.getenv("GROQ_API_KEY")

# llm = ChatGroq(
#     model="llama-3.1-8b-instant",
#     temperature=0.3,
#     api_key=api_key
# )

# response = llm.invoke([
#     HumanMessage(content="What is data scientist. Explain step by step.")
# ])

# print(response.content)


# from langchain_groq import ChatGroq
# from langchain_core.messages import HumanMessage

# llm = ChatGroq(
#     model="llama-3.1-8b-instant",
#     temperature=0.3,
# )

# response = llm.invoke([
#     HumanMessage(content="What is data scientist. Explain step by step.")
# ])

# print(response.content)



# import streamlit as st
# from dotenv import load_dotenv
# import os
# from langchain_groq import ChatGroq
# from langchain_core.messages import HumanMessage

# # Load .env file
# load_dotenv()

# # Get API key
# api_key = os.getenv("GROQ_API_KEY")

# st.title("Groq LLM Test (LangChain + Streamlit)")

# if not api_key:
#     st.error("GROQ_API_KEY not found. Please set it in your .env file.")
# else:
#     llm = ChatGroq(
#         model="openai/gpt-oss-120b",
#         temperature=0.3,
#         api_key=api_key
#     )

#     # ✅ Single-line input box
#     user_input = st.text_area(
#         "Enter your prompt:",
#         value="What is a data scientist? Explain step by step."
#     )

#     if st.button("Run LLM"):
#         if not user_input.strip():
#             st.warning("Please enter a prompt.")
#         else:
#             with st.spinner("Thinking..."):
#                 response = llm.invoke([
#                     HumanMessage(content=user_input)
#                 ])

#             st.subheader("Response:")
#             st.write(response.content)



# from groq import Groq

# client = Groq()
# completion = client.chat.completions.create(
#     model="openai/gpt-oss-120b",
#     messages=[
#       {
#         "role": "user",
#         "content": ""
#       }
#     ],
#     temperature=1,
#     max_completion_tokens=8192,
#     top_p=1,
#     reasoning_effort="medium",
#     stream=True,
#     stop=None
# )

# for chunk in completion:
#     print(chunk.choices[0].delta.content or "", end="")
