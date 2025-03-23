import pandas as pd
import chainlit as cl
import os
from dotenv import load_dotenv
from pandasai import SmartDataframe
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from utils import extract_image_path

is_pandas = True
# Load environment variables
load_dotenv()

gemini_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")


@cl.step(type="tool")
async def tool():
    # Simulate a running task
    await cl.sleep(2)

    return "Response from the tool!"


@cl.on_chat_start
async def on_chat_start():
    # Set initial message history
    cl.user_session.set(
        "message_history",
        [{"role": "system",
          "content": "You are a helpful assistant. Provide Greeting if user sent Greetings. Don't answer anything else than data provied."}],
    )

    files = None

    # Wait for the user to upload a file
    while files is None:
        files = await cl.AskFileMessage(
            content="Please upload a CSV/Excel file to begin!",
            accept=["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.ms-excel"],
            max_size_mb=20,
            timeout=180,
            max_files=1,
        ).send()

    # Assuming `file` is the uploaded file object
    file = files[0]

    # Send a message indicating the processing of the file
    msg = cl.Message(content=f"Processing `{file.name}`...", author="AnalytiChat")
    await msg.send()

    # Check file extension or MIME type to determine the type
    file_extension = os.path.splitext(file.name)[1].lower()

    if file_extension == ".csv":
        # If the file is CSV, load it with pd.read_csv
        df = pd.read_csv(file.path)
    elif file_extension in [".xls", ".xlsx"]:
        # If the file is Excel, load it with pd.read_excel
        df = pd.read_excel(file.path)
    else:
        # If the file type is unsupported, handle the case (optional)
        msg = cl.Message(content=f"Unsupported file type: `{file.name}`.", author="AnalytiChat")
        await msg.send()
        return

    global smart_df
    if is_pandas:
        smart_df = SmartDataframe(df, config={"llm": gemini_llm})
        print("Using PandasAI")
    else:
        smart_df = create_pandas_dataframe_agent(gemini_llm, df, verbose=False,
                                                 allow_dangerous_code=False,
                                                 agent_executor_kwargs={
                                                     'handle_parsing_errors': True
                                                 })
        print("Using Langchain Agent")

    print("Smart Dataframe loaded!!")

    elements = [cl.Dataframe(data=df.head(), display="inline", name="Dataframe")]
    await cl.Message(content="This message has a Dataframe", elements=elements, author="AnalytiChat").send()
    await cl.Message(content="You can ask me now a question about your data.", author="AnalytiChat").send()


@cl.on_message
async def on_message(message: cl.Message):
    # Retrieve message history
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    # # Call the tool
    # tool_res = await tool()
    # print(tool_res)

    question = message.content

    if is_pandas:
        response = smart_df.chat(question)
    else:
        response = smart_df.invoke(question)['output']

    image_path = extract_image_path(response)

    if image_path:
        # Display the image in Chainlit
        try:
            image = cl.Image(path=image_path, name="Generated Image", display="inline")
            await cl.Message(content="Here is your Metrics image", elements=[image]).send()
        except FileNotFoundError:
            await cl.Message(content=f"Could not generate an metric as you asked.",
                             author="AnalytiChat").send()

        except Exception as e:
            await cl.Message(content=f"An error occured while displaying image: {e}", author="AnalytiChat").send()

    else:
        # Display the response as usual
        msg = cl.Message(content=response, author="AnalytiChat")
        await msg.send()

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()
